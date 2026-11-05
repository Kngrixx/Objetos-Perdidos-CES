from sqlalchemy import select, func
from app.extensions import db
from app.models.object_type import ObjectType
from app.models.object_category import ObjectCategory
from app.models.object_lost import ObjectLost
from app.common.constants import DISPONIBLE
from app.common.errors import AppError
from app.common.normalization import normalize_name
from app.common.pagination import paginate
from app.common.dates import utc_now
from app.services.audit_service import add_audit_log, snapshot, only_changes


def get_object_types_by_filter(filters, page, page_size):
    query = select(ObjectType).join(ObjectCategory, ObjectType.category_id == ObjectCategory.id)
    if filters.get("id") is not None:
        query = query.where(ObjectType.id == filters["id"])
    if filters.get("category_id") is not None:
        query = query.where(ObjectType.category_id == filters["category_id"])
    if filters.get("name"):
        query = query.where(ObjectType.normalized_name.contains(normalize_name(filters["name"]), autoescape=True))
    if filters.get("is_active") is not None:
        query = query.where(ObjectType.is_active == filters["is_active"])
    query = query.order_by(ObjectCategory.name, ObjectType.name, ObjectType.id)
    return paginate(query, page, page_size)


def get_object_type_by_id(object_type_id, lock=False):
    query = select(ObjectType).where(ObjectType.id == object_type_id)
    if lock:
        query = query.with_for_update().execution_options(populate_existing=True)
    object_type = db.session.execute(query).scalar_one_or_none()
    if object_type is None:
        raise AppError("Tipo de objeto no encontrado.", 404)
    return object_type


def get_active_category(category_id):
    category = db.session.execute(
        select(ObjectCategory).where(ObjectCategory.id == category_id).with_for_update(read=True)
    ).scalar_one_or_none()
    if category is None:
        raise AppError("La categoría indicada no existe.", 400)
    if not category.is_active:
        raise AppError("La categoría indicada está inactiva.", 400)
    return category


def check_duplicate_name(category_id, normalized, current_id=None):
    """Antes de crear se busca coincidencia normalizando espacios, mayúsculas y tildes."""
    query = select(ObjectType).where(
        ObjectType.category_id == category_id,
        ObjectType.normalized_name == normalized
    )
    if current_id is not None:
        query = query.where(ObjectType.id != current_id)
    existing = db.session.execute(query).scalar_one_or_none()
    if existing:
        raise AppError(
            f'Ya existe el tipo "{existing.name}" en esa categoría.', 409,
            {"existing_id": existing.id, "existing_name": existing.name, "is_active": existing.is_active}
        )


def create_object_type(category_id, name, actor):
    category = get_active_category(category_id)
    normalized = normalize_name(name)
    check_duplicate_name(category.id, normalized)
    object_type = ObjectType(category_id=category.id, name=name, normalized_name=normalized,
                             created_by=actor.id, updated_by=actor.id)
    db.session.add(object_type)
    db.session.flush()
    add_audit_log("object_type", object_type.id, "CREATE", actor.id, after=snapshot(object_type))
    db.session.commit()
    return object_type


def update_object_type(object_type_id, data, reason, actor):
    object_type = get_object_type_by_id(object_type_id)
    if not object_type.is_active:
        raise AppError("No se puede editar un tipo de objeto inactivo.", 409)
    before = snapshot(object_type)

    category_id = object_type.category_id
    if data.get("category_id") is not None and data["category_id"] != object_type.category_id:
        category_id = get_active_category(data["category_id"]).id
    name = data.get("name") or object_type.name
    normalized = normalize_name(name)
    check_duplicate_name(category_id, normalized, object_type.id)

    object_type.category_id = category_id
    object_type.name = name
    object_type.normalized_name = normalized
    object_type.updated_by = actor.id
    db.session.flush()
    changes_before, changes_after = only_changes(before, snapshot(object_type))
    add_audit_log("object_type", object_type.id, "UPDATE", actor.id, reason, changes_before, changes_after)
    db.session.commit()
    return object_type


def inactivate_object_type(object_type_id, reason, actor):
    object_type = get_object_type_by_id(object_type_id, lock=True)
    if not object_type.is_active:
        raise AppError("El tipo de objeto ya está inactivo.", 409)
    available_objects = db.session.execute(
        select(func.count(ObjectLost.id)).where(
            ObjectLost.object_type_id == object_type.id,
            ObjectLost.is_active.is_(True),
            ObjectLost.status == DISPONIBLE
        )
    ).scalar_one()
    if available_objects > 0:
        raise AppError(
            f"No se puede inactivar el tipo: {available_objects} objeto(s) activo(s) DISPONIBLE(S) lo usan.", 409
        )
    before = snapshot(object_type)
    object_type.is_active = False
    object_type.inactivated_at = utc_now()
    object_type.inactivated_by = actor.id
    object_type.inactivation_reason = reason
    object_type.updated_by = actor.id
    db.session.flush()
    add_audit_log("object_type", object_type.id, "INACTIVATE", actor.id, reason, before, snapshot(object_type))
    db.session.commit()
    return object_type


def reactivate_object_type(object_type_id, reason, actor):
    object_type = get_object_type_by_id(object_type_id, lock=True)
    if object_type.is_active:
        raise AppError("El tipo de objeto ya está activo.", 409)
    if not object_type.category.is_active:
        raise AppError("No se puede reactivar el tipo: su categoría está inactiva.", 409)
    before = snapshot(object_type)
    object_type.is_active = True
    object_type.inactivated_at = None
    object_type.inactivated_by = None
    object_type.inactivation_reason = None
    object_type.updated_by = actor.id
    db.session.flush()
    add_audit_log("object_type", object_type.id, "REACTIVATE", actor.id, reason, before, snapshot(object_type))
    db.session.commit()
    return object_type
