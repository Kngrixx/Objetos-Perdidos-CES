import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { API_URL } from './api.config';
import { toParams } from './http-helpers';
import { ApiResponse, Claim, Page } from '../models/api.models';

@Injectable({
  providedIn: 'root',
})
export class ClaimService {
  private apiUrl = `${API_URL}/claims`;

  constructor(private http: HttpClient) {}

  list(filters: Record<string, unknown> = {}): Observable<ApiResponse<Page<Claim>>> {
    return this.http.get<ApiResponse<Page<Claim>>>(this.apiUrl, { params: toParams(filters) });
  }

  get(id: number): Observable<ApiResponse<Claim>> {
    return this.http.get<ApiResponse<Claim>>(`${this.apiUrl}/${id}`);
  }

  create(body: Record<string, unknown>): Observable<ApiResponse<Claim>> {
    return this.http.post<ApiResponse<Claim>>(this.apiUrl, body);
  }

  update(id: number, body: Record<string, unknown>): Observable<ApiResponse<Claim>> {
    return this.http.patch<ApiResponse<Claim>>(`${this.apiUrl}/${id}`, body);
  }

  decide(id: number, decision: 'ACEPTADA' | 'RECHAZADA', reason: string): Observable<ApiResponse<Claim>> {
    return this.http.patch<ApiResponse<Claim>>(`${this.apiUrl}/${id}/decision`, { decision, reason });
  }

  inactivate(id: number, reason: string): Observable<ApiResponse<Claim>> {
    return this.http.patch<ApiResponse<Claim>>(`${this.apiUrl}/${id}/inactivate`, { reason });
  }

  reactivate(id: number, reason: string): Observable<ApiResponse<Claim>> {
    return this.http.patch<ApiResponse<Claim>>(`${this.apiUrl}/${id}/reactivate`, { reason });
  }
}
