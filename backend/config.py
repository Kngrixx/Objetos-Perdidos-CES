import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

# Carpeta donde está este archivo (backend/). Las rutas relativas del .env se resuelven desde aquí.
BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def get_bool(name, default="false"):
    return os.getenv(name, default).strip().lower() in ("1", "true", "si", "yes")


def get_path(name, default):
    return os.path.join(BASE_DIR, os.getenv(name, default))


class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    # El enunciado pide access token de 30 minutos.
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=int(os.getenv("JWT_ACCESS_MINUTES", "30")))

    # Orígenes del frontend (Angular) autorizados, separados por coma en el .env.
    CORS_ALLOWED_ORIGINS = [
        origin.strip()
        for origin in os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:4200").split(",")
        if origin.strip()
    ]
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:4200")

    # Fotografías: se guardan en disco (fuera de carpetas públicas); en la base solo la referencia.
    UPLOAD_FOLDER = get_path("UPLOAD_FOLDER", "instance/uploads")
    MAX_PHOTO_BYTES = 5 * 1024 * 1024
    MAX_PHOTOS_PER_OBJECT = 5
    # Límite de toda la petición (5 fotos de 5 MB + campos). Si se supera, Flask responde 413.
    MAX_CONTENT_LENGTH = 30 * 1024 * 1024

    # Recuperación de contraseña
    PASSWORD_RESET_MINUTES = 15
    MAIL_MODE = os.getenv("MAIL_MODE", "file")  # file = buzón local en carpeta; smtp = servidor real
    MAIL_OUTBOX_FOLDER = get_path("MAIL_OUTBOX_FOLDER", "instance/outbox")
    MAIL_SERVER = os.getenv("MAIL_SERVER", "localhost")
    MAIL_PORT = int(os.getenv("MAIL_PORT", "1025"))
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
    MAIL_USE_TLS = get_bool("MAIL_USE_TLS")
    MAIL_FROM = os.getenv("MAIL_FROM", "no-reply@objetos-perdidos.ces.test")

    # Límite de intentos por IP en una ventana de tiempo (respuesta 429).
    RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
    LOGIN_MAX_ATTEMPTS = int(os.getenv("LOGIN_MAX_ATTEMPTS", "30"))
    REGISTER_MAX_ATTEMPTS = int(os.getenv("REGISTER_MAX_ATTEMPTS", "20"))
    FORGOT_MAX_ATTEMPTS = int(os.getenv("FORGOT_MAX_ATTEMPTS", "10"))

    # Solo para demostrar PA10 (fallo de archivo). Debe quedar en false fuera de la demo.
    ALLOW_FAULT_INJECTION = get_bool("ALLOW_FAULT_INJECTION")

    # Administrador inicial que crea el seed (credenciales ficticias de desarrollo).
    SEED_ADMIN_EMAIL = os.getenv("SEED_ADMIN_EMAIL", "admin@ces.test")
    SEED_ADMIN_PASSWORD = os.getenv("SEED_ADMIN_PASSWORD", "Admin2026!")
    SEED_ADMIN_NAME = os.getenv("SEED_ADMIN_NAME", "Administrador de Pruebas")
    SEED_ADMIN_IDENTIFICATION = os.getenv("SEED_ADMIN_IDENTIFICATION", "ADMIN-0001")


class TestConfig(Config):
    """Configuración para pytest: base de datos aparte y carpetas de prueba."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.getenv("TEST_DATABASE_URL")
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "instance", "test_uploads")
    MAIL_MODE = "file"
    MAIL_OUTBOX_FOLDER = os.path.join(BASE_DIR, "instance", "test_outbox")
    ALLOW_FAULT_INJECTION = True
    # Límites altos en pruebas (la prueba de 429 los baja temporalmente).
    LOGIN_MAX_ATTEMPTS = 100000
    REGISTER_MAX_ATTEMPTS = 100000
    FORGOT_MAX_ATTEMPTS = 100000
