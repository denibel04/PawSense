import { Injectable } from '@angular/core';
import { ApiService } from './api.service';
import { API_CONFIG } from '../constants/api.constants';
import { tap } from 'rxjs/operators';
import { Observable } from 'rxjs';
import { HttpClient } from '@angular/common/http';

@Injectable({
  providedIn: 'root'
})
export class DogService {

  constructor(private api: ApiService, private http: HttpClient) { }

  predictBreed(file: File) {
    const formData = new FormData();
    formData.append('file', file);

    return this.api.post(API_CONFIG.endpoints.predict, formData).pipe(
      tap(data => {
        console.log('Datos recibidos del backend:', data);
      })
    );
  }

  predictVideo(file: File) {
    const formData = new FormData();
    formData.append('file', file);
    return this.api.post(API_CONFIG.endpoints.predict + '/video', formData);
  }

  getPredictionDetails(breedName: string): Observable<any> {
    return this.http.get(`${API_CONFIG.localBaseUrl}/chat/prediction-details?breed_name=${breedName}`);
  }
}