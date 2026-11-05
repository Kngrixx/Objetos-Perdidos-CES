from flask import request
from app.common.dates import parse_date, bogota_day_range
from app.common.errors import AppError
from app.common.responses import success_response
from app.common.validators import arg_int
from app.controllers.object_lost_controller import object_to_dict
from app.services.dashboard_service import get_summary, get_by_category, get_by_campus, get_recent


def read_dashboard_filters():
    date_from = parse_date(request.args.get("date_from"), "date_from")
    date_to = parse_date(request.args.get("date_to"), "date_to")
    start, end = bogota_day_range(date_from, date_to)
    return {"campus_id": arg_int("campus_id"), "start": start, "end": end}


def dashboard_summary_controller():
    return success_response("Indicadores calculados.", get_summary(read_dashboard_filters()))


def dashboard_by_category_controller():
    return success_response("Objetos por categoría.", get_by_category(read_dashboard_filters()))


def dashboard_by_campus_controller():
    return success_response("Objetos por sede.", get_by_campus(read_dashboard_filters()))


def dashboard_recent_controller():
    limit = arg_int("limit")
    if limit is None:
        limit = 10
    if limit < 1 or limit > 50:
        raise AppError("El parámetro limit debe estar entre 1 y 50.", 400)
    objects = get_recent(read_dashboard_filters(), limit)
    return success_response("Últimos objetos recibidos.", [object_to_dict(item) for item in objects])
