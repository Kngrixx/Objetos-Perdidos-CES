# Backend – Objetos perdidos CES

# Pasos para crear el entorno virtual

python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.venv\Scripts\activate
deactivate

## Instalar librerías desde requirements.txt

pip install -r requirements.txt

Además de las librerías de clase (flask, flask-SQLAlchemy, psycopg[binary], python-dotenv, Flask-JWT-Extended, Flask-Migrate, flask-cors) se usan **fpdf2** (PDF) y **pytest** (pruebas).

## Configuración

copy .env.example .env      # y poner JWT_SECRET_KEY (ver README principal)

## Base de datos (migraciones de Flask-Migrate)

flask db upgrade            # aplica las 8 migraciones de migrations/versions

Para un cambio nuevo en los modelos (como en clase):
flask db migrate -m "descripcion del cambio"
flask db upgrade

## Datos iniciales

python seed.py              # se puede correr varias veces sin duplicar
python seed_demo.py         # opcional, datos ficticios de demostración

## Ejecutar

python run.py               # http://localhost:5000/api/health

## Pruebas

python -m pytest -q

## Estructura

- `app/models/`: un archivo por tabla (15).
- `app/routes/`: un Blueprint por módulo; cada ruta solo llama al controller. `@jwt_required()` en todas las rutas protegidas y `@roles_required(...)` donde aplica.
- `app/controllers/`: leen `request`, validan formato y responden con `success_response(...)`.
- `app/services/`: reglas de negocio, consultas con `select()` y transacciones con `db.session`.
- `app/common/`: respuesta `{ok, message, data}`, errores, seguridad JWT, paginación, fechas, fotos, PDF, correo y límite de intentos.

Rutas: 77 del enunciado + 4 del dashboard + 3 de salud (`/api/health`, `/api/health/status`, `/api/health/db_status`).
