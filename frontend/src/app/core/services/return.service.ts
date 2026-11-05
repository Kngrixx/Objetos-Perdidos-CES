import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { API_URL } from './api.config';
import { toParams } from './http-helpers';
import { ApiResponse, Page, ReturnRecord } from '../models/api.models';

@Injectable({
  providedIn: 'root',
})
export class ReturnService {
  private apiUrl = `${API_URL}/returns`;

  constructor(private http: HttpClient) {}

  list(filters: Record<string, unknown> = {}): Observable<ApiResponse<Page<ReturnRecord>>> {
    return this.http.get<ApiResponse<Page<ReturnRecord>>>(this.apiUrl, { params: toParams(filters) });
  }

  get(id: number): Observable<ApiResponse<ReturnRecord>> {
    return this.http.get<ApiResponse<ReturnRecord>>(`${this.apiUrl}/${id}`);
  }

  create(body: Record<string, unknown>): Observable<ApiResponse<ReturnRecord>> {
    return this.http.post<ApiResponse<ReturnRecord>>(this.apiUrl, body);
  }

  receipt(id: number): Observable<Blob> {
    return this.http.get(`${this.apiUrl}/${id}/receipt`, { responseType: 'blob' });
  }
}
