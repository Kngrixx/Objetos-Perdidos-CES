from app.common.dates import to_iso
from app.common.pagination import get_page_params
from app.common.responses import success_response, page_data, list_message
from app.common.security import get_current_user, active_filter_for_role, check_can_see
from app.common.validators import (
    get_json_data, require_fields, check_allowed_fields, clean_string, get_reason,
    arg_int, arg_bool, arg_text
)
from app.services.object_category_service import (
    get_categories_by_filter,
    get_category_by_id,
    create_category,
    update_category,
    inactivate_category,
    reactivate_category
)


def category_to_dict(category):
    return {
        "id": category.id,
        "name": category.name,
        "normalized_name": category.normalized_name,
        "is_active": category.is_active,
        "created_at": to_iso(category.created_at),
        "updated_at": to_iso(category.updated_at),
        "inactivated_at": to_iso(category.inactivated_at),
        "inactivation_reason": category.inactivation_reason,
    }


def list_categories_controller():
    page, page_size = get_page_params()
    filters = {
        "id": arg_int("id"),
        "name": arg_text("name"),
        "is_active": active_filter_for_role(arg_bool("is_active"), arg_bool("include_inactive")),
    }
    categories, total = get_categories_by_filter(filters, page, page_size)
    items = [category_to_dict(category) for category in categories]
    return success_response(list_message(total), page_data(items, page, page_size, total))


def get_category_controller(category_id):
    category = get_category_by_id(category_id)
    check_can_see(category)
    return success_response("Consulta exitosa.", category_to_dict(category))


def create_category_controller():
    data = get_json_data()
    require_fields(data, ["name"])
    name = clean_string(data.get("name"), "name", 100)
    category = create_category(name, get_current_user())
    return success_response("Categoría creada correctamente.", category_to_dict(category), 201)


def update_category_controller(category_id):
    data = get_json_data()
    check_allowed_fields(data, ["name", "reason"])
    require_fields(data, ["name"])
    name = clean_string(data.get("name"), "name", 100)
    category = update_category(category_id, name, get_reason(data, required=False), get_current_user())
    return success_response("Categoría actualizada correctamente.", category_to_dict(category))


def inactivate_category_controller(category_id):
    reason = get_reason(get_json_data())
    category = inactivate_category(category_id, reason, get_current_user())
    return success_response("Categoría inactivada correctamente.", category_to_dict(category))


def reactivate_category_controller(category_id):
    reason = get_reason(get_json_data())
    category = reactivate_category(category_id, reason, get_current_user())
    return success_response("Categoría reactivada correctamente.", category_to_dict(category))
