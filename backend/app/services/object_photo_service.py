import os
from sqlalchemy import select, func
from app.extensions import db
from app.models.object_photo import ObjectPhoto
from app.common.constants import DEVUELTO
from app.common.errors import AppError
from app.common.files import read_photo_files, save_photo, discard_uncommitted_files, photo_path
from app.common.dates import utc_now
from app.services.audit_service import add_audit_log, snapshot
from app.services.object_lost_service import get_object_by_id


def get_photos_by_object(object_id):
    get_object_by_id(object_id)  # 404 si el objeto no existe
    return db.session.execute(
        select(ObjectPhoto).where(ObjectPhoto.object_lost_id == object_id).order_by(ObjectPhoto.id)
    ).scalars().all()


def get_photo_by_id(photo_id):
    photo = db.session.get(ObjectPhoto, photo_id)
    if photo is None:
        raise AppError("Fotografía no encontrada.", 404)
    return photo


def count_active_photos(object_id):
    return db.session.execute(
        select(func.count(ObjectPhoto.id)).where(
            ObjectPhoto.object_lost_id == object_id,
            ObjectPhoto.is_active.is_(True)
        )
    ).scalar_one()


def check_object_editable(object_lost):
    if not object_lost.is_active:
        raise AppError("El objeto está inactivo: no se pueden modificar sus fotografías.", 409)
    if object_lost.status == DEVUELTO:
        raise AppError("El objeto ya fue devuelto: no se pueden modificar sus fotografías.", 409)


def add_photos(object_id, files, actor):
    # El objeto se bloquea para que dos cargas simultáneas no superen el máximo de 5.
    object_lost = get_object_by_id(object_id, lock=True)
    check_object_editable(object_lost)
    photos = read_photo_files(files, count_active_photos(object_lost.id))

    saved_keys = []
    new_photos = []
    try:
        for content, mime_type in photos:
            storage_key = save_photo(content, mime_type)
            saved_keys.append(storage_key)
            photo = ObjectPhoto(
                object_lost_id=object_lost.id,
                storage_key=storage_key,
                mime_type=mime_type,
                size_bytes=len(content),
                uploaded_by_user_id=actor.id,
                updated_by=actor.id
            )
            db.session.add(photo)
            new_photos.append(photo)
        db.session.flush()
        for photo in new_photos:
            add_audit_log("object_photo", photo.id, "CREATE", actor.id, after=snapshot(photo))
        db.session.commit()
    except Exception as error:
        db.session.rollback()
        discard_uncommitted_files(saved_keys)
        if isinstance(error, OSError):
            raise AppError("No se pudo guardar una fotografía; no se agregó ninguna.", 500)
        raise
    return new_photos


def get_photo_file(photo_id):
    photo = get_photo_by_id(photo_id)
    path = photo_path(photo.storage_key)
    if not os.path.exists(path):
        raise AppError("El archivo de la fotografía no está disponible en el almacenamiento.", 404)
    return photo, path


def inactivate_photo(photo_id, reason, actor):
    photo = get_photo_by_id(photo_id)
    # Se bloquea el objeto: dos inactivaciones simultáneas no pueden dejarlo sin fotos.
    object_lost = get_object_by_id(photo.object_lost_id, lock=True)
    check_object_editable(object_lost)
    db.session.refresh(photo)
    if not photo.is_active:
        raise AppError("La fotografía ya está inactiva.", 409)
    if count_active_photos(object_lost.id) <= 1:
        raise AppError("No se puede inactivar la última fotografía activa del objeto.", 409)

    before = snapshot(photo)
    photo.is_active = False
    photo.inactivated_at = utc_now()
    photo.inactivated_by = actor.id
    photo.inactivation_reason = reason
    photo.updated_by = actor.id
    db.session.flush()
    # El archivo NO se borra: se conserva junto con su metadata.
    add_audit_log("object_photo", photo.id, "INACTIVATE", actor.id, reason, before, snapshot(photo))
    db.session.commit()
    return photo


def reactivate_photo(photo_id, reason, actor):
    photo = get_photo_by_id(photo_id)
    object_lost = get_object_by_id(photo.object_lost_id, lock=True)
    check_object_editable(object_lost)
    db.session.refresh(photo)
    if photo.is_active:
        raise AppError("La fotografía ya está activa.", 409)
    if count_active_photos(object_lost.id) >= 5:
        raise AppError("El objeto ya tiene el máximo de 5 fotografías activas.", 409)

    before = snapshot(photo)
    photo.is_active = True
    photo.inactivated_at = None
    photo.inactivated_by = None
    photo.inactivation_reason = None
    photo.updated_by = actor.id
    db.session.flush()
    add_audit_log("object_photo", photo.id, "REACTIVATE", actor.id, reason, before, snapshot(photo))
    db.session.commit()
    return photo
