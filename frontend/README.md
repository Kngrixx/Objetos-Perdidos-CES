# Frontend (Angular 21)

Misma estructura de la clase (`fronted/appiot`):

```
src/app/
  app.ts, app.html, app.config.ts, app.routes.ts
  core/
    services/      # un servicio por recurso del backend (auth, campus, object-lost, claims...)
    guards/        # authGuard, roleGuard, homeRedirectGuard
    interceptors/  # agrega el token JWT a cada petición
    models/        # interfaces TypeScript de las respuestas {ok, message, data}
  pages/           # una carpeta por pantalla: login, register, home (menú), dashboard, object-list...
  components/      # piezas reutilizables: pager, reason-dialog, person-picker, secure-image, type-create-modal
```

Cada página tiene sus tres archivos: `nombre.ts`, `nombre.html` y `nombre.scss`, como `pages/login` en clase.

## Ejecutar (PowerShell)

```powershell
cd frontend
npm install
npm start          # equivale a ng serve -> http://localhost:4200
```

Abra **http://localhost:4200** (con `localhost`, no `127.0.0.1`, porque el CORS del backend solo autoriza ese origen).
El backend debe estar corriendo en `http://localhost:5000` (si usa otro puerto, cambie `src/app/core/services/api.config.ts`).

## Notas técnicas

- El proyecto se creó con `ng new frontend --style=scss --ssr=false --zoneless`. Sin SSR porque el token se guarda en `localStorage` (no existe en el servidor).
- Angular 21 es *zoneless*: los datos que llegan del backend se guardan en **signals** (`signal()`), así la vista se actualiza sola. Los campos de formulario usan `[(ngModel)]` como en clase.
- Las fotos se piden con el token (`/api/object-photos/{id}/file`) y se muestran como `Blob`; nunca son públicas.
- Las fechas se muestran en hora de Bogotá con `date: 'yyyy-MM-dd HH:mm' : '-0500'`.
- Ocultar botones según el rol es solo comodidad: el backend valida el rol en cada ruta.
