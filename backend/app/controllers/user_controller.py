from app.common.constants import ROLE_NAMES
from app.common.dates import to_iso
from app.common.pagination import get_page_params
from app.common.responses import success_response, page_data, list_message
from app.common.security import get_current_user
from app.common.validators import (
    get_json_data, check_allowed_fields, clean_string, validate_email, to_int, get_reason,
    arg_int, arg_bool, arg_text, arg_choice
)
from app.services.user_service import (
    get_users_by_filter,
    get_user_by_id,
    update_user,
    inactivate_user,
    reactivate_user
)


def user_to_dict(user):
    return {
        "id": user.id,
        "identification": user.identification,
        "full_name": user.full_name,
        "email": user.email,
        "role_id": user.role_id,
        "role": user.role.name,
        "is_active": user.is_active,
        "created_at": to_iso(user.created_at),
        "updated_at": to_iso(user.updated_at),
        "inactivated_at": to_iso(user.inactivated_at),
        "inactivation_reason": user.inactivation_reason,
    }


def list_users_controller():
    page, page_size = get_page_params()
    filters = {
        "id": arg_int("id"),
        "text": arg_text("text"),
        "role": arg_choice("role", ROLE_NAMES),
        "is_active": arg_bool("is_active"),
    }
    users, total = get_users_by_filter(filters, page, page_size)
    items = [user_to_dict(user) for user in users]
    return success_response(list_message(total), page_data(items, page, page_size, total))


def get_user_controller(user_id):
    return success_response("Consulta exitosa.", user_to_dict(get_user_by_id(user_id)))


def update_user_controller(user_id):
    data = get_json_data()
    check_allowed_fields(data, ["full_name", "email", "identification", "role_id", "reason"])
    changes = {}
    if "full_name" in data:
        changes["full_name"] = clean_string(data.get("full_name"), "full_name", 150)
    if "email" in data:
        changes["email"] = validate_email(clean_string(data.get("email"), "email", 200).lower())
    if "identification" in data:
        changes["identification"] = clean_string(data.get("identification"), "identification", 50)
    if "role_id" in data:
        changes["role_id"] = to_int(data.get("role_id"), "role_id")
    changes["reason"] = get_reason(data, required=False)
    user = update_user(user_id, changes, get_current_user())
    return success_response("Usuario actualizado correctamente.", user_to_dict(user))


def inactivate_user_controller(user_id):
    reason = get_reason(get_json_data())
    user = inactivate_user(user_id, reason, get_current_user())
    return success_response("Usuario inactivado. Sus sesiones fueron cerradas.", user_to_dict(user))


def reactivate_user_controller(user_id):
    reason = get_reason(get_json_data())
    user = reactivate_user(user_id, reason, get_current_user())
    return success_response("Usuario reactivado correctamente.", user_to_dict(user))
