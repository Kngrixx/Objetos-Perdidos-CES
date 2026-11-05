import { Routes } from '@angular/router';
import { authGuard, homeRedirectGuard, roleGuard } from './core/guards/auth.guard';
import { Login } from './pages/login/login';
import { Register } from './pages/register/register';
import { ForgotPassword } from './pages/forgot-password/forgot-password';
import { ResetPassword } from './pages/reset-password/reset-password';
import { Home } from './pages/home/home';
import { Dashboard } from './pages/dashboard/dashboard';
import { ObjectList } from './pages/object-list/object-list';
import { ObjectForm } from './pages/object-form/object-form';
import { ObjectDetail } from './pages/object-detail/object-detail';
import { Inventory } from './pages/inventory/inventory';
import { Claims } from './pages/claims/claims';
import { Returns } from './pages/returns/returns';
import { Persons } from './pages/persons/persons';
import { Catalogs } from './pages/catalogs/catalogs';
import { Users } from './pages/users/users';
import { Audit } from './pages/audit/audit';
import { Account } from './pages/account/account';

export const routes: Routes = [
  { path: 'login', component: Login },
  { path: 'register', component: Register },
  { path: 'forgot-password', component: ForgotPassword },
  { path: 'reset-password', component: ResetPassword },
  {
    path: '',
    component: Home,
    canActivate: [authGuard],
    children: [
      { path: '', pathMatch: 'full', redirectTo: 'inicio' },
      { path: 'inicio', canActivate: [homeRedirectGuard], children: [] },
      { path: 'dashboard', component: Dashboard, canActivate: [roleGuard('ADMIN')] },
      { path: 'objetos', component: ObjectList },
      { path: 'objetos/nuevo', component: ObjectForm, canActivate: [roleGuard('ADMIN', 'OPERADOR')] },
      { path: 'objetos/:id', component: ObjectDetail },
      { path: 'objetos/:id/editar', component: ObjectForm, canActivate: [roleGuard('ADMIN', 'OPERADOR')] },
      { path: 'inventario', component: Inventory, canActivate: [roleGuard('ADMIN', 'OPERADOR')] },
      { path: 'reclamaciones', component: Claims, canActivate: [roleGuard('ADMIN', 'OPERADOR')] },
      { path: 'devoluciones', component: Returns, canActivate: [roleGuard('ADMIN', 'OPERADOR')] },
      { path: 'personas', component: Persons, canActivate: [roleGuard('ADMIN', 'OPERADOR')] },
      { path: 'catalogos', component: Catalogs, canActivate: [roleGuard('ADMIN', 'OPERADOR')] },
      { path: 'usuarios', component: Users, canActivate: [roleGuard('ADMIN')] },
      { path: 'auditoria', component: Audit, canActivate: [roleGuard('ADMIN')] },
      { path: 'cuenta', component: Account },
    ],
  },
  { path: '**', redirectTo: '' },
];
