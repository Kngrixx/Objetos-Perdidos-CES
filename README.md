# Gestión de objetos perdidos – Universidad CES

Proyecto final de Bases de Datos. Backend Flask + PostgreSQL con la estructura de clase (routes → controllers → services → models), frontend Angular 21 y colección de Postman.

```
objetos_perdidos_ces/
  backend/    API Flask (run.py, config.py, app/, migrations/, tests/, seed.py, seed_demo.py)
  frontend/   Angular 21 (core/services, pages/, components/)
  postman/    colección, entorno, fotos de prueba, prueba de concurrencia y reporte
  docs/       análisis, modelo E-R, diccionario, arquitectura, guion de demo, informe, matriz
```

## Requisitos

- Python 3.12, 3.13 o 3.14
- PostgreSQL 14 o superior (probado con 16) y DBeaver
- Node.js 20.19+ o 22.12+ (para Angular 21) y npm
- Postman (y opcionalmente newman)

## 1. Base de datos (una sola vez)

Abra DBeaver conectado como el usuario `postgres` (o *SQL Shell (psql)*) y ejecute:

```sql
CREATE USER objetos WITH PASSWORD 'objetos_dev';
CREATE DATABASE objetos_perdidos OWNER objetos;
CREATE DATABASE objetos_perdidos_test OWNER objetos;   -- solo para pytest
```

Son credenciales **ficticias de desarrollo**.

## 2. Backend (PowerShell)

```powershell
cd backend
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Abra `.env` y pegue la clave que imprimió el último comando en `JWT_SECRET_KEY=`. Luego:

```powershell
flask db upgrade        # crea las 15 tablas y los triggers (8 migraciones)
python seed.py          # roles, sedes, bloques, 15 dependencias, 12 categorías, 129 tipos y el ADMIN
python seed_demo.py     # opcional: 24 objetos de demostración con fotos
python run.py           # http://localhost:5000/api/health
```

Qué debe ver: `flask db upgrade` termina en `Running upgrade f357c059a7eb -> 8d6746a80648`; `python seed.py` imprime `Totales en la base: 12 categorías y 129 tipos de objeto.`; en el navegador `http://localhost:5000/api/health/db_status` responde `"ok": true`.

Pruebas automáticas (con el entorno virtual activo, dentro de `backend`):

```powershell
python -m pytest -q     # 55 pruebas; usan la base objetos_perdidos_test y la recrean cada vez
```

## 3. Ver las tablas en DBeaver

*Nueva conexión → PostgreSQL*: host `localhost`, puerto `5432`, base `objetos_perdidos`, usuario `objetos`, contraseña `objetos_dev` → *Test Connection* → *Finalizar*. En `Schemas → public → Tables` aparecen 15 tablas más `alembic_version`. Clic derecho en `public` → *View Diagram* muestra el E-R.

## 4. Frontend (otra ventana de PowerShell)

```powershell
cd frontend
npm install
npm start               # http://localhost:4200
```

## 5. Postman

Ver `postman/README.md`. En resumen: importar la colección y el entorno, escribir `Admin2026!` en `admin_password`, poner como *Working directory* la carpeta `postman` y correr la colección.

## Credenciales ficticias

| Usuario | Contraseña | Rol | Origen |
|---|---|---|---|
| `admin@ces.test` | `Admin2026!` | ADMIN | `python seed.py` |
| `operador.demo@ces.test` | `Demo2026!` | OPERADOR | `python seed_demo.py` |
| `consulta.demo@ces.test` | `Demo2026!` | CONSULTA | `python seed_demo.py` |

## Problemas comunes

| Mensaje | Causa y solución |
|---|---|
| `password authentication failed for user "objetos"` | El usuario o la clave del `DATABASE_URL` no coinciden con los creados en el paso 1. |
| `RuntimeError: JWT_SECRET_KEY no está en el .env…` | Falta pegar la clave en `.env` (mínimo 32 caracteres). |
| `Error: Could not locate a Flask application` | Falta `FLASK_APP=run.py` en `.env` o no está dentro de la carpeta `backend`. |
| `ZoneInfoNotFoundError: America/Bogota` | Falta `tzdata`: `pip install -r requirements.txt` de nuevo. |
| `No se pudo conectar con el servidor` en el frontend | El backend no está corriendo en el puerto 5000. |
| Error de CORS en el navegador | Abra el frontend con `http://localhost:4200` (no `127.0.0.1`). |
| `pip freeze > requirements.txt` deja el archivo raro | PowerShell lo guarda en UTF-16. Use `pip freeze \| Out-File -Encoding utf8 requirements.txt`. |
