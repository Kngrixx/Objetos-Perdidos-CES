from sqlalchemy import select, func, or_
from app.extensions import db
from app.models.block import Block
from app.models.campus import Campus
from app.models.object_lost import ObjectLost
from app.common.constants import DISPONIBLE
from app.common.errors import AppError
from app.common.normalization import normalize_name
from app.common.pagination import paginate
from app.common.dates import utc_now
from app.services.audit_service import add_audit_log, snapshot, only_changes


def get_blocks_by_filter(filters, page, page_size):
    query = select(Block)
    if filters.get("id") is not None:
        query = query.where(Block.id == filters["id"])
    if filters.get("campus_id") is not None:
        query = query.where(Block.campus_id == filters["campus_id"])
    if filters.get("name"):
        query = query.where(Block.normalized_name.contains(normalize_name(filters["name"]), autoescape=True))
    if filters.get("is_active") is not None:
        query = query.where(Block.is_active == filters["is_active"])
    query = query.order_by(Block.campus_id, Block.name, Block.id)
    return paginate(query, page, page_size)


def get_block_by_id(block_id, lock=False):
    query = select(Block).where(Block.id == block_id)
    if lock:
        query = query.with_for_update().execution_options(populate_existing=True)
    block = db.session.execute(query).scalar_one_or_none()
    if block is None:
        raise AppError("Bloque no encontrado.", 404)
    return block


def check_duplicate_name(campus_id, normalized, current_id=None):
    query = select(Block).where(Block.campus_id == campus_id, Block.normalized_name == normalized)
    if current_id is not None:
        query = query.where(Block.id != current_id)
    existing = db.session.execute(query).scalar_one_or_none()
    if existing:
        raise AppError(f'Ya existe un bloque con ese nombre en la sede: "{existing.name}".', 409)


def create_block(campus_id, name, actor):
    # La sede se bloquea en modo compartido: nadie puede inactivarla mientras se crea el bloque.
    campus = db.session.execute(
        select(Campus).where(Campus.id == campus_id).with_for_update(read=True)
    ).scalar_one_or_none()
    if campus is None:
        raise AppError("La sede indicada no existe.", 400)
    if not campus.is_active:
        raise AppError("La sede indicada está inactiva.", 400)

    normalized = normalize_name(name)
    check_duplicate_name(campus.id, normalized)
    block = Block(campus_id=campus.id, name=name, normalized_name=normalized,
                  created_by=actor.id, updated_by=actor.id)
    db.session.add(block)
    db.session.flush()
    add_audit_log("block", block.id, "CREATE", actor.id, after=snapshot(block))
    db.session.commit()
    return block


def update_block(block_id, name, reason, actor):
    block = get_block_by_id(block_id)
    if not block.is_active:
        raise AppError("No se puede editar un bloque inactivo.", 409)
    before = snapshot(block)
    normalized = normalize_name(name)
    check_duplicate_name(block.campus_id, normalized, block.id)
    block.name = name
    block.normalized_name = normalized
    block.updated_by = actor.id
    db.session.flush()
    changes_before, changes_after = only_changes(before, snapshot(block))
    add_audit_log("block", block.id, "UPDATE", actor.id, reason, changes_before, changes_after)
    db.session.commit()
    return block


def inactivate_block(block_id, reason, actor):
    block = get_block_by_id(block_id, lock=True)
    if not block.is_active:
        raise AppError("El bloque ya está inactivo.", 409)
    available_objects = db.session.execute(
        select(func.count(ObjectLost.id)).where(
            or_(ObjectLost.found_block_id == block.id, ObjectLost.custody_block_id == block.id),
            ObjectLost.is_active.is_(True),
            ObjectLost.status == DISPONIBLE
        )
    ).scalar_one()
    if available_objects > 0:
        raise AppError(
            f"No se puede inactivar el bloque: {available_objects} objeto(s) activo(s) DISPONIBLE(S) "
            f"dependen de él (hallazgo o custodia).", 409
        )
    before = snapshot(block)
    block.is_active = False
    block.inactivated_at = utc_now()
    block.inactivated_by = actor.id
    block.inactivation_reason = reason
    block.updated_by = actor.id
    db.session.flush()
    add_audit_log("block", block.id, "INACTIVATE", actor.id, reason, before, snapshot(block))
    db.session.commit()
    return block


def reactivate_block(block_id, reason, actor):
    block = get_block_by_id(block_id, lock=True)
    if block.is_active:
        raise AppError("El bloque ya está activo.", 409)
    if not block.campus.is_active:
        raise AppError("No se puede reactivar el bloque: su sede está inactiva.", 409)
    before = snapshot(block)
    block.is_active = True
    block.inactivated_at = None
    block.inactivated_by = None
    block.inactivation_reason = None
    block.updated_by = actor.id
    db.session.flush()
    add_audit_log("block", block.id, "REACTIVATE", actor.id, reason, before, snapshot(block))
    db.session.commit()
    return block
