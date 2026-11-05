import logging
from werkzeug.exceptions import HTTPException
from sqlalchemy.exc import IntegrityError
from app.extensions import db
from app.common.responses import error_response

logger = logging.getLogger(__name__)


class AppError(Exception):
    """Error de negocio con su código HTTP.

    En clase el service lanzaba ValueError y el controller respondía 409.
    Aquí hay más casos (400, 403, 404, 409, 429), así que el service lanza
    AppError("mensaje", código) y un único manejador lo convierte en la
    respuesta {ok, message, data}.
    """

    def __init__(self, message, status_code=400, data=None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.data = data


HTTP_MESSAGES = {
    400: "La petición no es válida.",
    401: "No autenticado.",
    403: "No tiene permisos para realizar esta acción.",
    404: "Recurso no encontrado.",
    405: "Método no permitido para esta ruta.",
    413: "La carga excede el tamaño máximo permitido.",
    415: "Tipo de contenido no soportado.",
    429: "Demasiados intentos. Espere un momento e intente de nuevo.",
}


def register_error_handlers(app):

    @app.errorhandler(AppError)
    def handle_app_error(error):
        db.session.rollback()
        return error_response(error.message, error.status_code, error.data)

    @app.errorhandler(IntegrityError)
    def handle_integrity_error(error):
        # Respaldo de la base de datos: UNIQUE, FK o CHECK violados (por ejemplo, dos
        # peticiones simultáneas que pasaron la validación del service al mismo tiempo).
        db.session.rollback()
        return error_response("La operación entra en conflicto con datos existentes.", 409)

    @app.errorhandler(HTTPException)
    def handle_http_error(error):
        message = HTTP_MESSAGES.get(error.code, error.description)
        return error_response(message, error.code)

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        db.session.rollback()
        logger.exception("Error no controlado")
        # Nunca se envían detalles internos al cliente.
        return error_response("Error interno del servidor.", 500)
