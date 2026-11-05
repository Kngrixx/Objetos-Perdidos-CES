import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { API_URL } from './api.config';
import { toParams } from './http-helpers';
import { ApiResponse, InventorySummary, ObjectLost, Page } from '../models/api.models';

@Injectable({
  providedIn: 'root',
})
export class InventoryService {
  private apiUrl = `${API_URL}/inventory`;

  constructor(private http: HttpClient) {}

  list(filters: Record<string, unknown> = {}): Observable<ApiResponse<Page<ObjectLost>>> {
    return this.http.get<ApiResponse<Page<ObjectLost>>>(this.apiUrl, { params: toParams(filters) });
  }

  summary(filters: Record<string, unknown> = {}): Observable<ApiResponse<InventorySummary>> {
    return this.http.get<ApiResponse<InventorySummary>>(`${this.apiUrl}/summary`, { params: toParams(filters) });
  }

  // PDF con los mismos filtros de la consulta
  export(filters: Record<string, unknown> = {}): Observable<Blob> {
    return this.http.get(`${this.apiUrl}/export`, { params: toParams(filters), responseType: 'blob' });
  }
}
