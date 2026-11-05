import { Component, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { AuthService } from '../../core/services/auth.service';
import { errorMessage } from '../../core/services/http-helpers';

@Component({
  imports: [FormsModule, RouterLink],
  selector: 'app-reset-password',
  styleUrl: './reset-password.scss',
  templateUrl: './reset-password.html',
})
export class ResetPassword {
  token = '';
  password = '';
  passwordConfirmation = '';
  error = signal('');
  loading = signal(false);

  constructor(
    route: ActivatedRoute,
    private router: Router,
    private authService: AuthService,
  ) {
    // El enlace del correo trae el token: /reset-password?token=...
    this.token = route.snapshot.queryParamMap.get('token') || '';
  }

  reset(): void {
    if (this.loading()) {
      return;
    }
    if (!this.token.trim()) {
      this.error.set('Falta el token del enlace de recuperación.');
      return;
    }
    if (this.password.length < 8 || !/[A-Za-z]/.test(this.password) || !/\d/.test(this.password)) {
      this.error.set('La contraseña debe tener al menos 8 caracteres y combinar letras y números.');
      return;
    }
    if (this.password !== this.passwordConfirmation) {
      this.error.set('La confirmación no coincide.');
      return;
    }
    this.loading.set(true);
    this.error.set('');
    this.authService.resetPassword(this.token.trim(), this.password, this.passwordConfirmation).subscribe({
      next: () => {
        this.loading.set(false);
        this.router.navigate(['/login'], { queryParams: { reset: 1 } });
      },
      error: (error) => {
        this.loading.set(false);
        this.error.set(errorMessage(error));
      },
    });
  }
}
