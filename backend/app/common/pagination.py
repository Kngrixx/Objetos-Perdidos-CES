from flask import request
from sqlalchemy import select, func
from app.extensions import db
from app.common.errors import AppError
from app.common.validators import to_int


def get_page_params():
    """Lee page y page_size de la URL. page_size debe estar entre 1 y 100."""
    page = to_int(request.args.get("page"), "page") or 1
    page_size = to_int(request.args.get("page_size"), "page_size")
    if page_size is None:
        page_size = 20
    if page < 1:
        raise AppError("El parámetro page debe ser mayor o igual a 1.", 400)
    if page_size < 1 or page_size > 100:
        raise AppError("El parámetro page_size debe estar entre 1 y 100.", 400)
    return page, page_size


def paginate(query, page, page_size):
    """Ejecuta la consulta (ya filtrada y ordenada) y devuelve (filas de la página, total)."""
    total = db.session.execute(
        select(func.count()).select_from(query.order_by(None).subquery())
    ).scalar_one()
    items = db.session.execute(
        query.limit(page_size).offset((page - 1) * page_size)
    ).scalars().all()
    return items, total
