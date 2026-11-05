import hashlib
import logging
import secrets
from datetime import datetime, timedelta, timezone
from flask import current_app
from flask_jwt_extended import create_access_token
from sqlalchemy import select, update
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db
from app.models.user import User
from app.models.role import Role
from app.models.password_reset_token import PasswordResetToken
from app.models.token_revocation import TokenRevocation
from app.common.constants import CONSULTA
from app.common.errors import AppError
from app.common.mail import send_email
from app.common.normalization import normalize_email
from app.common.dates import utc_now
from app.services.audit_service import add_audit_log, snapshot

logger = logging.getLogger(__name__)

# Hash de una contraseña cualquiera: se usa para gastar el mismo tiempo cuando el
# correo no existe, y así no revelar qué correos están registrados.
DUMMY_HASH = generate_password_hash("contrasena-ficticia-123")


def get_user_by_email(email):
    return db.session.execute(
        select(User).where(User.email == normalize_email(email))
    ).scalar_one_or_none()


def register_user(identification, full_name, email, password):
    email = normalize_email(email)

    existing_user = db.session.execute(
        select(User).where(User.email == email)
    ).scalar_one_or_none()
    if existing_user:
        raise AppError("El correo ya está registrado.", 409)

    existing_user = db.session.execute(
        select(User).where(User.identification == identification)
    ).scalar_one_or_none()
    if existing_user:
        raise AppError("La identificación ya está registrada.", 409)

    # El registro público SIEMPRE asigna CONSULTA: el cliente nunca decide el rol.
    role = db.session.execute(select(Role).where(Role.name == CONSULTA)).scalar_one_or_none()
    if role is None:
        raise AppError("Los roles no están configurados. Ejecute el seed (python seed.py).", 500)

    user = User(
        identification=identification,
        full_name=full_name,
        email=email,
        password_hash=generate_password_hash(password),
        role_id=role.id
    )
    db.session.add(user)
    db.session.flush()
    add_audit_log("user", user.id, "REGISTER", user.id, after=snapshot(user))
    db.session.commit()
    return user


def validate_credentials(email, password):
    """Devuelve el usuario si la contraseña es correcta (activo o no); si no, None."""
    user = get_user_by_email(email)
    if user is None:
        check_password_hash(DUMMY_HASH, password)
        return None
    if not check_password_hash(user.password_hash, password):
        return None
    return user


def create_token_for(user):
    # "tv" (token_version) permite invalidar todos los tokens previos del usuario.
    # El rol se incluye solo como información para el frontend; el backend lo lee de la base.
    return create_access_token(
        identity=str(user.id),
        additional_claims={"tv": user.token_version, "role": user.role.name}
    )


def logout_user(user, jwt_payload):
    revocation = TokenRevocation(
        jti=jwt_payload["jti"],
        user_id=user.id,
        expires_at=datetime.fromtimestamp(jwt_payload["exp"], tz=timezone.utc)
    )
    db.session.add(revocation)
    db.session.commit()


def hash_token(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def request_password_reset(email):
    """Siempre termina igual para el cliente, exista o no el correo."""
    user = get_user_by_email(email)
    if user is None or not user.is_active:
        # Un usuario inactivo no puede recuperar acceso para reactivarse.
        return

    token = secrets.token_urlsafe(32)
    minutes = current_app.config["PASSWORD_RESET_MINUTES"]
    reset = PasswordResetToken(
        user_id=user.id,
        token_hash=hash_token(token),
        expires_at=utc_now() + timedelta(minutes=minutes)
    )
    db.session.add(reset)
    db.session.flush()
    add_audit_log("user", user.id, "PASSWORD_RESET_REQUEST", user.id)
    db.session.commit()

    link = f'{current_app.config["FRONTEND_URL"]}/reset-password?token={token}'
    body = (
        f"Hola {user.full_name},\n\n"
        f"Recibimos una solicitud para restablecer su contraseña.\n"
        f"Use este enlace (vence en {minutes} minutos y sirve una sola vez):\n\n{link}\n\n"
        f"Si usted no lo solicitó, ignore este mensaje.\n"
    )
    try:
        send_email(user.email, "Recuperación de contraseña - Objetos perdidos CES", body)
    except Exception as error:
        # No se registra el enlace en el log; solo el tipo de error.
        logger.error("No se pudo enviar el correo de recuperación: %s", type(error).__name__)


def reset_password(token, new_password):
    reset = db.session.execute(
        select(PasswordResetToken)
        .where(PasswordResetToken.token_hash == hash_token(token))
        .with_for_update()
    ).scalar_one_or_none()

    invalid_message = "El enlace de recuperación no es válido, ya fue usado o venció."
    if reset is None or reset.used_at is not None or reset.revoked_at is not None:
        raise AppError(invalid_message, 400)
    if reset.expires_at <= utc_now():
        raise AppError(invalid_message, 400)

    user = db.session.get(User, reset.user_id)
    if user is None or not user.is_active:
        raise AppError(invalid_message, 400)

    now = utc_now()
    user.password_hash = generate_password_hash(new_password)
    user.token_version = user.token_version + 1  # invalida las sesiones anteriores
    reset.used_at = now

    # Revoca los demás tokens de recuperación pendientes del usuario (no se borran).
    db.session.execute(
        update(PasswordResetToken)
        .where(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.id != reset.id,
            PasswordResetToken.used_at.is_(None),
            PasswordResetToken.revoked_at.is_(None)
        )
        .values(revoked_at=now)
    )
    add_audit_log("user", user.id, "PASSWORD_RESET", user.id)
    db.session.commit()


def change_password(user, current_password, new_password):
    if not check_password_hash(user.password_hash, current_password):
        raise AppError("La contraseña actual no es correcta.", 400)
    if current_password == new_password:
        raise AppError("La nueva contraseña debe ser distinta de la actual.", 400)

    user.password_hash = generate_password_hash(new_password)
    user.token_version = user.token_version + 1
    user.updated_by = user.id
    add_audit_log("user", user.id, "PASSWORD_CHANGE", user.id)
    db.session.commit()
    return create_token_for(user)
