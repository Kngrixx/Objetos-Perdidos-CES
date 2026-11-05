# 1. Documento de análisis

## Problema

En las sedes de la Universidad CES (Poblado y Sabaneta) se encuentran objetos que alguien entrega en una oficina. Hoy no hay un registro único que diga qué se recibió, quién lo entregó, dónde se guarda, quién lo reclamó y a quién se devolvió. El sistema debe **recibir, identificar, custodiar, consultar y devolver** esos objetos sin borrar nunca información y dejando historial de cada cambio.

## Alcance (obligatorio según el enunciado)

- Registro, login, recuperación de contraseña y control de acceso por roles.
- Catálogos de sedes, bloques, dependencias, categorías y tipos de objeto (crecen desde la aplicación).
- Recepción de objetos con responsables, ubicación de hallazgo, custodia y de 1 a 5 fotografías.
- Consulta con filtros, edición controlada, inactivación y reactivación con trazabilidad.
- Reclamación, devolución única con constancia PDF, inventario con exportación PDF, historial y auditoría.
- Dashboard del administrador.
- Colección de Postman por módulos.

Fuera de alcance: el control de ingreso y salida de personas (AccessEvent) es una ampliación opcional y no se implementó.

## Actores y roles

| Actor | Descripción |
|---|---|
| ADMIN | Administra usuarios y catálogos, recibe y devuelve, corrige con motivo, inactiva y reactiva, consulta auditoría, exporta y ve el dashboard. |
| OPERADOR | Consulta catálogos, crea tipos de objeto, recibe y edita objetos disponibles, registra reclamaciones y devoluciones, inactiva errores con motivo y exporta. |
| CONSULTA | Consulta el inventario activo con una proyección reducida (sin datos personales, ubicaciones ni fotos). No modifica nada. |
| Persona (sin cuenta) | Estudiante, empleado, contratista, proveedor o visitante que **entrega** o **reclama** un objeto. Se registra en `persons`. |

El registro público siempre crea cuentas CONSULTA. Un ADMIN promueve a OPERADOR. El primer ADMIN lo crea el seed.

## Requisitos funcionales

| Código | Requisito | Dónde se cumple |
|---|---|---|
| RF01 | Sedes: crear, consultar, filtrar, editar, inactivar y reactivar; nombre único normalizado. | `campus_*`, UNIQUE `uq_campuses_normalized_name` |
| RF02 | Bloques asociados a una sede, nombre único en la sede; un bloque de otra sede se rechaza. | `block_*`, UNIQUE (campus_id, normalized_name), validación en recepción |
| RF03 | Dependencias y categorías con selección desde listas activas. | `department_*`, `object_category_*` |
| RF04 | Tipos de objeto con buscador, creación desde el formulario y prevención de duplicados. | `object_type_*`, modal del frontend, UNIQUE (category_id, normalized_name) |
| RF05 | Persona que entrega: identificación, nombre, vinculación, dependencia, contacto opcional. | `person_*` |
| RF06 | Cada objeto físico con tipo, descripción, hallazgo, custodia, responsables y fotos. | `POST /object-lost` (multipart) |
| RF07 | Listados paginados, detalle y filtros combinables; mensaje sin resultados. | `GET /object-lost` (getByFilter) |
| RF08 | Editar disponibles con motivo; valores anteriores en auditoría. | `PATCH /object-lost/{id}` + `audit_logs` |
| RF09 | Inactivar sin borrar (motivo, fecha, responsable); solo ADMIN reactiva. | `/inactivate`, `/reactivate` |
| RF10 | Agregar e inactivar fotos conservando archivo y metadata; mínimo una foto activa. | `object_photo_*` |
| RF11 | Reclamaciones y una sola devolución con constancia. | `claim_*`, `return_*` |
| RF12 | Inventario, indicadores y PDF con los filtros aplicados. | `inventory_*`, `dashboard_*` |
| RF13 | Cuentas, roles, estado, perfil y contraseña; auditoría con permisos. | `auth_*`, `user_*`, `audit_*` |

## Reglas de negocio

1. **Nada se borra.** No hay rutas DELETE; las FK son `ON DELETE RESTRICT`; triggers de la base rechazan DELETE/TRUNCATE en todas las tablas y UPDATE en `audit_logs` y `return_records`.
2. **`is_active` y `status` son ejes distintos.** `status` = situación física (DISPONIBLE/DEVUELTO); `is_active` = validez del registro. Un DEVUELTO sigue activo como histórico.
3. Un registro inactivo no se edita, no recibe fotos ni se devuelve. Reactivar exige ADMIN, motivo y referencias válidas; conserva el estado.
4. Un DEVUELTO no admite edición ordinaria ni inactivación; solo **corrección administrativa** (ADMIN, motivo) que no toca propietario, devolución ni estado.
5. No se aceptan referencias inexistentes ni catálogos inactivos para nuevos registros (400). Un catálogo inactivo sigue visible en los registros históricos.
6. No se inactiva una sede con bloques activos ni un catálogo del que dependan objetos activos DISPONIBLES (409 con explicación).
7. Fecha de hallazgo: no futura y no posterior a la recepción. Se guarda en UTC y se muestra en hora de Bogotá.
8. Fotos: 1 a 5 activas, JPEG o PNG verificados por contenido, máximo 5 MB, nombre interno generado, archivo en almacenamiento controlado y servido solo por ruta autorizada.
9. Recepción atómica: si falla una foto no queda recepción parcial (rollback + compensación de archivos temporales).
10. Edición con **bloqueo optimista** (`version`): versión desactualizada → 409.
11. Devolución: exige objeto activo DISPONIBLE y reclamación ACEPTADA de ese objeto; transacción con `SELECT … FOR UPDATE` + UNIQUE en `return_records.object_lost_id` y `claim_id`. Una segunda devolución → 409.
12. A lo sumo una reclamación ACEPTADA por objeto (índice único parcial).
13. Cambios de estado y su auditoría se guardan en la **misma transacción**.
14. JWT de 30 minutos; logout revoca el `jti`; cambiar/restablecer contraseña o inactivar incrementa `token_version`; el rol se lee de la base en cada petición.
15. Recuperación: mismo mensaje exista o no el correo; token aleatorio guardado como hash, 15 minutos, un solo uso; al usarlo se revocan los demás pendientes.
16. ADMIN no puede inactivar ni degradar al último administrador activo.

## Estados

```
Objeto:        DISPONIBLE ──(devolución)──> DEVUELTO        (irreversible)
Registro:      activo <──(inactivar / reactivar ADMIN)──> inactivo   (solo si DISPONIBLE)
Reclamación:   PENDIENTE ──> ACEPTADA | RECHAZADA           (una decisión, con motivo)
```

## Supuestos y decisiones propias (confirmar con el docente)

| # | Supuesto |
|---|---|
| S1 | Las rutas del dashboard (`/dashboard/summary`, `/by-category`, `/by-campus`, `/recent`) son propuesta nuestra: el PDF pide el dashboard pero no define sus rutas. |
| S2 | Normalización de nombres: sin tildes ni diéresis, minúsculas y espacios colapsados; **la ñ se conserva** («año» ≠ «ano»). |
| S3 | Mecanismo de recepción en la devolución: **confirmación digital** (`owner_confirmation = true`) más constancia PDF generada por el sistema. |
| S4 | CONSULTA no ve descripción, ubicaciones precisas, bloque, personas ni fotos (pueden exponer datos personales); ve código, tipo, categoría, sede, fecha y estado. |
| S5 | «Operaciones pendientes» de una persona = reclamaciones PENDIENTES o ACEPTADAS sin devolución. |
| S6 | Para aceptar una reclamación debe estar registrada la verificación de identidad (`identity_verified`). |
| S7 | Los catálogos inactivos no se editan (primero se reactivan). Inactivar y reactivar siempre exige motivo (mínimo 5 caracteres). |
| S8 | Las fotos de un objeto DEVUELTO o inactivo no se modifican. |
| S9 | El correo de recuperación usa un **buzón local** (archivos `.eml` en `backend/instance/outbox`) por defecto; SMTP real es configurable en `.env`. |
| S10 | El código del objeto es `OBJ-` + id con 6 dígitos; si una recepción falla, ese número no se reutiliza (puede haber saltos). |
