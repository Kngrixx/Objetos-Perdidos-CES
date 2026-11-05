from app.common.responses import success_response, error_response
from app.services.health_service import (
    get_health_status,
    get_health,
    db_status
)


def db_status_controller():
    try:
        data = db_status()
        return success_response("La base de datos responde.", data, 200)
    except Exception:
        return error_response("No hay conexión con la base de datos.", 500)


def health_controller():
    data = get_health()
    return success_response("Servicio activo.", data, 200)


def health_status_controller():
    data = get_health_status()
    return success_response("Servicio activo.", data, 200)
