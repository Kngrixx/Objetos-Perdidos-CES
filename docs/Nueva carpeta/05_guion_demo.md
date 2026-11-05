# 5. Guion de demostración (≈15 minutos)

Preparación: base recién creada (`flask db upgrade`, `python seed.py`, `python seed_demo.py`), backend (`python run.py`) y frontend (`npm start`) corriendo. Navegador en `http://localhost:4200`. Credenciales ficticias: `admin@ces.test` / `Admin2026!`, `operador.demo@ces.test` y `consulta.demo@ces.test` / `Demo2026!`.

| # | Paso | Qué mostrar | Regla / caso |
|---|---|---|---|
| 1 | Login con contraseña errónea y luego correcta como ADMIN | Mensaje genérico «Credenciales inválidas.» | PA02 |
| 2 | Dashboard: filtrar por sede y fechas; clic en «Disponibles» y en «Reclamaciones pendientes» | Los indicadores abren el listado correspondiente | §8 Dashboard |
| 3 | Catálogos → Sedes: crear «Sede Norte» y un bloque; intentar «  POBLADO » | 409 por nombre normalizado duplicado | PA05, RF01 |
| 4 | Salir y entrar como OPERADOR. Recepción: categoría Tecnología → «+ Crear tipo de objeto» | El tipo nuevo queda seleccionado; un duplicado con otras mayúsculas da 409 | PA07 |
| 5 | Sede → bloque (lista dependiente), lugar, fecha, buscar persona `DEMO-1001`, 3 fotos y quitar una | Vista previa y retiro antes de guardar | PA08 |
| 6 | Guardar: detalle con código `OBJ-…`, «Recibe (operador)» = usuario logueado | Responsables de cada etapa | PA08 |
| 7 | Editar descripción sin motivo (rechaza) y con motivo; Historial muestra antes → después | | PA11 |
| 8 | Inactivar una foto (motivo); intentar inactivar la última | 409 «última fotografía activa» | PA14 |
| 9 | Registrar reclamación de `DEMO-1004` sin verificar → Rechazar con motivo | El objeto sigue DISPONIBLE | PA16 |
| 10 | Nueva reclamación con identidad verificada → Aceptar → Registrar devolución con confirmación | Estado DEVUELTO, constancia `CONST-…`, descargar PDF | PA16, RF11 |
| 11 | Inventario: el objeto devuelto no aparece; filtrar por sede y exportar PDF | El PDF lista filtros, fecha de generación y total | PA18, PA20 |
| 12 | Entrar como CONSULTA: listado sin fotos, bloque ni personas; abrir `/usuarios` | Redirige; el backend responde 403 | PA19 |
| 13 | ADMIN: Usuarios (promover cuenta a OPERADOR, intentar degradarse) y Auditoría | 409 último ADMIN | PA23 |
| 14 | ADMIN: Corrección administrativa del objeto devuelto | Conserva propietario y devolución | PA24 |
| 15 | DBeaver: `DELETE FROM object_lost WHERE id = 1;` | `ERROR: No se permite eliminar registros…` | PA22 |
| 16 | PowerShell: `python prueba_concurrencia.py` en `postman/` | Una 201 y las demás 409 | PA17 |

Para PA10 (fallo de archivo) en vivo: poner `ALLOW_FAULT_INJECTION=true` en `.env`, reiniciar y ejecutar en Postman `11 ObjectLost / Validaciones / … fallo de archivo simulado`; luego el request siguiente muestra que el inventario no tiene la recepción.

Cada integrante debe poder explicar: una regla de negocio (por ejemplo, la devolución única), una relación de datos (por ejemplo, Block 1:N ObjectLost dos veces) y una prueba negativa (por ejemplo, el ejecutable renombrado).
