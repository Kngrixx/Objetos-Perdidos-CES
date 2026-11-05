import { Component, OnDestroy, OnInit, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import {
  Block, Campus, Category, Department, ObjectLost, ObjectType, Person,
} from '../../core/models/api.models';
import { AuthService } from '../../core/services/auth.service';
import { ObjectLostService } from '../../core/services/object-lost.service';
import { CampusService } from '../../core/services/campus.service';
import { BlockService } from '../../core/services/block.service';
import { CategoryService } from '../../core/services/category.service';
import { ObjectTypeService } from '../../core/services/object-type.service';
import { DepartmentService } from '../../core/services/department.service';
import { errorMessage } from '../../core/services/http-helpers';
import { PersonPicker } from '../../components/person-picker/person-picker';
import { TypeCreateModal } from '../../components/type-create-modal/type-create-modal';

interface PhotoPreview {
  file: File;
  url: string;
}

const MAX_PHOTOS = 5;
const MAX_BYTES = 5 * 1024 * 1024;

// Convierte una fecha ISO (UTC) al formato del input datetime-local en hora de Bogotá.
function toBogotaInput(iso: string | undefined): string {
  if (!iso) return '';
  const date = new Date(new Date(iso).getTime() - 5 * 3600 * 1000);
  return date.toISOString().slice(0, 16);
}

// Recepción (crear) y edición de objetos. En edición exige motivo y la versión leída.
@Component({
  selector: 'app-object-form',
  imports: [FormsModule, RouterLink, PersonPicker, TypeCreateModal],
  templateUrl: './object-form.html',
  styleUrl: './object-form.scss',
})
export class ObjectForm implements OnInit, OnDestroy {
  mode: 'create' | 'edit' | 'correction' = 'create';
  objectId: number | null = null;
  original: ObjectLost | null = null;

  form = {
    category_id: null as number | null,
    object_type_id: null as number | null,
    description: '',
    found_campus_id: null as number | null,
    found_block_id: null as number | null,
    found_location: '',
    found_at: '',
    custody_campus_id: null as number | null,
    custody_block_id: null as number | null,
    custody_location: '',
    finder_department_id: null as number | null,
  };
  reason = '';
  typeSearch = '';
  maxDate = toBogotaInput(new Date().toISOString());

  campuses = signal<Campus[]>([]);
  foundBlocks = signal<Block[]>([]);
  custodyBlocks = signal<Block[]>([]);
  categories = signal<Category[]>([]);
  types = signal<ObjectType[]>([]);
  departments = signal<Department[]>([]);
  finder = signal<Person | null>(null);
  photos = signal<PhotoPreview[]>([]);
  showTypeModal = signal(false);
  loading = signal(false);
  saving = signal(false);
  error = signal('');

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private authService: AuthService,
    private objectService: ObjectLostService,
    private campusService: CampusService,
    private blockService: BlockService,
    private categoryService: CategoryService,
    private typeService: ObjectTypeService,
    private departmentService: DepartmentService,
  ) {}

  ngOnInit(): void {
    // Solo catálogos ACTIVOS en los selectores de nuevos registros.
    this.campusService.list({ page_size: 100, is_active: true }).subscribe((r) => this.campuses.set(r.data.items));
    this.categoryService.list({ page_size: 100, is_active: true }).subscribe((r) => this.categories.set(r.data.items));
    this.departmentService.list({ page_size: 100, is_active: true }).subscribe((r) => this.departments.set(r.data.items));
    this.form.found_at = this.maxDate;

    const id = this.route.snapshot.paramMap.get('id');
    if (id) {
      this.objectId = Number(id);
      this.loadObject();
    }
  }

  ngOnDestroy(): void {
    this.photos().forEach((photo) => URL.revokeObjectURL(photo.url));
  }

  loadObject(): void {
    this.loading.set(true);
    this.objectService.get(this.objectId!).subscribe({
      next: (response) => {
        const item = response.data;
        this.original = item;
        this.mode = item.status === 'DEVUELTO' ? 'correction' : 'edit';
        this.form = {
          category_id: item.category.id,
          object_type_id: item.object_type.id,
          description: item.description || '',
          found_campus_id: item.found_campus?.id ?? null,
          found_block_id: item.found_block?.id ?? null,
          found_location: item.found_location || '',
          found_at: toBogotaInput(item.found_at),
          custody_campus_id: item.custody_campus?.id ?? null,
          custody_block_id: item.custody_block?.id ?? null,
          custody_location: item.custody_location || '',
          finder_department_id: item.finder_department?.id ?? null,
        };
        this.loadTypes();
        this.loadBlocks('found');
        this.loadBlocks('custody');
        if (this.mode === 'correction' && !this.authService.hasRole('ADMIN')) {
          this.error.set('El objeto ya fue devuelto: solo un ADMIN puede hacer una corrección administrativa.');
        }
        if (item.is_active === false) {
          this.error.set('El objeto está inactivo: no se puede editar.');
        }
        this.loading.set(false);
      },
      error: (error) => {
        this.error.set(errorMessage(error));
        this.loading.set(false);
      },
    });
  }

  // ---------------- listas dependientes
  onCategoryChange(): void {
    this.form.object_type_id = null;
    this.typeSearch = '';
    this.loadTypes();
  }

  loadTypes(): void {
    this.types.set([]);
    if (!this.form.category_id) return;
    this.typeService
      .list({ category_id: this.form.category_id, name: this.typeSearch, is_active: true, page_size: 100 })
      .subscribe((r) => this.types.set(r.data.items));
  }

  onCampusChange(kind: 'found' | 'custody'): void {
    if (kind === 'found') this.form.found_block_id = null;
    else this.form.custody_block_id = null;
    this.loadBlocks(kind);
  }

  loadBlocks(kind: 'found' | 'custody'): void {
    const campusId = kind === 'found' ? this.form.found_campus_id : this.form.custody_campus_id;
    const target = kind === 'found' ? this.foundBlocks : this.custodyBlocks;
    target.set([]);
    if (campusId) {
      this.blockService.list({ campus_id: campusId, is_active: true, page_size: 100 }).subscribe((r) => target.set(r.data.items));
    }
  }

  onTypeCreated(type: ObjectType): void {
    // Vuelve al formulario con el tipo nuevo seleccionado.
    this.showTypeModal.set(false);
    this.form.category_id = type.category_id;
    this.typeSearch = '';
    this.typeService.list({ category_id: type.category_id, is_active: true, page_size: 100 }).subscribe((r) => {
      this.types.set(r.data.items);
      this.form.object_type_id = type.id;
    });
  }

  onFinderSelected(person: Person | null): void {
    this.finder.set(person);
    if (person && person.department_id && !this.form.finder_department_id) {
      this.form.finder_department_id = person.department_id;
    }
  }

  // ---------------- fotos (vista previa y retiro antes de guardar)
  onFilesSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    const files = Array.from(input.files || []);
    const current = [...this.photos()];
    const problems: string[] = [];
    for (const file of files) {
      if (current.length >= MAX_PHOTOS) {
        problems.push(`Máximo ${MAX_PHOTOS} fotos por objeto.`);
        break;
      }
      if (!['image/jpeg', 'image/png'].includes(file.type)) {
        problems.push(`${file.name}: solo se aceptan JPEG o PNG.`);
        continue;
      }
      if (file.size > MAX_BYTES) {
        problems.push(`${file.name}: supera 5 MB.`);
        continue;
      }
      current.push({ file, url: URL.createObjectURL(file) });
    }
    this.photos.set(current);
    this.error.set(problems.join(' '));
    input.value = '';
  }

  removePhoto(index: number): void {
    const current = [...this.photos()];
    URL.revokeObjectURL(current[index].url);
    current.splice(index, 1);
    this.photos.set(current);
  }

  // ---------------- guardar
  validate(): string {
    const f = this.form;
    if (!f.object_type_id) return 'Seleccione el tipo de objeto.';
    if (!f.description.trim()) return 'Describa las características del objeto.';
    if (!f.found_campus_id || !f.found_block_id || !f.found_location.trim()) return 'Complete sede, bloque y lugar del hallazgo.';
    if (!f.found_at) return 'Indique la fecha y hora del hallazgo.';
    if (f.found_at > toBogotaInput(new Date().toISOString())) return 'La fecha de hallazgo no puede ser futura.';
    if (!f.custody_campus_id || !f.custody_block_id || !f.custody_location.trim()) return 'Complete la ubicación de custodia.';
    if (this.mode === 'create') {
      if (!this.finder()) return 'Seleccione o registre la persona que entrega el objeto.';
      if (this.photos().length === 0) return 'Agregue al menos una fotografía.';
    } else if (this.reason.trim().length < 5) {
      return 'Escriba el motivo de la corrección (mínimo 5 caracteres).';
    }
    return '';
  }

  save(): void {
    if (this.saving()) return; // evita doble envío
    const problem = this.validate();
    if (problem) {
      this.error.set(problem);
      return;
    }
    this.error.set('');
    this.saving.set(true);
    if (this.mode === 'create') {
      this.create();
    } else {
      this.update();
    }
  }

  private create(): void {
    const f = this.form;
    const data = new FormData();
    data.append('object_type_id', String(f.object_type_id));
    data.append('description', f.description);
    data.append('found_campus_id', String(f.found_campus_id));
    data.append('found_block_id', String(f.found_block_id));
    data.append('found_location', f.found_location);
    data.append('found_at', f.found_at); // hora local de Bogotá; el backend la guarda en UTC
    data.append('custody_campus_id', String(f.custody_campus_id));
    data.append('custody_block_id', String(f.custody_block_id));
    data.append('custody_location', f.custody_location);
    data.append('finder_person_id', String(this.finder()!.id));
    if (f.finder_department_id) data.append('finder_department_id', String(f.finder_department_id));
    this.photos().forEach((photo) => data.append('photos', photo.file, photo.file.name));

    this.objectService.create(data).subscribe({
      next: (response) => {
        this.saving.set(false);
        this.router.navigate(['/objetos', response.data.id], { queryParams: { created: 1 } });
      },
      error: (error) => {
        // Los datos del formulario se conservan para corregir y reintentar.
        this.saving.set(false);
        this.error.set(errorMessage(error));
      },
    });
  }

  private update(): void {
    const item = this.original!;
    const f = this.form;
    const body: Record<string, unknown> = { reason: this.reason.trim(), version: item.version };
    if (f.object_type_id !== item.object_type.id) body['object_type_id'] = f.object_type_id;
    if (f.description !== item.description) body['description'] = f.description;
    if (f.found_block_id !== item.found_block?.id) {
      body['found_block_id'] = f.found_block_id;
      body['found_campus_id'] = f.found_campus_id;
    }
    if (f.found_location !== item.found_location) body['found_location'] = f.found_location;
    if (f.found_at !== toBogotaInput(item.found_at)) body['found_at'] = f.found_at;
    if (f.custody_block_id !== item.custody_block?.id) {
      body['custody_block_id'] = f.custody_block_id;
      body['custody_campus_id'] = f.custody_campus_id;
    }
    if (f.custody_location !== item.custody_location) body['custody_location'] = f.custody_location;
    if (this.mode === 'edit' && f.finder_department_id !== (item.finder_department?.id ?? null)) {
      body['finder_department_id'] = f.finder_department_id;
    }
    if (this.mode === 'edit' && this.finder() && this.finder()!.id !== item.finder_person?.id) {
      body['finder_person_id'] = this.finder()!.id;
    }
    if (Object.keys(body).length === 2) {
      this.saving.set(false);
      this.error.set('No hay cambios para guardar.');
      return;
    }
    const request =
      this.mode === 'correction'
        ? this.objectService.administrativeCorrection(item.id, body)
        : this.objectService.update(item.id, body);
    request.subscribe({
      next: (response) => {
        this.saving.set(false);
        this.router.navigate(['/objetos', response.data.id], { queryParams: { updated: 1 } });
      },
      error: (error) => {
        this.saving.set(false);
        this.error.set(errorMessage(error));
      },
    });
  }
}
