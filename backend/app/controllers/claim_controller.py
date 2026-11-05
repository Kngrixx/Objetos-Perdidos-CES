from app.common.constants import CLAIM_STATUSES, ACEPTADA, RECHAZADA
from app.common.dates import to_iso
from app.common.errors import AppError
from app.common.pagination import get_page_params
from app.common.responses import success_response, page_data, list_message
from app.common.security import get_current_user
from app.common.validators import (
    get_json_data, require_fields, check_allowed_fields, clean_string, get_reason, to_int, to_bool,
    choice, arg_int, arg_bool, arg_text, arg_choice
)
from app.services.claim_service import (
    EDITABLE_FIELDS,
    get_claims_by_filter,
    get_claim_by_id,
    create_claim,
    update_claim,
    decide_claim,
    inactivate_claim,
    reactivate_claim
)


def claim_to_dict(claim):
    claimant = claim.claimant
    return {
        "id": claim.id,
        "object_lost": {"id": claim.object_lost.id, "code": claim.object_lost.code,
                        "status": claim.object_lost.status},
        "claimant": {"id": claimant.id, "identification": claimant.identification,
                     "full_name": claimant.full_name},
        "evidence": claim.evidence,
        "identity_verified": claim.identity_verified,
        "verification_notes": claim.verification_notes,
        "status": claim.status,
        "reviewed_by": {"id": claim.reviewer.id, "name": claim.reviewer.full_name} if claim.reviewer else None,
        "reviewed_at": to_iso(claim.reviewed_at),
        "decision_reason": claim.decision_reason,
        "correction_reason": claim.correction_reason,
        "is_active": claim.is_active,
        "created_at": to_iso(claim.created_at),
        "updated_at": to_iso(claim.updated_at),
        "inactivated_at": to_iso(claim.inactivated_at),
        "inactivation_reason": claim.inactivation_reason,
    }


def read_claim_fields(data):
    values = {}
    if "object_lost_id" in data:
        values["object_lost_id"] = to_int(data.get("object_lost_id"), "object_lost_id")
    if "claimant_person_id" in data:
        values["claimant_person_id"] = to_int(data.get("claimant_person_id"), "claimant_person_id")
    if "evidence" in data:
        values["evidence"] = clean_string(data.get("evidence"), "evidence", 2000)
    if "identity_verified" in data:
        values["identity_verified"] = bool(to_bool(data.get("identity_verified"), "identity_verified"))
    if "verification_notes" in data:
        values["verification_notes"] = clean_string(data.get("verification_notes"), "verification_notes",
                                                    2000, required=False)
    return values


def list_claims_controller():
    page, page_size = get_page_params()
    filters = {
        "id": arg_int("id"),
        "object_lost_id": arg_int("object_lost_id"),
        "code": arg_text("code"),
        "claimant_person_id": arg_int("claimant_person_id"),
        "status": arg_choice("status", CLAIM_STATUSES),
        "is_active": arg_bool("is_active"),
    }
    claims, total = get_claims_by_filter(filters, page, page_size)
    items = [claim_to_dict(claim) for claim in claims]
    return success_response(list_message(total), page_data(items, page, page_size, total))


def get_claim_controller(claim_id):
    return success_response("Consulta exitosa.", claim_to_dict(get_claim_by_id(claim_id)))


def create_claim_controller():
    data = get_json_data()
    check_allowed_fields(data, ["object_lost_id"] + EDITABLE_FIELDS)
    require_fields(data, ["object_lost_id", "claimant_person_id", "evidence"])
    claim = create_claim(read_claim_fields(data), get_current_user())
    return success_response("Reclamación registrada como PENDIENTE.", claim_to_dict(claim), 201)


def update_claim_controller(claim_id):
    data = get_json_data()
    check_allowed_fields(data, EDITABLE_FIELDS + ["reason"])
    reason = get_reason(data)
    changes = read_claim_fields(data)
    if not changes:
        raise AppError("No se envió ningún campo para modificar.", 400)
    claim = update_claim(claim_id, changes, reason, get_current_user())
    return success_response("Reclamación corregida correctamente.", claim_to_dict(claim))


def decide_claim_controller(claim_id):
    data = get_json_data()
    check_allowed_fields(data, ["decision", "reason"])
    require_fields(data, ["decision"])
    decision = choice(data.get("decision"), "decision", [ACEPTADA, RECHAZADA])
    reason = get_reason(data)
    claim = decide_claim(claim_id, decision, reason, get_current_user())
    if decision == ACEPTADA:
        message = "Reclamación ACEPTADA. Ya puede registrar la devolución."
    else:
        message = "Reclamación RECHAZADA. El objeto continúa DISPONIBLE."
    return success_response(message, claim_to_dict(claim))


def inactivate_claim_controller(claim_id):
    reason = get_reason(get_json_data())
    claim = inactivate_claim(claim_id, reason, get_current_user())
    return success_response("Reclamación inactivada correctamente.", claim_to_dict(claim))


def reactivate_claim_controller(claim_id):
    reason = get_reason(get_json_data())
    claim = reactivate_claim(claim_id, reason, get_current_user())
    return success_response("Reclamación reactivada correctamente.", claim_to_dict(claim))
