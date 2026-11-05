import { Component, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { AuthService } from '../../core/services/auth.service';
import { errorMessage } from '../../core/services/http-helpers';

@Component({
  imports: [FormsModule, RouterLink],
  selector: 'app-register',
  styleUrl: './register.scss',
  templateUrl: './register.html',
})
export class Register {
  identification = '';
  fullName = '';
  email = '';
  password = '';
  passwordConfirmation = '';
  message = signal('');
  loading = signal(false);

  constructor(
    private router: Router,
    private authService: AuthService,
  ) {}

  validate(): string {
    if (!this.identification.trim() || !this.fullName.trim() || !this.email.trim() || !this.password) {
      return 'Todos los campos son obligatorios.';
    }
    if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(this.email.trim())) {
      return 'El correo no tiene un formato válido.';
    }
    if (this.password.length < 8 || !/[A-Za-z]/.test(this.password) || !/\d/.test(this.password)) {
      return 'La contraseña debe tener al menos 8 caracteres y combinar letras y números.';
    }
    if (this.password !== this.passwordConfirmation) {
      return 'La confirmación no coincide con la contraseña.';
    }
    return '';
  }

  register(): void {
    if (this.loading()) {
      return;
    }
    const problem = this.validate();
    if (problem) {
      this.message.set(problem);
      return;
    }
    this.loading.set(true);
    this.message.set('');
    // No se envía rol: el backend siempre asigna CONSULTA.
    this.authService
      .register({
        identification: this.identification.trim(),
        full_name: this.fullName.trim(),
        email: this.email.trim(),
        password: this.password,
        password_confirmation: this.passwordConfirmation,
      })
      .subscribe({
        next: () => {
          this.loading.set(false);
          this.router.navigate(['/login'], { queryParams: { registered: 1 } });
        },
        error: (error) => {
          // Los datos del formulario se conservan para corregir y reintentar.
          this.loading.set(false);
          this.message.set(errorMessage(error));
        },
      });
  }
}
