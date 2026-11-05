import { Component, OnInit, signal } from '@angular/core';
import { DatePipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { ReturnRecord } from '../../core/models/api.models';
import { ReturnService } from '../../core/services/return.service';
import { errorMessage, saveBlob } from '../../core/services/http-helpers';
import { Pager } from '../../components/pager/pager';

// Histórico de devoluciones (solo lectura) con descarga de la constancia PDF.
@Component({
  selector: 'app-returns',
  imports: [FormsModule, RouterLink, DatePipe, Pager],
  templateUrl: './returns.html',
  styleUrl: './returns.scss',
})
export class Returns implements OnInit {
  filters = { date_from: '', date_to: '' };
  page = 1;
  pageSize = 20;
  items = signal<ReturnRecord[]>([]);
  total = signal(0);
  message = signal('');
  error = signal('');
  loading = signal(false);

  constructor(private returnService: ReturnService) {}

  ngOnInit(): void {
    this.search();
  }

  search(page = 1): void {
    this.page = page;
    this.loading.set(true);
    this.error.set('');
    this.returnService.list({ ...this.filters, page: this.page, page_size: this.pageSize }).subscribe({
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

  download(record: ReturnRecord): void {
    this.returnService.receipt(record.id).subscribe({
      next: (blob) => saveBlob(blob, `constancia_${record.receipt_reference}.pdf`),
      error: (error) => this.error.set(errorMessage(error)),
    });
  }
}
