from sqlalchemy import select, or_, text
from sqlalchemy.orm import aliased, selectinload
from app.extensions import db
from app.models.object_lost import ObjectLost
from app.models.object_photo import ObjectPhoto
from app.models.object_type import ObjectType
from app.models.block import Block
from app.models.person import Person
from app.models.department import Department
from app.common.constants import DISPONIBLE, DEVUELTO
from app.common.errors import AppError
from app.common.files import read_photo_files, save_photo, discard_uncommitted_files
from app.common.pagination import paginate
from app.common.dates import utc_now
from app.services.audit_service import add_audit_log, snapshot, only_changes

# Lista explícita de campos editables (cualquier otro se rechaza en el controller).
EDITABLE_FIELDS = [
    "object_type_id", "description", "found_block_id", "found_location", "found_at",
    "custody_block_id", "custody_location", "finder_person_id", "finder_department_id",
]
# Corrección administrativa de un DEVUELTO: no toca propietario, devolución ni estado.
CORRECTION_FIELDS = [
    "object_type_id", "description", "found_block_id", "found_location", "found_at",
    "custody_block_id", "custody_location",
]


# ------------------------------------------------------------------ consultas (getByFilter)

def build_object_query(filters):
    """Una sola consulta con filtros combinables (sin duplicar rutas por cada filtro).
    La usan el listado de objetos, el inventario, la exportación PDF y el dashboard."""
    found_block = aliased(Block)
    query = (
        select(ObjectLost)
        .join(ObjectType, ObjectLost.object_type_id == ObjectType.id)
        .join(found_block, ObjectLost.found_block_id == found_block.id)
        .options(selectinload(ObjectLost.photos))
    )
    if filters.get("id") is not None:
        query = query.where(ObjectLost.id == filters["id"])
    if filters.get("code"):
        query = query.where(ObjectLost.code.ilike(f'%{filters["code"]}%'))
    if filters.get("object_type_id") is not None:
        query = query.where(ObjectLost.object_type_id == filters["object_type_id"])
    if filters.get("category_id") is not None:
        query = query.where(ObjectType.category_id == filters["category_id"])
    if filters.get("campus_id") is not None:
        query = query.where(found_block.campus_id == filters["campus_id"])
    if filters.get("block_id") is not None:
        query = query.where(ObjectLost.found_block_id == filters["block_id"])
    if filters.get("status"):
        query = query.where(ObjectLost.status == filters["status"])
    if filters.get("is_active") is not None:
        query = query.where(ObjectLost.is_active == filters["is_active"])
    if filters.get("start"):
        query = query.where(ObjectLost.received_at >= filters["start"])
    if filters.get("end"):
        query = query.where(ObjectLost.received_at < filters["end"])  # fin exclusivo
    if filters.get("text"):
        pattern = f'%{filters["text"]}%'
        conditions = [ObjectLost.code.ilike(pattern), ObjectType.name.ilike(pattern)]
        if not filters.get("public_text_only"):
            conditions.append(ObjectLost.description.ilike(pattern))
        query = query.where(or_(*conditions))
    # Orden estable: por fecha de recepción y, si empatan, por id.
    return query.order_by(ObjectLost.received_at.desc(), ObjectLost.id.desc())


def get_objects_by_filter(filters, page, page_size):
    return paginate(build_object_query(filters), page, page_size)


def get_object_by_id(object_id, lock=False):
    query = select(ObjectLost).where(ObjectLost.id == object_id)
    if lock:
        query = query.with_for_update().execution_options(populate_existing=True)
    object_lost = db.session.execute(query).scalar_one_or_none()
    if object_lost is None:
        raise AppError("Objeto no encontrado.", 404)
    return object_lost


# ------------------------------------------------------------------ validación de referencias
# Para nuevos registros no se aceptan referencias inexistentes ni catálogos inactivos (400).
# Las filas se leen con FOR SHARE: nadie puede inactivarlas mientras se guarda el objeto.

def get_valid_object_type(object_type_id):
    object_type = db.session.execute(
        select(ObjectType).where(ObjectType.id == object_type_id).with_for_update(read=True)
    ).scalar_one_or_none()
    if object_type is None:
        raise AppError("El tipo de objeto indicado no existe.", 400)
    if not object_type.is_active or not object_type.category.is_active:
        raise AppError("El tipo de objeto indicado (o su categoría) está inactivo.", 400)
    return object_type


def get_valid_block(block_id, campus_id, label):
    block = db.session.execute(
        select(Block).where(Block.id == block_id).with_for_update(read=True)
    ).scalar_one_or_none()
    if block is None:
        raise AppError(f"El bloque {label} no existe.", 400)
    if campus_id is not None and block.campus_id != campus_id:
        raise AppError(f"El bloque {label} no pertenece a la sede seleccionada.", 400)
    if not block.is_active or not block.campus.is_active:
        raise AppError(f"El bloque {label} (o su sede) está inactivo.", 400)
    return block


def get_valid_person(person_id):
    person = db.session.execute(
        select(Person).where(Person.id == person_id).with_for_update(read=True)
    ).scalar_one_or_none()
    if person is None:
        raise AppError("La persona que entrega no existe.", 400)
    if not person.is_active:
        raise AppError("La persona que entrega está inactiva.", 400)
    return person


def get_valid_department(department_id):
    if department_id is None:
        return None
    department = db.session.get(Department, department_id)
    if department is None:
        raise AppError("La dependencia indicada no existe.", 400)
    if not department.is_active:
        raise AppError("La dependencia indicada está inactiva.", 400)
    return department


def check_found_at(found_at, received_at):
    if found_at > utc_now():
        raise AppError("La fecha de hallazgo no puede ser futura.", 400)
    if found_at > received_at:
        raise AppError("La fecha de hallazgo no puede ser posterior a la recepción.", 400)


def check_version(object_lost, version):
    if version != object_lost.version:
        raise AppError(
            f"El objeto fue modificado por otra persona (versión actual {object_lost.version}). "
            f"Recargue los datos e intente de nuevo.", 409,
            {"current_version": object_lost.version}
        )


# ------------------------------------------------------------------ recepción

def next_object_code():
    """Toma el siguiente id de la secuencia de PostgreSQL para armar el código OBJ-000015."""
    next_id = db.session.execute(
        text("SELECT nextval(pg_get_serial_sequence('object_lost', 'id'))")
    ).scalar_one()
    return next_id, f"OBJ-{next_id:06d}"


def create_object(data, files, actor, simulate_failure=False):
    object_type = get_valid_object_type(data["object_type_id"])
    found_block = get_valid_block(data["found_block_id"], data.get("found_campus_id"), "de hallazgo")
    custody_block = get_valid_block(data["custody_block_id"], data.get("custody_campus_id"), "de custodia")
    finder = get_valid_person(data["finder_person_id"])
    # Dependencia declarada por quien entrega; si no se envía, se usa la de la persona.
    department_id = data.get("finder_department_id") or finder.department_id
    get_valid_department(department_id)

    received_at = utc_now()
    check_found_at(data["found_at"], received_at)

    # Las fotos se validan ANTES de escribir cualquier archivo.
    photos = read_photo_files(files)

    object_id, code = next_object_code()
    object_lost = ObjectLost(
        id=object_id,
        code=code,
        object_type_id=object_type.id,
        description=data["description"],
        found_block_id=found_block.id,
        found_location=data["found_location"],
        found_at=data["found_at"],
        custody_block_id=custody_block.id,
        custody_location=data["custody_location"],
        finder_person_id=finder.id,
        finder_department_id=department_id,
        received_by_user_id=actor.id,  # siempre del JWT, nunca del cliente
        received_at=received_at,
        status=DISPONIBLE,
        is_active=True,
        version=1,
        created_by=actor.id,
        updated_by=actor.id
    )
    db.session.add(object_lost)

    # Recepción atómica: objeto + fotos + auditoría en una sola transacción.
    # Si falla una foto, se hace rollback y se retiran los archivos ya escritos (compensación).
    saved_keys = []
    try:
        db.session.flush()
        for index, (content, mime_type) in enumerate(photos):
            if simulate_failure and index == len(photos) - 1:
                raise OSError("Fallo de almacenamiento simulado (PA10)")
            storage_key = save_photo(content, mime_type)
            saved_keys.append(storage_key)
            db.session.add(ObjectPhoto(
                object_lost_id=object_lost.id,
                storage_key=storage_key,
                mime_type=mime_type,
                size_bytes=len(content),
                uploaded_by_user_id=actor.id,
                updated_by=actor.id
            ))
        db.session.flush()
        add_audit_log("object_lost", object_lost.id, "CREATE", actor.id, after=snapshot(object_lost))
        for photo in db.session.execute(
            select(ObjectPhoto).where(ObjectPhoto.object_lost_id == object_lost.id)
        ).scalars():
            add_audit_log("object_photo", photo.id, "CREATE", actor.id, after=snapshot(photo))
        db.session.commit()
    except Exception as error:
        db.session.rollback()
        discard_uncommitted_files(saved_keys)
        if isinstance(error, OSError):
            raise AppError(
                "No se pudo guardar una fotografía. La recepción NO se registró; intente de nuevo.", 500
            )
        raise
    return object_lost


# ------------------------------------------------------------------ edición y estados

def apply_changes(object_lost, data, campus_ids):
    if "object_type_id" in data and data["object_type_id"] != object_lost.object_type_id:
        object_lost.object_type_id = get_valid_object_type(data["object_type_id"]).id
    if "found_block_id" in data and (data["found_block_id"] != object_lost.found_block_id
                                     or campus_ids.get("found_campus_id") is not None):
        object_lost.found_block_id = get_valid_block(
            data["found_block_id"], campus_ids.get("found_campus_id"), "de hallazgo").id
    if "custody_block_id" in data and (data["custody_block_id"] != object_lost.custody_block_id
                                       or campus_ids.get("custody_campus_id") is not None):
        object_lost.custody_block_id = get_valid_block(
            data["custody_block_id"], campus_ids.get("custody_campus_id"), "de custodia").id
    if "finder_person_id" in data and data["finder_person_id"] != object_lost.finder_person_id:
        object_lost.finder_person_id = get_valid_person(data["finder_person_id"]).id
    if "finder_department_id" in data and data["finder_department_id"] != object_lost.finder_department_id:
        get_valid_department(data["finder_department_id"])
        object_lost.finder_department_id = data["finder_department_id"]
    if "found_at" in data:
        check_found_at(data["found_at"], object_lost.received_at)
        object_lost.found_at = data["found_at"]
    for field in ["description", "found_location", "custody_location"]:
        if field in data:
            setattr(object_lost, field, data[field])


def update_object(object_id, data, campus_ids, version, reason, actor):
    object_lost = get_object_by_id(object_id, lock=True)
    if not object_lost.is_active:
        raise AppError("El objeto está inactivo: no se puede editar.", 409)
    if object_lost.status == DEVUELTO:
        raise AppError("El objeto ya fue devuelto: no admite edición ordinaria "
                       "(solo corrección administrativa de un ADMIN).", 409)
    check_version(object_lost, version)

    before = snapshot(object_lost)
    apply_changes(object_lost, data, campus_ids)
    object_lost.version = object_lost.version + 1
    object_lost.correction_reason = reason
    object_lost.updated_by = actor.id
    db.session.flush()
    changes_before, changes_after = only_changes(before, snapshot(object_lost))
    add_audit_log("object_lost", object_lost.id, "UPDATE", actor.id, reason, changes_before, changes_after)
    db.session.commit()
    return object_lost


def administrative_correction(object_id, data, campus_ids, version, reason, actor):
    object_lost = get_object_by_id(object_id, lock=True)
    if object_lost.status != DEVUELTO:
        raise AppError("La corrección administrativa solo aplica a objetos DEVUELTOS; "
                       "para objetos disponibles use la edición normal.", 409)
    check_version(object_lost, version)

    before = snapshot(object_lost)
    apply_changes(object_lost, data, campus_ids)
    # El estado, el propietario y la devolución no se tocan: nunca permite volver a devolver.
    object_lost.version = object_lost.version + 1
    object_lost.correction_reason = reason
    object_lost.updated_by = actor.id
    db.session.flush()
    changes_before, changes_after = only_changes(before, snapshot(object_lost))
    add_audit_log("object_lost", object_lost.id, "ADMIN_CORRECTION", actor.id, reason,
                  changes_before, changes_after)
    db.session.commit()
    return object_lost


def inactivate_object(object_id, reason, actor):
    object_lost = get_object_by_id(object_id, lock=True)
    if not object_lost.is_active:
        raise AppError("El objeto ya está inactivo.", 409)
    if object_lost.status == DEVUELTO:
        raise AppError("Un objeto DEVUELTO no se puede inactivar: es un registro histórico.", 409)

    before = snapshot(object_lost)
    object_lost.is_active = False
    object_lost.inactivated_at = utc_now()
    object_lost.inactivated_by = actor.id
    object_lost.inactivation_reason = reason
    object_lost.version = object_lost.version + 1
    object_lost.updated_by = actor.id
    db.session.flush()
    add_audit_log("object_lost", object_lost.id, "INACTIVATE", actor.id, reason, before, snapshot(object_lost))
    db.session.commit()
    return object_lost


def reactivate_object(object_id, reason, actor):
    object_lost = get_object_by_id(object_id, lock=True)
    if object_lost.is_active:
        raise AppError("El objeto ya está activo.", 409)

    # Reactivar exige referencias válidas (pero conserva el estado que tenía).
    problems = []
    if not object_lost.object_type.is_active or not object_lost.object_type.category.is_active:
        problems.append("el tipo de objeto o su categoría está inactivo")
    if not object_lost.found_block.is_active or not object_lost.found_block.campus.is_active:
        problems.append("el bloque de hallazgo o su sede está inactivo")
    if not object_lost.custody_block.is_active or not object_lost.custody_block.campus.is_active:
        problems.append("el bloque de custodia o su sede está inactivo")
    if not object_lost.finder_person.is_active:
        problems.append("la persona que entregó está inactiva")
    if object_lost.finder_department is not None and not object_lost.finder_department.is_active:
        problems.append("la dependencia está inactiva")
    if not any(photo.is_active for photo in object_lost.photos):
        problems.append("no tiene fotografías activas")
    if problems:
        raise AppError("No se puede reactivar: " + "; ".join(problems) + ".", 409)

    before = snapshot(object_lost)
    object_lost.is_active = True
    object_lost.inactivated_at = None
    object_lost.inactivated_by = None
    object_lost.inactivation_reason = None
    object_lost.version = object_lost.version + 1
    object_lost.updated_by = actor.id
    db.session.flush()
    add_audit_log("object_lost", object_lost.id, "REACTIVATE", actor.id, reason, before, snapshot(object_lost))
    db.session.commit()
    return object_lost
