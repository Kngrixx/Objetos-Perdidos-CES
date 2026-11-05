from app.common.dates import to_iso
from app.common.pagination import get_page_params
from app.common.responses import success_response, page_data, list_message
from app.common.security import get_current_user, active_filter_for_role, check_can_see
from app.common.validators import (
    get_json_data, require_fields, check_allowed_fields, clean_string, get_reason,
    arg_int, arg_bool, arg_text
)
from app.services.department_service import (
    get_departments_by_filter,
    get_department_by_id,
    create_department,
    update_department,
    inactivate_department,
    reactivate_department
)


def department_to_dict(department):
    return {
        "id": department.id,
        "name": department.name,
        "normalized_name": department.normalized_name,
        "is_active": department.is_active,
        "created_at": to_iso(department.created_at),
        "updated_at": to_iso(department.updated_at),
        "inactivated_at": to_iso(department.inactivated_at),
        "inactivation_reason": department.inactivation_reason,
    }


def list_departments_controller():
    page, page_size = get_page_params()
    filters = {
        "id": arg_int("id"),
        "name": arg_text("name"),
        "is_active": active_filter_for_role(arg_bool("is_active"), arg_bool("include_inactive")),
    }
    departments, total = get_departments_by_filter(filters, page, page_size)
    items = [department_to_dict(department) for department in departments]
    return success_response(list_message(total), page_data(items, page, page_size, total))


def get_department_controller(department_id):
    department = get_department_by_id(department_id)
    check_can_see(department)
    return success_response("Consulta exitosa.", department_to_dict(department))


def create_department_controller():
    data = get_json_data()
    require_fields(data, ["name"])
    name = clean_string(data.get("name"), "name", 150)
    department = create_department(name, get_current_user())
    return success_response("Dependencia creada correctamente.", department_to_dict(department), 201)


def update_department_controller(department_id):
    data = get_json_data()
    check_allowed_fields(data, ["name", "reason"])
    require_fields(data, ["name"])
    name = clean_string(data.get("name"), "name", 150)
    department = update_department(department_id, name, get_reason(data, required=False), get_current_user())
    return success_response("Dependencia actualizada correctamente.", department_to_dict(department))


def inactivate_department_controller(department_id):
    reason = get_reason(get_json_data())
    department = inactivate_department(department_id, reason, get_current_user())
    return success_response("Dependencia inactivada correctamente.", department_to_dict(department))


def reactivate_department_controller(department_id):
    reason = get_reason(get_json_data())
    department = reactivate_department(department_id, reason, get_current_user())
    return success_response("Dependencia reactivada correctamente.", department_to_dict(department))
