import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { API_URL } from './api.config';
import { toParams } from './http-helpers';
import { ApiResponse, DashboardSummary, ObjectLost } from '../models/api.models';

@Injectable({
  providedIn: 'root',
})
export class DashboardService {
  private apiUrl = `${API_URL}/dashboard`;

  constructor(private http: HttpClient) {}

  summary(filters: Record<string, unknown>): Observable<ApiResponse<DashboardSummary>> {
    return this.http.get<ApiResponse<DashboardSummary>>(`${this.apiUrl}/summary`, { params: toParams(filters) });
  }

  byCategory(filters: Record<string, unknown>) {
    return this.http.get<ApiResponse<{ category_id: number; category: string; total: number }[]>>(
      `${this.apiUrl}/by-category`,
      { params: toParams(filters) },
    );
  }

  byCampus(filters: Record<string, unknown>) {
    return this.http.get<ApiResponse<{ campus_id: number; campus: string; total: number }[]>>(
      `${this.apiUrl}/by-campus`,
      { params: toParams(filters) },
    );
  }

  recent(filters: Record<string, unknown>): Observable<ApiResponse<ObjectLost[]>> {
    return this.http.get<ApiResponse<ObjectLost[]>>(`${this.apiUrl}/recent`, { params: toParams(filters) });
  }
}
