from sqlalchemy import select
from app.extensions import db
from app.models.claim import Claim
from app.models.object_lost import ObjectLost
from app.models.person import Person
from app.models.return_record import ReturnRecord
from app.common.constants import DISPONIBLE, PENDIENTE, ACEPTADA
from app.common.errors import AppError
from app.common.pagination import paginate
from app.common.dates import utc_now
from app.services.audit_service import add_audit_log, snapshot, only_changes
from app.services.object_lost_service import get_object_by_id

EDITABLE_FIELDS = ["claimant_person_id", "evidence", "identity_verified", "verification_notes"]


def get_claims_by_filter(filters, page, page_size):
    query = select(Claim).join(ObjectLost, Claim.object_lost_id == ObjectLost.id)
    if filters.get("id") is not None:
        query = query.where(Claim.id == filters["id"])
    if filters.get("object_lost_id") is not None:
        query = query.where(Claim.object_lost_id == filters["object_lost_id"])
    if filters.get("code"):
        query = query.where(ObjectLost.code.ilike(f'%{filters["code"]}%'))
    if filters.get("claimant_person_id") is not None:
        query = query.where(Claim.claimant_person_id == filters["claimant_person_id"])
    if filters.get("status"):
        query = query.where(Claim.status == filters["status"])
    if filters.get("is_active") is not None:
        query = query.where(Claim.is_active == filters["is_active"])
    query = query.order_by(Claim.created_at.desc(), Claim.id.desc())
    return paginate(query, page, page_size)


def get_claim_by_id(claim_id, lock=False):
    query = select(Claim).where(Claim.id == claim_id)
    if lock:
        query = query.with_for_update().execution_options(populate_existing=True)
    claim = db.session.execute(query).scalar_one_or_none()
    if claim is None:
        raise AppError("Reclamación no encontrada.", 404)
    return claim


def get_valid_claimant(person_id):
    person = db.session.get(Person, person_id)
    if person is None:
        raise AppError("La persona reclamante no existe.", 400)
    if not person.is_active:
        raise AppError("La persona reclamante está inactiva.", 400)
    return person


def check_object_available(object_lost):
    if not object_lost.is_active:
        raise AppError("El objeto está inactivo: no admite reclamaciones ni devolución.", 409)
    if object_lost.status != DISPONIBLE:
        raise AppError("El objeto ya fue devuelto.", 409)


def create_claim(data, actor):
    object_lost = db.session.get(ObjectLost, data["object_lost_id"])
    if object_lost is None:
        raise AppError("El objeto indicado no existe.", 400)
    check_object_available(object_lost)
    claimant = get_valid_claimant(data["claimant_person_id"])

    duplicate = db.session.execute(
        select(Claim).where(
            Claim.object_lost_id == object_lost.id,
            Claim.claimant_person_id == claimant.id,
            Claim.status == PENDIENTE,
            Claim.is_active.is_(True)
        )
    ).scalar_one_or_none()
    if duplicate:
        raise AppError("Esa persona ya tiene una reclamación PENDIENTE para este objeto.", 409,
                       {"existing_id": duplicate.id})

    claim = Claim(
        object_lost_id=object_lost.id,
        claimant_person_id=claimant.id,
        evidence=data["evidence"],
        identity_verified=data.get("identity_verified") or False,
        verification_notes=data.get("verification_notes"),
        status=PENDIENTE,
        created_by=actor.id,
        updated_by=actor.id
    )
    db.session.add(claim)
    db.session.flush()
    add_audit_log("claim", claim.id, "CREATE", actor.id, after=snapshot(claim))
    db.session.commit()
    return claim


def check_pending(claim):
    if not claim.is_active:
        raise AppError("La reclamación está inactiva.", 409)
    if claim.status != PENDIENTE:
        raise AppError(f"La reclamación ya fue decidida ({claim.status}); no se puede modificar.", 409)


def update_claim(claim_id, data, reason, actor):
    claim = get_claim_by_id(claim_id, lock=True)
    check_pending(claim)
    before = snapshot(claim)
    if "claimant_person_id" in data and data["claimant_person_id"] != claim.claimant_person_id:
        claim.claimant_person_id = get_valid_claimant(data["claimant_person_id"]).id
    for field in ["evidence", "identity_verified", "verification_notes"]:
        if field in data:
            setattr(claim, field, data[field])
    claim.correction_reason = reason
    claim.updated_by = actor.id
    db.session.flush()
    changes_before, changes_after = only_changes(before, snapshot(claim))
    add_audit_log("claim", claim.id, "UPDATE", actor.id, reason, changes_before, changes_after)
    db.session.commit()
    return claim


def decide_claim(claim_id, decision, reason, actor):
    claim = get_claim_by_id(claim_id)
    # Primero se bloquea el objeto y luego la reclamación (mismo orden que la devolución).
    object_lost = get_object_by_id(claim.object_lost_id, lock=True)
    claim = get_claim_by_id(claim_id, lock=True)
    check_pending(claim)

    if decision == ACEPTADA:
        check_object_available(object_lost)
        if not claim.identity_verified:
            raise AppError("Para aceptar, primero registre que la identificación del reclamante "
                           "fue verificada (identity_verified = true).", 400)
        accepted = db.session.execute(
            select(Claim).where(Claim.object_lost_id == object_lost.id, Claim.status == ACEPTADA)
        ).scalar_one_or_none()
        if accepted:
            raise AppError(f"El objeto ya tiene una reclamación ACEPTADA (#{accepted.id}).", 409)

    before = snapshot(claim)
    claim.status = decision
    claim.decision_reason = reason
    claim.reviewed_by = actor.id
    claim.reviewed_at = utc_now()
    claim.updated_by = actor.id
    db.session.flush()  # aquí actúa el índice único parcial si hubo una carrera
    add_audit_log("claim", claim.id, "DECISION_" + decision, actor.id, reason, before, snapshot(claim))
    db.session.commit()
    return claim


def inactivate_claim(claim_id, reason, actor):
    claim = get_claim_by_id(claim_id, lock=True)
    if not claim.is_active:
        raise AppError("La reclamación ya está inactiva.", 409)
    if claim.status != PENDIENTE:
        raise AppError("Solo se pueden inactivar reclamaciones PENDIENTES.", 409)
    has_return = db.session.execute(
        select(ReturnRecord.id).where(ReturnRecord.claim_id == claim.id)
    ).scalar_one_or_none()
    if has_return:
        raise AppError("La reclamación tiene una devolución asociada.", 409)

    before = snapshot(claim)
    claim.is_active = False
    claim.inactivated_at = utc_now()
    claim.inactivated_by = actor.id
    claim.inactivation_reason = reason
    claim.updated_by = actor.id
    db.session.flush()
    add_audit_log("claim", claim.id, "INACTIVATE", actor.id, reason, before, snapshot(claim))
    db.session.commit()
    return claim


def reactivate_claim(claim_id, reason, actor):
    claim = get_claim_by_id(claim_id, lock=True)
    if claim.is_active:
        raise AppError("La reclamación ya está activa.", 409)
    if claim.status != PENDIENTE:
        raise AppError("Solo se pueden reactivar reclamaciones PENDIENTES.", 409)
    check_object_available(claim.object_lost)

    before = snapshot(claim)
    claim.is_active = True
    claim.inactivated_at = None
    claim.inactivated_by = None
    claim.inactivation_reason = None
    claim.updated_by = actor.id
    db.session.flush()
    add_audit_log("claim", claim.id, "REACTIVATE", actor.id, reason, before, snapshot(claim))
    db.session.commit()
    return claim
