# 2. Modelo de datos

Motor: **PostgreSQL 16** (cualquier versión 14+ sirve). Las tablas se crean con **Flask-Migrate**: 7 migraciones generadas con `flask db migrate` (una por grupo de cambios, como en clase) y 1 revisión escrita a mano para lo que Alembic no detecta (triggers).

![Diagrama entidad-relación](img/diagrama_er.png)

El diagrama muestra las columnas principales; el detalle completo (tipos, nulabilidad, FK, CHECK e índices) está en `03_diccionario_datos.md`. La fuente del diagrama es `img/diagrama_er.mmd` (Mermaid). En DBeaver: clic derecho en el esquema `public` → *View Diagram*.

## Migraciones

| Revisión | Mensaje | Qué crea |
|---|---|---|
| `2ce4759b8957` | create roles and users tables | `roles`, `users` |
| `8cc5e752e915` | create password reset and token revocation tables | `password_reset_tokens`, `token_revocations` |
| `e9355e9dc03f` | create catalog tables | `campuses`, `blocks`, `departments`, `object_categories`, `object_types` |
| `bfabf501638e` | create persons table | `persons` |
| `15059d970a87` | create object lost and object photos tables | `object_lost`, `object_photos` |
| `9db9c7695304` | create claims and return records tables | `claims`, `return_records` (incluye el índice único parcial) |
| `f357c059a7eb` | create audit logs table | `audit_logs` |
| `8d6746a80648` | add triggers that block delete and update of history | funciones `prevent_delete()`, `prevent_update()` y sus triggers (manual) |

## Relaciones y cardinalidades

| Relación | Cardinalidad | FK |
|---|---|---|
| Role → User | 1:N | `users.role_id` |
| Campus → Block | 1:N | `blocks.campus_id` |
| ObjectCategory → ObjectType | 1:N | `object_types.category_id` |
| Department → Person | 1:N (opcional) | `persons.department_id` |
| ObjectType → ObjectLost | 1:N | `object_lost.object_type_id` |
| Block → ObjectLost | 1:N dos veces (hallazgo y custodia) | `found_block_id`, `custody_block_id` |
| Person → ObjectLost | 1:N (quien entrega) | `finder_person_id` |
| User → ObjectLost | 1:N (quien recibe) | `received_by_user_id` |
| ObjectLost → ObjectPhoto | 1:N (1 a 5 activas) | `object_photos.object_lost_id` |
| ObjectLost → Claim | 1:N | `claims.object_lost_id` |
| Person → Claim | 1:N (reclamante) | `claims.claimant_person_id` |
| ObjectLost → ReturnRecord | 1:0..1 | `return_records.object_lost_id` **UNIQUE** |
| Claim → ReturnRecord | 1:0..1 | `return_records.claim_id` **UNIQUE** |
| User → AuditLog | 1:N (actor) | `audit_logs.actor_user_id` |

Todas las FK son `ON DELETE RESTRICT`: no hay borrado en cascada.

**Person y User son entidades distintas.** User inicia sesión y tiene rol; Person es alguien externo que entrega o reclama sin cuenta.

**ObjectType vs ObjectLost.** ObjectType es el catálogo («Celular»); ObjectLost es un objeto físico concreto. Dos celulares son dos filas de `object_lost` con su código, fotos y responsables. El tipo nunca se escribe como texto en `object_lost`: se guarda `object_type_id`.

## Restricciones que protegen la integridad

| Restricción | Para qué |
|---|---|
| `UNIQUE(normalized_name)` en sedes, dependencias y categorías; `UNIQUE(campus_id, normalized_name)` en bloques; `UNIQUE(category_id, normalized_name)` en tipos | Evitar duplicados aunque cambien mayúsculas, tildes o espacios, incluso con dos peticiones simultáneas. |
| `CHECK status IN ('DISPONIBLE','DEVUELTO')`, `CHECK version >= 1`, `CHECK found_at <= received_at` | Estados válidos y fechas coherentes en `object_lost`. |
| `CHECK mime_type IN (...)` y `CHECK size_bytes > 0 AND <= 5242880` | Metadata de fotos válida. |
| `CHECK affiliation_type IN (...)` | Tipos de vinculación válidos. |
| `CHECK status IN ('PENDIENTE','ACEPTADA','RECHAZADA')` | Estados de reclamación. |
| Índice único parcial `uq_claims_one_accepted_per_object` `WHERE status = 'ACEPTADA'` | A lo sumo una reclamación aceptada por objeto (las pendientes y rechazadas pueden ser varias). |
| `UNIQUE return_records.object_lost_id` y `claim_id` | Una sola devolución por objeto y por reclamación. |
| `CHECK owner_confirmation = TRUE` | No existe devolución sin confirmación del propietario. |
| Triggers `prevent_delete` / `prevent_update` | Nada se borra; auditoría y devoluciones son de solo lectura. |

## Índices para los filtros

`object_lost`: `code` (único), `object_type_id`, `found_block_id`, `custody_block_id`, `finder_person_id`, `received_at`, `status`, `is_active` y el compuesto `(status, is_active)` que usa el inventario. También índices en todas las FK de búsqueda (`blocks.campus_id`, `object_types.category_id`, `claims.object_lost_id`, `claims.status`, `audit_logs (entity, entity_id)`, `audit_logs.occurred_at`, etc.).

## Normalización

El modelo está en **tercera forma normal**:

- 1FN: cada columna guarda un solo valor; las fotos (varias por objeto) están en su propia tabla en vez de columnas `foto1…foto5`; un objeto es una unidad física (no hay columna «cantidad»).
- 2FN: todas las tablas tienen clave primaria simple (`id`), así que no hay dependencias parciales.
- 3FN: no hay dependencias transitivas guardadas. Ejemplo: la sede del hallazgo **no** se guarda en `object_lost`; se obtiene de `found_block_id → blocks.campus_id`. El nombre del tipo y su categoría tampoco se repiten en el objeto.

Desnormalizaciones conscientes: `normalized_name` (derivado de `name`) existe para que la base pueda exigir UNIQUE sobre él; `return_records.owner_person_id` repite al reclamante de la reclamación para que el histórico de la devolución sea autocontenido.

## Historial

Cada creación, edición, inactivación, reactivación, decisión y devolución inserta una fila en `audit_logs` **en la misma transacción** del cambio, con `before_data` y `after_data` (solo los campos que cambiaron) en JSON. Nunca guarda contraseñas, hashes de tokens ni archivos. La tabla no acepta UPDATE ni DELETE (trigger). Además, los registros conservan `created_by`, `updated_by`, `inactivated_at`, `inactivated_by` e `inactivation_reason`.
