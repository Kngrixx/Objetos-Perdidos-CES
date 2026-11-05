from app.extensions import db
from sqlalchemy import text


def db_status():
    db.session.execute(text("SELECT 1"))
    return {
        "status": "OK",
        "service": "DB Status Service",
    }


def get_health_status():
    return {
        "status": "OK",
        "service": "Health Status Service",
    }


def get_health():
    return {
        "status": "OK",
        "service": "Health Service",
    }
