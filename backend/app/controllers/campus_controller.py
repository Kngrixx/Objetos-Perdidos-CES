from app.common.dates import to_iso
from app.common.pagination import get_page_params
from app.common.responses import success_response, page_data, list_message
from app.common.security import get_current_user, active_filter_for_role, check_can_see
from app.common.validators import (
    get_json_data, require_fields, check_allowed_fields, clean_string, get_reason,
    arg_int, arg_bool, arg_text
)
from app.services.campus_service import (
    get_campuses_by_filter,
    get_campus_by_id,
    create_campus,
    update_campus,
    inactivate_campus,
    reactivate_campus
)


def campus_to_dict(campus):
    return {
        "id": campus.id,
        "name": campus.name,
        "normalized_name": campus.normalized_name,
        "is_active": campus.is_active,
        "created_at": to_iso(campus.created_at),
        "updated_at": to_iso(campus.updated_at),
        "inactivated_at": to_iso(campus.inactivated_at),
        "inactivation_reason": campus.inactivation_reason,
    }


def list_campuses_controller():
    page, page_size = get_page_params()
    filters = {
        "id": arg_int("id"),
        "name": arg_text("name"),
        "is_active": active_filter_for_role(arg_bool("is_active"), arg_bool("include_inactive")),
    }
    campuses, total = get_campuses_by_filter(filters, page, page_size)
    items = [campus_to_dict(campus) for campus in campuses]
    return success_response(list_message(total), page_data(items, page, page_size, total))


def get_campus_controller(campus_id):
    campus = get_campus_by_id(campus_id)
    check_can_see(campus)
    return success_response("Consulta exitosa.", campus_to_dict(campus))


def create_campus_controller():
    data = get_json_data()
    require_fields(data, ["name"])
    name = clean_string(data.get("name"), "name", 100)
    campus = create_campus(name, get_current_user())
    return success_response("Sede creada correctamente.", campus_to_dict(campus), 201)


def update_campus_controller(campus_id):
    data = get_json_data()
    check_allowed_fields(data, ["name", "reason"])
    require_fields(data, ["name"])
    name = clean_string(data.get("name"), "name", 100)
    campus = update_campus(campus_id, name, get_reason(data, required=False), get_current_user())
    return success_response("Sede actualizada correctamente.", campus_to_dict(campus))


def inactivate_campus_controller(campus_id):
    reason = get_reason(get_json_data())
    campus = inactivate_campus(campus_id, reason, get_current_user())
    return success_response("Sede inactivada correctamente.", campus_to_dict(campus))


def reactivate_campus_controller(campus_id):
    reason = get_reason(get_json_data())
    campus = reactivate_campus(campus_id, reason, get_current_user())
    return success_response("Sede reactivada correctamente.", campus_to_dict(campus))
