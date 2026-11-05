import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { API_URL } from './api.config';
import { toParams } from './http-helpers';
import { ApiResponse, AuditLog, ObjectLost, Page } from '../models/api.models';

@Injectable({
  providedIn: 'root',
})
export class ObjectLostService {
  private apiUrl = `${API_URL}/object-lost`;

  constructor(private http: HttpClient) {}

  list(filters: Record<string, unknown> = {}): Observable<ApiResponse<Page<ObjectLost>>> {
    return this.http.get<ApiResponse<Page<ObjectLost>>>(this.apiUrl, { params: toParams(filters) });
  }

  get(id: number): Observable<ApiResponse<ObjectLost>> {
    return this.http.get<ApiResponse<ObjectLost>>(`${this.apiUrl}/${id}`);
  }

  // Recepción: multipart/form-data con los campos y las fotos (campo "photos").
  create(form: FormData): Observable<ApiResponse<ObjectLost>> {
    return this.http.post<ApiResponse<ObjectLost>>(this.apiUrl, form);
  }

  update(id: number, body: Record<string, unknown>): Observable<ApiResponse<ObjectLost>> {
    return this.http.patch<ApiResponse<ObjectLost>>(`${this.apiUrl}/${id}`, body);
  }

  administrativeCorrection(id: number, body: Record<string, unknown>): Observable<ApiResponse<ObjectLost>> {
    return this.http.patch<ApiResponse<ObjectLost>>(`${this.apiUrl}/${id}/administrative-correction`, body);
  }

  inactivate(id: number, reason: string): Observable<ApiResponse<ObjectLost>> {
    return this.http.patch<ApiResponse<ObjectLost>>(`${this.apiUrl}/${id}/inactivate`, { reason });
  }

  reactivate(id: number, reason: string): Observable<ApiResponse<ObjectLost>> {
    return this.http.patch<ApiResponse<ObjectLost>>(`${this.apiUrl}/${id}/reactivate`, { reason });
  }

  history(id: number): Observable<ApiResponse<{ code: string; items: AuditLog[] }>> {
    return this.http.get<ApiResponse<{ code: string; items: AuditLog[] }>>(`${this.apiUrl}/${id}/history`);
  }
}
