from app.common.dates import to_iso
from app.common.pagination import get_page_params
from app.common.responses import success_response, page_data, list_message
from app.common.security import get_current_user, active_filter_for_role, check_can_see
from app.common.validators import (
    get_json_data, require_fields, check_allowed_fields, clean_string, get_reason, to_int,
    arg_int, arg_bool, arg_text
)
from app.services.object_type_service import (
    get_object_types_by_filter,
    get_object_type_by_id,
    create_object_type,
    update_object_type,
    inactivate_object_type,
    reactivate_object_type
)


def object_type_to_dict(object_type):
    return {
        "id": object_type.id,
        "category_id": object_type.category_id,
        "category_name": object_type.category.name,
        "name": object_type.name,
        "normalized_name": object_type.normalized_name,
        "is_active": object_type.is_active,
        "created_at": to_iso(object_type.created_at),
        "updated_at": to_iso(object_type.updated_at),
        "inactivated_at": to_iso(object_type.inactivated_at),
        "inactivation_reason": object_type.inactivation_reason,
    }


def list_object_types_controller():
    page, page_size = get_page_params()
    filters = {
        "id": arg_int("id"),
        "category_id": arg_int("category_id"),
        "name": arg_text("name"),
        "is_active": active_filter_for_role(arg_bool("is_active"), arg_bool("include_inactive")),
    }
    object_types, total = get_object_types_by_filter(filters, page, page_size)
    items = [object_type_to_dict(object_type) for object_type in object_types]
    return success_response(list_message(total), page_data(items, page, page_size, total))


def get_object_type_controller(object_type_id):
    object_type = get_object_type_by_id(object_type_id)
    check_can_see(object_type)
    return success_response("Consulta exitosa.", object_type_to_dict(object_type))


def create_object_type_controller():
    data = get_json_data()
    require_fields(data, ["category_id", "name"])
    category_id = to_int(data.get("category_id"), "category_id")
    name = clean_string(data.get("name"), "name", 100)
    object_type = create_object_type(category_id, name, get_current_user())
    return success_response("Tipo de objeto creado correctamente.", object_type_to_dict(object_type), 201)


def update_object_type_controller(object_type_id):
    data = get_json_data()
    check_allowed_fields(data, ["name", "category_id", "reason"])
    changes = {}
    if "name" in data:
        changes["name"] = clean_string(data.get("name"), "name", 100)
    if "category_id" in data:
        changes["category_id"] = to_int(data.get("category_id"), "category_id")
    object_type = update_object_type(object_type_id, changes, get_reason(data, required=False), get_current_user())
    return success_response("Tipo de objeto actualizado correctamente.", object_type_to_dict(object_type))


def inactivate_object_type_controller(object_type_id):
    reason = get_reason(get_json_data())
    object_type = inactivate_object_type(object_type_id, reason, get_current_user())
    return success_response("Tipo de objeto inactivado correctamente.", object_type_to_dict(object_type))


def reactivate_object_type_controller(object_type_id):
    reason = get_reason(get_json_data())
    object_type = reactivate_object_type(object_type_id, reason, get_current_user())
    return success_response("Tipo de objeto reactivado correctamente.", object_type_to_dict(object_type))
