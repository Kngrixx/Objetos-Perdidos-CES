import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, throwError } from 'rxjs';
import { API_URL } from '../services/api.config';
import { AuthService } from '../services/auth.service';

// Agrega "Authorization: Bearer <token>" a cada petición al backend.
// Si el backend responde 401 (token vencido, revocado o invalidado), cierra la sesión local.
export const authInterceptor: HttpInterceptorFn = (request, next) => {
  const auth = inject(AuthService);
  const router = inject(Router);
  const token = auth.token();
  const withToken =
    token && request.url.startsWith(API_URL)
      ? request.clone({ setHeaders: { Authorization: `Bearer ${token}` } })
      : request;

  return next(withToken).pipe(
    catchError((error) => {
      if (error instanceof HttpErrorResponse && error.status === 401 && token) {
        auth.clearSession();
        router.navigate(['/login'], { queryParams: { expired: 1 } });
      }
      return throwError(() => error);
    }),
  );
};
