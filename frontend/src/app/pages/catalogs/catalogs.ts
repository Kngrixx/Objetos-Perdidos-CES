import { Component, OnInit, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Observable } from 'rxjs';
import { ApiResponse, Campus, Category, Page } from '../../core/models/api.models';
import { AuthService } from '../../core/services/auth.service';
import { CampusService } from '../../core/services/campus.service';
import { BlockService } from '../../core/services/block.service';
import { DepartmentService } from '../../core/services/department.service';
import { CategoryService } from '../../core/services/category.service';
import { ObjectTypeService } from '../../core/services/object-type.service';
import { errorMessage } from '../../core/services/http-helpers';
import { Pager } from '../../components/pager/pager';
import { ReasonDialog } from '../../components/reason-dialog/reason-dialog';

type Kind = 'campus' | 'block' | 'department' | 'category' | 'type';

interface CatalogItem {
  id: number;
  name: string;
  is_active: boolean;
  inactivation_reason: string | null;
  campus_name?: string;
  category_name?: string;
}

// Lo que tienen en común los servicios de catálogos (mismas rutas en el backend).
interface CatalogApi {
  list(filters: Record<string, unknown>): Observable<ApiResponse<Page<CatalogItem>>>;
  create(body: Record<string, unknown>): Observable<ApiResponse<CatalogItem>>;
  update(id: number, body: Record<string, unknown>): Observable<ApiResponse<CatalogItem>>;
  inactivate(id: number, reason: string): Observable<ApiResponse<CatalogItem>>;
  reactivate(id: number, reason: string): Observable<ApiResponse<CatalogItem>>;
}

@Component({
  selector: 'app-catalogs',
  imports: [FormsModule, Pager, ReasonDialog],
  templateUrl: './catalogs.html',
  styleUrl: './catalogs.scss',
})
export class Catalogs implements OnInit {
  readonly tabs: { kind: Kind; label: string }[] = [
    { kind: 'campus', label: 'Sedes' },
    { kind: 'block', label: 'Bloques' },
    { kind: 'department', label: 'Dependencias' },
    { kind: 'category', label: 'Categorías' },
    { kind: 'type', label: 'Tipos de objeto' },
  ];
  kind: Kind = 'campus';
  filters = { name: '', parent_id: null as number | null, is_active: 'true' };
  newItem = { name: '', parent_id: null as number | null };
  editing: { id: number; name: string } | null = null;
  page = 1;
  pageSize = 20;

  items = signal<CatalogItem[]>([]);
  total = signal(0);
  campuses = signal<Campus[]>([]);
  categories = signal<Category[]>([]);
  message = signal('');
  error = signal('');
  success = signal('');
  loading = signal(false);
  saving = signal(false);
  dialogItem = signal<CatalogItem | null>(null);
  dialogBusy = signal(false);
  dialogError = signal('');

  isAdmin: boolean;
  private apis: Record<Kind, CatalogApi>;

  constructor(
    authService: AuthService,
    campusService: CampusService,
    blockService: BlockService,
    departmentService: DepartmentService,
    categoryService: CategoryService,
    typeService: ObjectTypeService,
  ) {
    this.isAdmin = authService.hasRole('ADMIN');
    this.apis = {
      campus: campusService,
      block: blockService,
      department: departmentService,
      category: categoryService,
      type: typeService,
    };
  }

  ngOnInit(): void {
    this.loadParents();
    this.search();
  }

  get hasParent(): boolean {
    return this.kind === 'block' || this.kind === 'type';
  }

  get parentLabel(): string {
    return this.kind === 'block' ? 'Sede' : 'Categoría';
  }

  get parentOptions(): { id: number; name: string }[] {
    return this.kind === 'block' ? this.campuses() : this.categories();
  }

  // OPERADOR puede crear tipos de objeto; el resto de cambios en catálogos es solo ADMIN.
  get canCreate(): boolean {
    return this.isAdmin || this.kind === 'type';
  }

  loadParents(): void {
    this.apis.campus.list({ page_size: 100, is_active: true }).subscribe((r) => this.campuses.set(r.data.items as Campus[]));
    this.apis.category.list({ page_size: 100, is_active: true }).subscribe((r) => this.categories.set(r.data.items as Category[]));
  }

  selectTab(kind: Kind): void {
    this.kind = kind;
    this.filters = { name: '', parent_id: null, is_active: 'true' };
    this.newItem = { name: '', parent_id: null };
    this.editing = null;
    this.error.set('');
    this.success.set('');
    this.search();
  }

  search(page = 1): void {
    this.page = page;
    this.loading.set(true);
    const query: Record<string, unknown> = {
      name: this.filters.name,
      is_active: this.filters.is_active === 'all' ? null : this.filters.is_active,
      page: this.page,
      page_size: this.pageSize,
    };
    if (this.kind === 'block') query['campus_id'] = this.filters.parent_id;
    if (this.kind === 'type') query['category_id'] = this.filters.parent_id;
    this.apis[this.kind].list(query).subscribe({
      next: (response) => {
        this.items.set(response.data.items);
        this.total.set(response.data.total);
        this.message.set(response.message);
        this.loading.set(false);
      },
      error: (error) => {
        this.items.set([]);
        this.error.set(errorMessage(error));
        this.loading.set(false);
      },
    });
  }

  create(): void {
    if (this.saving()) return;
    if (!this.newItem.name.trim()) {
      this.error.set('Escriba el nombre.');
      return;
    }
    const body: Record<string, unknown> = { name: this.newItem.name };
    if (this.kind === 'block') body['campus_id'] = this.newItem.parent_id;
    if (this.kind === 'type') body['category_id'] = this.newItem.parent_id;
    this.saving.set(true);
    this.apis[this.kind].create(body).subscribe({
      next: (response) => {
        this.saving.set(false);
        this.newItem = { name: '', parent_id: this.newItem.parent_id };
        this.success.set(response.message);
        this.error.set('');
        this.search();
        this.loadParents();
      },
      error: (error) => {
        this.saving.set(false);
        this.error.set(errorMessage(error));
      },
    });
  }

  saveEdit(): void {
    if (!this.editing || this.saving()) return;
    this.saving.set(true);
    this.apis[this.kind].update(this.editing.id, { name: this.editing.name }).subscribe({
      next: (response) => {
        this.saving.set(false);
        this.editing = null;
        this.success.set(response.message);
        this.error.set('');
        this.search(this.page);
        this.loadParents();
      },
      error: (error) => {
        this.saving.set(false);
        this.error.set(errorMessage(error));
      },
    });
  }

  openDialog(item: CatalogItem): void {
    this.dialogError.set('');
    this.dialogItem.set(item);
  }

  toggleActive(reason: string): void {
    const item = this.dialogItem();
    if (!item) return;
    this.dialogBusy.set(true);
    const api = this.apis[this.kind];
    const request = item.is_active ? api.inactivate(item.id, reason) : api.reactivate(item.id, reason);
    request.subscribe({
      next: (response) => {
        this.dialogBusy.set(false);
        this.dialogItem.set(null);
        this.success.set(response.message);
        this.search(this.page);
        this.loadParents();
      },
      error: (error) => {
        this.dialogBusy.set(false);
        this.dialogError.set(errorMessage(error));
      },
    });
  }
}
