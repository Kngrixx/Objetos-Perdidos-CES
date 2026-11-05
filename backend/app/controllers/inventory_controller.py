import io
from flask import request, send_file
from app.common.dates import bogota_text, bogota_now_text
from app.common.errors import AppError
from app.common.pagination import get_page_params
from app.common.pdf import build_inventory_pdf
from app.common.responses import success_response, page_data, list_message
from app.controllers.object_lost_controller import read_object_filters, object_to_dict
from app.services.campus_service import get_campus_by_id
from app.services.block_service import get_block_by_id
from app.services.object_category_service import get_category_by_id
from app.services.object_type_service import get_object_type_by_id
from app.services.inventory_service import (
    get_inventory,
    get_inventory_for_export,
    get_inventory_summary
)


def read_inventory_filters():
    filters = read_object_filters()
    # El inventario siempre es "activo y DISPONIBLE"; no se aceptan otros valores.
    if filters["status"] not in (None, "DISPONIBLE") or filters["is_active"] is False:
        raise AppError("El inventario solo incluye objetos activos y DISPONIBLES; "
                       "use GET /api/object-lost para consultar devueltos o inactivos.", 400)
    return filters


def name_or_id(getter, record_id):
    try:
        return f"{getter(record_id).name} (id {record_id})"
    except AppError:
        return f"id {record_id}"


def describe_filters(filters):
    """Texto con los filtros aplicados, para imprimirlo en el PDF."""
    parts = []
    if filters.get("code"):
        parts.append(f'código contiene "{filters["code"]}"')
    if filters.get("text"):
        parts.append(f'texto "{filters["text"]}"')
    if filters.get("campus_id") is not None:
        parts.append("sede " + name_or_id(get_campus_by_id, filters["campus_id"]))
    if filters.get("block_id") is not None:
        parts.append("bloque " + name_or_id(get_block_by_id, filters["block_id"]))
    if filters.get("category_id") is not None:
        parts.append("categoría " + name_or_id(get_category_by_id, filters["category_id"]))
    if filters.get("object_type_id") is not None:
        parts.append("tipo " + name_or_id(get_object_type_by_id, filters["object_type_id"]))
    if request.args.get("date_from"):
        parts.append("recibidos desde " + request.args["date_from"])
    if request.args.get("date_to"):
        parts.append("hasta " + request.args["date_to"] + " (inclusive, hora de Bogotá)")
    parts.append("solo activos y DISPONIBLES")
    return "; ".join(parts)


def list_inventory_controller():
    page, page_size = get_page_params()
    objects, total = get_inventory(read_inventory_filters(), page, page_size)
    items = [object_to_dict(object_lost) for object_lost in objects]
    return success_response(list_message(total), page_data(items, page, page_size, total))


def inventory_summary_controller():
    summary = get_inventory_summary(read_inventory_filters())
    return success_response("Resumen del inventario.", summary)


def export_inventory_controller():
    filters = read_inventory_filters()
    objects = get_inventory_for_export(filters)
    rows = [{
        "code": object_lost.code,
        "object_type": object_lost.object_type.name,
        "category": object_lost.object_type.category.name,
        "campus": object_lost.found_block.campus.name,
        "found_block": object_lost.found_block.name,
        "received_at": bogota_text(object_lost.received_at),
        "custody": f"{object_lost.custody_block.name} - {object_lost.custody_location}",
    } for object_lost in objects]
    pdf_bytes = build_inventory_pdf(rows, describe_filters(filters), bogota_now_text(), len(rows))
    response = send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name="inventario_objetos_disponibles.pdf"
    )
    # El total viaja también en una cabecera para comparar con GET /inventory (PA20).
    response.headers["X-Total-Count"] = str(len(rows))
    return response
