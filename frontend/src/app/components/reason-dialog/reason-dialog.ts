import { Component, EventEmitter, Input, Output, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

// Ventana de confirmación que exige un motivo (inactivar, reactivar, decidir...).
@Component({
  selector: 'app-reason-dialog',
  imports: [FormsModule],
  templateUrl: './reason-dialog.html',
  styleUrl: './reason-dialog.scss',
})
export class ReasonDialog {
  @Input() title = 'Confirmar';
  @Input() description = '';
  @Input() confirmLabel = 'Confirmar';
  @Input() danger = false;
  @Input() busy = false;
  @Input() errorText = '';
  @Output() confirmed = new EventEmitter<string>();
  @Output() cancelled = new EventEmitter<void>();

  reason = '';
  localError = signal('');

  confirm(): void {
    if (this.reason.trim().length < 5) {
      this.localError.set('Escriba un motivo de al menos 5 caracteres.');
      return;
    }
    this.localError.set('');
    this.confirmed.emit(this.reason.trim());
  }
}
