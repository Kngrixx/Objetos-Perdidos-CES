from flask import request
from app.common.dates import to_iso, parse_date, bogota_day_range
from app.common.pagination import get_page_params
from app.common.responses import success_response, page_data, list_message
from app.common.validators import arg_int, arg_text
from app.services.audit_service import get_audit_logs_by_filter, get_object_history
from app.services.object_lost_service import get_object_by_id


def audit_to_dict(log):
    return {
        "id": log.id,
        "entity": log.entity,
        "entity_id": log.entity_id,
        "action": log.action,
        "actor": {"id": log.actor.id, "name": log.actor.full_name} if log.actor else None,
        "occurred_at": to_iso(log.occurred_at),
        "reason": log.reason,
        "before_data": log.before_data,
        "after_data": log.after_data,
    }


def list_audit_logs_controller():
    page, page_size = get_page_params()
    date_from = parse_date(request.args.get("date_from"), "date_from")
    date_to = parse_date(request.args.get("date_to"), "date_to")
    start, end = bogota_day_range(date_from, date_to)
    filters = {
        "entity": arg_text("entity"),
        "entity_id": arg_int("entity_id"),
        "actor_user_id": arg_int("actor_user_id"),
        "action": (arg_text("action") or "").upper() or None,
        "start": start,
        "end": end,
    }
    logs, total = get_audit_logs_by_filter(filters, page, page_size)
    items = [audit_to_dict(log) for log in logs]
    return success_response(list_message(total), page_data(items, page, page_size, total))


def object_history_controller(object_id):
    object_lost = get_object_by_id(object_id)
    logs = get_object_history(object_lost.id)
    return success_response("Historial del objeto " + object_lost.code + ".", {
        "object_lost_id": object_lost.id,
        "code": object_lost.code,
        "items": [audit_to_dict(log) for log in logs],
    })
