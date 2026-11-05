import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { API_URL } from './api.config';
import { toParams } from './http-helpers';
import { ApiResponse, Page, Department } from '../models/api.models';

@Injectable({
  providedIn: 'root',
})
export class DepartmentService {
  private apiUrl = `${API_URL}/departments`;

  constructor(private http: HttpClient) {}

  list(filters: Record<string, unknown> = {}): Observable<ApiResponse<Page<Department>>> {
    return this.http.get<ApiResponse<Page<Department>>>(this.apiUrl, { params: toParams(filters) });
  }

  get(id: number): Observable<ApiResponse<Department>> {
    return this.http.get<ApiResponse<Department>>(`${this.apiUrl}/${id}`);
  }

  create(body: Record<string, unknown>): Observable<ApiResponse<Department>> {
    return this.http.post<ApiResponse<Department>>(this.apiUrl, body);
  }

  update(id: number, body: Record<string, unknown>): Observable<ApiResponse<Department>> {
    return this.http.patch<ApiResponse<Department>>(`${this.apiUrl}/${id}`, body);
  }

  inactivate(id: number, reason: string): Observable<ApiResponse<Department>> {
    return this.http.patch<ApiResponse<Department>>(`${this.apiUrl}/${id}/inactivate`, { reason });
  }

  reactivate(id: number, reason: string): Observable<ApiResponse<Department>> {
    return this.http.patch<ApiResponse<Department>>(`${this.apiUrl}/${id}/reactivate`, { reason });
  }
}
