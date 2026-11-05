import { Injectable, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap } from 'rxjs';
import { API_URL } from './api.config';
import { ApiResponse, LoginData, Role, SessionUser } from '../models/api.models';

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  identification: string;
  full_name: string;
  email: string;
  password: string;
  password_confirmation: string;
}

const TOKEN_KEY = 'op_token';
const USER_KEY = 'op_user';
const EXPIRES_KEY = 'op_expires_at';

@Injectable({
  providedIn: 'root',
})
export class AuthService {
  private apiUrl = `${API_URL}/auth`;
  // Usuario de la sesión (signal: la vista se actualiza sola cuando cambia).
  readonly user = signal<SessionUser | null>(this.readUser());

  constructor(private http: HttpClient) {}

  login(data: LoginRequest): Observable<ApiResponse<LoginData>> {
    return this.http
      .post<ApiResponse<LoginData>>(`${this.apiUrl}/login`, data)
      .pipe(tap((response) => this.saveSession(response.data)));
  }

  register(data: RegisterRequest): Observable<ApiResponse<SessionUser>> {
    return this.http.post<ApiResponse<SessionUser>>(`${this.apiUrl}/register`, data);
  }

  forgotPassword(email: string): Observable<ApiResponse<null>> {
    return this.http.post<ApiResponse<null>>(`${this.apiUrl}/forgot-password`, { email });
  }

  resetPassword(token: string, password: string, confirmation: string): Observable<ApiResponse<null>> {
    return this.http.post<ApiResponse<null>>(`${this.apiUrl}/reset-password`, {
      token,
      password,
      password_confirmation: confirmation,
    });
  }

  changePassword(current: string, next: string, confirmation: string) {
    return this.http
      .patch<ApiResponse<{ access_token: string }>>(`${this.apiUrl}/change-password`, {
        current_password: current,
        new_password: next,
        new_password_confirmation: confirmation,
      })
      .pipe(tap((response) => localStorage.setItem(TOKEN_KEY, response.data.access_token)));
  }

  me(): Observable<ApiResponse<SessionUser>> {
    return this.http.get<ApiResponse<SessionUser>>(`${this.apiUrl}/me`);
  }

  logout(): Observable<ApiResponse<null>> {
    return this.http.post<ApiResponse<null>>(`${this.apiUrl}/logout`, {});
  }

  token(): string | null {
    const expiresAt = Number(localStorage.getItem(EXPIRES_KEY) || 0);
    if (!expiresAt || Date.now() > expiresAt) {
      return null;
    }
    return localStorage.getItem(TOKEN_KEY);
  }

  isLoggedIn(): boolean {
    return this.token() !== null && this.user() !== null;
  }

  // El menú usa el rol para mostrar u ocultar opciones; el backend valida el rol en cada ruta.
  hasRole(...roles: Role[]): boolean {
    const user = this.user();
    return user !== null && roles.includes(user.role);
  }

  saveSession(data: LoginData): void {
    localStorage.setItem(TOKEN_KEY, data.access_token);
    localStorage.setItem(USER_KEY, JSON.stringify(data.user));
    localStorage.setItem(EXPIRES_KEY, String(Date.now() + data.expires_in * 1000));
    this.user.set(data.user);
  }

  clearSession(): void {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    localStorage.removeItem(EXPIRES_KEY);
    this.user.set(null);
  }

  private readUser(): SessionUser | null {
    try {
      const raw = localStorage.getItem(USER_KEY);
      return raw ? (JSON.parse(raw) as SessionUser) : null;
    } catch {
      return null;
    }
  }
}
