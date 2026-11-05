import { HttpErrorResponse, HttpParams } from '@angular/common/http';

// Mensaje para mostrar al usuario: el "message" del backend o uno genérico.
export function errorMessage(error: unknown): string {
  if (error instanceof HttpErrorResponse) {
    if (error.status === 0) {
      return 'No se pudo conectar con el servidor. ¿Está corriendo el backend (flask run)?';
    }
    const body = error.error as { message?: string } | null;
    if (body && typeof body.message === 'string') {
      return body.message;
    }
    return `Error ${error.status} del servidor.`;
  }
  return 'Ocurrió un error inesperado.';
}

// Convierte un objeto de filtros en parámetros de URL, omitiendo los vacíos.
export function toParams(filters: Record<string, unknown>): HttpParams {
  let params = new HttpParams();
  for (const [key, value] of Object.entries(filters)) {
    if (value !== null && value !== undefined && value !== '') {
      params = params.set(key, String(value));
    }
  }
  return params;
}

// Descarga un archivo (PDF) recibido como Blob.
export function saveBlob(blob: Blob, fileName: string): void {
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = fileName;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
