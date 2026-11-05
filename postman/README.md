# Colección de Postman

Archivos:

- `Objetos_Perdidos_CES.postman_collection.json`: 18 carpetas (una por módulo del enunciado, más Health y Dashboard), cada una con subcarpetas **Exitosos**, **Validaciones** y **Permisos**. Cubre las 84 rutas del backend (77 del PDF, 4 del dashboard y 3 de salud).
- `Objetos_Perdidos_CES.postman_environment.json`: entorno sin secretos. Variables mínimas del PDF (`base_url`, `access_token`, `campus_id`, `block_id`, `category_id`, `object_type_id`, `person_id`, `object_lost_id`, `claim_id`) y otras que la colección llena sola.
- `fotos/`: archivos de prueba (dos JPEG, un PNG, un ejecutable renombrado a `.jpg` y un JPEG de 6 MB).
- `prueba_concurrencia.py`: script de PA17 (devoluciones simultáneas).
- `reporte_ejecucion.md`: resultado del Collection Runner / newman.

## Cómo correrla

1. Backend con la base recién creada y el seed aplicado (`flask db upgrade` y `python seed.py`). Para la prueba PA10 ponga `ALLOW_FAULT_INJECTION=true` en `backend/.env` y reinicie el servidor (vuelva a dejarlo en `false` después de la demo).
2. En Postman: **Import** → los dos archivos JSON. Seleccione el entorno *Objetos perdidos CES - local*.
3. En el entorno, escriba en `admin_password` la contraseña ficticia del ADMIN del seed (`Admin2026!`, salvo que la haya cambiado en `.env`). No guarde contraseñas reales.
4. **Fotos (multipart/form-data):** en *Settings → General → Working directory* elija la carpeta `postman` de este proyecto. Los requests usan rutas relativas como `fotos/foto_prueba_1.jpg`. Si Postman dice que no encuentra el archivo, revise ese ajuste.
5. Clic derecho en la colección → **Run collection** → **Run**. Se puede correr varias veces: cada ejecución genera un `run_id` y crea datos únicos.

Con newman (línea de comandos, opcional):

```powershell
npm install -g newman
cd postman
newman run Objetos_Perdidos_CES.postman_collection.json -e Objetos_Perdidos_CES.postman_environment.json --env-var admin_password=Admin2026! --working-dir .
```

## Cómo funcionan los tokens

- `01 Login` inicia sesión como ADMIN y un script guarda el token en `access_token` (todas las carpetas lo heredan como `Authorization: Bearer {{access_token}}`).
- También registra dos cuentas nuevas (quedan como CONSULTA) y guarda `operador_token` y `consulta_token`. En `03 Users` el ADMIN promueve la primera a OPERADOR; como el backend lee el rol de la base en cada petición, el mismo token pasa a tener permisos de operador.
- Los requests de otros roles sobrescriben la autorización con `{{operador_token}}` o `{{consulta_token}}`.

## Orden de ejecución

Health → Login → Password → Users → Roles → Campus → Blocks → Departments → ObjectCategories → ObjectTypes → Persons → ObjectLost (recepción, consulta, edición) → ObjectPhotos → Claims → Returns → Inventory → Audit → Dashboard.

## Evidencias que Postman no automatiza

- **Correo de recuperación (PA04):** con `MAIL_MODE=file`, cada correo queda como archivo `.eml` en `backend/instance/outbox/`. Ábralo, copie el token del enlace y envíelo en `POST /auth/reset-password` (o use la pantalla «Restablecer contraseña» del frontend). Un segundo uso del mismo token responde 400. Las pruebas de pytest lo verifican automáticamente (`test_pa04_forgot_and_reset_password`).
- **Concurrencia (PA17):** `python prueba_concurrencia.py --peticiones 10` (pide la contraseña del ADMIN). Debe mostrar una respuesta 201 y nueve 409.
- **Límite de intentos (429):** lo verifica pytest (`test_rate_limit_returns_429`) bajando el límite temporalmente.
