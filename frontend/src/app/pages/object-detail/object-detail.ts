import { Component, OnInit, computed, signal } from '@angular/core';
import { DatePipe, KeyValuePipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { Observable } from 'rxjs';
import { AuditLog, Claim, Department, ObjectLost, Person, Photo } from '../../core/models/api.models';
import { AuthService } from '../../core/services/auth.service';
import { ObjectLostService } from '../../core/services/object-lost.service';
import { PhotoService } from '../../core/services/photo.service';
import { ClaimService } from '../../core/services/claim.service';
import { ReturnService } from '../../core/services/return.service';
import { DepartmentService } from '../../core/services/department.service';
import { errorMessage, saveBlob } from '../../core/services/http-helpers';
import { SecureImage } from '../../components/secure-image/secure-image';
import { ReasonDialog } from '../../components/reason-dialog/reason-dialog';
import { PersonPicker } from '../../components/person-picker/person-picker';

interface DialogConfig {
  title: string;
  description: string;
  confirmLabel: string;
  danger: boolean;
  action: (reason: string) => Observable<unknown>;
  success: string;
}

// Detalle del objeto: datos, responsables, fotos, reclamaciones, devolución e historial.
@Component({
  selector: 'app-object-detail',
  imports: [FormsModule, RouterLink, DatePipe, KeyValuePipe, SecureImage, ReasonDialog, PersonPicker],
  templateUrl: './object-detail.html',
  styleUrl: './object-detail.scss',
})
export class ObjectDetail implements OnInit {
  objectId = 0;
  item = signal<ObjectLost | null>(null);
  photos = signal<Photo[]>([]);
  claims = signal<Claim[]>([]);
  history = signal<AuditLog[]>([]);
  departments = signal<Department[]>([]);
  loading = signal(true);
  error = signal('');
  success = signal('');

  dialog = signal<DialogConfig | null>(null);
  dialogBusy = signal(false);
  dialogError = signal('');

  // Nueva reclamación
  showClaimForm = signal(false);
  claimant = signal<Person | null>(null);
  claimForm = { evidence: '', identity_verified: false, verification_notes: '' };
  savingClaim = signal(false);
  claimError = signal('');

  // Devolución
  returnForm = { verification_summary: '', owner_confirmation: false, notes: '' };
  savingReturn = signal(false);
  returnError = signal('');

  uploading = signal(false);

  isConsulta: boolean;
  isAdmin: boolean;
  canOperate: boolean;

  isEditable = computed(() => {
    const item = this.item();
    return !!item && item.is_active === true && item.status === 'DISPONIBLE';
  });
  acceptedClaim = computed(() => this.claims().find((claim) => claim.status === 'ACEPTADA') || null);

  constructor(
    private route: ActivatedRoute,
    private authService: AuthService,
    private objectService: ObjectLostService,
    private photoService: PhotoService,
    private claimService: ClaimService,
    private returnService: ReturnService,
    private departmentService: DepartmentService,
  ) {
    this.isConsulta = this.authService.hasRole('CONSULTA');
    this.isAdmin = this.authService.hasRole('ADMIN');
    this.canOperate = this.authService.hasRole('ADMIN', 'OPERADOR');
  }

  ngOnInit(): void {
    this.objectId = Number(this.route.snapshot.paramMap.get('id'));
    const params = this.route.snapshot.queryParamMap;
    if (params.get('created')) this.success.set('Objeto registrado correctamente.');
    if (params.get('updated')) this.success.set('Cambios guardados. Los valores anteriores quedaron en el historial.');
    if (this.canOperate) {
      this.departmentService.list({ page_size: 100, is_active: true }).subscribe((r) => this.departments.set(r.data.items));
    }
    this.load();
  }

  load(): void {
    this.loading.set(true);
    this.objectService.get(this.objectId).subscribe({
      next: (response) => {
        this.item.set(response.data);
        this.loading.set(false);
        if (this.canOperate) {
          this.loadPhotos();
          this.loadClaims();
          this.loadHistory();
        }
      },
      error: (error) => {
        this.error.set(errorMessage(error));
        this.loading.set(false);
      },
    });
  }

  loadPhotos(): void {
    this.photoService.list(this.objectId).subscribe((r) => this.photos.set(r.data));
  }

  loadClaims(): void {
    this.claimService.list({ object_lost_id: this.objectId, page_size: 100 }).subscribe((r) => this.claims.set(r.data.items));
  }

  loadHistory(): void {
    this.objectService.history(this.objectId).subscribe((r) => this.history.set(r.data.items));
  }

  // ---------------- confirmaciones con motivo
  openDialog(config: DialogConfig): void {
    this.dialogError.set('');
    this.dialog.set(config);
  }

  runDialog(reason: string): void {
    const config = this.dialog();
    if (!config) return;
    this.dialogBusy.set(true);
    config.action(reason).subscribe({
      next: () => {
        this.dialogBusy.set(false);
        this.dialog.set(null);
        this.success.set(config.success);
        this.error.set('');
        this.load();
      },
      error: (error) => {
        this.dialogBusy.set(false);
        this.dialogError.set(errorMessage(error));
      },
    });
  }

  inactivateObject(): void {
    this.openDialog({
      title: 'Inactivar objeto',
      description: 'Use esta opción para registros equivocados. El registro NO se borra: queda en la base y en la auditoría.',
      confirmLabel: 'Inactivar',
      danger: true,
      action: (reason) => this.objectService.inactivate(this.objectId, reason),
      success: 'Objeto inactivado. Ya no aparece en el inventario disponible.',
    });
  }

  reactivateObject(): void {
    this.openDialog({
      title: 'Reactivar objeto',
      description: 'Solo ADMIN. Se validan de nuevo sus referencias y se conserva el estado.',
      confirmLabel: 'Reactivar',
      danger: false,
      action: (reason) => this.objectService.reactivate(this.objectId, reason),
      success: 'Objeto reactivado.',
    });
  }

  inactivatePhoto(photo: Photo): void {
    this.openDialog({
      title: 'Inactivar fotografía',
      description: 'El archivo y su metadata se conservan. Debe quedar al menos una foto activa.',
      confirmLabel: 'Inactivar foto',
      danger: true,
      action: (reason) => this.photoService.inactivate(photo.id, reason),
      success: 'Fotografía inactivada.',
    });
  }

  reactivatePhoto(photo: Photo): void {
    this.openDialog({
      title: 'Reactivar fotografía',
      description: 'Se respeta el máximo de 5 fotos activas.',
      confirmLabel: 'Reactivar foto',
      danger: false,
      action: (reason) => this.photoService.reactivate(photo.id, reason),
      success: 'Fotografía reactivada.',
    });
  }

  decide(claim: Claim, decision: 'ACEPTADA' | 'RECHAZADA'): void {
    this.openDialog({
      title: decision === 'ACEPTADA' ? 'Aceptar reclamación' : 'Rechazar reclamación',
      description:
        decision === 'ACEPTADA'
          ? 'Confirme que verificó la identificación y las características no públicas.'
          : 'El objeto seguirá DISPONIBLE.',
      confirmLabel: decision === 'ACEPTADA' ? 'Aceptar' : 'Rechazar',
      danger: decision === 'RECHAZADA',
      action: (reason) => this.claimService.decide(claim.id, decision, reason),
      success: decision === 'ACEPTADA' ? 'Reclamación aceptada. Ya puede registrar la devolución.' : 'Reclamación rechazada.',
    });
  }

  markVerified(claim: Claim): void {
    this.openDialog({
      title: 'Registrar verificación de identidad',
      description: 'Se corrige la reclamación pendiente: identificación verificada.',
      confirmLabel: 'Guardar',
      danger: false,
      action: (reason) => this.claimService.update(claim.id, { identity_verified: true, reason }),
      success: 'Verificación registrada.',
    });
  }

  inactivateClaim(claim: Claim): void {
    this.openDialog({
      title: 'Inactivar reclamación',
      description: 'Solo ADMIN y solo reclamaciones pendientes.',
      confirmLabel: 'Inactivar',
      danger: true,
      action: (reason) => this.claimService.inactivate(claim.id, reason),
      success: 'Reclamación inactivada.',
    });
  }

  // ---------------- fotos nuevas
  onAddPhotos(event: Event): void {
    const input = event.target as HTMLInputElement;
    const files = Array.from(input.files || []);
    input.value = '';
    if (files.length === 0 || this.uploading()) return;
    this.uploading.set(true);
    this.photoService.add(this.objectId, files).subscribe({
      next: (response) => {
        this.uploading.set(false);
        this.success.set(response.message);
        this.error.set('');
        this.load();
      },
      error: (error) => {
        this.uploading.set(false);
        this.error.set(errorMessage(error));
      },
    });
  }

  // ---------------- reclamación
  saveClaim(): void {
    if (this.savingClaim()) return;
    if (!this.claimant()) {
      this.claimError.set('Seleccione o registre a la persona que reclama.');
      return;
    }
    if (this.claimForm.evidence.trim().length < 5) {
      this.claimError.set('Describa la evidencia de pertenencia.');
      return;
    }
    this.savingClaim.set(true);
    this.claimService
      .create({
        object_lost_id: this.objectId,
        claimant_person_id: this.claimant()!.id,
        evidence: this.claimForm.evidence,
        identity_verified: this.claimForm.identity_verified,
        verification_notes: this.claimForm.verification_notes,
      })
      .subscribe({
        next: (response) => {
          this.savingClaim.set(false);
          this.showClaimForm.set(false);
          this.claimForm = { evidence: '', identity_verified: false, verification_notes: '' };
          this.claimError.set('');
          this.success.set(response.message);
          this.load();
        },
        error: (error) => {
          this.savingClaim.set(false);
          this.claimError.set(errorMessage(error));
        },
      });
  }

  // ---------------- devolución
  saveReturn(): void {
    const claim = this.acceptedClaim();
    if (!claim || this.savingReturn()) return;
    if (this.returnForm.verification_summary.trim().length < 5) {
      this.returnError.set('Escriba el resumen de la verificación.');
      return;
    }
    if (!this.returnForm.owner_confirmation) {
      this.returnError.set('Marque la confirmación de recepción del propietario.');
      return;
    }
    this.savingReturn.set(true);
    this.returnService
      .create({
        claim_id: claim.id,
        object_lost_id: this.objectId,
        verification_summary: this.returnForm.verification_summary,
        owner_confirmation: true,
        notes: this.returnForm.notes,
      })
      .subscribe({
        next: (response) => {
          this.savingReturn.set(false);
          this.returnError.set('');
          this.success.set(response.message);
          this.load();
        },
        error: (error) => {
          this.savingReturn.set(false);
          this.returnError.set(errorMessage(error));
        },
      });
  }

  downloadReceipt(returnId: number, reference: string): void {
    this.returnService.receipt(returnId).subscribe({
      next: (blob) => saveBlob(blob, `constancia_${reference}.pdf`),
      error: (error) => this.error.set(errorMessage(error)),
    });
  }

  // ---------------- historial
  actionLabel(action: string): string {
    const labels: Record<string, string> = {
      CREATE: 'Creación',
      UPDATE: 'Edición',
      INACTIVATE: 'Inactivación',
      REACTIVATE: 'Reactivación',
      RETURN: 'Devolución',
      ADMIN_CORRECTION: 'Corrección administrativa',
      DECISION_ACEPTADA: 'Reclamación aceptada',
      DECISION_RECHAZADA: 'Reclamación rechazada',
    };
    return labels[action] || action;
  }

  entityLabel(entity: string): string {
    const labels: Record<string, string> = {
      object_lost: 'Objeto',
      object_photo: 'Foto',
      claim: 'Reclamación',
      return_record: 'Devolución',
    };
    return labels[entity] || entity;
  }

  showValue(value: unknown): string {
    if (value === null || value === undefined) return '—';
    return String(value);
  }
}
