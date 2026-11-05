import { Component, OnInit, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { SessionUser } from '../../core/models/api.models';
import { AuthService } from '../../core/services/auth.service';
import { errorMessage } from '../../core/services/http-helpers';

// Perfil del usuario autenticado y cambio de contraseña.
@Component({
  selector: 'app-account',
  imports: [FormsModule],
  templateUrl: './account.html',
  styleUrl: './account.scss',
})
export class Account implements OnInit {
  current = '';
  next = '';
  confirmation = '';
  me = signal<SessionUser | null>(null);
  saving = signal(false);
  error = signal('');
  success = signal('');

  constructor(private authService: AuthService) {}

  ngOnInit(): void {
    this.authService.me().subscribe((response) => this.me.set(response.data));
  }

  changePassword(): void {
    if (this.saving()) return;
    if (!this.current || !this.next) {
      this.error.set('Complete los campos.');
      return;
    }
    if (this.next.length < 8 || !/[A-Za-z]/.test(this.next) || !/\d/.test(this.next)) {
      this.error.set('La nueva contraseña debe tener al menos 8 caracteres y combinar letras y números.');
      return;
    }
    if (this.next !== this.confirmation) {
      this.error.set('La confirmación no coincide.');
      return;
    }
    this.saving.set(true);
    this.error.set('');
    this.authService.changePassword(this.current, this.next, this.confirmation).subscribe({
      next: (response) => {
        this.saving.set(false);
        this.current = '';
        this.next = '';
        this.confirmation = '';
        this.success.set(response.message);
      },
      error: (error) => {
        this.saving.set(false);
        this.error.set(errorMessage(error));
      },
    });
  }
}
