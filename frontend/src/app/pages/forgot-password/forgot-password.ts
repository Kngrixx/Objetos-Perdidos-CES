import { Component, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { AuthService } from '../../core/services/auth.service';
import { errorMessage } from '../../core/services/http-helpers';

@Component({
  imports: [FormsModule, RouterLink],
  selector: 'app-forgot-password',
  styleUrl: './forgot-password.scss',
  templateUrl: './forgot-password.html',
})
export class ForgotPassword {
  email = '';
  message = signal('');
  error = signal('');
  loading = signal(false);

  constructor(private authService: AuthService) {}

  send(): void {
    if (this.loading()) {
      return;
    }
    if (!this.email.trim()) {
      this.error.set('Escriba su correo.');
      return;
    }
    this.loading.set(true);
    this.error.set('');
    this.authService.forgotPassword(this.email.trim()).subscribe({
      next: (response) => {
        this.loading.set(false);
        this.message.set(response.message);
      },
      error: (error) => {
        this.loading.set(false);
        this.error.set(errorMessage(error));
      },
    });
  }
}
