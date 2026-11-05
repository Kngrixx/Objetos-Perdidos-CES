import { Component, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { AuthService, LoginRequest } from '../../core/services/auth.service';
import { errorMessage } from '../../core/services/http-helpers';

@Component({
  imports: [FormsModule, RouterLink],
  selector: 'app-login',
  styleUrl: './login.scss',
  templateUrl: './login.html',
})
export class Login {
  email = '';
  password = '';
  message = signal('');
  info = signal('');
  loading = signal(false);

  constructor(
    private router: Router,
    private authService: AuthService,
    route: ActivatedRoute,
  ) {
    const params = route.snapshot.queryParamMap;
    if (params.get('expired')) this.info.set('Su sesión terminó. Inicie sesión nuevamente.');
    if (params.get('registered')) this.info.set('Cuenta creada. Ya puede iniciar sesión.');
    if (params.get('reset')) this.info.set('Contraseña restablecida. Inicie sesión con la nueva.');
    if (params.get('logout')) this.info.set('Sesión cerrada.');
  }

  login(): void {
    if (this.loading()) {
      return; // evita doble envío
    }
    if (!this.email.trim() || !this.password) {
      this.message.set('Escriba su correo y su contraseña.');
      return;
    }
    const data: LoginRequest = {
      email: this.email.trim(),
      password: this.password,
    };
    this.loading.set(true);
    this.message.set('');
    this.authService.login(data).subscribe({
      next: () => {
        this.loading.set(false);
        this.router.navigate(['/inicio']);
      },
      error: (error) => {
        this.loading.set(false);
        this.message.set(errorMessage(error));
      },
    });
  }
}
