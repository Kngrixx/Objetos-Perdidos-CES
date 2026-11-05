from tests.helpers import new_object, get_block, returned_object


# ---------------------------------------------------------------- PA20

def test_pa20_export_pdf_matches_inventory_query(client, operador_headers):
    campus_id, block_id = get_block(client, operador_headers, "Sabaneta", "Bloque principal")
    new_object(client, operador_headers, found_campus_id=campus_id, found_block_id=block_id)
    params = {"campus_id": campus_id, "date_from": "2026-01-01", "date_to": "2030-12-31"}
    inventory = client.get("/api/inventory", query_string=params, headers=operador_headers).get_json()["data"]
    export = client.get("/api/inventory/export", query_string=params, headers=operador_headers)
    assert export.status_code == 200
    assert export.content_type == "application/pdf" and export.data.startswith(b"%PDF")
    assert int(export.headers["X-Total-Count"]) == inventory["total"] >= 1
    assert "attachment" in export.headers["Content-Disposition"]


def test_inventory_summary_and_validations(client, operador_headers):
    new_object(client, operador_headers)
    summary = client.get("/api/inventory/summary", headers=operador_headers).get_json()["data"]
    assert summary["total_available"] == sum(item["total"] for item in summary["by_type"])
    assert {item["status"] for item in summary["by_status"]} == {"DISPONIBLE", "DEVUELTO", "INACTIVO"}
    assert client.get("/api/inventory?status=DEVUELTO", headers=operador_headers).status_code == 400


def test_audit_logs_admin_only(client, admin_headers, operador_headers):
    object_lost = new_object(client, operador_headers)
    logs = client.get("/api/audit-logs", query_string={"entity": "object_lost", "entity_id": object_lost["id"]},
                      headers=admin_headers).get_json()["data"]
    assert logs["total"] >= 1 and logs["items"][0]["action"] == "CREATE"
    assert "password_hash" not in str(client.get("/api/audit-logs?entity=user", headers=admin_headers).get_json())
    assert client.get("/api/audit-logs", headers=operador_headers).status_code == 403
    assert client.get(f"/api/object-lost/{object_lost['id']}/history", headers=operador_headers).status_code == 200


def test_dashboard_admin_only_and_consistent(client, admin_headers, operador_headers, consulta_headers):
    returned_object(client, operador_headers)
    for url in ["/api/dashboard/summary", "/api/dashboard/by-category", "/api/dashboard/by-campus", "/api/dashboard/recent"]:
        assert client.get(url, headers=operador_headers).status_code == 403
        assert client.get(url, headers=consulta_headers).status_code == 403
        assert client.get(url).status_code == 401
        assert client.get(url, headers=admin_headers).status_code == 200

    summary = client.get("/api/dashboard/summary", headers=admin_headers).get_json()["data"]
    assert summary["total"] == summary["available"] + summary["returned"] + summary["inactive"]
    by_campus = client.get("/api/dashboard/by-campus", headers=admin_headers).get_json()["data"]
    assert sum(item["total"] for item in by_campus) == summary["available"] + summary["returned"]
    campus_id = by_campus[0]["campus_id"]
    filtered = client.get("/api/dashboard/summary", query_string={"campus_id": campus_id},
                          headers=admin_headers).get_json()["data"]
    assert filtered["available"] + filtered["returned"] == by_campus[0]["total"]
    old = client.get("/api/dashboard/summary", query_string={"date_from": "2000-01-01", "date_to": "2000-01-31"},
                     headers=admin_headers).get_json()["data"]
    assert old["total"] == 0
    recent = client.get("/api/dashboard/recent?limit=3", headers=admin_headers).get_json()["data"]
    assert len(recent) <= 3
    assert client.get("/api/dashboard/recent?limit=0", headers=admin_headers).status_code == 400
