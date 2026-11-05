from fpdf import FPDF

# Generación de PDF con fpdf2 (librería añadida: la clase no tenía PDF).
# Las fuentes base de PDF (Helvetica) usan latin-1: cubren tildes y ñ del español.


def pdf_text(value):
    text = "" if value is None else str(value)
    return text.encode("latin-1", "replace").decode("latin-1")


def new_document(title, orientation="P"):
    pdf = FPDF(orientation=orientation, unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 8, pdf_text("Universidad CES - Gestión de objetos perdidos"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, pdf_text(title), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    return pdf


def label_value(pdf, label, value):
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(55, 7, pdf_text(label))
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 7, pdf_text(value), new_x="LMARGIN", new_y="NEXT")


def build_receipt_pdf(receipt):
    """Constancia de devolución: código, descripción, propietario, operador y fecha."""
    pdf = new_document("Constancia de devolución " + receipt["receipt_reference"])
    label_value(pdf, "Código del objeto:", receipt["code"])
    label_value(pdf, "Tipo / categoría:", f'{receipt["object_type"]} / {receipt["category"]}')
    label_value(pdf, "Descripción:", receipt["description"])
    label_value(pdf, "Propietario:", f'{receipt["owner_name"]} (identificación {receipt["owner_identification"]})')
    label_value(pdf, "Operador que entrega:", receipt["delivered_by"])
    label_value(pdf, "Fecha de devolución:", receipt["returned_at"])
    label_value(pdf, "Reclamación:", f'#{receipt["claim_id"]}')
    label_value(pdf, "Verificación:", receipt["verification_summary"])
    label_value(pdf, "Mecanismo de recepción:", "Confirmación digital del propietario registrada en el sistema.")
    pdf.ln(4)
    pdf.set_font("Helvetica", "I", 9)
    pdf.multi_cell(0, 5, pdf_text("Documento generado por el sistema. Generado: " + receipt["generated_at"]))
    return bytes(pdf.output())


def build_inventory_pdf(rows, filters_text, generated_at, total):
    pdf = new_document("Inventario de objetos disponibles", orientation="L")
    pdf.set_font("Helvetica", "", 9)
    pdf.multi_cell(0, 5, pdf_text("Generado: " + generated_at), new_x="LMARGIN", new_y="NEXT")
    pdf.multi_cell(0, 5, pdf_text("Filtros aplicados: " + filters_text), new_x="LMARGIN", new_y="NEXT")
    pdf.multi_cell(0, 5, pdf_text(f"Total de objetos: {total}"), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    headers = ["Código", "Tipo", "Categoría", "Sede", "Bloque hallazgo", "Recibido", "Custodia"]
    widths = [26, 42, 40, 30, 34, 32, 73]
    pdf.set_font("Helvetica", "B", 9)
    for header, width in zip(headers, widths):
        pdf.cell(width, 7, pdf_text(header), border=1)
    pdf.ln()

    pdf.set_font("Helvetica", "", 8)
    for row in rows:
        values = [row["code"], row["object_type"], row["category"], row["campus"],
                  row["found_block"], row["received_at"], row["custody"]]
        for value, width in zip(values, widths):
            text = pdf_text(value)
            while pdf.get_string_width(text) > width - 2 and len(text) > 3:
                text = text[:-4] + "..."
            pdf.cell(width, 6, text, border=1)
        pdf.ln()

    if not rows:
        pdf.cell(0, 7, pdf_text("No hay objetos que coincidan con los filtros."), new_x="LMARGIN", new_y="NEXT")
    return bytes(pdf.output())
