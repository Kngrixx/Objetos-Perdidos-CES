from sqlalchemy import select, func, case
from sqlalchemy.orm import aliased
from app.extensions import db
from app.models.object_type import ObjectType
from app.models.object_category import ObjectCategory
from app.models.block import Block
from app.models.campus import Campus
from app.models.claim import Claim
from app.common.constants import DISPONIBLE, DEVUELTO, PENDIENTE
from app.services.object_lost_service import build_object_query

# Todos los indicadores se calculan en la base de datos con los filtros recibidos
# (rango de fechas de recepción y sede). Solo ADMIN (validado en la ruta).


def filtered_objects(filters):
    base_filters = {
        "campus_id": filters.get("campus_id"),
        "start": filters.get("start"),
        "end": filters.get("end"),
    }
    return build_object_query(base_filters).order_by(None).subquery()


def get_summary(filters):
    base = filtered_objects(filters)
    row = db.session.execute(
        select(
            func.count(base.c.id),
            func.count(case((base.c.is_active.is_(True) & (base.c.status == DISPONIBLE), 1))),
            func.count(case((base.c.is_active.is_(True) & (base.c.status == DEVUELTO), 1))),
            func.count(case((base.c.is_active.is_(False), 1))),
        )
    ).one()
    pending_claims = db.session.execute(
        select(func.count(Claim.id))
        .where(Claim.object_lost_id.in_(select(base.c.id)), Claim.status == PENDIENTE, Claim.is_active.is_(True))
    ).scalar_one()
    return {
        "total": row[0],
        "available": row[1],
        "returned": row[2],
        "inactive": row[3],
        "pending_claims": pending_claims,
    }


def get_by_category(filters):
    base = filtered_objects(filters)
    rows = db.session.execute(
        select(ObjectCategory.id, ObjectCategory.name, func.count(base.c.id))
        .select_from(base)
        .join(ObjectType, ObjectType.id == base.c.object_type_id)
        .join(ObjectCategory, ObjectCategory.id == ObjectType.category_id)
        .where(base.c.is_active.is_(True))
        .group_by(ObjectCategory.id, ObjectCategory.name)
        .order_by(func.count(base.c.id).desc(), ObjectCategory.name)
    ).all()
    return [{"category_id": row[0], "category": row[1], "total": row[2]} for row in rows]


def get_by_campus(filters):
    base = filtered_objects(filters)
    found_block = aliased(Block)
    rows = db.session.execute(
        select(Campus.id, Campus.name, func.count(base.c.id))
        .select_from(base)
        .join(found_block, found_block.id == base.c.found_block_id)
        .join(Campus, Campus.id == found_block.campus_id)
        .where(base.c.is_active.is_(True))
        .group_by(Campus.id, Campus.name)
        .order_by(func.count(base.c.id).desc(), Campus.name)
    ).all()
    return [{"campus_id": row[0], "campus": row[1], "total": row[2]} for row in rows]


def get_recent(filters, limit):
    base_filters = {
        "campus_id": filters.get("campus_id"),
        "start": filters.get("start"),
        "end": filters.get("end"),
    }
    query = build_object_query(base_filters).limit(limit)
    return db.session.execute(query).scalars().all()
