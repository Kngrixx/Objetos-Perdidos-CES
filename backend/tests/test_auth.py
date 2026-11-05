import os
import re
import glob
from datetime import timedelta
from email import message_from_bytes
from flask_jwt_extended import create_access_token
from sqlalchemy import text
from app.extensions import db
from app.models.user import User
from app.common.rate_limit import reset_rate_limits
from tests.helpers import unique, login_headers

PASSWORD = "Segura2026!"


def register(client, **fields):
    body = {"identification": unique("ID"), "full_name": "Usuario Nuevo",
            "email": unique("user") + "@test.ces", "password": PASSWORD}
    body.update(fields)
    return client.post("/api/auth/register", json=body)


def latest_reset_token(app, email):
    files = sorted(glob.glob(os.path.join(app.config["MAIL_OUTBOX_FOLDER"], "*" + email.replace("@", "_at_") + ".eml")))
    assert files, "No llegó el correo de recuperación al buzón local"
    with open(files[-1], "rb") as mail_file:
        body = message_from_bytes(mail_file.read()).get_payload(decode=True).decode("utf-8")
    return re.search(r"token=([A-Za-z0-9_\-]+)", body).group(1)


# ---------------------------------------------------------------- PA01

def test_pa01_register_assigns_consulta_and_ignores_role(client):
    response = register(client, role="ADMIN", role_id=1)
    assert response.status_code == 201
    body = response.get_json()
    assert body["ok"] is True and body["data"]["role"] == "CONSULTA"
    assert "password_hash" not in body["data"]


def test_pa01_register_rejects_duplicates(client):
    email = unique("dup") + "@test.ces"
    identification = unique("ID")
    assert register(client, email=email, identification=identification).status_code == 201
    duplicate_email = register(client, email=email.upper())
    assert duplicate_email.status_code == 409
    assert duplicate_email.get_json()["ok"] is False
    assert register(client, identification=identification).status_code == 409


def test_register_validations(client):
    assert register(client, email="no-es-correo").status_code == 400
    assert register(client, password="corta1").status_code == 400
    response = client.post("/api/auth/register", json={"email": "x@test.ces"})
    assert response.status_code == 400
    assert "Campos obligatorios" in response.get_json()["message"]


# ---------------------------------------------------------------- PA02

def test_pa02_login_ok_and_errors(client, app):
    email = unique("login") + "@test.ces"
    register(client, email=email)
    ok = client.post("/api/auth/login", json={"email": email, "password": PASSWORD})
    assert ok.status_code == 200
    data = ok.get_json()["data"]
    assert data["access_token"] and data["expires_in"] == 1800 and data["user"]["role"] == "CONSULTA"

    wrong = client.post("/api/auth/login", json={"email": email, "password": "Otra2026!"})
    missing_user = client.post("/api/auth/login", json={"email": "nadie@test.ces", "password": "Otra2026!"})
    assert wrong.status_code == 401 and missing_user.status_code == 401
    assert wrong.get_json()["message"] == missing_user.get_json()["message"]  # mensaje genérico

    assert client.get("/api/auth/me").status_code == 401  # sin JWT

    with app.app_context():
        user = db.session.query(User).filter_by(email=email).one()
        expired = create_access_token(identity=str(user.id), additional_claims={"tv": user.token_version},
                                      expires_delta=timedelta(seconds=-5))
    response = client.get("/api/auth/me", headers={"Authorization": "Bearer " + expired})
    assert response.status_code == 401 and "expiró" in response.get_json()["message"]


def test_pa02_inactive_user_cannot_login(client, admin_headers):
    email = unique("inactive") + "@test.ces"
    user_id = register(client, email=email).get_json()["data"]["id"]
    headers = login_headers(client, email, PASSWORD)
    response = client.patch(f"/api/users/{user_id}/inactivate", headers=admin_headers, json={"reason": "Prueba de inactivación"})
    assert response.status_code == 200
    assert client.post("/api/auth/login", json={"email": email, "password": PASSWORD}).status_code == 403
    assert client.get("/api/auth/me", headers=headers).status_code == 401  # su token anterior ya no sirve


# ---------------------------------------------------------------- PA03

def test_pa03_logout_revokes_token(client):
    email = unique("logout") + "@test.ces"
    register(client, email=email)
    headers = login_headers(client, email, PASSWORD)
    assert client.get("/api/auth/me", headers=headers).status_code == 200
    assert client.post("/api/auth/logout", headers=headers).status_code == 200
    assert client.get("/api/auth/me", headers=headers).status_code == 401


def test_pa03_change_password_invalidates_sessions(client):
    email = unique("change") + "@test.ces"
    register(client, email=email)
    old_headers = login_headers(client, email, PASSWORD)
    response = client.patch("/api/auth/change-password", headers=old_headers, json={
        "current_password": PASSWORD, "new_password": "Nueva2026!", "new_password_confirmation": "Nueva2026!"})
    assert response.status_code == 200
    new_token = response.get_json()["data"]["access_token"]
    assert client.get("/api/auth/me", headers=old_headers).status_code == 401
    assert client.get("/api/auth/me", headers={"Authorization": "Bearer " + new_token}).status_code == 200
    assert client.post("/api/auth/login", json={"email": email, "password": "Nueva2026!"}).status_code == 200


def test_change_password_wrong_current(client):
    email = unique("change2") + "@test.ces"
    register(client, email=email)
    headers = login_headers(client, email, PASSWORD)
    response = client.patch("/api/auth/change-password", headers=headers, json={
        "current_password": "Mala2026!", "new_password": "Nueva2026!", "new_password_confirmation": "Nueva2026!"})
    assert response.status_code == 400


# ---------------------------------------------------------------- PA04

def test_pa04_forgot_and_reset_password(client, app):
    email = unique("forgot") + "@test.ces"
    register(client, email=email)
    old_headers = login_headers(client, email, PASSWORD)

    existing = client.post("/api/auth/forgot-password", json={"email": email})
    missing = client.post("/api/auth/forgot-password", json={"email": "no-existe@test.ces"})
    assert existing.status_code == missing.status_code == 200
    assert existing.get_json() == missing.get_json()
    assert "token" not in str(existing.get_json()["data"])

    token = latest_reset_token(app, email)
    with app.app_context():
        stored = db.session.execute(text("SELECT token_hash FROM password_reset_tokens ORDER BY id DESC LIMIT 1")).scalar()
        assert stored != token and len(stored) == 64  # solo se guarda el hash

    body = {"token": token, "password": "Reset2026!", "password_confirmation": "Reset2026!"}
    assert client.post("/api/auth/reset-password", json=body).status_code == 200
    assert client.get("/api/auth/me", headers=old_headers).status_code == 401  # sesiones previas invalidadas
    assert client.post("/api/auth/login", json={"email": email, "password": "Reset2026!"}).status_code == 200
    # Un solo uso
    assert client.post("/api/auth/reset-password", json=body).status_code == 400


def test_pa04_expired_reset_token_fails(client, app):
    email = unique("expired") + "@test.ces"
    register(client, email=email)
    client.post("/api/auth/forgot-password", json={"email": email})
    token = latest_reset_token(app, email)
    with app.app_context():
        db.session.execute(text("UPDATE password_reset_tokens SET expires_at = now() - interval '1 minute' "
                                "WHERE id = (SELECT max(id) FROM password_reset_tokens)"))
        db.session.commit()
    response = client.post("/api/auth/reset-password", json={
        "token": token, "password": "Reset2026!", "password_confirmation": "Reset2026!"})
    assert response.status_code == 400


def test_reset_revokes_other_pending_tokens(client, app):
    email = unique("revoke") + "@test.ces"
    register(client, email=email)
    client.post("/api/auth/forgot-password", json={"email": email})
    first_token = latest_reset_token(app, email)
    import time
    time.sleep(0.01)
    client.post("/api/auth/forgot-password", json={"email": email})
    second_token = latest_reset_token(app, email)
    assert first_token != second_token
    ok = client.post("/api/auth/reset-password", json={
        "token": second_token, "password": "Reset2026!", "password_confirmation": "Reset2026!"})
    assert ok.status_code == 200
    revoked = client.post("/api/auth/reset-password", json={
        "token": first_token, "password": "Reset2026!", "password_confirmation": "Reset2026!"})
    assert revoked.status_code == 400


# ---------------------------------------------------------------- Users / PA23

def test_users_admin_only(client, admin_headers, operador_headers, consulta_headers):
    assert client.get("/api/users", headers=admin_headers).status_code == 200
    assert client.get("/api/users", headers=operador_headers).status_code == 403
    assert client.get("/api/roles", headers=consulta_headers).status_code == 403
    roles = client.get("/api/roles", headers=admin_headers).get_json()["data"]
    assert [role["name"] for role in roles] == ["ADMIN", "OPERADOR", "CONSULTA"]


def test_admin_promotes_user_to_operador(client, admin_headers):
    email = unique("promote") + "@test.ces"
    user_id = register(client, email=email).get_json()["data"]["id"]
    roles = {role["name"]: role["id"] for role in client.get("/api/roles", headers=admin_headers).get_json()["data"]}
    response = client.patch(f"/api/users/{user_id}", headers=admin_headers, json={"role_id": roles["OPERADOR"]})
    assert response.status_code == 200 and response.get_json()["data"]["role"] == "OPERADOR"
    # El rol se lee de la BD: el token viejo ya actúa como OPERADOR sin volver a iniciar sesión
    headers = login_headers(client, email, PASSWORD)
    assert client.get("/api/persons", headers=headers).status_code == 200


def test_pa23_last_admin_protection(client, app, admin_headers):
    roles = {role["name"]: role["id"] for role in client.get("/api/roles", headers=admin_headers).get_json()["data"]}
    admins = client.get("/api/users?role=ADMIN&is_active=true", headers=admin_headers).get_json()["data"]["items"]
    seed_admin = [user for user in admins if user["email"] == app.config["SEED_ADMIN_EMAIL"]][0]
    second_admin = [user for user in admins if user["email"] == "admin2@test.ces"][0]

    # No puede inactivarse a sí mismo
    assert client.patch(f"/api/users/{seed_admin['id']}/inactivate", headers=admin_headers,
                        json={"reason": "Prueba propia"}).status_code == 409
    # Hay dos ADMIN: se puede degradar al segundo...
    assert client.patch(f"/api/users/{second_admin['id']}", headers=admin_headers,
                        json={"role_id": roles["OPERADOR"]}).status_code == 200
    # ...pero no al último administrador activo
    response = client.patch(f"/api/users/{seed_admin['id']}", headers=admin_headers, json={"role_id": roles["CONSULTA"]})
    assert response.status_code == 409 and "último administrador" in response.get_json()["message"]
    # Se restaura el segundo ADMIN para no afectar otras pruebas
    assert client.patch(f"/api/users/{second_admin['id']}", headers=admin_headers,
                        json={"role_id": roles["ADMIN"]}).status_code == 200


def test_rate_limit_returns_429(client, app):
    reset_rate_limits()
    original = app.config["LOGIN_MAX_ATTEMPTS"]
    app.config["LOGIN_MAX_ATTEMPTS"] = 3
    try:
        codes = [client.post("/api/auth/login", json={"email": "x@test.ces", "password": "Mala2026!"}).status_code
                 for _ in range(4)]
        assert codes == [401, 401, 401, 429]
    finally:
        app.config["LOGIN_MAX_ATTEMPTS"] = original
        reset_rate_limits()
