from tests.helpers import unique, get_block, get_type_id, new_object, create_person, create_object, accepted_claim


def test_health_routes(client):
    for url in ["/api/health", "/api/health/status", "/api/health/db_status"]:
        response = client.get(url)
        assert response.status_code == 200 and response.get_json()["ok"] is True


def test_seed_catalog_minimums(client, admin_headers):
    categories = client.get("/api/object-categories?page_size=100", headers=admin_headers).get_json()["data"]
    types = client.get("/api/object-types?page_size=1", headers=admin_headers).get_json()["data"]
    assert categories["total"] >= 10 and types["total"] >= 100
    blocks = client.get("/api/blocks?page_size=100", headers=admin_headers).get_json()["data"]["items"]
    assert {"Bloque A", "Bloque B", "Bloque C", "Bloque principal"} <= {block["name"] for block in blocks}


def test_pa05_new_campus_and_block_visible_in_selector(client, admin_headers, operador_headers):
    name = unique("Sede Norte")
    campus = client.post("/api/campuses", headers=admin_headers, json={"name": name})
    assert campus.status_code == 201
    campus_id = campus.get_json()["data"]["id"]
    block = client.post("/api/blocks", headers=admin_headers, json={"campus_id": campus_id, "name": "Bloque 1"})
    assert block.status_code == 201
    # El operador lo ve en el selector (GET filtrado) sin cambios de código
    campuses = client.get("/api/campuses", query_string={"name": name},
                          headers=operador_headers).get_json()["data"]["items"]
    assert campuses[0]["id"] == campus_id
    blocks = client.get(f"/api/blocks?campus_id={campus_id}", headers=operador_headers).get_json()["data"]["items"]
    assert [item["name"] for item in blocks] == ["Bloque 1"]


def test_catalog_unique_normalized_name(client, admin_headers):
    name = unique("Cámara Térmica")
    assert client.post("/api/object-categories", headers=admin_headers, json={"name": name}).status_code == 201
    variant = "  " + name.upper().replace("Á", "A").replace("É", "E") + "  "
    response = client.post("/api/object-categories", headers=admin_headers, json={"name": variant})
    assert response.status_code == 409 and response.get_json()["ok"] is False


def test_catalog_permissions(client, operador_headers, consulta_headers):
    assert client.post("/api/campuses", headers=operador_headers, json={"name": unique("X")}).status_code == 403
    assert client.post("/api/departments", headers=consulta_headers, json={"name": unique("X")}).status_code == 403
    assert client.patch("/api/blocks/1", headers=operador_headers, json={"name": "Otro"}).status_code == 403
    assert client.patch("/api/object-types/1/inactivate", headers=operador_headers,
                        json={"reason": "No permitido"}).status_code == 403
    assert client.get("/api/campuses", headers=consulta_headers).status_code == 200


def test_only_admin_sees_inactive_catalogs(client, admin_headers, operador_headers):
    department = client.post("/api/departments", headers=admin_headers, json={"name": unique("Dep")}).get_json()["data"]
    client.patch(f"/api/departments/{department['id']}/inactivate", headers=admin_headers, json={"reason": "Ya no existe"})
    assert client.get("/api/departments?is_active=false", headers=operador_headers).status_code == 403
    assert client.get(f"/api/departments/{department['id']}", headers=operador_headers).status_code == 403
    inactive = client.get("/api/departments?is_active=false", headers=admin_headers).get_json()["data"]["items"]
    assert department["id"] in [item["id"] for item in inactive]
    active_ids = [item["id"] for item in client.get("/api/departments?page_size=100", headers=operador_headers).get_json()["data"]["items"]]
    assert department["id"] not in active_ids


def test_pa06_filter_blocks_by_campus(client, operador_headers):
    campus_id, _ = get_block(client, operador_headers, "Sabaneta", "Bloque principal")
    blocks = client.get(f"/api/blocks?campus_id={campus_id}", headers=operador_headers).get_json()["data"]["items"]
    assert blocks and all(block["campus_id"] == campus_id for block in blocks)


def test_pa07_create_type_from_form_and_duplicates(client, operador_headers):
    categories = client.get("/api/object-categories?name=tecnologia", headers=operador_headers).get_json()["data"]["items"]
    category_id = categories[0]["id"]
    name = unique("Gafas de Realidad Virtual")
    created = client.post("/api/object-types", headers=operador_headers, json={"category_id": category_id, "name": name})
    assert created.status_code == 201
    type_id = created.get_json()["data"]["id"]
    found = client.get("/api/object-types", query_string={"category_id": category_id, "name": name.lower()},
                       headers=operador_headers)
    assert found.get_json()["data"]["items"][0]["id"] == type_id

    duplicate = client.post("/api/object-types", headers=operador_headers,
                            json={"category_id": category_id, "name": "  " + name.upper() + " "})
    assert duplicate.status_code == 409
    assert duplicate.get_json()["data"]["existing_id"] == type_id
    missing_category = client.post("/api/object-types", headers=operador_headers, json={"category_id": 999999, "name": "X"})
    assert missing_category.status_code == 400


def test_pa21_inactivation_blocked_by_dependencies(client, admin_headers, operador_headers):
    campus_id, block_id = get_block(client, admin_headers, "Poblado", "Bloque A")
    response = client.patch(f"/api/campuses/{campus_id}/inactivate", headers=admin_headers, json={"reason": "Prueba de bloqueo"})
    assert response.status_code == 409 and "bloque" in response.get_json()["message"]

    new_object(client, operador_headers)  # al menos un objeto DISPONIBLE en el Bloque A
    response = client.patch(f"/api/blocks/{block_id}/inactivate", headers=admin_headers, json={"reason": "Prueba de bloqueo"})
    assert response.status_code == 409

    type_id = get_type_id(client, admin_headers, "Celular")
    response = client.patch(f"/api/object-types/{type_id}/inactivate", headers=admin_headers, json={"reason": "Prueba de bloqueo"})
    assert response.status_code == 409


def test_pa21_inactive_catalog_stays_in_history(client, admin_headers, operador_headers):
    categories = client.get("/api/object-categories?name=papeleria", headers=admin_headers).get_json()["data"]["items"]
    category_id = categories[0]["id"]
    new_type = client.post("/api/object-types", headers=admin_headers,
                           json={"category_id": category_id, "name": unique("Tipo histórico")}).get_json()["data"]
    object_lost, _, _ = returned_object_with_type(client, operador_headers, new_type["id"])
    # El objeto está DEVUELTO: ya no bloquea la inactivación del tipo
    assert client.patch(f"/api/object-types/{new_type['id']}/inactivate", headers=admin_headers,
                        json={"reason": "Tipo obsoleto"}).status_code == 200
    detail = client.get(f"/api/object-lost/{object_lost['id']}", headers=operador_headers).get_json()["data"]
    assert detail["object_type"]["name"] == new_type["name"]
    # Un tipo inactivo no se acepta en nuevos registros
    response = create_object(client, operador_headers, object_type_id=new_type["id"])
    assert response.status_code == 400


def returned_object_with_type(client, headers, type_id):
    object_lost = new_object(client, headers, object_type_id=type_id)
    claim = accepted_claim(client, headers, object_lost["id"])
    record = client.post("/api/returns", headers=headers, json={
        "claim_id": claim["id"], "verification_summary": "Verificado", "owner_confirmation": True})
    assert record.status_code == 201
    return object_lost, claim, record.get_json()["data"]


def test_block_reactivation_requires_active_campus(client, admin_headers):
    campus = client.post("/api/campuses", headers=admin_headers, json={"name": unique("Sede Temporal")}).get_json()["data"]
    block = client.post("/api/blocks", headers=admin_headers, json={"campus_id": campus["id"], "name": "Único"}).get_json()["data"]
    assert client.patch(f"/api/blocks/{block['id']}/inactivate", headers=admin_headers, json={"reason": "Cierre"}).status_code == 200
    assert client.patch(f"/api/campuses/{campus['id']}/inactivate", headers=admin_headers, json={"reason": "Cierre"}).status_code == 200
    response = client.patch(f"/api/blocks/{block['id']}/reactivate", headers=admin_headers, json={"reason": "Reapertura"})
    assert response.status_code == 409
    assert client.patch(f"/api/campuses/{campus['id']}/reactivate", headers=admin_headers, json={"reason": "Reapertura"}).status_code == 200
    assert client.patch(f"/api/blocks/{block['id']}/reactivate", headers=admin_headers, json={"reason": "Reapertura"}).status_code == 200


def test_reason_required_for_inactivation(client, admin_headers):
    department = client.post("/api/departments", headers=admin_headers, json={"name": unique("Dep")}).get_json()["data"]
    response = client.patch(f"/api/departments/{department['id']}/inactivate", headers=admin_headers, json={})
    assert response.status_code == 400 and "motivo" in response.get_json()["message"]


def test_pagination_validation(client, admin_headers):
    assert client.get("/api/campuses?page_size=0", headers=admin_headers).status_code == 400
    assert client.get("/api/campuses?page_size=101", headers=admin_headers).status_code == 400
    assert client.get("/api/campuses?page=abc", headers=admin_headers).status_code == 400
    empty = client.get("/api/campuses?name=" + unique("nada"), headers=admin_headers).get_json()
    assert empty["data"]["total"] == 0 and "No se encontraron" in empty["message"]


# ---------------------------------------------------------------- Persons

def test_persons_crud_and_permissions(client, operador_headers, consulta_headers, admin_headers):
    person = create_person(client, operador_headers, affiliation_type="visitante", email="Visit@Test.ces")
    assert person["affiliation_type"] == "VISITANTE" and person["email"] == "visit@test.ces"
    duplicate = client.post("/api/persons", headers=operador_headers, json={
        "identification": person["identification"], "full_name": "Otra", "affiliation_type": "EMPLEADO"})
    assert duplicate.status_code == 409
    bad_type = client.post("/api/persons", headers=operador_headers, json={
        "identification": unique("CC"), "full_name": "Otra", "affiliation_type": "ALIEN"})
    assert bad_type.status_code == 400
    updated = client.patch(f"/api/persons/{person['id']}", headers=operador_headers, json={"phone": "3000000000"})
    assert updated.status_code == 200 and updated.get_json()["data"]["phone"] == "3000000000"
    found = client.get(f"/api/persons?identification={person['identification']}", headers=operador_headers)
    assert found.get_json()["data"]["total"] == 1
    assert client.get("/api/persons", headers=consulta_headers).status_code == 403
    assert client.patch(f"/api/persons/{person['id']}/inactivate", headers=operador_headers,
                        json={"reason": "No permitido"}).status_code == 403
    assert client.patch(f"/api/persons/{person['id']}/inactivate", headers=admin_headers,
                        json={"reason": "Registro duplicado"}).status_code == 200
    assert client.patch(f"/api/persons/{person['id']}/reactivate", headers=admin_headers,
                        json={"reason": "Se necesitaba"}).status_code == 200


def test_person_inactivation_blocked_with_pending_claim(client, operador_headers, admin_headers):
    object_lost = new_object(client, operador_headers)
    claimant = create_person(client, operador_headers)
    client.post("/api/claims", headers=operador_headers, json={
        "object_lost_id": object_lost["id"], "claimant_person_id": claimant["id"], "evidence": "Es mío"})
    response = client.patch(f"/api/persons/{claimant['id']}/inactivate", headers=admin_headers,
                            json={"reason": "Prueba de pendientes"})
    assert response.status_code == 409
