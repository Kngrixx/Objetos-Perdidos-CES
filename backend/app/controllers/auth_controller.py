from flask import current_app
from flask_jwt_extended import get_jwt
from app.common.responses import success_response, error_response
from app.common.validators import (
    get_json_data, require_fields, clean_string, validate_email, validate_password
)
from app.common.rate_limit import check_rate_limit
from app.common.security import get_current_user
from app.services.auth_service import (
    register_user,
    validate_credentials,
    create_token_for,
    logout_user,
    request_password_reset,
    reset_password,
    change_password
)


def user_to_dict(user):
    """Datos mínimos del usuario. Nunca se expone password_hash."""
    return {
        "id": user.id,
        "identification": user.identification,
        "full_name": user.full_name,
        "email": user.email,
        "role": user.role.name,
        "is_active": user.is_active,
    }


def register_controller():
    check_rate_limit("register", current_app.config["REGISTER_MAX_ATTEMPTS"])
    data = get_json_data()
    require_fields(data, ["identification", "full_name", "email", "password"])
    identification = clean_string(data.get("identification"), "identification", 50)
    full_name = clean_string(data.get("full_name"), "full_name", 150)
    email = validate_email(clean_string(data.get("email"), "email", 200).lower())
    password = validate_password(data.get("password"))
    if "password_confirmation" in data and data.get("password_confirmation") != password:
        return error_response("La confirmación de la contraseña no coincide.", 400)
    # Si el cliente envía "role" (por ejemplo ADMIN) se ignora: el service asigna CONSULTA.
    user = register_user(identification, full_name, email, password)
    return success_response("Cuenta creada correctamente. Ya puede iniciar sesión.", user_to_dict(user), 201)


def login_controller():
    check_rate_limit("login", current_app.config["LOGIN_MAX_ATTEMPTS"])
    data = get_json_data()
    email = data.get("email")
    password = data.get("password")
    if not email or not password:
        return error_response("email y password son obligatorios.", 400)

    user = validate_credentials(email=str(email), password=str(password))
    if user is None:
        # Mensaje genérico: no revela si el correo existe.
        return error_response("Credenciales inválidas.", 401)
    if not user.is_active:
        return error_response("La cuenta está inactiva. Contacte al administrador.", 403)

    access_token = create_token_for(user)
    expires_in = int(current_app.config["JWT_ACCESS_TOKEN_EXPIRES"].total_seconds())
    return success_response("Inicio de sesión exitoso.", {
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": expires_in,
        "user": user_to_dict(user),
    }, 200)


def me_controller():
    return success_response("Usuario autenticado.", user_to_dict(get_current_user()), 200)


def logout_controller():
    logout_user(get_current_user(), get_jwt())
    return success_response("Sesión cerrada. El token ya no se puede reutilizar.", None, 200)


def forgot_password_controller():
    check_rate_limit("forgot", current_app.config["FORGOT_MAX_ATTEMPTS"])
    data = get_json_data()
    email = data.get("email")
    if not email or not isinstance(email, str):
        return error_response("email es obligatorio.", 400)
    request_password_reset(email)
    # Mismo mensaje exista o no el correo.
    return success_response(
        "Si el correo está registrado, recibirá un enlace para restablecer la contraseña.", None, 200
    )


def reset_password_controller():
    check_rate_limit("reset", current_app.config["FORGOT_MAX_ATTEMPTS"])
    data = get_json_data()
    require_fields(data, ["token", "password", "password_confirmation"])
    password = validate_password(data.get("password"))
    if data.get("password_confirmation") != password:
        return error_response("La confirmación de la contraseña no coincide.", 400)
    reset_password(str(data.get("token")), password)
    return success_response("Contraseña restablecida. Inicie sesión con la nueva contraseña.", None, 200)


def change_password_controller():
    data = get_json_data()
    require_fields(data, ["current_password", "new_password", "new_password_confirmation"])
    new_password = validate_password(data.get("new_password"), "new_password")
    if data.get("new_password_confirmation") != new_password:
        return error_response("La confirmación de la nueva contraseña no coincide.", 400)
    access_token = change_password(get_current_user(), str(data.get("current_password")), new_password)
    # Las sesiones anteriores quedan invalidadas; se entrega un token nuevo para seguir trabajando.
    return success_response("Contraseña actualizada. Las demás sesiones se cerraron.", {
        "access_token": access_token
    }, 200)
