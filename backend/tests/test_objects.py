import os
from datetime import datetime, timedelta, timezone
from sqlalchemy import text
from app.extensions import db
from tests.helpers import (
    unique, photo, jpeg_bytes, png_bytes, object_form, create_object, new_object, get_block,
    create_person, returned_object
)


def count_files(app):
    return len(os.listdir(app.config["UPLOAD_FOLDER"]))


# ---------------------------------------------------------------- PA08

def test_pa08_reception_with_two_photos(client, operador_headers):
    me = client.get("/api/auth/me", headers=operador_headers).get_json()["data"]
    response = create_object(client, operador_headers, photos=2, received_by_user_id=1, status="DEVUELTO", code="HACK")
    assert response.status_code == 201
    body = response.get_json()
    assert body["ok"] is True and body["message"] == "Objeto registrado correctamente."
    data = body["data"]
    assert data["code"] == f"OBJ-{data['id']:06d}"
    assert data["received_by"]["id"] == me["id"]          # tomado del JWT, no del cliente
    assert data["status"] == "DISPONIBLE" and data["is_active"] is True and data["version"] == 1
    assert data["active_photos"] == 2
    assert data["finder_person"]["full_name"] == "Persona de prueba"
    photos = client.get(f"/api/object-lost/{data['id']}/photos", headers=operador_headers).get_json()["data"]
    assert len(photos) == 2 and {item["mime_type"] for item in photos} == {"image/jpeg"}
    file_response = client.get(photos[0]["file_url"], headers=operador_headers)
    assert file_response.status_code == 200 and file_response.content_type == "image/jpeg"


# ---------------------------------------------------------------- PA06

def test_pa06_rejects_foreign_missing_or_inactive_block(client, operador_headers, admin_headers):
    sabaneta_id, _ = get_block(client, operador_headers, "Sabaneta", "Bloque principal")
    response = create_object(client, operador_headers, found_campus_id=sabaneta_id)  # Bloque A es de Poblado
    assert response.status_code == 400
    assert response.get_json()["message"] == "El bloque de hallazgo no pertenece a la sede seleccionada."
    assert create_object(client, operador_headers, found_block_id=999999).status_code == 400

    campus_id, _ = get_block(client, admin_headers, "Poblado", "Bloque A")
    block = client.post("/api/blocks", headers=admin_headers, json={"campus_id": campus_id, "name": unique("Bloque Z")}).get_json()["data"]
    client.patch(f"/api/blocks/{block['id']}/inactivate", headers=admin_headers, json={"reason": "Bloque cerrado"})
    response = create_object(client, operador_headers, found_block_id=block["id"])
    assert response.status_code == 400 and "inactivo" in response.get_json()["message"]


# ---------------------------------------------------------------- PA09

def test_pa09_rejects_invalid_receptions(client, operador_headers, app):
    files_before = count_files(app)
    assert create_object(client, operador_headers, photos=0).status_code == 400
    assert create_object(client, operador_headers, photos=6).status_code == 400

    form = object_form(client, operador_headers)
    form["photos"] = [photo(b"MZ\x90\x00 esto es un ejecutable renombrado", "virus.jpg")]
    response = client.post("/api/object-lost", headers=operador_headers, data=form, content_type="multipart/form-data")
    assert response.status_code == 400 and "JPEG o PNG" in response.get_json()["message"]

    form = object_form(client, operador_headers)
    big = jpeg_bytes() + b"0" * (5 * 1024 * 1024)
    form["photos"] = [photo(big, "grande.jpg")]
    response = client.post("/api/object-lost", headers=operador_headers, data=form, content_type="multipart/form-data")
    assert response.status_code == 400 and "5 MB" in response.get_json()["message"]

    future = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    response = create_object(client, operador_headers, found_at=future)
    assert response.status_code == 400 and "futura" in response.get_json()["message"]
    assert count_files(app) == files_before  # ningún archivo quedó escrito


def test_reception_accepts_png_and_missing_fields(client, operador_headers):
    form = object_form(client, operador_headers)
    form["photos"] = [photo(png_bytes(), "foto.png")]
    assert client.post("/api/object-lost", headers=operador_headers, data=form,
                       content_type="multipart/form-data").status_code == 201
    form = object_form(client, operador_headers)
    del form["description"]
    form["photos"] = [photo()]
    response = client.post("/api/object-lost", headers=operador_headers, data=form, content_type="multipart/form-data")
    assert response.status_code == 400 and "description" in response.get_json()["message"]


# ---------------------------------------------------------------- PA10

def test_pa10_storage_failure_leaves_no_partial_reception(client, operador_headers, app):
    description = unique("Reception que fallará")
    files_before = count_files(app)
    response = create_object(client, operador_headers, photos=3, description=description,
                             extra_headers={"X-Simulate-Storage-Failure": "true"})
    assert response.status_code == 500
    assert response.get_json()["ok"] is False
    assert count_files(app) == files_before  # compensación: archivos temporales retirados
    found = client.get("/api/object-lost", query_string={"text": description}, headers=operador_headers).get_json()
    assert found["data"]["total"] == 0
    inventory = client.get("/api/inventory", query_string={"text": description}, headers=operador_headers).get_json()
    assert inventory["data"]["total"] == 0


# ---------------------------------------------------------------- PA11

def test_pa11_edit_with_reason_history_and_version(client, operador_headers):
    object_lost = new_object(client, operador_headers)
    old_description = object_lost["description"]
    no_reason = client.patch(f"/api/object-lost/{object_lost['id']}", headers=operador_headers,
                             json={"description": "Nueva", "version": 1})
    assert no_reason.status_code == 400
    ok = client.patch(f"/api/object-lost/{object_lost['id']}", headers=operador_headers,
                      json={"description": "Celular negro con funda azul", "reason": "Se precisa el color", "version": 1})
    assert ok.status_code == 200 and ok.get_json()["data"]["version"] == 2
    stale = client.patch(f"/api/object-lost/{object_lost['id']}", headers=operador_headers,
                         json={"description": "Otro cambio", "reason": "Versión vieja", "version": 1})
    assert stale.status_code == 409 and stale.get_json()["data"]["current_version"] == 2

    history = client.get(f"/api/object-lost/{object_lost['id']}/history", headers=operador_headers).get_json()["data"]["items"]
    update = [item for item in history if item["action"] == "UPDATE"][0]
    assert update["before_data"]["description"] == old_description
    assert update["after_data"]["description"] == "Celular negro con funda azul"
    assert update["reason"] == "Se precisa el color"


def test_edit_rejects_not_editable_fields(client, operador_headers):
    object_lost = new_object(client, operador_headers)
    for field, value in [("status", "DEVUELTO"), ("received_by_user_id", 1), ("code", "X"), ("is_active", False)]:
        response = client.patch(f"/api/object-lost/{object_lost['id']}", headers=operador_headers,
                                json={field: value, "reason": "Intento manipulado", "version": 1})
        assert response.status_code == 400 and "no permitidos" in response.get_json()["message"]


# ---------------------------------------------------------------- PA12 y PA13

def test_pa12_pa13_inactivate_and_reactivate(client, operador_headers, admin_headers, app):
    object_lost = new_object(client, operador_headers)
    object_id = object_lost["id"]
    response = client.patch(f"/api/object-lost/{object_id}/inactivate", headers=operador_headers,
                            json={"reason": "Registro equivocado"})
    assert response.status_code == 200 and response.get_json()["data"]["is_active"] is False

    with app.app_context():
        assert db.session.execute(text("SELECT count(*) FROM object_lost WHERE id = :id"), {"id": object_id}).scalar() == 1
    inventory = client.get("/api/inventory", query_string={"code": object_lost["code"]}, headers=operador_headers).get_json()
    assert inventory["data"]["total"] == 0
    history = client.get(f"/api/object-lost/{object_id}/history", headers=operador_headers).get_json()["data"]["items"]
    assert "INACTIVATE" in [item["action"] for item in history]

    # Operaciones sobre un objeto inactivo se rechazan
    assert client.patch(f"/api/object-lost/{object_id}", headers=operador_headers,
                        json={"description": "x", "reason": "No se puede", "version": 2}).status_code == 409
    assert client.post(f"/api/object-lost/{object_id}/photos", headers=operador_headers,
                       data={"photos": [photo()]}, content_type="multipart/form-data").status_code == 409
    person = create_person(client, operador_headers)
    assert client.post("/api/claims", headers=operador_headers, json={
        "object_lost_id": object_id, "claimant_person_id": person["id"], "evidence": "Es mío"}).status_code == 409

    # Solo ADMIN reactiva
    assert client.patch(f"/api/object-lost/{object_id}/reactivate", headers=operador_headers,
                        json={"reason": "Quiero reactivar"}).status_code == 403
    response = client.patch(f"/api/object-lost/{object_id}/reactivate", headers=admin_headers,
                            json={"reason": "Fue un error inactivarlo"})
    assert response.status_code == 200
    assert response.get_json()["data"]["is_active"] is True and response.get_json()["data"]["status"] == "DISPONIBLE"


# ---------------------------------------------------------------- PA14

def test_pa14_photo_inactivation_keeps_file_and_last_photo(client, operador_headers, admin_headers, app):
    object_lost = new_object(client, operador_headers, photos=2)
    photos = client.get(f"/api/object-lost/{object_lost['id']}/photos", headers=operador_headers).get_json()["data"]
    first, second = photos
    response = client.patch(f"/api/object-photos/{first['id']}/inactivate", headers=operador_headers,
                            json={"reason": "Foto equivocada"})
    assert response.status_code == 200 and response.get_json()["data"]["is_active"] is False
    assert client.get(first["file_url"], headers=admin_headers).status_code == 200  # el archivo se conserva
    last = client.patch(f"/api/object-photos/{second['id']}/inactivate", headers=operador_headers,
                        json={"reason": "Tampoco sirve"})
    assert last.status_code == 409 and "última" in last.get_json()["message"]
    assert client.patch(f"/api/object-photos/{first['id']}/reactivate", headers=operador_headers,
                        json={"reason": "Sí servía"}).status_code == 403
    assert client.patch(f"/api/object-photos/{first['id']}/reactivate", headers=admin_headers,
                        json={"reason": "Sí servía"}).status_code == 200


def test_add_photos_respects_maximum(client, operador_headers):
    object_lost = new_object(client, operador_headers, photos=4)
    url = f"/api/object-lost/{object_lost['id']}/photos"
    assert client.post(url, headers=operador_headers, data={"photos": [photo(), photo()]},
                       content_type="multipart/form-data").status_code == 400
    response = client.post(url, headers=operador_headers, data={"photos": [photo(png_bytes(), "x.png")]},
                           content_type="multipart/form-data")
    assert response.status_code == 201
    photos = client.get(url, headers=operador_headers).get_json()["data"]
    assert len([item for item in photos if item["is_active"]]) == 5


# ---------------------------------------------------------------- PA15

def test_pa15_combined_filters_day_limits_and_pagination(client, operador_headers, app):
    sabaneta_id, sabaneta_block = get_block(client, operador_headers, "Sabaneta", "Bloque principal")
    marker = unique("filtro")
    created = [new_object(client, operador_headers, description=f"{marker} {index}",
                          found_campus_id=sabaneta_id, found_block_id=sabaneta_block) for index in range(3)]
    # 14 oct 2026, 23:30 hora de Bogotá = 15 oct 04:30 UTC (límite del día)
    with app.app_context():
        db.session.execute(text(
            "UPDATE object_lost SET found_at = '2026-10-14 20:00-05', received_at = '2026-10-14 23:30-05' WHERE id = :id"
        ), {"id": created[0]["id"]})
        db.session.execute(text(
            "UPDATE object_lost SET found_at = '2026-10-15 00:10-05', received_at = '2026-10-15 00:30-05' WHERE id = :id"
        ), {"id": created[1]["id"]})
        db.session.commit()

    def search(**params):
        params.update({"text": marker, "campus_id": sabaneta_id})
        return client.get("/api/object-lost", query_string=params, headers=operador_headers).get_json()["data"]

    day_14 = search(date_from="2026-10-14", date_to="2026-10-14")
    assert [item["id"] for item in day_14["items"]] == [created[0]["id"]]
    day_15 = search(date_from="2026-10-15", date_to="2026-10-15")
    assert [item["id"] for item in day_15["items"]] == [created[1]["id"]]
    assert search(date_from="2026-10-14", date_to="2026-10-15")["total"] == 2

    page_1 = search(page=1, page_size=2)
    page_2 = search(page=2, page_size=2)
    assert page_1["total"] == 3 and len(page_1["items"]) == 2 and len(page_2["items"]) == 1
    assert page_1["items"][0]["id"] == created[2]["id"]  # orden: received_at desc, id desc

    type_id = page_1["items"][0]["object_type"]["id"]
    assert search(object_type_id=type_id, date_from="2026-10-14", date_to="2026-10-14")["total"] == 1
    empty = client.get("/api/object-lost", query_string={"text": marker, "date_from": "2020-01-01", "date_to": "2020-01-02"},
                       headers=operador_headers).get_json()
    assert empty["data"]["total"] == 0 and "No se encontraron" in empty["message"]
    inverted = client.get("/api/object-lost", query_string={"date_from": "2026-10-15", "date_to": "2026-10-14"},
                          headers=operador_headers)
    assert inverted.status_code == 400
    assert client.get("/api/object-lost?page_size=500", headers=operador_headers).status_code == 400


# ---------------------------------------------------------------- PA19

def test_pa19_consulta_reduced_projection_and_no_changes(client, operador_headers, consulta_headers):
    object_lost = new_object(client, operador_headers)
    listing = client.get("/api/object-lost", query_string={"code": object_lost["code"]}, headers=consulta_headers)
    assert listing.status_code == 200
    item = listing.get_json()["data"]["items"][0]
    assert set(item.keys()) == {"id", "code", "object_type", "category", "campus", "received_at", "status"}
    detail = client.get(f"/api/object-lost/{object_lost['id']}", headers=consulta_headers).get_json()["data"]
    for private in ["description", "finder_person", "found_location", "custody_location", "received_by", "cover_photo_id"]:
        assert private not in detail
    assert client.get(f"/api/object-lost/{object_lost['id']}/photos", headers=consulta_headers).status_code == 403
    assert client.get(f"/api/object-photos/{object_lost['cover_photo_id']}/file", headers=consulta_headers).status_code == 403
    assert client.get("/api/object-lost?status=DEVUELTO", headers=consulta_headers).status_code == 403
    assert client.get("/api/object-lost?is_active=false", headers=consulta_headers).status_code == 403
    assert client.get("/api/persons", headers=consulta_headers).status_code == 403
    assert client.get(f"/api/object-lost/{object_lost['id']}/history", headers=consulta_headers).status_code == 403
    # No modifica nada
    assert create_object(client, operador_headers, photos=1).status_code == 201
    form = object_form(client, operador_headers)
    form["photos"] = [photo()]
    assert client.post("/api/object-lost", headers=consulta_headers, data=form,
                       content_type="multipart/form-data").status_code == 403
    assert client.patch(f"/api/object-lost/{object_lost['id']}", headers=consulta_headers,
                        json={"description": "x", "reason": "No debe", "version": 1}).status_code == 403
    assert client.patch(f"/api/object-lost/{object_lost['id']}/inactivate", headers=consulta_headers,
                        json={"reason": "No debe"}).status_code == 403
    assert client.post("/api/object-types", headers=consulta_headers, json={"category_id": 1, "name": "X"}).status_code == 403


# ---------------------------------------------------------------- PA22

def test_pa22_no_delete_routes_and_database_blocks_delete(app, client, operador_headers):
    returned_object(client, operador_headers)  # asegura filas en todas las tablas revisadas
    delete_routes = [rule.rule for rule in app.url_map.iter_rules() if "DELETE" in rule.methods]
    assert delete_routes == []
    with app.app_context():
        for table in ["object_lost", "object_photos", "audit_logs", "return_records", "users"]:
            try:
                db.session.execute(text(f"DELETE FROM {table}"))
                db.session.commit()
                assert False, f"Se pudo borrar en {table}"
            except Exception as error:
                db.session.rollback()
                assert "No se permite eliminar" in str(error)
        try:
            db.session.execute(text("TRUNCATE claims CASCADE"))
            db.session.commit()
            assert False, "Se pudo vaciar claims"
        except Exception as error:
            db.session.rollback()
            assert "No se permite eliminar" in str(error)
        try:
            db.session.execute(text("UPDATE audit_logs SET reason = 'cambiado'"))
            db.session.commit()
            assert False, "Se pudo modificar la auditoría"
        except Exception as error:
            db.session.rollback()
            assert "solo lectura" in str(error)


def test_delete_method_not_allowed(client, admin_headers):
    response = client.delete("/api/campuses/1", headers=admin_headers)
    assert response.status_code == 405 and response.get_json()["ok"] is False
