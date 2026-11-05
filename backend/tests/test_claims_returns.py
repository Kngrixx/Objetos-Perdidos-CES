import threading
from sqlalchemy import text
from app.extensions import db
from tests.helpers import new_object, create_person, accepted_claim, returned_object


def new_claim(client, headers, object_id, verified=True):
    person = create_person(client, headers)
    response = client.post("/api/claims", headers=headers, json={
        "object_lost_id": object_id, "claimant_person_id": person["id"],
        "evidence": "Describe un raspón en la esquina", "identity_verified": verified})
    assert response.status_code == 201, response.get_json()
    return response.get_json()["data"]


# ---------------------------------------------------------------- PA16

def test_pa16_rejected_claim_keeps_object_available(client, operador_headers):
    object_lost = new_object(client, operador_headers)
    claim = new_claim(client, operador_headers, object_lost["id"])
    assert claim["status"] == "PENDIENTE"
    no_reason = client.patch(f"/api/claims/{claim['id']}/decision", headers=operador_headers, json={"decision": "RECHAZADA"})
    assert no_reason.status_code == 400
    response = client.patch(f"/api/claims/{claim['id']}/decision", headers=operador_headers,
                            json={"decision": "RECHAZADA", "reason": "La evidencia no coincide"})
    assert response.status_code == 200 and response.get_json()["data"]["status"] == "RECHAZADA"
    detail = client.get(f"/api/object-lost/{object_lost['id']}", headers=operador_headers).get_json()["data"]
    assert detail["status"] == "DISPONIBLE"
    # Una decisión tomada ya no se cambia
    again = client.patch(f"/api/claims/{claim['id']}/decision", headers=operador_headers,
                         json={"decision": "ACEPTADA", "reason": "Cambio de opinión"})
    assert again.status_code == 409


def test_pa16_accepted_claim_allows_return_with_receipt(client, operador_headers):
    me = client.get("/api/auth/me", headers=operador_headers).get_json()["data"]
    object_lost = new_object(client, operador_headers)
    claim = accepted_claim(client, operador_headers, object_lost["id"])
    without_confirmation = client.post("/api/returns", headers=operador_headers, json={
        "claim_id": claim["id"], "verification_summary": "Verificado", "owner_confirmation": False})
    assert without_confirmation.status_code == 400
    manipulated = client.post("/api/returns", headers=operador_headers, json={
        "claim_id": claim["id"], "verification_summary": "Verificado", "owner_confirmation": True,
        "delivered_by_user_id": 1})
    assert manipulated.status_code == 400  # el responsable no lo decide el cliente

    response = client.post("/api/returns", headers=operador_headers, json={
        "claim_id": claim["id"], "object_lost_id": object_lost["id"],
        "verification_summary": "Cédula y marcas verificadas", "owner_confirmation": True})
    assert response.status_code == 201
    record = response.get_json()["data"]
    assert record["delivered_by"]["id"] == me["id"]
    assert record["owner"]["id"] == claim["claimant"]["id"]
    assert record["object_lost"]["status"] == "DEVUELTO"
    receipt = client.get(record["receipt_url"], headers=operador_headers)
    assert receipt.status_code == 200 and receipt.content_type == "application/pdf"
    assert receipt.data.startswith(b"%PDF") and len(receipt.data) > 500

    second = client.post("/api/returns", headers=operador_headers, json={
        "claim_id": claim["id"], "verification_summary": "Otra vez", "owner_confirmation": True})
    assert second.status_code == 409
    detail = client.get(f"/api/object-lost/{object_lost['id']}", headers=operador_headers).get_json()["data"]
    assert detail["status"] == "DEVUELTO" and detail["return"]["owner"]["id"] == claim["claimant"]["id"]


def test_claim_rules(client, operador_headers, admin_headers):
    object_lost = new_object(client, operador_headers)
    not_verified = new_claim(client, operador_headers, object_lost["id"], verified=False)
    response = client.patch(f"/api/claims/{not_verified['id']}/decision", headers=operador_headers,
                            json={"decision": "ACEPTADA", "reason": "Parece suyo"})
    assert response.status_code == 400  # exige identificación verificada
    corrected = client.patch(f"/api/claims/{not_verified['id']}", headers=operador_headers,
                             json={"identity_verified": True, "reason": "Se verificó la cédula"})
    assert corrected.status_code == 200 and corrected.get_json()["data"]["identity_verified"] is True

    other = new_claim(client, operador_headers, object_lost["id"])
    assert client.patch(f"/api/claims/{not_verified['id']}/decision", headers=operador_headers,
                        json={"decision": "ACEPTADA", "reason": "Coincide"}).status_code == 200
    second_accept = client.patch(f"/api/claims/{other['id']}/decision", headers=operador_headers,
                                 json={"decision": "ACEPTADA", "reason": "También coincide"})
    assert second_accept.status_code == 409  # a lo sumo una ACEPTADA por objeto

    # Inactivar: solo ADMIN y solo pendientes
    assert client.patch(f"/api/claims/{other['id']}/inactivate", headers=operador_headers,
                        json={"reason": "Duplicada"}).status_code == 403
    assert client.patch(f"/api/claims/{not_verified['id']}/inactivate", headers=admin_headers,
                        json={"reason": "Ya aceptada"}).status_code == 409
    assert client.patch(f"/api/claims/{other['id']}/inactivate", headers=admin_headers,
                        json={"reason": "Reclamación duplicada"}).status_code == 200
    listing = client.get("/api/claims", query_string={"object_lost_id": object_lost["id"], "status": "ACEPTADA"},
                         headers=operador_headers).get_json()["data"]
    assert listing["total"] == 1


def test_database_partial_unique_index_blocks_second_accepted(client, operador_headers, app):
    object_lost = new_object(client, operador_headers)
    first = new_claim(client, operador_headers, object_lost["id"])
    second = new_claim(client, operador_headers, object_lost["id"])
    with app.app_context():
        db.session.execute(text("UPDATE claims SET status = 'ACEPTADA' WHERE id = :id"), {"id": first["id"]})
        db.session.commit()
        try:
            db.session.execute(text("UPDATE claims SET status = 'ACEPTADA' WHERE id = :id"), {"id": second["id"]})
            db.session.commit()
            assert False, "La base aceptó dos reclamaciones ACEPTADAS"
        except Exception as error:
            db.session.rollback()
            assert "uq_claims_one_accepted_per_object" in str(error)


# ---------------------------------------------------------------- PA17

def test_pa17_concurrent_returns_only_one_succeeds(client, app, operador_headers):
    object_lost = new_object(client, operador_headers)
    claim = accepted_claim(client, operador_headers, object_lost["id"])
    workers = 8
    barrier = threading.Barrier(workers)
    results = []

    def try_return():
        local_client = app.test_client()
        barrier.wait()
        response = local_client.post("/api/returns", headers=operador_headers, json={
            "claim_id": claim["id"], "verification_summary": "Concurrencia", "owner_confirmation": True})
        results.append(response.status_code)

    threads = [threading.Thread(target=try_return) for _ in range(workers)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert sorted(results) == [201] + [409] * (workers - 1)
    with app.app_context():
        total = db.session.execute(text("SELECT count(*) FROM return_records WHERE object_lost_id = :id"),
                                   {"id": object_lost["id"]}).scalar()
    assert total == 1


# ---------------------------------------------------------------- PA18 y PA24

def test_pa18_inventory_excludes_returned_and_inactive(client, operador_headers, consulta_headers):
    returned, _, _ = returned_object(client, operador_headers)
    inactive = new_object(client, operador_headers)
    client.patch(f"/api/object-lost/{inactive['id']}/inactivate", headers=operador_headers, json={"reason": "Error de registro"})
    available = new_object(client, operador_headers)

    codes = [item["code"] for item in client.get("/api/inventory?page_size=100", headers=operador_headers)
             .get_json()["data"]["items"]]
    assert available["code"] in codes
    assert returned["code"] not in codes and inactive["code"] not in codes
    # Siguen accesibles para roles autorizados
    assert client.get(f"/api/object-lost/{returned['id']}", headers=operador_headers).status_code == 200
    assert client.get(f"/api/object-lost/{inactive['id']}", headers=operador_headers).status_code == 200
    assert client.get("/api/object-lost", query_string={"status": "DEVUELTO"}, headers=operador_headers).get_json()["data"]["total"] >= 1
    # CONSULTA no los ve
    assert client.get(f"/api/object-lost/{returned['id']}", headers=consulta_headers).status_code == 404
    assert client.get("/api/inventory", headers=consulta_headers).status_code == 403


def test_pa24_administrative_correction_of_returned(client, operador_headers, admin_headers):
    returned, claim, record = returned_object(client, operador_headers)
    detail = client.get(f"/api/object-lost/{returned['id']}", headers=admin_headers).get_json()["data"]
    body = {"description": "Descripción corregida por el ADMIN", "reason": "Error de digitación", "version": detail["version"]}

    assert client.patch(f"/api/object-lost/{returned['id']}", headers=operador_headers,
                        json=body).status_code == 409  # edición ordinaria no aplica a DEVUELTO
    assert client.patch(f"/api/object-lost/{returned['id']}/administrative-correction",
                        headers=operador_headers, json=body).status_code == 403
    assert client.patch(f"/api/object-lost/{returned['id']}/inactivate", headers=admin_headers,
                        json={"reason": "No se puede"}).status_code == 409
    response = client.patch(f"/api/object-lost/{returned['id']}/administrative-correction",
                            headers=admin_headers, json=body)
    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["description"] == body["description"] and data["status"] == "DEVUELTO"
    assert data["return"]["id"] == record["id"] and data["return"]["owner"]["id"] == claim["claimant"]["id"]
    forbidden_field = client.patch(f"/api/object-lost/{returned['id']}/administrative-correction", headers=admin_headers,
                                   json={"finder_person_id": 1, "reason": "No permitido", "version": data["version"]})
    assert forbidden_field.status_code == 400
    available = new_object(client, operador_headers)
    not_returned = client.patch(f"/api/object-lost/{available['id']}/administrative-correction", headers=admin_headers,
                                json={"description": "x", "reason": "No aplica", "version": 1})
    assert not_returned.status_code == 409
    returns = client.get("/api/returns", query_string={"object_lost_id": returned["id"]}, headers=operador_headers)
    assert returns.get_json()["data"]["total"] == 1
