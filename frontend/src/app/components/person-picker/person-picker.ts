import { Component, EventEmitter, Input, Output, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { HttpErrorResponse } from '@angular/common/http';
import { Department, Person } from '../../core/models/api.models';
import { PersonService } from '../../core/services/person.service';
import { errorMessage } from '../../core/services/http-helpers';

// Busca una persona por identificación o nombre, o la registra si no existe.
// La persona que entrega o reclama NO necesita cuenta en el sistema.
@Component({
  selector: 'app-person-picker',
  imports: [FormsModule],
  templateUrl: './person-picker.html',
  styleUrl: './person-picker.scss',
})
export class PersonPicker {
  @Input() label = 'Persona';
  @Input() departments: Department[] = [];
  @Output() selected = new EventEmitter<Person | null>();

  readonly affiliationTypes = ['ESTUDIANTE', 'EMPLEADO', 'CONTRATISTA', 'PROVEEDOR', 'VISITANTE'];
  search = '';
  results = signal<Person[]>([]);
  searched = signal(false);
  chosen = signal<Person | null>(null);
  creating = signal(false);
  saving = signal(false);
  error = signal('');
  newPerson = this.emptyPerson();

  constructor(private personService: PersonService) {}

  doSearch(): void {
    if (this.search.trim().length < 2) {
      this.error.set('Escriba al menos 2 caracteres.');
      return;
    }
    this.error.set('');
    this.personService.list({ text: this.search.trim(), is_active: true, page_size: 10 }).subscribe({
      next: (response) => {
        this.results.set(response.data.items);
        this.searched.set(true);
      },
      error: (error) => this.error.set(errorMessage(error)),
    });
  }

  choose(person: Person): void {
    this.chosen.set(person);
    this.results.set([]);
    this.creating.set(false);
    this.selected.emit(person);
  }

  clear(): void {
    this.chosen.set(null);
    this.searched.set(false);
    this.selected.emit(null);
  }

  startCreate(): void {
    this.newPerson = this.emptyPerson();
    this.newPerson.identification = /^\d+$/.test(this.search.trim()) ? this.search.trim() : '';
    this.creating.set(true);
    this.error.set('');
  }

  create(): void {
    if (!this.newPerson.identification.trim() || !this.newPerson.full_name.trim()) {
      this.error.set('Identificación y nombre son obligatorios.');
      return;
    }
    this.saving.set(true);
    const body: Record<string, unknown> = {
      identification: this.newPerson.identification,
      full_name: this.newPerson.full_name,
      affiliation_type: this.newPerson.affiliation_type,
    };
    if (this.newPerson.department_id) body['department_id'] = this.newPerson.department_id;
    if (this.newPerson.email.trim()) body['email'] = this.newPerson.email;
    if (this.newPerson.phone.trim()) body['phone'] = this.newPerson.phone;
    this.personService.create(body).subscribe({
      next: (response) => {
        this.saving.set(false);
        this.choose(response.data);
      },
      error: (error) => {
        this.saving.set(false);
        this.error.set(errorMessage(error));
        if (error instanceof HttpErrorResponse && error.status === 409 && error.error?.data?.existing_id) {
          this.personService.get(error.error.data.existing_id).subscribe((response) => this.choose(response.data));
        }
      },
    });
  }

  private emptyPerson() {
    return {
      identification: '',
      full_name: '',
      affiliation_type: 'ESTUDIANTE',
      department_id: null as number | null,
      email: '',
      phone: '',
    };
  }
}
