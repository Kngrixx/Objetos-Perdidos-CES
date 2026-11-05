import { Component, OnInit, signal } from '@angular/core';
import { DatePipe, JsonPipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AuditLog } from '../../core/models/api.models';
import { AuditService } from '../../core/services/audit.service';
import { errorMessage } from '../../core/services/http-helpers';
import { Pager } from '../../components/pager/pager';

// Auditoría (solo ADMIN): historial de todos los cambios, solo lectura.
@Component({
  selector: 'app-audit',
  imports: [FormsModule, DatePipe, JsonPipe, Pager],
  templateUrl: './audit.html',
  styleUrl: './audit.scss',
})
export class Audit implements OnInit {
  readonly entities = ['object_lost', 'object_photo', 'claim', 'return_record', 'person', 'user', 'campus', 'block',
    'department', 'object_category', 'object_type'];
  filters = { entity: '', entity_id: '', actor_user_id: '', action: '', date_from: '', date_to: '' };
  page = 1;
  pageSize = 20;
  expanded: Record<number, boolean> = {};

  items = signal<AuditLog[]>([]);
  total = signal(0);
  message = signal('');
  error = signal('');
  loading = signal(false);

  constructor(private auditService: AuditService) {}

  ngOnInit(): void {
    this.search();
  }

  search(page = 1): void {
    this.page = page;
    this.loading.set(true);
    this.error.set('');
    this.auditService.list({ ...this.filters, page: this.page, page_size: this.pageSize }).subscribe({
      next: (response) => {
        this.items.set(response.data.items);
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

  toggle(id: number): void {
    this.expanded[id] = !this.expanded[id];
  }
}
