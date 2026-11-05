"""PA17: dos (o más) solicitudes SIMULTÁNEAS de devolución del mismo objeto.

Resultado esperado: exactamente una respuesta 201 y el resto 409; en la base queda
una sola fila en return_records para ese objeto.

Solo usa la librería estándar de Python (no hay que instalar nada).
Uso, con el backend corriendo (flask run) y el seed aplicado:
    python prueba_concurrencia.py
    python prueba_concurrencia.py --peticiones 10 --base-url http://localhost:5000/api
La contraseña del ADMIN se toma de la variable ADMIN_PASSWORD o se pide por teclado.
"""
import argparse
import getpass
import json
import os
import threading
import time
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timedelta, timezone

FOTO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fotos", "foto_prueba_1.jpg")


def call(base_url, method, path, token=None, body=None, multipart=None):
    headers = {}
    data = None
    if token:
        headers["Authorization"] = "Bearer " + token
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if multipart is not None:
        boundary = uuid.uuid4().hex
        parts = []
        for key, value in multipart["fields"].items():
            parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{key}"\r\n\r\n{value}\r\n'.encode())
        for name, content in multipart["files"]:
            parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="photos"; filename="{name}"\r\n'
                         f'Content-Type: image/jpeg\r\n\r\n'.encode() + content + b"\r\n")
        parts.append(f"--{boundary}--\r\n".encode())
        data = b"".join(parts)
        headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
    request = urllib.request.Request(base_url + path, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read().decode("utf-8"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://localhost:5000/api")
    parser.add_argument("--email", default="admin@ces.test")
    parser.add_argument("--peticiones", type=int, default=8)
    args = parser.parse_args()
    password = os.getenv("ADMIN_PASSWORD") or getpass.getpass("Contraseña del ADMIN de pruebas: ")
    base = args.base_url
    run = uuid.uuid4().hex[:6]

    status, body = call(base, "POST", "/auth/login", body={"email": args.email, "password": password})
    assert status == 200, body
    token = body["data"]["access_token"]

    _, campuses = call(base, "GET", "/campuses?name=poblado", token)
    campus_id = campuses["data"]["items"][0]["id"]
    _, blocks = call(base, "GET", f"/blocks?campus_id={campus_id}", token)
    block_id = blocks["data"]["items"][0]["id"]
    _, types = call(base, "GET", "/object-types?name=celular", token)
    type_id = types["data"]["items"][0]["id"]
    _, finder = call(base, "POST", "/persons", token, {"identification": "CONC-F-" + run, "full_name": "Quien entrega",
                                                       "affiliation_type": "ESTUDIANTE"})
    _, owner = call(base, "POST", "/persons", token, {"identification": "CONC-O-" + run, "full_name": "Propietario",
                                                      "affiliation_type": "VISITANTE"})
    with open(FOTO, "rb") as photo_file:
        photo = photo_file.read()
    status, created = call(base, "POST", "/object-lost", token, multipart={
        "fields": {
            "object_type_id": type_id, "description": "Objeto para prueba de concurrencia " + run,
            "found_campus_id": campus_id, "found_block_id": block_id, "found_location": "Prueba",
            "found_at": (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(),
            "custody_campus_id": campus_id, "custody_block_id": block_id, "custody_location": "Oficina",
            "finder_person_id": finder["data"]["id"],
        },
        "files": [("foto.jpg", photo)],
    })
    assert status == 201, created
    object_id = created["data"]["id"]
    _, claim = call(base, "POST", "/claims", token, {"object_lost_id": object_id,
                                                     "claimant_person_id": owner["data"]["id"],
                                                     "evidence": "Prueba de concurrencia", "identity_verified": True})
    claim_id = claim["data"]["id"]
    status, _ = call(base, "PATCH", f"/claims/{claim_id}/decision", token,
                     {"decision": "ACEPTADA", "reason": "Prueba de concurrencia"})
    assert status == 200

    print(f"Objeto {created['data']['code']} con reclamación ACEPTADA #{claim_id}.")
    print(f"Enviando {args.peticiones} devoluciones simultáneas...")
    barrier = threading.Barrier(args.peticiones)
    results = []

    def worker(number):
        barrier.wait()
        started = time.perf_counter()
        code, response = call(base, "POST", "/returns", token, {
            "claim_id": claim_id, "verification_summary": "Concurrencia", "owner_confirmation": True})
        results.append((number, code, response["message"], round((time.perf_counter() - started) * 1000)))

    threads = [threading.Thread(target=worker, args=(n,)) for n in range(1, args.peticiones + 1)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    for number, code, message, ms in sorted(results):
        print(f"  petición {number}: HTTP {code} ({ms} ms) - {message}")
    _, returns = call(base, "GET", f"/returns?object_lost_id={object_id}", token)
    codes = sorted(code for _, code, _, _ in results)
    ok = codes == [201] + [409] * (args.peticiones - 1) and returns["data"]["total"] == 1
    print(f"Devoluciones registradas en la base para el objeto: {returns['data']['total']}")
    print("RESULTADO:", "CORRECTO (una 201, las demás 409)" if ok else "FALLÓ")
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
