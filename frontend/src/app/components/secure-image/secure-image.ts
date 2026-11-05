import { Component, Input, OnChanges, OnDestroy, signal } from '@angular/core';
import { PhotoService } from '../../core/services/photo.service';

// Muestra una foto pidiéndola al backend CON el token (ruta autorizada).
@Component({
  selector: 'app-secure-image',
  imports: [],
  templateUrl: './secure-image.html',
  styleUrl: './secure-image.scss',
})
export class SecureImage implements OnChanges, OnDestroy {
  @Input() photoId: number | null | undefined = null;
  @Input() alt = 'Foto del objeto';
  @Input() cssClass = 'thumb';

  src = signal<string | null>(null);

  constructor(private photoService: PhotoService) {}

  ngOnChanges(): void {
    this.release();
    if (!this.photoId) {
      return;
    }
    this.photoService.file(this.photoId).subscribe({
      next: (blob) => this.src.set(URL.createObjectURL(blob)),
      error: () => this.src.set(null),
    });
  }

  ngOnDestroy(): void {
    this.release();
  }

  private release(): void {
    const current = this.src();
    if (current) {
      URL.revokeObjectURL(current);
    }
    this.src.set(null);
  }
}
