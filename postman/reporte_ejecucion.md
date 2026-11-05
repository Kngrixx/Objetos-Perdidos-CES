# Reporte de ejecución de la colección (newman)

| Dato | Valor |
|---|---|
| Fecha | 2026-11-03 21:25 (hora de Bogotá) |
| Colección | Objetos perdidos CES |
| Entorno | Objetos perdidos CES - local (`base_url = http://localhost:5000/api`) |
| Base de datos | PostgreSQL 16, recién creada con `flask db upgrade` + `python seed.py` + `python seed_demo.py` |
| Backend | `python run.py` con `ALLOW_FAULT_INJECTION=true` (para PA10) |
| Herramienta | newman 6.2.1 (motor del Collection Runner de Postman), entorno Linux de pruebas |
| Iteraciones | 1 |
| Solicitudes | 253 (fallidas: 0) |
| Aserciones | 781 (fallidas: 0) |
| Scripts de prueba | 506 (con error: 0) |
| Duración total | 7.4 s |
| Tiempo de respuesta promedio | 12 ms (mín 2 ms, máx 152 ms) |

## Resultado por carpeta

| Carpeta | Solicitudes | Aserciones correctas | Aserciones fallidas |
|---|---|---|---|
| 00 Health | 3 | 10 | 0 |
| 01 Login | 19 | 62 | 0 |
| 02 Password | 10 | 31 | 0 |
| 03 Users | 18 | 56 | 0 |
| 04 Roles | 3 | 10 | 0 |
| 05 Campus | 18 | 53 | 0 |
| 06 Blocks | 14 | 40 | 0 |
| 07 Departments | 11 | 31 | 0 |
| 08 ObjectCategories | 12 | 34 | 0 |
| 09 ObjectTypes | 14 | 41 | 0 |
| 10 Persons | 16 | 45 | 0 |
| 11 ObjectLost | 37 | 120 | 0 |
| 12 ObjectPhotos | 15 | 46 | 0 |
| 13 Claims | 23 | 70 | 0 |
| 14 Returns | 15 | 48 | 0 |
| 15 Inventory | 9 | 31 | 0 |
| 16 Audit | 5 | 18 | 0 |
| 17 Dashboard | 11 | 35 | 0 |

## Códigos HTTP obtenidos

| Código | Cantidad |
|---|---|
| 200 | 104 |
| 201 | 24 |
| 400 | 44 |
| 401 | 12 |
| 403 | 43 |
| 404 | 4 |
| 409 | 21 |
| 500 | 1 |

Las respuestas 4xx son esperadas: corresponden a las subcarpetas **Validaciones** y **Permisos**, cuyas pruebas verifican que el backend rechace la petición con el código correcto.

## Evidencias adicionales (no automatizables en el runner)

- Correo de recuperación y restablecimiento exitoso: `backend/tests/test_auth.py::test_pa04_forgot_and_reset_password` (lee el `.eml` del buzón local).
- Concurrencia PA17: `docs/evidencias/concurrencia_resultado.txt` (10 peticiones simultáneas: una 201 y nueve 409).
- Pruebas de navegador con los tres roles: `docs/evidencias/e2e_resultado.json`.

Nota: este reporte se generó en el entorno de pruebas de Claude (Linux), no en el computador con Windows. Al correr la colección en su equipo, exporte el resultado del Runner y agréguelo aquí.
