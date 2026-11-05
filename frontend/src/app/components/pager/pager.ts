import { Component, EventEmitter, Input, Output } from '@angular/core';

@Component({
  selector: 'app-pager',
  imports: [],
  templateUrl: './pager.html',
  styleUrl: './pager.scss',
})
export class Pager {
  @Input() page = 1;
  @Input() pageSize = 20;
  @Input() total = 0;
  @Output() pageChange = new EventEmitter<number>();

  get pages(): number {
    return Math.max(1, Math.ceil(this.total / this.pageSize));
  }

  go(page: number): void {
    if (page >= 1 && page <= this.pages && page !== this.page) {
      this.pageChange.emit(page);
    }
  }
}
