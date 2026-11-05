# 6. Informe de resultados

## Qué se construyó

- **Backend** Flask con la estructura de clase: 15 modelos (uno por archivo), 17 módulos con su `*_routes.py` → `*_controller.py` → `*_service.py`, 84 rutas (77 del enunciado, 4 del dashboard y 3 de salud), 8 migraciones de Flask-Migrate, seed y dataset de demostración.
- **Frontend** Angular 21 con la estructura de clase (`core/services`, `pages/`): 17 pantallas, 16 servicios y 5 componentes reutilizables.
- **Postman**: 18 carpetas con subcarpetas Exitosos/Validaciones/Permisos, 253 solicitudes que cubren las 84 rutas, fotos de prueba y script de concurrencia.
- **Documentación**: análisis, modelo E-R, diccionario de datos, arquitectura y decisiones, guion de demostración, matriz de trazabilidad y este informe.

## Resultados verificados

Todo lo siguiente se ejecutó de verdad, el 3 de noviembre de 2026, **en el entorno Linux de pruebas de Claude** (Python 3.14.6, PostgreSQL 16.15, Node 22, Chromium), con la base recreada desde cero. **Aún no se ha ejecutado en el computador con Windows**: es el siguiente paso.

| Verificación | Resultado | Evidencia |
|---|---|---|
| `flask db upgrade` sobre base vacía (8 migraciones) | Correcto; `flask db migrate` posterior: «No changes in schema detected» (modelos y base coinciden) | `evidencias/instalacion_resultado.txt` |
| `python seed.py` dos veces | Correcto; la segunda vez no crea nada (reproducible) | `evidencias/instalacion_resultado.txt` |
| `python seed_demo.py` | 24 objetos (ambas sedes), 5 devueltos, 2 inactivos, fotos, 12 personas | `evidencias/instalacion_resultado.txt` |
| pytest | **55 de 55 aprobadas** (PA01–PA24, incluida la concurrencia con 8 hilos) | `evidencias/pytest_resultado.txt` |
| Colección de Postman con newman | **253 solicitudes, 781 aserciones, 0 fallidas** | `postman/reporte_ejecucion.md` |
| Concurrencia contra el servidor real | 10 devoluciones simultáneas: 1 × 201 y 9 × 409; 1 fila en `return_records` | `evidencias/concurrencia_resultado.txt` |
| Pruebas de uso en el navegador con los 3 roles | **34 de 34 comprobaciones** (incluye vista móvil) | `evidencias/e2e_resultado.json`, `img/ui_*.png` |
| `ng build` del frontend | Correcto, sin errores ni advertencias | — |
| Ruedas de `requirements.txt` para Windows | Disponibles para Python 3.12, 3.13 y 3.14 (win_amd64) | — |
| Triggers de conservación | `DELETE` y `TRUNCATE` rechazados; `UPDATE` en `audit_logs` rechazado | `test_pa22_*` |

## Limitaciones conocidas

1. El **límite de intentos** vive en la memoria del proceso: se reinicia al reiniciar el servidor y no se comparte entre varios procesos (suficiente para el proyecto; en producción usaría Redis o una tabla).
2. El **correo** de recuperación queda por defecto en un buzón local de archivos `.eml`; para un SMTP real hay que configurar `MAIL_MODE=smtp` y credenciales de prueba en `.env` (no se probó con un servidor SMTP externo).
3. Las **fotos** se guardan en disco local (`backend/instance/uploads`), no en un almacenamiento externo; para respaldar el sistema hay que copiar esa carpeta junto con la base.
4. La **constancia** usa confirmación digital (casilla del operador) y un PDF generado; no hay firma manuscrita ni verificación criptográfica del PDF (opcional en el enunciado).
5. Las rutas del **dashboard** y los supuestos S1–S10 (ver `01_analisis.md`) son propuestas propias; conviene confirmarlas con el docente.
6. Los **gráficos** del dashboard son barras hechas con CSS (sin librería de gráficos).
7. El control de **ingreso y salida de personas** (ampliación opcional) no se implementó.

## Mejoras pendientes

- Probar todo en Windows con PostgreSQL local y DBeaver (siguiente paso).
- Repositorio Git con historial de commits por hito.
- Notificaciones de coincidencia entre reportes de pérdida y objetos recibidos (opcional del enunciado).
- Refresco del token (opcional) y almacenamiento de fotos en un servicio externo.
