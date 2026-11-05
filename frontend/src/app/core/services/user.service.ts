import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { API_URL } from './api.config';
import { toParams } from './http-helpers';
import { ApiResponse, Page, UserAccount } from '../models/api.models';

@Injectable({
  providedIn: 'root',
})
export class UserService {
  private apiUrl = `${API_URL}/users`;

  constructor(private http: HttpClient) {}

  list(filters: Record<string, unknown> = {}): Observable<ApiResponse<Page<UserAccount>>> {
    return this.http.get<ApiResponse<Page<UserAccount>>>(this.apiUrl, { params: toParams(filters) });
  }

  get(id: number): Observable<ApiResponse<UserAccount>> {
    return this.http.get<ApiResponse<UserAccount>>(`${this.apiUrl}/${id}`);
  }

  update(id: number, body: Record<string, unknown>): Observable<ApiResponse<UserAccount>> {
    return this.http.patch<ApiResponse<UserAccount>>(`${this.apiUrl}/${id}`, body);
  }

  inactivate(id: number, reason: string): Observable<ApiResponse<UserAccount>> {
    return this.http.patch<ApiResponse<UserAccount>>(`${this.apiUrl}/${id}/inactivate`, { reason });
  }

  reactivate(id: number, reason: string): Observable<ApiResponse<UserAccount>> {
    return this.http.patch<ApiResponse<UserAccount>>(`${this.apiUrl}/${id}/reactivate`, { reason });
  }
}
