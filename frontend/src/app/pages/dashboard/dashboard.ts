import { Component, OnInit, signal } from '@angular/core';
import { DatePipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { forkJoin } from 'rxjs';
import { Campus, DashboardSummary, ObjectLost } from '../../core/models/api.models';
import { DashboardService } from '../../core/services/dashboard.service';
import { CampusService } from '../../core/services/campus.service';
import { errorMessage } from '../../core/services/http-helpers';

interface Bar {
  id: number;
  label: string;
  total: number;
  percent: number;
}

// Dashboard exclusivo del ADMIN: todos los números se calculan en el backend.
@Component({
  selector: 'app-dashboard',
  imports: [FormsModule, RouterLink, DatePipe],
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.scss',
})
export class Dashboard implements OnInit {
  dateFrom = '';
  dateTo = '';
  campusId: number | null = null;

  campuses = signal<Campus[]>([]);
  summary = signal<DashboardSummary | null>(null);
  byCategory = signal<Bar[]>([]);
  byCampus = signal<Bar[]>([]);
  recent = signal<ObjectLost[]>([]);
  loading = signal(false);
  error = signal('');

  constructor(
    private dashboardService: DashboardService,
    private campusService: CampusService,
    private router: Router,
  ) {}

  ngOnInit(): void {
    this.campusService.list({ page_size: 100 }).subscribe((response) => this.campuses.set(response.data.items));
    this.load();
  }

  filters(): Record<string, unknown> {
    return { date_from: this.dateFrom, date_to: this.dateTo, campus_id: this.campusId };
  }

  load(): void {
    this.loading.set(true);
    this.error.set('');
    const filters = this.filters();
    forkJoin({
      summary: this.dashboardService.summary(filters),
      byCategory: this.dashboardService.byCategory(filters),
      byCampus: this.dashboardService.byCampus(filters),
      recent: this.dashboardService.recent({ ...filters, limit: 8 }),
    }).subscribe({
      next: (result) => {
        this.summary.set(result.summary.data);
        this.byCategory.set(this.toBars(result.byCategory.data.map((r) => ({ id: r.category_id, label: r.category, total: r.total }))));
        this.byCampus.set(this.toBars(result.byCampus.data.map((r) => ({ id: r.campus_id, label: r.campus, total: r.total }))));
        this.recent.set(result.recent.data);
        this.loading.set(false);
      },
      error: (error) => {
        this.error.set(errorMessage(error));
        this.loading.set(false);
      },
    });
  }

  clear(): void {
    this.dateFrom = '';
    this.dateTo = '';
    this.campusId = null;
    this.load();
  }

  // Al seleccionar un indicador se abre el listado correspondiente con los mismos filtros.
  open(kind: 'total' | 'available' | 'returned' | 'inactive' | 'pending'): void {
    const base = { date_from: this.dateFrom || null, date_to: this.dateTo || null, campus_id: this.campusId };
    if (kind === 'pending') {
      this.router.navigate(['/reclamaciones'], { queryParams: { status: 'PENDIENTE' } });
      return;
    }
    const extra: Record<string, string | null> = {
      total: { is_active: 'all' },
      available: { status: 'DISPONIBLE', is_active: 'true' },
      returned: { status: 'DEVUELTO', is_active: 'true' },
      inactive: { is_active: 'false' },
    }[kind] as Record<string, string | null>;
    this.router.navigate(['/objetos'], { queryParams: { ...base, ...extra } });
  }

  openCategory(categoryId: number): void {
    this.router.navigate(['/objetos'], {
      queryParams: { category_id: categoryId, is_active: 'true', date_from: this.dateFrom || null, date_to: this.dateTo || null, campus_id: this.campusId },
    });
  }

  openCampus(campusId: number): void {
    this.router.navigate(['/objetos'], {
      queryParams: { campus_id: campusId, is_active: 'true', date_from: this.dateFrom || null, date_to: this.dateTo || null },
    });
  }

  private toBars(rows: { id: number; label: string; total: number }[]): Bar[] {
    const max = Math.max(1, ...rows.map((row) => row.total));
    return rows.map((row) => ({ ...row, percent: Math.round((row.total / max) * 100) }));
  }
}
