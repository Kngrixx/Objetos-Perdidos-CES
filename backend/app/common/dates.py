from datetime import datetime, date, time, timedelta, timezone
from zoneinfo import ZoneInfo
from app.common.errors import AppError

# Regla del enunciado: guardar en UTC y mostrar en America/Bogota.
# El "día" de los filtros es el día de Bogotá.
BOGOTA = ZoneInfo("America/Bogota")


def utc_now():
    return datetime.now(timezone.utc)


def to_iso(value):
    """Fecha para el JSON: ISO 8601 en UTC (el frontend la muestra en hora de Bogotá)."""
    if value is None:
        return None
    return value.astimezone(timezone.utc).isoformat()


def parse_datetime(value, field_name):
    """Convierte texto ISO 8601 a datetime en UTC. Sin zona horaria se asume hora de Bogotá."""
    if value in (None, ""):
        return None
    try:
        parsed = datetime.fromisoformat(str(value).strip().replace("Z", "+00:00"))
    except ValueError:
        raise AppError(f"El campo {field_name} debe ser una fecha y hora válida (ISO 8601).", 400)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=BOGOTA)
    return parsed.astimezone(timezone.utc)


def parse_date(value, field_name):
    if value in (None, ""):
        return None
    try:
        return date.fromisoformat(str(value).strip())
    except ValueError:
        raise AppError(f"El parámetro {field_name} debe tener el formato AAAA-MM-DD.", 400)


def bogota_day_range(date_from, date_to):
    """Rango de fechas locales -> rango UTC [inicio, fin) con fin EXCLUSIVO del día siguiente.

    Ejemplo: date_to=2026-10-14 incluye todo el 14 de octubre en Bogotá, es decir,
    hasta antes de 2026-10-15 00:00 de Bogotá (= 2026-10-15 05:00 UTC).
    """
    if date_from and date_to and date_from > date_to:
        raise AppError("El rango de fechas está invertido: date_from es posterior a date_to.", 400)
    start = None
    end = None
    if date_from:
        start = datetime.combine(date_from, time.min, tzinfo=BOGOTA).astimezone(timezone.utc)
    if date_to:
        end = datetime.combine(date_to + timedelta(days=1), time.min, tzinfo=BOGOTA).astimezone(timezone.utc)
    return start, end


def bogota_now_text():
    return datetime.now(BOGOTA).strftime("%Y-%m-%d %H:%M") + " (hora de Bogotá)"


def bogota_text(value):
    if value is None:
        return ""
    return value.astimezone(BOGOTA).strftime("%Y-%m-%d %H:%M")
