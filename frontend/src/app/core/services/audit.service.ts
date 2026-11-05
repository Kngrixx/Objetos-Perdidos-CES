import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { API_URL } from './api.config';
import { toParams } from './http-helpers';
import { ApiResponse, AuditLog, Page } from '../models/api.models';

@Injectable({
  providedIn: 'root',
})
export class AuditService {
  private apiUrl = `${API_URL}/audit-logs`;

  constructor(private http: HttpClient) {}

  list(filters: Record<string, unknown> = {}): Observable<ApiResponse<Page<AuditLog>>> {
    return this.http.get<ApiResponse<Page<AuditLog>>>(this.apiUrl, { params: toParams(filters) });
  }
}
