import io
from flask import request, send_file
from app.common.dates import to_iso, parse_date, bogota_day_range
from app.common.errors import AppError
from app.common.pagination import get_page_params
from app.common.pdf import build_receipt_pdf
from app.common.responses import success_response, page_data, list_message
from app.common.security import get_current_user
from app.common.validators import (
    get_json_data, require_fields, check_allowed_fields, clean_string, to_int, to_bool, arg_int
)
from app.services.return_service import (
    get_returns_by_filter,
    get_return_by_id,
    create_return,
    get_receipt_data
)


def return_to_dict(record):
    return {
        "id": record.id,
        "object_lost": {"id": record.object_lost.id, "code": record.object_lost.code,
                        "status": record.object_lost.status},
        "claim_id": record.claim_id,
        "owner": {"id": record.owner.id, "identification": record.owner.identification,
                  "full_name": record.owner.full_name},
        "delivered_by": {"id": record.delivered_by.id, "name": record.delivered_by.full_name},
        "returned_at": to_iso(record.returned_at),
        "receipt_reference": record.receipt_reference,
        "receipt_method": record.receipt_method,
        "owner_confirmation": record.owner_confirmation,
        "verification_summary": record.verification_summary,
        "notes": record.notes,
        "receipt_url": f"/api/returns/{record.id}/receipt",
    }


def list_returns_controller():
    page, page_size = get_page_params()
    date_from = parse_date(request.args.get("date_from"), "date_from")
    date_to = parse_date(request.args.get("date_to"), "date_to")
    start, end = bogota_day_range(date_from, date_to)
    filters = {
        "id": arg_int("id"),
        "object_lost_id": arg_int("object_lost_id"),
        "claim_id": arg_int("claim_id"),
        "owner_person_id": arg_int("owner_person_id"),
        "start": start,
        "end": end,
    }
    records, total = get_returns_by_filter(filters, page, page_size)
    items = [return_to_dict(record) for record in records]
    return success_response(list_message(total), page_data(items, page, page_size, total))


def get_return_controller(return_id):
    return success_response("Consulta exitosa.", return_to_dict(get_return_by_id(return_id)))


def create_return_controller():
    data = get_json_data()
    # owner_person_id y delivered_by_user_id NO se aceptan: salen de la reclamación y del JWT.
    check_allowed_fields(data, ["claim_id", "object_lost_id", "verification_summary",
                                "owner_confirmation", "notes"])
    require_fields(data, ["claim_id", "verification_summary", "owner_confirmation"])
    if to_bool(data.get("owner_confirmation"), "owner_confirmation") is not True:
        raise AppError("Debe registrarse la confirmación de recepción del propietario "
                       "(owner_confirmation = true).", 400)
    values = {
        "claim_id": to_int(data.get("claim_id"), "claim_id"),
        "object_lost_id": to_int(data.get("object_lost_id"), "object_lost_id"),
        "verification_summary": clean_string(data.get("verification_summary"), "verification_summary", 2000),
        "owner_confirmation": to_bool(data.get("owner_confirmation"), "owner_confirmation"),
        "notes": clean_string(data.get("notes"), "notes", 2000, required=False),
    }
    record = create_return(values, get_current_user())
    return success_response("Devolución registrada. El objeto quedó DEVUELTO.", return_to_dict(record), 201)


def receipt_controller(return_id):
    receipt = get_receipt_data(return_id)
    pdf_bytes = build_receipt_pdf(receipt)
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f'constancia_{receipt["receipt_reference"]}.pdf'
    )
