import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { API_URL } from './api.config';
import { ApiResponse, Photo } from '../models/api.models';

@Injectable({
  providedIn: 'root',
})
export class PhotoService {
  constructor(private http: HttpClient) {}

  list(objectId: number): Observable<ApiResponse<Photo[]>> {
    return this.http.get<ApiResponse<Photo[]>>(`${API_URL}/object-lost/${objectId}/photos`);
  }

  add(objectId: number, files: File[]): Observable<ApiResponse<Photo[]>> {
    const form = new FormData();
    files.forEach((file) => form.append('photos', file));
    return this.http.post<ApiResponse<Photo[]>>(`${API_URL}/object-lost/${objectId}/photos`, form);
  }

  // Las fotos se piden con el token (ruta autorizada), por eso se descargan como Blob.
  file(photoId: number): Observable<Blob> {
    return this.http.get(`${API_URL}/object-photos/${photoId}/file`, { responseType: 'blob' });
  }

  inactivate(photoId: number, reason: string): Observable<ApiResponse<Photo>> {
    return this.http.patch<ApiResponse<Photo>>(`${API_URL}/object-photos/${photoId}/inactivate`, { reason });
  }

  reactivate(photoId: number, reason: string): Observable<ApiResponse<Photo>> {
    return this.http.patch<ApiResponse<Photo>>(`${API_URL}/object-photos/${photoId}/reactivate`, { reason });
  }
}
