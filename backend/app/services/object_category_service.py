from sqlalchemy import select, func
from app.extensions import db
from app.models.object_category import ObjectCategory
from app.models.object_type import ObjectType
from app.models.object_lost import ObjectLost
from app.common.constants import DISPONIBLE
from app.common.errors import AppError
from app.common.normalization import normalize_name
from app.common.pagination import paginate
from app.common.dates import utc_now
from app.services.audit_service import add_audit_log, snapshot, only_changes


def get_categories_by_filter(filters, page, page_size):
    query = select(ObjectCategory)
    if filters.get("id") is not None:
        query = query.where(ObjectCategory.id == filters["id"])
    if filters.get("name"):
        query = query.where(ObjectCategory.normalized_name.contains(normalize_name(filters["name"]), autoescape=True))
    if filters.get("is_active") is not None:
        query = query.where(ObjectCategory.is_active == filters["is_active"])
    query = query.order_by(ObjectCategory.name, ObjectCategory.id)
    return paginate(query, page, page_size)


def get_category_by_id(category_id, lock=False):
    query = select(ObjectCategory).where(ObjectCategory.id == category_id)
    if lock:
        query = query.with_for_update().execution_options(populate_existing=True)
    category = db.session.execute(query).scalar_one_or_none()
    if category is None:
        raise AppError("Categoría no encontrada.", 404)
    return category


def check_duplicate_name(normalized, current_id=None):
    query = select(ObjectCategory).where(ObjectCategory.normalized_name == normalized)
    if current_id is not None:
        query = query.where(ObjectCategory.id != current_id)
    existing = db.session.execute(query).scalar_one_or_none()
    if existing:
        raise AppError(f'Ya existe una categoría con ese nombre: "{existing.name}".', 409)


def create_category(name, actor):
    normalized = normalize_name(name)
    check_duplicate_name(normalized)
    category = ObjectCategory(name=name, normalized_name=normalized, created_by=actor.id, updated_by=actor.id)
    db.session.add(category)
    db.session.flush()
    add_audit_log("object_category", category.id, "CREATE", actor.id, after=snapshot(category))
    db.session.commit()
    return category


def update_category(category_id, name, reason, actor):
    category = get_category_by_id(category_id)
    if not category.is_active:
        raise AppError("No se puede editar una categoría inactiva.", 409)
    before = snapshot(category)
    normalized = normalize_name(name)
    check_duplicate_name(normalized, category.id)
    category.name = name
    category.normalized_name = normalized
    category.updated_by = actor.id
    db.session.flush()
    changes_before, changes_after = only_changes(before, snapshot(category))
    add_audit_log("object_category", category.id, "UPDATE", actor.id, reason, changes_before, changes_after)
    db.session.commit()
    return category


def inactivate_category(category_id, reason, actor):
    category = get_category_by_id(category_id, lock=True)
    if not category.is_active:
        raise AppError("La categoría ya está inactiva.", 409)
    available_objects = db.session.execute(
        select(func.count(ObjectLost.id))
        .join(ObjectType, ObjectLost.object_type_id == ObjectType.id)
        .where(
            ObjectType.category_id == category.id,
            ObjectLost.is_active.is_(True),
            ObjectLost.status == DISPONIBLE
        )
    ).scalar_one()
    if available_objects > 0:
        raise AppError(
            f"No se puede inactivar la categoría: {available_objects} objeto(s) activo(s) "
            f"DISPONIBLE(S) son de tipos de esta categoría.", 409
        )
    before = snapshot(category)
    category.is_active = False
    category.inactivated_at = utc_now()
    category.inactivated_by = actor.id
    category.inactivation_reason = reason
    category.updated_by = actor.id
    db.session.flush()
    add_audit_log("object_category", category.id, "INACTIVATE", actor.id, reason, before, snapshot(category))
    db.session.commit()
    return category


def reactivate_category(category_id, reason, actor):
    category = get_category_by_id(category_id, lock=True)
    if category.is_active:
        raise AppError("La categoría ya está activa.", 409)
    before = snapshot(category)
    category.is_active = True
    category.inactivated_at = None
    category.inactivated_by = None
    category.inactivation_reason = None
    category.updated_by = actor.id
    db.session.flush()
    add_audit_log("object_category", category.id, "REACTIVATE", actor.id, reason, before, snapshot(category))
    db.session.commit()
    return category
