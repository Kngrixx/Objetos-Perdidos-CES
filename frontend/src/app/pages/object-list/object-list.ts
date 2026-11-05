import { Component, OnInit, signal } from '@angular/core';
import { DatePipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { Block, Campus, Category, ObjectLost, ObjectType } from '../../core/models/api.models';
import { AuthService } from '../../core/services/auth.service';
import { ObjectLostService } from '../../core/services/object-lost.service';
import { CampusService } from '../../core/services/campus.service';
import { BlockService } from '../../core/services/block.service';
import { CategoryService } from '../../core/services/category.service';
import { ObjectTypeService } from '../../core/services/object-type.service';
import { errorMessage } from '../../core/services/http-helpers';
import { Pager } from '../../components/pager/pager';
import { SecureImage } from '../../components/secure-image/secure-image';

// Consulta de objetos con filtros combinables y paginación (getByFilter del backend).
@Component({
  selector: 'app-object-list',
  imports: [FormsModule, RouterLink, DatePipe, Pager, SecureImage],
  templateUrl: './object-list.html',
  styleUrl: './object-list.scss',
})
export class ObjectList implements OnInit {
  filters = {
    text: '',
    code: '',
    campus_id: null as number | null,
    block_id: null as number | null,
    category_id: null as number | null,
    object_type_id: null as number | null,
    status: '',
    is_active: 'true',
    date_from: '',
    date_to: '',
  };
  page = 1;
  pageSize = 20;

  campuses = signal<Campus[]>([]);
  blocks = signal<Block[]>([]);
  categories = signal<Category[]>([]);
  types = signal<ObjectType[]>([]);
  items = signal<ObjectLost[]>([]);
  total = signal(0);
  message = signal('');
  error = signal('');
  loading = signal(false);
  isConsulta = false;
  canReceive = false;

  constructor(
    private objectService: ObjectLostService,
    private campusService: CampusService,
    private blockService: BlockService,
    private categoryService: CategoryService,
    private typeService: ObjectTypeService,
    private authService: AuthService,
    private route: ActivatedRoute,
    private router: Router,
  ) {
    this.isConsulta = this.authService.hasRole('CONSULTA');
    this.canReceive = this.authService.hasRole('ADMIN', 'OPERADOR');
  }

  ngOnInit(): void {
    // Filtros que llegan desde el dashboard (al seleccionar un indicador)
    const params = this.route.snapshot.queryParamMap;
    const number = (key: string) => (params.get(key) ? Number(params.get(key)) : null);
    this.filters.campus_id = number('campus_id');
    this.filters.category_id = number('category_id');
    this.filters.status = params.get('status') || '';
    this.filters.is_active = params.get('is_active') || 'true';
    this.filters.date_from = params.get('date_from') || '';
    this.filters.date_to = params.get('date_to') || '';

    this.campusService.list({ page_size: 100 }).subscribe((r) => this.campuses.set(r.data.items));
    this.categoryService.list({ page_size: 100 }).subscribe((r) => this.categories.set(r.data.items));
    if (this.filters.campus_id) this.loadBlocks();
    if (this.filters.category_id) this.loadTypes();
    this.search();
  }

  // Listas dependientes: la sede filtra los bloques y la categoría filtra los tipos.
  onCampusChange(): void {
    this.filters.block_id = null;
    this.loadBlocks();
  }

  onCategoryChange(): void {
    this.filters.object_type_id = null;
    this.loadTypes();
  }

  loadBlocks(): void {
    this.blocks.set([]);
    if (this.filters.campus_id) {
      this.blockService.list({ campus_id: this.filters.campus_id, page_size: 100 }).subscribe((r) => this.blocks.set(r.data.items));
    }
  }

  loadTypes(): void {
    this.types.set([]);
    if (this.filters.category_id) {
      this.typeService.list({ category_id: this.filters.category_id, page_size: 100 }).subscribe((r) => this.types.set(r.data.items));
    }
  }

  search(page = 1): void {
    this.page = page;
    this.loading.set(true);
    this.error.set('');
    const query: Record<string, unknown> = {
      ...this.filters,
      is_active: this.filters.is_active === 'all' ? null : this.filters.is_active,
      page: this.page,
      page_size: this.pageSize,
    };
    if (this.isConsulta) {
      // CONSULTA solo puede ver activos y DISPONIBLES (el backend lo exige)
      query['status'] = null;
      query['is_active'] = null;
    }
    this.objectService.list(query).subscribe({
      next: (response) => {
        this.items.set(response.data.items);
        this.total.set(response.data.total);
        this.message.set(response.message);
        this.loading.set(false);
      },
      error: (error) => {
        this.error.set(errorMessage(error));
        this.items.set([]);
        this.total.set(0);
        this.loading.set(false);
      },
    });
  }

  clear(): void {
    this.filters = { text: '', code: '', campus_id: null, block_id: null, category_id: null, object_type_id: null,
      status: '', is_active: 'true', date_from: '', date_to: '' };
    this.blocks.set([]);
    this.types.set([]);
    this.search();
  }

  open(item: ObjectLost): void {
    this.router.navigate(['/objetos', item.id]);
  }
}
