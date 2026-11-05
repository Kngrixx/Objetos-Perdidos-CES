from datetime import date, datetime
from sqlalchemy import select, or_, and_
from app.extensions import db
from app.models.audit_log import AuditLog
from app.models.object_photo import ObjectPhoto
from app.models.claim import Claim
from app.models.return_record import ReturnRecord
from app.common.pagination import paginate

# La auditoría nunca guarda contraseñas, hashes de tokens ni archivos.
SENSITIVE_FIELDS = ["password_hash", "token_hash"]


def snapshot(record):
    """Copia de las columnas de un registro (para guardar el antes y el después)."""
    data = {}
    for column in record.__table__.columns:
        if column.name in SENSITIVE_FIELDS:
            continue
        value = getattr(record, column.name)
        if isinstance(value, (datetime, date)):
            value = value.isoformat()
        data[column.name] = value
    return data


def only_changes(before, after):
    """Deja solo los campos que cambiaron, para que el historial muestre antes/después claros."""
    ignored = ["updated_at"]
    changed = [key for key in after if before.get(key) != after.get(key) and key not in ignored]
    return {key: before.get(key) for key in changed}, {key: after.get(key) for key in changed}


def add_audit_log(entity, entity_id, action, actor_id, reason=None, before=None, after=None):
    """Agrega el registro a la MISMA transacción del cambio. No hace commit:
    el service que llama hace un solo commit para el cambio y su auditoría."""
    if before is not None and after is not None:
        before, after = only_changes(before, after)
    log = AuditLog(
        entity=entity,
        entity_id=entity_id,
        action=action,
        actor_user_id=actor_id,
        reason=reason,
        before_data=before,
        after_data=after
    )
    db.session.add(log)
    return log


def get_audit_logs_by_filter(filters, page, page_size):
    query = select(AuditLog)
    if filters.get("entity"):
        query = query.where(AuditLog.entity == filters["entity"])
    if filters.get("entity_id") is not None:
        query = query.where(AuditLog.entity_id == filters["entity_id"])
    if filters.get("actor_user_id") is not None:
        query = query.where(AuditLog.actor_user_id == filters["actor_user_id"])
    if filters.get("action"):
        query = query.where(AuditLog.action == filters["action"])
    if filters.get("start"):
        query = query.where(AuditLog.occurred_at >= filters["start"])
    if filters.get("end"):
        query = query.where(AuditLog.occurred_at < filters["end"])
    query = query.order_by(AuditLog.occurred_at.desc(), AuditLog.id.desc())
    return paginate(query, page, page_size)


def get_object_history(object_lost_id):
    """Historial operativo de un objeto: el objeto, sus fotos, sus reclamaciones y su devolución."""
    photo_ids = select(ObjectPhoto.id).where(ObjectPhoto.object_lost_id == object_lost_id)
    claim_ids = select(Claim.id).where(Claim.object_lost_id == object_lost_id)
    return_ids = select(ReturnRecord.id).where(ReturnRecord.object_lost_id == object_lost_id)

    query = select(AuditLog).where(or_(
        and_(AuditLog.entity == "object_lost", AuditLog.entity_id == object_lost_id),
        and_(AuditLog.entity == "object_photo", AuditLog.entity_id.in_(photo_ids)),
        and_(AuditLog.entity == "claim", AuditLog.entity_id.in_(claim_ids)),
        and_(AuditLog.entity == "return_record", AuditLog.entity_id.in_(return_ids)),
    )).order_by(AuditLog.occurred_at.asc(), AuditLog.id.asc())
    return db.session.execute(query).scalars().all()
