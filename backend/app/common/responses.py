from flask import jsonify

# Contrato de respuesta que exige el enunciado (sección 5):
# {"ok": true/false, "message": "...", "data": ...}


def success_response(message, data=None, status_code=200):
    return jsonify({
        "ok": True,
        "message": message,
        "data": data
    }), status_code


def error_response(message, status_code=400, data=None):
    return jsonify({
        "ok": False,
        "message": message,
        "data": data
    }), status_code


def page_data(items, page, page_size, total):
    """Formato de los listados paginados: items, page, page_size y total."""
    return {
        "items": items,
        "page": page,
        "page_size": page_size,
        "total": total
    }


def list_message(total):
    if total == 0:
        return "No se encontraron resultados con los filtros aplicados."
    return "Consulta exitosa."
