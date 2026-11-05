# 4. Arquitectura y decisiones

## Estructura del backend (la de clase)

```
backend/
  run.py  config.py  .env.example  requirements.txt  create_structure.ps1  seed.py  seed_demo.py  pytest.ini
  migrations/            # flask db init / migrate (env.py idéntico al de backend_profe)
  app/
    __init__.py          # create_app(): Config, CORS, db/migrate/jwt.init_app, blueprints con url_prefix='/api'
    extensions.py        # db = SQLAlchemy(); migrate = Migrate(); jwt = JWTManager()   (igual que en clase)
    models/              # 15 archivos, uno por tabla; models/__init__.py los importa
    routes/              # 17 archivos <modulo>_routes.py: Blueprint + @jwt_required() (+ @roles_required)
    controllers/         # 17 archivos <modulo>_controller.py: leen request, validan, llaman al service, responden
    services/            # 17 servicios de negocio + audit_service + seed_service + demo_seed_service
    common/              # utilidades compartidas (ver abajo)
  tests/                 # pytest
```

Flujo de una petición (ejemplo `PATCH /api/object-lost/5`):

```
object_lost_routes.update_object_route      -> @jwt_required() + @roles_required(ADMIN, OPERADOR)
  object_lost_controller.update_object_controller  -> lee el JSON, lista de campos editables, motivo, versión
    object_lost_service.update_object               -> SELECT ... FOR UPDATE, reglas, auditoría, commit
      models.ObjectLost / models.AuditLog
  <- success_response("Objeto actualizado correctamente.", data)  -> {"ok": true, "message": ..., "data": ...}
```

Nombres: rutas `*_route`, controladores `*_controller`, servicios con verbos (`get_..._by_filter`, `create_...`, `inactivate_...`). Se unificaron los nombres mezclados del material de clase (`getAll`, `create_m1`) a snake_case en inglés; los mensajes al usuario están en español.

## Qué se agregó a la estructura de clase y por qué

| Agregado | Dónde | Por qué |
|---|---|---|
| `success_response` / `error_response` | `common/responses.py` | El proyecto exige el contrato `{ok, message, data}`. |
| `AppError(mensaje, código)` y manejadores de error | `common/errors.py` | En clase el service lanzaba `ValueError` y el controller respondía 409. Aquí hay 400/403/404/409/429/500, así que el service lanza `AppError` y un manejador único (registrado en `create_app`) lo convierte en `{ok:false, message}`. También responde JSON para 404/405/413/500 y traduce `IntegrityError` a 409. |
| Callbacks JWT y `@roles_required` | `common/security.py` | El PDF exige validar en cada ruta: firma, expiración, revocación (`jti`), usuario activo, `token_version` y rol **leído de la base**. `@jwt_required()` sigue en cada ruta como en clase; los callbacks de Flask-JWT-Extended hacen el resto. |
| Paginación, validaciones, fechas, normalización | `common/pagination.py`, `validators.py`, `dates.py`, `normalization.py` | Código que usan varios módulos. |
| Fotos, PDF, correo, límite de intentos | `common/files.py`, `pdf.py`, `mail.py`, `rate_limit.py` | Requisitos del PDF que la clase no cubría. |
| `TestConfig` y `create_app(config_class=Config)` | `config.py`, `app/__init__.py` | Para que pytest use una base aparte. |
| `seed.py`, `seed_demo.py` | raíz de backend | Seed reproducible y dataset de demostración (entregables §10). Se corren con `python seed.py` igual que `python run.py`. |

## Librerías (además de las de clase)

Las versiones de clase se mantuvieron exactas (Flask 3.1.3, Flask-SQLAlchemy 3.1.1, Flask-Migrate 4.1.0, Flask-JWT-Extended 4.7.4, SQLAlchemy 2.0.52, Alembic 1.19.1, psycopg 3.3.4, flask-cors 6.0.5, python-dotenv 1.2.2, tzdata 2026.3). Se añadieron solo:

- **fpdf2** (y sus dependencias Pillow y fontTools): constancia de devolución e inventario en PDF.
- **pytest**: pruebas automáticas.

Se verificó que todo `requirements.txt` tiene ruedas para Windows con Python 3.12, 3.13 y 3.14.

## Decisiones técnicas

| Tema | Decisión | Motivo |
|---|---|---|
| Hash de contraseñas | `werkzeug.security` (scrypt), como en clase | El PDF pide «biblioteca adecuada»; werkzeug ya viene con Flask. |
| Límite de intentos | Función propia en memoria (`check_rate_limit`) por IP y acción: login, registro, olvidé y reset → 429 | Fácil de explicar y sin dependencias. Limitación: se reinicia con el servidor y no se comparte entre procesos. |
| Tokens de recuperación | `secrets.token_urlsafe(32)`, se guarda SHA-256, 15 min, un solo uso, se revocan los demás al usarlo | Requisito del PDF; nunca se devuelve en el JSON. |
| Correo | `MAIL_MODE=file` (buzón local `.eml`) por defecto; `smtp` configurable | El PDF acepta «buzón de pruebas local documentado». |
| Fechas | UTC en la base (`timestamptz`); rangos con días de Bogotá: `[inicio 00:00 Bogotá, día siguiente 00:00 Bogotá)` | Fin exclusivo del día siguiente, como pide §8. |
| Fotos | Se valida la firma de bytes (JPEG `FF D8 FF`, PNG `89 50 4E 47…`), tamaño y cantidad **antes** de escribir; nombre `uuid4` | No se confía en la extensión ni en el nombre recibido. |
| Recepción atómica | Una transacción para objeto + fotos + auditoría; si algo falla: `rollback` y se retiran los archivos ya escritos de esa recepción (compensación) | PA10. Los archivos de fotos ya registradas nunca se borran. |
| Código del objeto | `nextval` de la secuencia de `object_lost` → `OBJ-000015` | Único, generado por el servidor, sin carreras. |
| Concurrencia en devolución | `SELECT … FOR UPDATE` sobre el objeto + `UNIQUE` en `return_records` | El bloqueo da un 409 claro; el UNIQUE es la garantía de la base. Probado con 8 y 10 peticiones simultáneas. |
| Concurrencia en edición | `version` (bloqueo optimista) + `FOR UPDATE` al guardar | PA11. |
| Último ADMIN | Se cuentan los ADMIN activos con `FOR UPDATE` antes de degradar o inactivar | Dos cambios simultáneos no dejan el sistema sin administrador. |
| Proyección por rol | CONSULTA recibe `object_to_public_dict` y solo objetos activos DISPONIBLES; fotos y personas → 403 | PA19. |
| Lista explícita de campos | En PATCH, cualquier campo fuera de la lista → 400; en POST los campos del servidor (`received_by_user_id`, `status`, `code`) no se leen | «Peticiones manipuladas» del §8. |
| Triggers | `prevent_delete` (todas las tablas) y `prevent_update` (`audit_logs`, `return_records`) | Conservación demostrable también desde la base. |

## Frontend (estructura de clase)

Angular 21 como `fronted/appiot`: `core/services` (un servicio por recurso), `pages/<pantalla>/<pantalla>.ts|html|scss`, `FormsModule` + `[(ngModel)]`, `HttpClient`, inyección por constructor. Se agregaron `core/guards` (sesión y rol), `core/interceptors` (token JWT y cierre de sesión ante 401), `core/models` (interfaces) y `components/` reutilizables. Como Angular 21 es *zoneless*, el estado que llega del backend se guarda en `signal()`. Se creó sin SSR porque la sesión vive en `localStorage`.
