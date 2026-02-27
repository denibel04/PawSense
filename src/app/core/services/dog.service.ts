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
    formData.append('image_file', file); // Asegúrate de que este nombre coincida con tu FastAPI

    return this.api.post(API_CONFIG.endpoints.predict, formData).pipe(
      tap(data => {
        console.log('Datos recibidos del backend:', data);
      })
    );
  }
}