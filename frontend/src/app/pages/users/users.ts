import { Component, OnInit, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RoleItem, UserAccount } from '../../core/models/api.models';
import { AuthService } from '../../core/services/auth.service';
import { UserService } from '../../core/services/user.service';
import { RoleService } from '../../core/services/role.service';
import { errorMessage } from '../../core/services/http-helpers';
import { Pager } from '../../components/pager/pager';
import { ReasonDialog } from '../../components/reason-dialog/reason-dialog';

// Administración de cuentas (solo ADMIN): rol y estado.
@Component({
  selector: 'app-users',
  imports: [FormsModule, Pager, ReasonDialog],
  templateUrl: './users.html',
  styleUrl: './users.scss',
})
export class Users implements OnInit {
  filters = { text: '', role: '', is_active: 'all' };
  page = 1;
  pageSize = 20;
  roleChanges: Record<number, number> = {};

  items = signal<UserAccount[]>([]);
  roles = signal<RoleItem[]>([]);
  total = signal(0);
  message = signal('');
  error = signal('');
  success = signal('');
  loading = signal(false);
  dialogUser = signal<UserAccount | null>(null);
  dialogBusy = signal(false);
  dialogError = signal('');
  myId: number;

  constructor(
    private userService: UserService,
    private roleService: RoleService,
    authService: AuthService,
  ) {
    this.myId = authService.user()?.id ?? 0;
  }

  ngOnInit(): void {
    this.roleService.list().subscribe((r) => this.roles.set(r.data));
    this.search();
  }

  search(page = 1): void {
    this.page = page;
    this.loading.set(true);
    const query = { ...this.filters, is_active: this.filters.is_active === 'all' ? null : this.filters.is_active };
    this.userService.list({ ...query, page: this.page, page_size: this.pageSize }).subscribe({
      next: (response) => {
        this.items.set(response.data.items);
        this.roleChanges = {};
        response.data.items.forEach((user) => (this.roleChanges[user.id] = user.role_id));
        this.total.set(response.data.total);
        this.message.set(response.message);
        this.loading.set(false);
      },
      error: (error) => {
        this.error.set(errorMessage(error));
        this.loading.set(false);
      },
    });
  }

  saveRole(user: UserAccount): void {
    const roleId = this.roleChanges[user.id];
    if (roleId === user.role_id) return;
    this.userService.update(user.id, { role_id: roleId }).subscribe({
      next: (response) => {
        this.success.set(`${response.message} ${user.full_name} ahora es ${response.data.role}.`);
        this.error.set('');
        this.search(this.page);
      },
      error: (error) => {
        this.error.set(errorMessage(error));
        this.roleChanges[user.id] = user.role_id;
        this.items.set([...this.items()]);
      },
    });
  }

  openDialog(user: UserAccount): void {
    this.dialogError.set('');
    this.dialogUser.set(user);
  }

  toggleActive(reason: string): void {
    const user = this.dialogUser();
    if (!user) return;
    this.dialogBusy.set(true);
    const request = user.is_active ? this.userService.inactivate(user.id, reason) : this.userService.reactivate(user.id, reason);
    request.subscribe({
      next: (response) => {
        this.dialogBusy.set(false);
        this.dialogUser.set(null);
        this.success.set(response.message);
        this.search(this.page);
      },
      error: (error) => {
        this.dialogBusy.set(false);
        this.dialogError.set(errorMessage(error));
      },
    });
  }
}
