import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from '../services/auth.service';
import { Role } from '../models/api.models';

// Solo entra quien tiene una sesión vigente.
export const authGuard: CanActivateFn = () => {
  const auth = inject(AuthService);
  if (auth.isLoggedIn()) {
    return true;
  }
  auth.clearSession();
  return inject(Router).createUrlTree(['/login']);
};

// Restringe una pantalla a ciertos roles (el backend vuelve a validar en cada petición).
export function roleGuard(...roles: Role[]): CanActivateFn {
  return () => {
    const auth = inject(AuthService);
    return auth.hasRole(...roles) ? true : inject(Router).createUrlTree(['/inicio']);
  };
}

// Página de inicio según el rol: ADMIN al dashboard, los demás a la consulta de objetos.
export const homeRedirectGuard: CanActivateFn = () => {
  const auth = inject(AuthService);
  const target = auth.hasRole('ADMIN') ? '/dashboard' : '/objetos';
  return inject(Router).createUrlTree([target]);
};
