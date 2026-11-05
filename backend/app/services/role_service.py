from sqlalchemy import select
from app.extensions import db
from app.models.role import Role


def get_all_roles():
    return db.session.execute(
        select(Role).order_by(Role.id)
    ).scalars().all()
