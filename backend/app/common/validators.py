import re
from flask import request
from app.common.errors import AppError
from app.common.normalization import clean_text

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def get_json_data():
    """Cuerpo JSON de la petición (como en clase: request.get_json(silent=True) or {})."""
    data = request.get_json(silent=True)
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise AppError("El cuerpo de la petición debe ser un objeto JSON.", 400)
    return data


def is_blank(value):
    return value is None or (isinstance(value, str) and value.strip() == "")


def require_fields(data, fields):
    missing = [field for field in fields if is_blank(data.get(field))]
    if missing:
        raise AppError("Campos obligatorios faltantes: " + ", ".join(missing) + ".", 400)


def check_allowed_fields(data, allowed_fields):
    """Lista explícita de campos editables: cualquier otro campo se rechaza con 400."""
    not_allowed = [field for field in data if field not in allowed_fields]
    if not_allowed:
        raise AppError("Campos no permitidos en esta operación: " + ", ".join(sorted(not_allowed)) + ".", 400)


def get_reason(data, required=True):
    reason = clean_text(data.get("reason") or "")
    if required and len(reason) < 5:
        raise AppError("El motivo (reason) es obligatorio y debe tener al menos 5 caracteres.", 400)
    return reason or None


def to_int(value, field_name):
    if is_blank(value):
        return None
    if isinstance(value, bool):
        raise AppError(f"El campo {field_name} debe ser un número entero.", 400)
    try:
        return int(str(value).strip())
    except ValueError:
        raise AppError(f"El campo {field_name} debe ser un número entero.", 400)


def to_bool(value, field_name):
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in ("true", "1", "si", "sí"):
        return True
    if text in ("false", "0", "no"):
        return False
    raise AppError(f"El campo {field_name} debe ser true o false.", 400)


def clean_string(value, field_name, max_length, required=True):
    if value is not None and not isinstance(value, str):
        raise AppError(f"El campo {field_name} debe ser texto.", 400)
    text = clean_text(value)
    if required and not text:
        raise AppError(f"El campo {field_name} es obligatorio.", 400)
    if text and len(text) > max_length:
        raise AppError(f"El campo {field_name} admite máximo {max_length} caracteres.", 400)
    return text or None


def validate_email(email, field_name="email"):
    if not email or not EMAIL_PATTERN.match(email) or len(email) > 200:
        raise AppError(f"El campo {field_name} no tiene un formato de correo válido.", 400)
    return email


def validate_password(password, field_name="password"):
    if not isinstance(password, str) or len(password) < 8:
        raise AppError(f"La contraseña ({field_name}) debe tener al menos 8 caracteres.", 400)
    if not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
        raise AppError(f"La contraseña ({field_name}) debe combinar letras y números.", 400)
    return password


def arg_int(name):
    return to_int(request.args.get(name), name)


def arg_bool(name):
    return to_bool(request.args.get(name), name)


def arg_text(name):
    return clean_text(request.args.get(name)) or None


def arg_choice(name, choices):
    value = arg_text(name)
    if value is None:
        return None
    value = value.upper()
    if value not in choices:
        raise AppError(f"El parámetro {name} debe ser uno de: " + ", ".join(choices) + ".", 400)
    return value


def choice(value, field_name, choices):
    text = (clean_text(value) or "").upper()
    if text not in choices:
        raise AppError(f"El campo {field_name} debe ser uno de: " + ", ".join(choices) + ".", 400)
    return text
