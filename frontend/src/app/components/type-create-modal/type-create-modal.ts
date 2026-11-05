import { Component, EventEmitter, Input, OnInit, Output, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { HttpErrorResponse } from '@angular/common/http';
import { Category, ObjectType } from '../../core/models/api.models';
import { ObjectTypeService } from '../../core/services/object-type.service';
import { errorMessage } from '../../core/services/http-helpers';

// "Crear tipo de objeto" desde el formulario de recepción (enunciado, sección 1).
@Component({
  selector: 'app-type-create-modal',
  imports: [FormsModule],
  templateUrl: './type-create-modal.html',
  styleUrl: './type-create-modal.scss',
})
export class TypeCreateModal implements OnInit {
  @Input() categories: Category[] = [];
  @Input() categoryId: number | null = null;
  @Output() created = new EventEmitter<ObjectType>();
  @Output() closed = new EventEmitter<void>();

  name = '';
  selectedCategory: number | null = null;
  saving = signal(false);
  error = signal('');
  existingId = signal<number | null>(null);

  constructor(private objectTypeService: ObjectTypeService) {}

  ngOnInit(): void {
    this.selectedCategory = this.categoryId;
  }

  save(): void {
    this.existingId.set(null);
    if (!this.selectedCategory || this.name.trim().length < 2) {
      this.error.set('Seleccione la categoría y escriba el nombre del tipo.');
      return;
    }
    this.saving.set(true);
    this.error.set('');
    this.objectTypeService.create({ category_id: this.selectedCategory, name: this.name }).subscribe({
      next: (response) => {
        this.saving.set(false);
        this.created.emit(response.data);
      },
      error: (error) => {
        this.saving.set(false);
        this.error.set(errorMessage(error));
        // Si ya existe (409), el backend devuelve su id para poder seleccionarlo.
        if (error instanceof HttpErrorResponse && error.status === 409 && error.error?.data?.existing_id) {
          this.existingId.set(error.error.data.existing_id);
        }
      },
    });
  }

  useExisting(): void {
    const id = this.existingId();
    if (id) {
      this.objectTypeService.get(id).subscribe({
        next: (response) => this.created.emit(response.data),
        error: (error) => this.error.set(errorMessage(error)),
      });
    }
  }
}
