import { Component, OnInit, signal } from '@angular/core';
import { DatePipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { Claim } from '../../core/models/api.models';
import { ClaimService } from '../../core/services/claim.service';
import { errorMessage } from '../../core/services/http-helpers';
import { Pager } from '../../components/pager/pager';

// Listado de reclamaciones. Las decisiones se toman desde el detalle de cada objeto.
@Component({
  selector: 'app-claims',
  imports: [FormsModule, RouterLink, DatePipe, Pager],
  templateUrl: './claims.html',
  styleUrl: './claims.scss',
})
export class Claims implements OnInit {
  filters = { status: '', code: '', is_active: 'true' };
  page = 1;
  pageSize = 20;
  items = signal<Claim[]>([]);
  total = signal(0);
  message = signal('');
  error = signal('');
  loading = signal(false);

  constructor(
    private claimService: ClaimService,
    private route: ActivatedRoute,
  ) {}

  ngOnInit(): void {
    this.filters.status = this.route.snapshot.queryParamMap.get('status') || '';
    this.search();
  }

  search(page = 1): void {
    this.page = page;
    this.loading.set(true);
    this.error.set('');
    const query = { ...this.filters, is_active: this.filters.is_active === 'all' ? null : this.filters.is_active };
    this.claimService.list({ ...query, page: this.page, page_size: this.pageSize }).subscribe({
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
}
