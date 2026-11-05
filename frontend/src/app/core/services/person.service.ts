import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { API_URL } from './api.config';
import { toParams } from './http-helpers';
import { ApiResponse, Page, Person } from '../models/api.models';

@Injectable({
  providedIn: 'root',
})
export class PersonService {
  private apiUrl = `${API_URL}/persons`;

  constructor(private http: HttpClient) {}

  list(filters: Record<string, unknown> = {}): Observable<ApiResponse<Page<Person>>> {
    return this.http.get<ApiResponse<Page<Person>>>(this.apiUrl, { params: toParams(filters) });
  }

  get(id: number): Observable<ApiResponse<Person>> {
    return this.http.get<ApiResponse<Person>>(`${this.apiUrl}/${id}`);
  }

  create(body: Record<string, unknown>): Observable<ApiResponse<Person>> {
    return this.http.post<ApiResponse<Person>>(this.apiUrl, body);
  }

  update(id: number, body: Record<string, unknown>): Observable<ApiResponse<Person>> {
    return this.http.patch<ApiResponse<Person>>(`${this.apiUrl}/${id}`, body);
  }

  inactivate(id: number, reason: string): Observable<ApiResponse<Person>> {
    return this.http.patch<ApiResponse<Person>>(`${this.apiUrl}/${id}/inactivate`, { reason });
  }

  reactivate(id: number, reason: string): Observable<ApiResponse<Person>> {
    return this.http.patch<ApiResponse<Person>>(`${this.apiUrl}/${id}/reactivate`, { reason });
  }
}
