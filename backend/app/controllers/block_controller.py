from app.common.dates import to_iso
from app.common.pagination import get_page_params
from app.common.responses import success_response, page_data, list_message
from app.common.security import get_current_user, active_filter_for_role, check_can_see
from app.common.validators import (
    get_json_data, require_fields, check_allowed_fields, clean_string, get_reason, to_int,
    arg_int, arg_bool, arg_text
)
from app.services.block_service import (
    get_blocks_by_filter,
    get_block_by_id,
    create_block,
    update_block,
    inactivate_block,
    reactivate_block
)


def block_to_dict(block):
    return {
        "id": block.id,
        "campus_id": block.campus_id,
        "campus_name": block.campus.name,
        "name": block.name,
        "normalized_name": block.normalized_name,
        "is_active": block.is_active,
        "created_at": to_iso(block.created_at),
        "updated_at": to_iso(block.updated_at),
        "inactivated_at": to_iso(block.inactivated_at),
        "inactivation_reason": block.inactivation_reason,
    }


def list_blocks_controller():
    page, page_size = get_page_params()
    filters = {
        "id": arg_int("id"),
        "campus_id": arg_int("campus_id"),
        "name": arg_text("name"),
        "is_active": active_filter_for_role(arg_bool("is_active"), arg_bool("include_inactive")),
    }
    blocks, total = get_blocks_by_filter(filters, page, page_size)
    items = [block_to_dict(block) for block in blocks]
    return success_response(list_message(total), page_data(items, page, page_size, total))


def get_block_controller(block_id):
    block = get_block_by_id(block_id)
    check_can_see(block)
    return success_response("Consulta exitosa.", block_to_dict(block))


def create_block_controller():
    data = get_json_data()
    require_fields(data, ["campus_id", "name"])
    campus_id = to_int(data.get("campus_id"), "campus_id")
    name = clean_string(data.get("name"), "name", 100)
    block = create_block(campus_id, name, get_current_user())
    return success_response("Bloque creado correctamente.", block_to_dict(block), 201)


def update_block_controller(block_id):
    data = get_json_data()
    # La sede de un bloque no se cambia: alteraría el historial de los objetos.
    check_allowed_fields(data, ["name", "reason"])
    require_fields(data, ["name"])
    name = clean_string(data.get("name"), "name", 100)
    block = update_block(block_id, name, get_reason(data, required=False), get_current_user())
    return success_response("Bloque actualizado correctamente.", block_to_dict(block))


def inactivate_block_controller(block_id):
    reason = get_reason(get_json_data())
    block = inactivate_block(block_id, reason, get_current_user())
    return success_response("Bloque inactivado correctamente.", block_to_dict(block))


def reactivate_block_controller(block_id):
    reason = get_reason(get_json_data())
    block = reactivate_block(block_id, reason, get_current_user())
    return success_response("Bloque reactivado correctamente.", block_to_dict(block))
