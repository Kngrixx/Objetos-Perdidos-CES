import io
import uuid
from datetime import datetime, timedelta, timezone
from PIL import Image


def unique(prefix):
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def jpeg_bytes(size=(64, 64), color="red"):
    buffer = io.BytesIO()
    Image.new("RGB", size, color).save(buffer, "JPEG")
    return buffer.getvalue()


def png_bytes(size=(64, 64), color="blue"):
    buffer = io.BytesIO()
    Image.new("RGB", size, color).save(buffer, "PNG")
    return buffer.getvalue()


def photo(content=None, name="foto.jpg"):
    return (io.BytesIO(content if content is not None else jpeg_bytes()), name)


def login_headers(client, email, password):
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.get_json()
    return {"Authorization": "Bearer " + response.get_json()["data"]["access_token"]}


def iso_hours_ago(hours):
    return (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()


def get_block(client, headers, campus_name, block_name):
    campus = client.get("/api/campuses", query_string={"name": campus_name},
                        headers=headers).get_json()["data"]["items"][0]
    blocks = client.get("/api/blocks", query_string={"campus_id": campus["id"], "name": block_name},
                        headers=headers).get_json()
    return campus["id"], blocks["data"]["items"][0]["id"]


def get_type_id(client, headers, name):
    items = client.get("/api/object-types", query_string={"name": name},
                       headers=headers).get_json()["data"]["items"]
    return [item for item in items if item["name"] == name][0]["id"]


def create_person(client, headers, **fields):
    body = {
        "identification": unique("CC"),
        "full_name": "Persona de prueba",
        "affiliation_type": "ESTUDIANTE",
    }
    body.update(fields)
    response = client.post("/api/persons", headers=headers, json=body)
    assert response.status_code == 201, response.get_json()
    return response.get_json()["data"]


def object_form(client, headers, **fields):
    campus_id, block_id = get_block(client, headers, "Poblado", "Bloque A")
    person = create_person(client, headers)
    form = {
        "object_type_id": str(get_type_id(client, headers, "Celular")),
        "description": "Celular de prueba " + unique("desc"),
        "found_campus_id": str(campus_id),
        "found_block_id": str(block_id),
        "found_location": "Cafetería",
        "found_at": iso_hours_ago(2),
        "custody_campus_id": str(campus_id),
        "custody_block_id": str(block_id),
        "custody_location": "Oficina 101",
        "finder_person_id": str(person["id"]),
    }
    form.update({key: str(value) for key, value in fields.items()})
    return form


def create_object(client, headers, photos=2, extra_headers=None, **fields):
    form = object_form(client, headers, **fields)
    form["photos"] = [photo() for _ in range(photos)]
    all_headers = dict(headers)
    all_headers.update(extra_headers or {})
    return client.post("/api/object-lost", headers=all_headers, data=form, content_type="multipart/form-data")


def new_object(client, headers, **fields):
    response = create_object(client, headers, **fields)
    assert response.status_code == 201, response.get_json()
    return response.get_json()["data"]


def accepted_claim(client, headers, object_id):
    person = create_person(client, headers)
    claim = client.post("/api/claims", headers=headers, json={
        "object_lost_id": object_id, "claimant_person_id": person["id"],
        "evidence": "Conoce el fondo de pantalla y el contenido", "identity_verified": True,
    }).get_json()["data"]
    response = client.patch(f"/api/claims/{claim['id']}/decision", headers=headers,
                            json={"decision": "ACEPTADA", "reason": "Evidencia suficiente"})
    assert response.status_code == 200, response.get_json()
    return response.get_json()["data"]


def returned_object(client, headers):
    object_lost = new_object(client, headers)
    claim = accepted_claim(client, headers, object_lost["id"])
    response = client.post("/api/returns", headers=headers, json={
        "claim_id": claim["id"], "verification_summary": "Cédula verificada", "owner_confirmation": True,
    })
    assert response.status_code == 201, response.get_json()
    return object_lost, claim, response.get_json()["data"]
