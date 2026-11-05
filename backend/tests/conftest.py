"""Configuración de pytest.

Las pruebas usan una base de datos APARTE (TEST_DATABASE_URL en el .env). En cada ejecución
se borra el esquema de esa base, se aplican TODAS las migraciones (incluidos los triggers)
y se corre el seed. Nunca toca la base de desarrollo.
"""
import os
import shutil
import pytest
from flask_migrate import upgrade
from sqlalchemy import text
from werkzeug.security import generate_password_hash
from config import TestConfig
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.role import Role
from app.services.seed_service import run_seed
from tests.helpers import login_headers

TEST_PASSWORD = "Prueba2026!"


@pytest.fixture(scope="session")
def app():
    if not TestConfig.SQLALCHEMY_DATABASE_URI:
        pytest.exit("Falta TEST_DATABASE_URL en el archivo .env")
    application = create_app(TestConfig)
    for folder in [application.config["UPLOAD_FOLDER"], application.config["MAIL_OUTBOX_FOLDER"]]:
        shutil.rmtree(folder, ignore_errors=True)
        os.makedirs(folder, exist_ok=True)

    with application.app_context():
        db.session.execute(text("DROP SCHEMA public CASCADE"))
        db.session.execute(text("CREATE SCHEMA public"))
        db.session.commit()
        upgrade()   # mismas migraciones que flask db upgrade
        run_seed()
        for email, role_name in [("operador@test.ces", "OPERADOR"), ("consulta@test.ces", "CONSULTA"),
                                 ("admin2@test.ces", "ADMIN")]:
            role = db.session.query(Role).filter_by(name=role_name).one()
            db.session.add(User(identification="ID-" + email, full_name="Usuario " + role_name,
                                email=email, password_hash=generate_password_hash(TEST_PASSWORD),
                                role_id=role.id))
        db.session.commit()
    yield application
    with application.app_context():
        db.session.remove()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def admin_headers(client, app):
    return login_headers(client, app.config["SEED_ADMIN_EMAIL"], app.config["SEED_ADMIN_PASSWORD"])


@pytest.fixture()
def operador_headers(client):
    return login_headers(client, "operador@test.ces", TEST_PASSWORD)


@pytest.fixture()
def consulta_headers(client):
    return login_headers(client, "consulta@test.ces", TEST_PASSWORD)
