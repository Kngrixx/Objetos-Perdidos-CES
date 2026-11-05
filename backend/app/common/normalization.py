import re
import unicodedata

# Tratamiento de nombres de catálogo (decisión documentada):
#   - se quitan espacios al inicio y al final y se colapsan los repetidos,
#   - se pasa a minúsculas,
#   - se quitan las tildes y diéresis (á -> a, ü -> u),
#   - se CONSERVA la ñ (año y ano son palabras distintas).
# Ejemplo: "  Cámara   Web " -> "camara web"
# La base de datos tiene UNIQUE sobre este valor normalizado.


def clean_text(value):
    """Texto para mostrar: sin espacios sobrantes, conserva mayúsculas y tildes."""
    if value is None:
        return None
    return re.sub(r"\s+", " ", str(value)).strip()


def normalize_name(value):
    text = clean_text(value) or ""
    text = text.lower().replace("ñ", "\u0000")
    text = unicodedata.normalize("NFD", text)
    text = "".join(char for char in text if unicodedata.category(char) != "Mn")
    return text.replace("\u0000", "ñ")


def normalize_email(value):
    return (value or "").strip().lower()
