from sqlalchemy import select, func
from app.extensions import db
from app.models.campus import Campus
from app.models.block import Block
from app.common.errors import AppError
from app.common.normalization import normalize_name
from app.common.pagination import paginate
from app.common.dates import utc_now
from app.services.audit_service import add_audit_log, snapshot, only_changes


def get_campuses_by_filter(filters, page, page_size):
    query = select(Campus)
    if filters.get("id") is not None:
        query = query.where(Campus.id == filters["id"])
    if filters.get("name"):
        query = query.where(Campus.normalized_name.contains(normalize_name(filters["name"]), autoescape=True))
    if filters.get("is_active") is not None:
        query = query.where(Campus.is_active == filters["is_active"])
    query = query.order_by(Campus.name, Campus.id)
    return paginate(query, page, page_size)


def get_campus_by_id(campus_id, lock=False):
    query = select(Campus).where(Campus.id == campus_id)
    if lock:
        query = query.with_for_update().execution_options(populate_existing=True)
    campus = db.session.execute(query).scalar_one_or_none()
    if campus is None:
        raise AppError("Sede no encontrada.", 404)
    return campus


def check_duplicate_name(normalized, current_id=None):
    query = select(Campus).where(Campus.normalized_name == normalized)
    if current_id is not None:
        query = query.where(Campus.id != current_id)
    existing = db.session.execute(query).scalar_one_or_none()
    if existing:
        raise AppError(f'Ya existe una sede con ese nombre: "{existing.name}".', 409)


def create_campus(name, actor):
    normalized = normalize_name(name)
    check_duplicate_name(normalized)
    campus = Campus(name=name, normalized_name=normalized, created_by=actor.id, updated_by=actor.id)
    db.session.add(campus)
    db.session.flush()
    add_audit_log("campus", campus.id, "CREATE", actor.id, after=snapshot(campus))
    db.session.commit()
    return campus


def update_campus(campus_id, name, reason, actor):
    campus = get_campus_by_id(campus_id)
    if not campus.is_active:
        raise AppError("No se puede editar una sede inactiva.", 409)
    before = snapshot(campus)
    normalized = normalize_name(name)
    check_duplicate_name(normalized, campus.id)
    campus.name = name
    campus.normalized_name = normalized
    campus.updated_by = actor.id
    db.session.flush()
    changes_before, changes_after = only_changes(before, snapshot(campus))
    add_audit_log("campus", campus.id, "UPDATE", actor.id, reason, changes_before, changes_after)
    db.session.commit()
    return campus


def inactivate_campus(campus_id, reason, actor):
    campus = get_campus_by_id(campus_id, lock=True)
    if not campus.is_active:
        raise AppError("La sede ya está inactiva.", 409)
    active_blocks = db.session.execute(
        select(func.count(Block.id)).where(Block.campus_id == campus.id, Block.is_active.is_(True))
    ).scalar_one()
    if active_blocks > 0:
        raise AppError(
            f"No se puede inactivar la sede: tiene {active_blocks} bloque(s) activo(s). "
            f"Inactive primero sus bloques.", 409
        )
    before = snapshot(campus)
    campus.is_active = False
    campus.inactivated_at = utc_now()
    campus.inactivated_by = actor.id
    campus.inactivation_reason = reason
    campus.updated_by = actor.id
    db.session.flush()
    add_audit_log("campus", campus.id, "INACTIVATE", actor.id, reason, before, snapshot(campus))
    db.session.commit()
    return campus


def reactivate_campus(campus_id, reason, actor):
    campus = get_campus_by_id(campus_id, lock=True)
    if campus.is_active:
        raise AppError("La sede ya está activa.", 409)
    before = snapshot(campus)
    campus.is_active = True
    campus.inactivated_at = None
    campus.inactivated_by = None
    campus.inactivation_reason = None
    campus.updated_by = actor.id
    db.session.flush()
    add_audit_log("campus", campus.id, "REACTIVATE", actor.id, reason, before, snapshot(campus))
    db.session.commit()
    return campus
