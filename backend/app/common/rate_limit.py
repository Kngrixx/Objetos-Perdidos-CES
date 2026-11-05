import time
from flask import current_app, request
from app.common.errors import AppError

# Límite de intentos sencillo, en memoria del proceso.
# Guarda la hora de cada intento por "acción + IP" y, si en la ventana de tiempo
# hay más intentos de los permitidos, responde 429.
# Limitación conocida: se reinicia al reiniciar el servidor y no se comparte entre
# varios procesos (suficiente para el proyecto; documentado en decisiones).

attempts = {}


def check_rate_limit(action, max_attempts):
    window = current_app.config["RATE_LIMIT_WINDOW_SECONDS"]
    key = f"{action}:{request.remote_addr}"
    now = time.time()

    recent = [moment for moment in attempts.get(key, []) if now - moment < window]
    if len(recent) >= max_attempts:
        attempts[key] = recent
        raise AppError("Demasiados intentos. Espere un momento e intente de nuevo.", 429)

    recent.append(now)
    attempts[key] = recent


def reset_rate_limits():
    attempts.clear()
