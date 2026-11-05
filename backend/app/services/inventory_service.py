from sqlalchemy import select, func
from sqlalchemy.orm import aliased
from app.extensions import db
from app.models.object_type import ObjectType
from app.models.block import Block
from app.models.campus import Campus
from app.common.constants import DISPONIBLE, DEVUELTO
from app.common.pagination import paginate
from app.services.object_lost_service import build_object_query


def inventory_filters(filters):
    """Inventario disponible = registro activo Y estado DISPONIBLE (se fuerza siempre)."""
    forced = dict(filters)
    forced["is_active"] = True
    forced["status"] = DISPONIBLE
    return forced


def get_inventory(filters, page, page_size):
    return paginate(build_object_query(inventory_filters(filters)), page, page_size)


def get_inventory_for_export(filters):
    """Misma consulta que GET /inventory (mismos filtros y orden) pero sin paginar."""
    return db.session.execute(build_object_query(inventory_filters(filters))).scalars().all()


def count_by(filters, group_column, label_column, extra_joins):
    base = build_object_query(filters).order_by(None).subquery()
    query = select(group_column, label_column, func.count(base.c.id)).select_from(base)
    for target, condition in extra_joins(base):
        query = query.join(target, condition)
    query = query.group_by(group_column, label_column).order_by(func.count(base.c.id).desc(), label_column)
    return [{"id": row[0], "name": row[1], "total": row[2]} for row in db.session.execute(query).all()]


def get_inventory_summary(filters):
    """Conteos por sede, tipo y estado, respetando los filtros recibidos."""
    available = inventory_filters(filters)
    found_block = aliased(Block)

    by_campus = count_by(
        available, Campus.id, Campus.name,
        lambda base: [(found_block, found_block.id == base.c.found_block_id),
                      (Campus, Campus.id == found_block.campus_id)]
    )
    by_type = count_by(
        available, ObjectType.id, ObjectType.name,
        lambda base: [(ObjectType, ObjectType.id == base.c.object_type_id)]
    )

    status_filters = dict(filters)
    status_filters.pop("status", None)
    status_filters.pop("is_active", None)
    base = build_object_query(status_filters).order_by(None).subquery()
    rows = db.session.execute(
        select(base.c.is_active, base.c.status, func.count(base.c.id))
        .group_by(base.c.is_active, base.c.status)
    ).all()
    by_status = {DISPONIBLE: 0, DEVUELTO: 0, "INACTIVO": 0}
    for is_active, status, total in rows:
        if is_active:
            by_status[status] += total
        else:
            by_status["INACTIVO"] += total

    return {
        "total_available": sum(item["total"] for item in by_campus),
        "by_campus": by_campus,
        "by_type": by_type,
        "by_status": [{"status": key, "total": value} for key, value in by_status.items()],
    }
