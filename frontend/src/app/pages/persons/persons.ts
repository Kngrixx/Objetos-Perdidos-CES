import { Component, OnInit, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Department, Person } from '../../core/models/api.models';
import { AuthService } from '../../core/services/auth.service';
import { PersonService } from '../../core/services/person.service';
import { DepartmentService } from '../../core/services/department.service';
import { errorMessage } from '../../core/services/http-helpers';
import { Pager } from '../../components/pager/pager';
import { ReasonDialog } from '../../components/reason-dialog/reason-dialog';

// Personas que entregan o reclaman objetos (no tienen cuenta en el sistema).
@Component({
  selector: 'app-persons',
  imports: [FormsModule, Pager, ReasonDialog],
  templateUrl: './persons.html',
  styleUrl: './persons.scss',
})
export class Persons implements OnInit {
  readonly affiliationTypes = ['ESTUDIANTE', 'EMPLEADO', 'CONTRATISTA', 'PROVEEDOR', 'VISITANTE'];
  filters = { text: '', affiliation_type: '', is_active: 'true' };
  page = 1;
  pageSize = 20;
  form = this.emptyForm();
  editingId: number | null = null;

  items = signal<Person[]>([]);
  total = signal(0);
  departments = signal<Department[]>([]);
  message = signal('');
  error = signal('');
  success = signal('');
  loading = signal(false);
  saving = signal(false);
  showForm = signal(false);
  dialogPerson = signal<Person | null>(null);
  dialogBusy = signal(false);
  dialogError = signal('');
  isAdmin: boolean;

  constructor(
    private personService: PersonService,
    private departmentService: DepartmentService,
    authService: AuthService,
  ) {
    this.isAdmin = authService.hasRole('ADMIN');
  }

  ngOnInit(): void {
    this.departmentService.list({ page_size: 100, is_active: true }).subscribe((r) => this.departments.set(r.data.items));
    this.search();
  }

  search(page = 1): void {
    this.page = page;
    this.loading.set(true);
    const query = { ...this.filters, is_active: this.filters.is_active === 'all' ? null : this.filters.is_active };
    this.personService.list({ ...query, page: this.page, page_size: this.pageSize }).subscribe({
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

  newPerson(): void {
    this.editingId = null;
    this.form = this.emptyForm();
    this.error.set('');
    this.showForm.set(true);
  }

  edit(person: Person): void {
    this.editingId = person.id;
    this.form = {
      identification: person.identification,
      full_name: person.full_name,
      affiliation_type: person.affiliation_type,
      department_id: person.department_id,
      email: person.email || '',
      phone: person.phone || '',
      reason: '',
    };
    this.error.set('');
    this.showForm.set(true);
  }

  save(): void {
    if (this.saving()) return;
    if (!this.form.identification.trim() || !this.form.full_name.trim()) {
      this.error.set('Identificación y nombre son obligatorios.');
      return;
    }
    const body: Record<string, unknown> = {
      identification: this.form.identification,
      full_name: this.form.full_name,
      affiliation_type: this.form.affiliation_type,
      department_id: this.form.department_id,
      email: this.form.email || null,
      phone: this.form.phone || null,
    };
    if (this.editingId && this.form.reason.trim()) body['reason'] = this.form.reason;
    this.saving.set(true);
    const request = this.editingId ? this.personService.update(this.editingId, body) : this.personService.create(body);
    request.subscribe({
      next: (response) => {
        this.saving.set(false);
        this.showForm.set(false);
        this.success.set(response.message);
        this.error.set('');
        this.search(this.page);
      },
      error: (error) => {
        this.saving.set(false);
        this.error.set(errorMessage(error));
      },
    });
  }

  toggleActive(reason: string): void {
    const person = this.dialogPerson();
    if (!person) return;
    this.dialogBusy.set(true);
    const request = person.is_active
      ? this.personService.inactivate(person.id, reason)
      : this.personService.reactivate(person.id, reason);
    request.subscribe({
      next: (response) => {
        this.dialogBusy.set(false);
        this.dialogPerson.set(null);
        this.success.set(response.message);
        this.search(this.page);
      },
      error: (error) => {
        this.dialogBusy.set(false);
        this.dialogError.set(errorMessage(error));
      },
    });
  }

  openDialog(person: Person): void {
    this.dialogError.set('');
    this.dialogPerson.set(person);
  }

  private emptyForm() {
    return {
      identification: '',
      full_name: '',
      affiliation_type: 'ESTUDIANTE',
      department_id: null as number | null,
      email: '',
      phone: '',
      reason: '',
    };
  }
}
