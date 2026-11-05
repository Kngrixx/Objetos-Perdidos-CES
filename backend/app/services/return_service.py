from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from app.extensions import db
from app.models.return_record import ReturnRecord
from app.models.claim import Claim
from app.common.constants import DEVUELTO, ACEPTADA, RECEIPT_METHOD
from app.common.errors import AppError
from app.common.pagination import paginate
from app.common.dates import bogota_text, bogota_now_text
from app.services.audit_service import add_audit_log, snapshot
from app.services.object_lost_service import get_object_by_id


def get_returns_by_filter(filters, page, page_size):
    query = select(ReturnRecord)
    if filters.get("id") is not None:
        query = query.where(ReturnRecord.id == filters["id"])
    if filters.get("object_lost_id") is not None:
        query = query.where(ReturnRecord.object_lost_id == filters["object_lost_id"])
    if filters.get("claim_id") is not None:
        query = query.where(ReturnRecord.claim_id == filters["claim_id"])
    if filters.get("owner_person_id") is not None:
        query = query.where(ReturnRecord.owner_person_id == filters["owner_person_id"])
    if filters.get("start"):
        query = query.where(ReturnRecord.returned_at >= filters["start"])
    if filters.get("end"):
        query = query.where(ReturnRecord.returned_at < filters["end"])
    query = query.order_by(ReturnRecord.returned_at.desc(), ReturnRecord.id.desc())
    return paginate(query, page, page_size)


def get_return_by_id(return_id):
    record = db.session.get(ReturnRecord, return_id)
    if record is None:
        raise AppError("Devolución no encontrada.", 404)
    return record


def create_return(data, actor):
    """Devolución al propietario en UNA transacción.

    Control de concurrencia en dos capas:
      1. SELECT ... FOR UPDATE sobre el objeto: la segunda petición espera a la primera
         y, al continuar, ya ve el objeto DEVUELTO -> 409 claro.
      2. UNIQUE en return_records.object_lost_id y claim_id: garantía de la base de datos
         aunque algún camino de código olvidara el bloqueo.
    """
    claim = db.session.get(Claim, data["claim_id"])
    if claim is None:
        raise AppError("La reclamación indicada no existe.", 400)
    if data.get("object_lost_id") is not None and data["object_lost_id"] != claim.object_lost_id:
        raise AppError("La reclamación no corresponde al objeto indicado.", 400)

    object_lost = get_object_by_id(claim.object_lost_id, lock=True)
    db.session.refresh(claim, with_for_update=True)

    if not object_lost.is_active:
        raise AppError("El objeto está inactivo: no se puede devolver.", 409)
    if object_lost.status == DEVUELTO:
        raise AppError("El objeto ya fue devuelto. No se permite una segunda devolución.", 409)
    if not claim.is_active or claim.status != ACEPTADA:
        raise AppError("La devolución exige una reclamación ACEPTADA y activa para este objeto.", 409)
    if data.get("owner_confirmation") is not True:
        raise AppError("Debe registrarse la confirmación de recepción del propietario "
                       "(owner_confirmation = true).", 400)

    object_before = snapshot(object_lost)
    record = ReturnRecord(
        object_lost_id=object_lost.id,
        claim_id=claim.id,
        owner_person_id=claim.claimant_person_id,  # el propietario es quien acreditó pertenencia
        delivered_by_user_id=actor.id,             # siempre del JWT
        receipt_reference="CONST-" + object_lost.code.replace("OBJ-", ""),
        receipt_method=RECEIPT_METHOD,
        owner_confirmation=True,
        verification_summary=data["verification_summary"],
        notes=data.get("notes")
    )
    db.session.add(record)

    object_lost.status = DEVUELTO
    object_lost.version = object_lost.version + 1
    object_lost.updated_by = actor.id
    try:
        db.session.flush()
    except IntegrityError:
        db.session.rollback()
        raise AppError("El objeto ya tiene una devolución registrada.", 409)

    add_audit_log("return_record", record.id, "CREATE", actor.id, after=snapshot(record))
    add_audit_log("object_lost", object_lost.id, "RETURN", actor.id, "Devolución al propietario",
                  {"status": object_before["status"], "version": object_before["version"]},
                  {"status": object_lost.status, "version": object_lost.version})
    db.session.commit()
    return record


def get_receipt_data(return_id):
    record = get_return_by_id(return_id)
    object_lost = record.object_lost
    return {
        "receipt_reference": record.receipt_reference,
        "code": object_lost.code,
        "object_type": object_lost.object_type.name,
        "category": object_lost.object_type.category.name,
        "description": object_lost.description,
        "owner_name": record.owner.full_name,
        "owner_identification": record.owner.identification,
        "delivered_by": record.delivered_by.full_name,
        "returned_at": bogota_text(record.returned_at) + " (hora de Bogotá)",
        "claim_id": record.claim_id,
        "verification_summary": record.verification_summary,
        "generated_at": bogota_now_text(),
    }


def get_return_by_object(object_id):
    return db.session.execute(
        select(ReturnRecord).where(ReturnRecord.object_lost_id == object_id)
    ).scalar_one_or_none()
