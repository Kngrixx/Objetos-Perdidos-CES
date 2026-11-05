import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { API_URL } from './api.config';
import { ApiResponse, RoleItem } from '../models/api.models';

@Injectable({
  providedIn: 'root',
})
export class RoleService {
  private apiUrl = `${API_URL}/roles`;

  constructor(private http: HttpClient) {}

  list(): Observable<ApiResponse<RoleItem[]>> {
    return this.http.get<ApiResponse<RoleItem[]>>(this.apiUrl);
  }
}
