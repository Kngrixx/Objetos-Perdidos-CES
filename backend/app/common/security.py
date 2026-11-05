from functools import wraps
from sqlalchemy import select
from flask_jwt_extended import current_user
from app.extensions import db
from app.models.user import User
from app.models.token_revocation import TokenRevocation
from app.common.responses import error_response
from app.common.constants import ADMIN
from app.common.errors import AppError

# "Auth centraliza JWT y permisos" (enunciado, sección 5).
#
# Cada ruta protegida lleva @jwt_required() como en clase. Con los callbacks de
# abajo, ese decorador valida en cada petición:
#   1. firma y expiración del token (Flask-JWT-Extended),
#   2. que el jti no esté revocado (logout),
#   3. que el usuario exista y esté activo,
#   4. que token_version (claim "tv") coincida con la de la base.
# Después, @roles_required(...) revisa el rol leído de la base de datos,
# nunca el rol que viaja dentro del token.


def register_jwt_callbacks(jwt):

    @jwt.token_in_blocklist_loader
    def is_token_revoked(jwt_header, jwt_payload):
        revoked = db.session.execute(
            select(TokenRevocation.id).where(TokenRevocation.jti == jwt_payload["jti"])
        ).scalar_one_or_none()
        return revoked is not None

    @jwt.user_lookup_loader
    def load_user_from_token(jwt_header, jwt_payload):
        user = db.session.get(User, int(jwt_payload["sub"]))
        if user is None or not user.is_active:
            return None
        if jwt_payload.get("tv") != user.token_version:
            return None
        return user

    @jwt.user_lookup_error_loader
    def invalid_user(jwt_header, jwt_payload):
        return error_response("La sesión ya no es válida. Inicie sesión nuevamente.", 401)

    @jwt.unauthorized_loader
    def missing_token(reason):
        return error_response("Falta el token de autenticación. Inicie sesión.", 401)

    @jwt.invalid_token_loader
    def invalid_token(reason):
        return error_response("El token de autenticación no es válido.", 401)

    @jwt.expired_token_loader
    def expired_token(jwt_header, jwt_payload):
        return error_response("El token expiró. Inicie sesión nuevamente.", 401)

    @jwt.revoked_token_loader
    def revoked_token(jwt_header, jwt_payload):
        return error_response("La sesión fue cerrada. Inicie sesión nuevamente.", 401)


def roles_required(*roles):
    """Se usa debajo de @jwt_required(): permite la ruta solo a los roles indicados."""
    def decorator(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            if current_user.role.name not in roles:
                return error_response("No tiene permisos para realizar esta acción.", 403)
            return function(*args, **kwargs)
        return wrapper
    return decorator


def get_current_user():
    """Usuario autenticado, ya cargado de la base por el callback user_lookup_loader."""
    return current_user


def current_role():
    return current_user.role.name


def active_filter_for_role(is_active, include_inactive=False):
    """Catálogos: cualquier usuario activo los consulta; ver inactivos exige ADMIN.
    ADMIN sin filtro ve todos; los demás roles solo ven los activos."""
    if current_role() == ADMIN:
        return is_active
    if is_active is False or include_inactive:
        raise AppError("Solo un ADMIN puede consultar registros inactivos.", 403)
    return True


def check_can_see(record):
    """Detalle de un catálogo inactivo: solo ADMIN."""
    if not record.is_active and current_role() != ADMIN:
        raise AppError("Solo un ADMIN puede consultar registros inactivos.", 403)
