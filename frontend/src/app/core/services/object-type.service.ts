import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { API_URL } from './api.config';
import { toParams } from './http-helpers';
import { ApiResponse, Page, ObjectType } from '../models/api.models';

@Injectable({
  providedIn: 'root',
})
export class ObjectTypeService {
  private apiUrl = `${API_URL}/object-types`;

  constructor(private http: HttpClient) {}

  list(filters: Record<string, unknown> = {}): Observable<ApiResponse<Page<ObjectType>>> {
    return this.http.get<ApiResponse<Page<ObjectType>>>(this.apiUrl, { params: toParams(filters) });
  }

  get(id: number): Observable<ApiResponse<ObjectType>> {
    return this.http.get<ApiResponse<ObjectType>>(`${this.apiUrl}/${id}`);
  }

  create(body: Record<string, unknown>): Observable<ApiResponse<ObjectType>> {
    return this.http.post<ApiResponse<ObjectType>>(this.apiUrl, body);
  }

  update(id: number, body: Record<string, unknown>): Observable<ApiResponse<ObjectType>> {
    return this.http.patch<ApiResponse<ObjectType>>(`${this.apiUrl}/${id}`, body);
  }

  inactivate(id: number, reason: string): Observable<ApiResponse<ObjectType>> {
    return this.http.patch<ApiResponse<ObjectType>>(`${this.apiUrl}/${id}/inactivate`, { reason });
  }

  reactivate(id: number, reason: string): Observable<ApiResponse<ObjectType>> {
    return this.http.patch<ApiResponse<ObjectType>>(`${this.apiUrl}/${id}/reactivate`, { reason });
  }
}
