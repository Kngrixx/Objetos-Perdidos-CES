import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { API_URL } from './api.config';
import { toParams } from './http-helpers';
import { ApiResponse, Page, Block } from '../models/api.models';

@Injectable({
  providedIn: 'root',
})
export class BlockService {
  private apiUrl = `${API_URL}/blocks`;

  constructor(private http: HttpClient) {}

  list(filters: Record<string, unknown> = {}): Observable<ApiResponse<Page<Block>>> {
    return this.http.get<ApiResponse<Page<Block>>>(this.apiUrl, { params: toParams(filters) });
  }

  get(id: number): Observable<ApiResponse<Block>> {
    return this.http.get<ApiResponse<Block>>(`${this.apiUrl}/${id}`);
  }

  create(body: Record<string, unknown>): Observable<ApiResponse<Block>> {
    return this.http.post<ApiResponse<Block>>(this.apiUrl, body);
  }

  update(id: number, body: Record<string, unknown>): Observable<ApiResponse<Block>> {
    return this.http.patch<ApiResponse<Block>>(`${this.apiUrl}/${id}`, body);
  }

  inactivate(id: number, reason: string): Observable<ApiResponse<Block>> {
    return this.http.patch<ApiResponse<Block>>(`${this.apiUrl}/${id}/inactivate`, { reason });
  }

  reactivate(id: number, reason: string): Observable<ApiResponse<Block>> {
    return this.http.patch<ApiResponse<Block>>(`${this.apiUrl}/${id}/reactivate`, { reason });
  }
}
