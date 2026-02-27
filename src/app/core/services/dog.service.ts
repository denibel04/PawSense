import { Injectable } from '@angular/core';
import { ApiService } from './api.service';
import { API_CONFIG } from '../constants/api.constants';
import { tap } from 'rxjs/operators';

@Injectable({
  providedIn: 'root'
})
export class DogService {

  constructor(private api: ApiService) { }

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

    // Usamos el endpoint de video que acabamos de crear
    return this.api.post(API_CONFIG.endpoints.predict + '/video', formData);
  }
}