import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { API_URL } from './api.config';
import { toParams } from './http-helpers';
import { ApiResponse, Page, Campus } from '../models/api.models';

@Injectable({
  providedIn: 'root',
})
export class CampusService {
  private apiUrl = `${API_URL}/campuses`;

  constructor(private http: HttpClient) {}

  list(filters: Record<string, unknown> = {}): Observable<ApiResponse<Page<Campus>>> {
    return this.http.get<ApiResponse<Page<Campus>>>(this.apiUrl, { params: toParams(filters) });
  }

  get(id: number): Observable<ApiResponse<Campus>> {
    return this.http.get<ApiResponse<Campus>>(`${this.apiUrl}/${id}`);
  }

  create(body: Record<string, unknown>): Observable<ApiResponse<Campus>> {
    return this.http.post<ApiResponse<Campus>>(this.apiUrl, body);
  }

  update(id: number, body: Record<string, unknown>): Observable<ApiResponse<Campus>> {
    return this.http.patch<ApiResponse<Campus>>(`${this.apiUrl}/${id}`, body);
  }

  inactivate(id: number, reason: string): Observable<ApiResponse<Campus>> {
    return this.http.patch<ApiResponse<Campus>>(`${this.apiUrl}/${id}/inactivate`, { reason });
  }

  reactivate(id: number, reason: string): Observable<ApiResponse<Campus>> {
    return this.http.patch<ApiResponse<Campus>>(`${this.apiUrl}/${id}/reactivate`, { reason });
  }
}
