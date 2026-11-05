import { Component, OnInit, signal } from '@angular/core';
import { DatePipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { Block, Campus, Category, InventorySummary, ObjectLost, ObjectType } from '../../core/models/api.models';
import { InventoryService } from '../../core/services/inventory.service';
import { CampusService } from '../../core/services/campus.service';
import { BlockService } from '../../core/services/block.service';
import { CategoryService } from '../../core/services/category.service';
import { ObjectTypeService } from '../../core/services/object-type.service';
import { errorMessage, saveBlob } from '../../core/services/http-helpers';
import { Pager } from '../../components/pager/pager';
import { SecureImage } from '../../components/secure-image/secure-image';

// Inventario disponible (activo y DISPONIBLE) con resumen y exportación PDF con los filtros.
@Component({
  selector: 'app-inventory',
  imports: [FormsModule, DatePipe, Pager, SecureImage],
  templateUrl: './inventory.html',
  styleUrl: './inventory.scss',
})
export class Inventory implements OnInit {
  filters = {
    text: '',
    campus_id: null as number | null,
    block_id: null as number | null,
    category_id: null as number | null,
    object_type_id: null as number | null,
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
  summary = signal<InventorySummary | null>(null);
  message = signal('');
  error = signal('');
  loading = signal(false);
  exporting = signal(false);

  constructor(
    private inventoryService: InventoryService,
    private campusService: CampusService,
    private blockService: BlockService,
    private categoryService: CategoryService,
    private typeService: ObjectTypeService,
    private router: Router,
  ) {}

  ngOnInit(): void {
    this.campusService.list({ page_size: 100 }).subscribe((r) => this.campuses.set(r.data.items));
    this.categoryService.list({ page_size: 100 }).subscribe((r) => this.categories.set(r.data.items));
    this.search();
  }

  onCampusChange(): void {
    this.filters.block_id = null;
    this.blocks.set([]);
    if (this.filters.campus_id) {
      this.blockService.list({ campus_id: this.filters.campus_id, page_size: 100 }).subscribe((r) => this.blocks.set(r.data.items));
    }
  }

  onCategoryChange(): void {
    this.filters.object_type_id = null;
    this.types.set([]);
    if (this.filters.category_id) {
      this.typeService.list({ category_id: this.filters.category_id, page_size: 100 }).subscribe((r) => this.types.set(r.data.items));
    }
  }

  search(page = 1): void {
    this.page = page;
    this.loading.set(true);
    this.error.set('');
    this.inventoryService.list({ ...this.filters, page: this.page, page_size: this.pageSize }).subscribe({
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
    this.inventoryService.summary(this.filters).subscribe({
      next: (response) => this.summary.set(response.data),
      error: () => this.summary.set(null),
    });
  }

  clear(): void {
    this.filters = { text: '', campus_id: null, block_id: null, category_id: null, object_type_id: null, date_from: '', date_to: '' };
    this.blocks.set([]);
    this.types.set([]);
    this.search();
  }

  // El PDF usa EXACTAMENTE los mismos filtros de la consulta en pantalla.
  exportPdf(): void {
    if (this.exporting()) return;
    this.exporting.set(true);
    this.inventoryService.export(this.filters).subscribe({
      next: (blob) => {
        this.exporting.set(false);
        saveBlob(blob, 'inventario_objetos_disponibles.pdf');
      },
      error: (error) => {
        this.exporting.set(false);
        this.error.set(errorMessage(error));
      },
    });
  }

  open(item: ObjectLost): void {
    this.router.navigate(['/objetos', item.id]);
  }

  topTypes() {
    return (this.summary()?.by_type || []).slice(0, 5);
  }
}
