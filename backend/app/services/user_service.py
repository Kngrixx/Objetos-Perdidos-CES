from sqlalchemy import select, or_
from app.extensions import db
from app.models.user import User
from app.models.role import Role
from app.common.constants import ADMIN
from app.common.errors import AppError
from app.common.normalization import normalize_email
from app.common.pagination import paginate
from app.common.dates import utc_now
from app.services.audit_service import add_audit_log, snapshot, only_changes


def get_users_by_filter(filters, page, page_size):
    query = select(User).join(Role, User.role_id == Role.id)
    if filters.get("id") is not None:
        query = query.where(User.id == filters["id"])
    if filters.get("text"):
        pattern = f'%{filters["text"]}%'
        query = query.where(or_(
            User.full_name.ilike(pattern),
            User.email.ilike(pattern),
            User.identification.ilike(pattern)
        ))
    if filters.get("role"):
        query = query.where(Role.name == filters["role"])
    if filters.get("is_active") is not None:
        query = query.where(User.is_active == filters["is_active"])
    query = query.order_by(User.full_name, User.id)
    return paginate(query, page, page_size)


def get_user_by_id(user_id):
    user = db.session.get(User, user_id)
    if user is None:
        raise AppError("Usuario no encontrado.", 404)
    return user


def count_active_admins():
    """Cuenta los ADMIN activos bloqueando sus filas: dos cambios simultáneos no pueden
    dejar el sistema sin administrador."""
    admins = db.session.execute(
        select(User)
        .join(Role, User.role_id == Role.id)
        .where(Role.name == ADMIN, User.is_active.is_(True))
        .with_for_update(of=User)
    ).scalars().all()
    return len(admins)


def update_user(user_id, data, actor):
    user = get_user_by_id(user_id)
    before = snapshot(user)

    if "full_name" in data:
        user.full_name = data["full_name"]

    if "email" in data:
        email = normalize_email(data["email"])
        duplicate = db.session.execute(
            select(User).where(User.email == email, User.id != user.id)
        ).scalar_one_or_none()
        if duplicate:
            raise AppError("El correo ya está registrado por otro usuario.", 409)
        user.email = email

    if "identification" in data:
        duplicate = db.session.execute(
            select(User).where(User.identification == data["identification"], User.id != user.id)
        ).scalar_one_or_none()
        if duplicate:
            raise AppError("La identificación ya está registrada por otro usuario.", 409)
        user.identification = data["identification"]

    action = "UPDATE"
    if "role_id" in data and data["role_id"] != user.role_id:
        new_role = db.session.get(Role, data["role_id"])
        if new_role is None:
            raise AppError("El rol indicado no existe.", 400)
        if user.role.name == ADMIN and new_role.name != ADMIN and user.is_active:
            if count_active_admins() <= 1:
                raise AppError("No se puede degradar al último administrador activo.", 409)
        user.role_id = new_role.id
        action = "ROLE_CHANGE"

    user.updated_by = actor.id
    db.session.flush()
    db.session.refresh(user)
    changes_before, changes_after = only_changes(before, snapshot(user))
    add_audit_log("user", user.id, action, actor.id, data.get("reason"), changes_before, changes_after)
    db.session.commit()
    return user


def inactivate_user(user_id, reason, actor):
    user = get_user_by_id(user_id)
    if not user.is_active:
        raise AppError("El usuario ya está inactivo.", 409)
    if user.id == actor.id:
        raise AppError("No puede inactivar su propia cuenta.", 409)
    if user.role.name == ADMIN and count_active_admins() <= 1:
        raise AppError("No se puede inactivar al último administrador activo.", 409)

    before = snapshot(user)
    user.is_active = False
    user.inactivated_at = utc_now()
    user.inactivated_by = actor.id
    user.inactivation_reason = reason
    user.token_version = user.token_version + 1  # cierra todas sus sesiones
    user.updated_by = actor.id
    db.session.flush()
    add_audit_log("user", user.id, "INACTIVATE", actor.id, reason, before, snapshot(user))
    db.session.commit()
    return user


def reactivate_user(user_id, reason, actor):
    user = get_user_by_id(user_id)
    if user.is_active:
        raise AppError("El usuario ya está activo.", 409)

    before = snapshot(user)
    user.is_active = True
    user.inactivated_at = None
    user.inactivated_by = None
    user.inactivation_reason = None
    user.updated_by = actor.id
    db.session.flush()
    add_audit_log("user", user.id, "REACTIVATE", actor.id, reason, before, snapshot(user))
    db.session.commit()
    return user
