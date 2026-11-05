import { Component, computed, signal } from '@angular/core';
import { Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { AuthService } from '../../core/services/auth.service';
import { Role } from '../../core/models/api.models';

interface MenuItem {
  label: string;
  link: string;
  roles: Role[];
}

// Plantilla de las páginas internas: barra superior con el menú según el rol.
@Component({
  selector: 'app-home',
  imports: [RouterOutlet, RouterLink, RouterLinkActive],
  templateUrl: './home.html',
  styleUrl: './home.scss',
})
export class Home {
  readonly menu: MenuItem[] = [
    { label: 'Dashboard', link: '/dashboard', roles: ['ADMIN'] },
    { label: 'Objetos', link: '/objetos', roles: ['ADMIN', 'OPERADOR', 'CONSULTA'] },
    { label: 'Recepción', link: '/objetos/nuevo', roles: ['ADMIN', 'OPERADOR'] },
    { label: 'Inventario', link: '/inventario', roles: ['ADMIN', 'OPERADOR'] },
    { label: 'Reclamaciones', link: '/reclamaciones', roles: ['ADMIN', 'OPERADOR'] },
    { label: 'Devoluciones', link: '/devoluciones', roles: ['ADMIN', 'OPERADOR'] },
    { label: 'Personas', link: '/personas', roles: ['ADMIN', 'OPERADOR'] },
    { label: 'Catálogos', link: '/catalogos', roles: ['ADMIN', 'OPERADOR'] },
    { label: 'Usuarios', link: '/usuarios', roles: ['ADMIN'] },
    { label: 'Auditoría', link: '/auditoria', roles: ['ADMIN'] },
  ];
  menuOpen = signal(false);
  visibleMenu = computed(() => this.menu.filter((item) => this.authService.hasRole(...item.roles)));

  constructor(
    public authService: AuthService,
    private router: Router,
  ) {}

  logout(): void {
    // Se revoca el token en el backend (logout) y luego se limpia la sesión local.
    this.authService.logout().subscribe({
      next: () => this.finishLogout(),
      error: () => this.finishLogout(),
    });
  }

  private finishLogout(): void {
    this.authService.clearSession();
    this.router.navigate(['/login'], { queryParams: { logout: 1 } });
  }
}
