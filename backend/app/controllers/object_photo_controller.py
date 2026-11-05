from flask import request, send_file
from app.common.dates import to_iso
from app.common.responses import success_response
from app.common.security import get_current_user
from app.common.validators import get_json_data, get_reason
from app.services.object_photo_service import (
    get_photos_by_object,
    add_photos,
    get_photo_file,
    inactivate_photo,
    reactivate_photo
)


def photo_to_dict(photo):
    # No se expone el nombre interno del archivo: la foto se pide por su ruta autorizada.
    return {
        "id": photo.id,
        "object_lost_id": photo.object_lost_id,
        "mime_type": photo.mime_type,
        "size_bytes": photo.size_bytes,
        "uploaded_by": {"id": photo.uploaded_by.id, "name": photo.uploaded_by.full_name},
        "uploaded_at": to_iso(photo.uploaded_at),
        "is_active": photo.is_active,
        "inactivated_at": to_iso(photo.inactivated_at),
        "inactivation_reason": photo.inactivation_reason,
        "file_url": f"/api/object-photos/{photo.id}/file",
    }


def list_photos_controller(object_id):
    photos = get_photos_by_object(object_id)
    return success_response("Consulta exitosa.", [photo_to_dict(photo) for photo in photos])


def add_photos_controller(object_id):
    files = request.files.getlist("photos")
    photos = add_photos(object_id, files, get_current_user())
    return success_response("Fotografías agregadas correctamente.", [photo_to_dict(photo) for photo in photos], 201)


def photo_file_controller(photo_id):
    photo, path = get_photo_file(photo_id)
    return send_file(path, mimetype=photo.mime_type, max_age=0)


def inactivate_photo_controller(photo_id):
    reason = get_reason(get_json_data())
    photo = inactivate_photo(photo_id, reason, get_current_user())
    return success_response("Fotografía inactivada. El archivo y su metadata se conservan.", photo_to_dict(photo))


def reactivate_photo_controller(photo_id):
    reason = get_reason(get_json_data())
    photo = reactivate_photo(photo_id, reason, get_current_user())
    return success_response("Fotografía reactivada correctamente.", photo_to_dict(photo))
