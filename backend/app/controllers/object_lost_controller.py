from flask import request, current_app
from app.common.constants import CONSULTA, DISPONIBLE, OBJECT_STATUSES
from app.common.dates import to_iso, parse_date, parse_datetime, bogota_day_range
from app.common.errors import AppError
from app.common.pagination import get_page_params
from app.common.responses import success_response, page_data, list_message
from app.common.security import get_current_user, current_role
from app.common.validators import (
    get_json_data, require_fields, check_allowed_fields, clean_string, get_reason, to_int,
    is_blank, arg_int, arg_bool, arg_text, arg_choice
)
from app.services.object_lost_service import (
    EDITABLE_FIELDS,
    CORRECTION_FIELDS,
    get_objects_by_filter,
    get_object_by_id,
    create_object,
    update_object,
    administrative_correction,
    inactivate_object,
    reactivate_object
)
from app.services.return_service import get_return_by_object

REQUIRED_FIELDS = [
    "object_type_id", "description", "found_block_id", "found_location", "found_at",
    "custody_block_id", "custody_location", "finder_person_id",
]


# ------------------------------------------------------------------ serialización

def ref(record, name_field="name"):
    if record is None:
        return None
    return {"id": record.id, "name": getattr(record, name_field)}


def object_to_dict(object_lost):
    """Proyección completa (OPERADOR y ADMIN)."""
    active_photos = [photo for photo in object_lost.photos if photo.is_active]
    finder = object_lost.finder_person
    return {
        "id": object_lost.id,
        "code": object_lost.code,
        "object_type": ref(object_lost.object_type),
        "category": ref(object_lost.object_type.category),
        "description": object_lost.description,
        "found_campus": ref(object_lost.found_block.campus),
        "found_block": ref(object_lost.found_block),
        "found_location": object_lost.found_location,
        "found_at": to_iso(object_lost.found_at),
        "custody_campus": ref(object_lost.custody_block.campus),
        "custody_block": ref(object_lost.custody_block),
        "custody_location": object_lost.custody_location,
        "finder_person": {
            "id": finder.id,
            "identification": finder.identification,
            "full_name": finder.full_name,
            "affiliation_type": finder.affiliation_type,
        },
        "finder_department": ref(object_lost.finder_department),
        "received_by": ref(object_lost.received_by, "full_name"),
        "received_at": to_iso(object_lost.received_at),
        "status": object_lost.status,
        "is_active": object_lost.is_active,
        "version": object_lost.version,
        "correction_reason": object_lost.correction_reason,
        "inactivated_at": to_iso(object_lost.inactivated_at),
        "inactivation_reason": object_lost.inactivation_reason,
        "active_photos": len(active_photos),
        "cover_photo_id": active_photos[0].id if active_photos else None,
        "created_at": to_iso(object_lost.created_at),
        "updated_at": to_iso(object_lost.updated_at),
    }


def object_to_public_dict(object_lost):
    """Proyección reducida para CONSULTA: sin descripción, ubicaciones, personas,
    identificaciones, contactos ni fotos."""
    return {
        "id": object_lost.id,
        "code": object_lost.code,
        "object_type": ref(object_lost.object_type),
        "category": ref(object_lost.object_type.category),
        "campus": ref(object_lost.found_block.campus),
        "received_at": to_iso(object_lost.received_at),
        "status": object_lost.status,
    }


def object_detail_to_dict(object_lost):
    data = object_to_dict(object_lost)
    record = get_return_by_object(object_lost.id)
    data["return"] = None
    if record is not None:
        data["return"] = {
            "id": record.id,
            "receipt_reference": record.receipt_reference,
            "returned_at": to_iso(record.returned_at),
            "delivered_by": ref(record.delivered_by, "full_name"),
            "owner": {"id": record.owner.id, "full_name": record.owner.full_name,
                      "identification": record.owner.identification},
            "claim_id": record.claim_id,
        }
    return data


# ------------------------------------------------------------------ lectura de filtros

def read_object_filters():
    """getByFilter: todos los filtros por parámetros de consulta, combinables."""
    date_from = parse_date(request.args.get("date_from"), "date_from")
    date_to = parse_date(request.args.get("date_to"), "date_to")
    start, end = bogota_day_range(date_from, date_to)
    return {
        "id": arg_int("id"),
        "code": arg_text("code"),
        "object_type_id": arg_int("object_type_id"),
        "category_id": arg_int("category_id"),
        "campus_id": arg_int("campus_id"),
        "block_id": arg_int("block_id"),
        "status": arg_choice("status", OBJECT_STATUSES),
        "is_active": arg_bool("is_active"),
        "text": arg_text("text"),
        "start": start,
        "end": end,
    }


def read_object_changes(data, allowed_fields):
    """Convierte los campos editables recibidos en JSON (solo los que vienen)."""
    changes = {}
    campus_ids = {
        "found_campus_id": to_int(data.get("found_campus_id"), "found_campus_id"),
        "custody_campus_id": to_int(data.get("custody_campus_id"), "custody_campus_id"),
    }
    for field in allowed_fields:
        if field not in data:
            continue
        value = data.get(field)
        if field != "finder_department_id" and is_blank(value):
            raise AppError(f"El campo {field} no puede quedar vacío.", 400)
        if field.endswith("_id"):
            changes[field] = to_int(value, field)
        elif field == "found_at":
            changes[field] = parse_datetime(value, field)
        elif field == "description":
            changes[field] = clean_string(value, field, 2000)
        else:
            changes[field] = clean_string(value, field, 255)
    if not changes:
        raise AppError("No se envió ningún campo para modificar.", 400)
    return changes, campus_ids


def read_version(data):
    version = to_int(data.get("version"), "version")
    if version is None:
        raise AppError("El campo version es obligatorio (bloqueo optimista).", 400)
    return version


# ------------------------------------------------------------------ controladores

def list_objects_controller():
    page, page_size = get_page_params()
    filters = read_object_filters()
    serializer = object_to_dict
    if current_role() == CONSULTA:
        if filters["status"] not in (None, DISPONIBLE) or filters["is_active"] is False:
            raise AppError("El rol CONSULTA solo puede consultar objetos activos y DISPONIBLES.", 403)
        filters["status"] = DISPONIBLE
        filters["is_active"] = True
        filters["public_text_only"] = True
        serializer = object_to_public_dict
    objects, total = get_objects_by_filter(filters, page, page_size)
    items = [serializer(object_lost) for object_lost in objects]
    return success_response(list_message(total), page_data(items, page, page_size, total))


def get_object_controller(object_id):
    object_lost = get_object_by_id(object_id)
    if current_role() == CONSULTA:
        if not object_lost.is_active or object_lost.status != DISPONIBLE:
            raise AppError("Objeto no encontrado.", 404)
        return success_response("Consulta exitosa.", object_to_public_dict(object_lost))
    return success_response("Consulta exitosa.", object_detail_to_dict(object_lost))


def create_object_controller():
    form = request.form
    require_fields(form, REQUIRED_FIELDS)
    data = {
        "object_type_id": to_int(form.get("object_type_id"), "object_type_id"),
        "description": clean_string(form.get("description"), "description", 2000),
        "found_campus_id": to_int(form.get("found_campus_id"), "found_campus_id"),
        "found_block_id": to_int(form.get("found_block_id"), "found_block_id"),
        "found_location": clean_string(form.get("found_location"), "found_location", 255),
        "found_at": parse_datetime(form.get("found_at"), "found_at"),
        "custody_campus_id": to_int(form.get("custody_campus_id"), "custody_campus_id"),
        "custody_block_id": to_int(form.get("custody_block_id"), "custody_block_id"),
        "custody_location": clean_string(form.get("custody_location"), "custody_location", 255),
        "finder_person_id": to_int(form.get("finder_person_id"), "finder_person_id"),
        "finder_department_id": to_int(form.get("finder_department_id"), "finder_department_id"),
    }
    # Campos como received_by_user_id, status o code NO se leen: los decide el servidor.
    files = request.files.getlist("photos")
    simulate_failure = (
        current_app.config["ALLOW_FAULT_INJECTION"]
        and request.headers.get("X-Simulate-Storage-Failure", "").lower() == "true"
    )
    object_lost = create_object(data, files, get_current_user(), simulate_failure)
    return success_response("Objeto registrado correctamente.", object_detail_to_dict(object_lost), 201)


def update_object_controller(object_id):
    data = get_json_data()
    check_allowed_fields(data, EDITABLE_FIELDS + ["found_campus_id", "custody_campus_id", "reason", "version"])
    reason = get_reason(data)
    version = read_version(data)
    changes, campus_ids = read_object_changes(data, EDITABLE_FIELDS)
    object_lost = update_object(object_id, changes, campus_ids, version, reason, get_current_user())
    return success_response("Objeto actualizado correctamente.", object_detail_to_dict(object_lost))


def administrative_correction_controller(object_id):
    data = get_json_data()
    check_allowed_fields(data, CORRECTION_FIELDS + ["found_campus_id", "custody_campus_id", "reason", "version"])
    reason = get_reason(data)
    version = read_version(data)
    changes, campus_ids = read_object_changes(data, CORRECTION_FIELDS)
    object_lost = administrative_correction(object_id, changes, campus_ids, version, reason, get_current_user())
    return success_response("Corrección administrativa registrada. La devolución se conserva.",
                            object_detail_to_dict(object_lost))


def inactivate_object_controller(object_id):
    reason = get_reason(get_json_data())
    object_lost = inactivate_object(object_id, reason, get_current_user())
    return success_response("Objeto inactivado. El registro se conserva en la base y en la auditoría.",
                            object_detail_to_dict(object_lost))


def reactivate_object_controller(object_id):
    reason = get_reason(get_json_data())
    object_lost = reactivate_object(object_id, reason, get_current_user())
    return success_response("Objeto reactivado correctamente.", object_detail_to_dict(object_lost))
