import { Injectable } from '@angular/core';
import { ApiService } from './api.service';
import { API_CONFIG } from '../constants/api.constants';

@Injectable({
  providedIn: 'root'
})
export class DogService {

  constructor(private api: ApiService) { }

  predictBreed(file: File) {
    const formData = new FormData();
    formData.append('file', file);

    // Usamos el servicio base y el endpoint de la constante
    return this.api.post(API_CONFIG.endpoints.predict, formData);
  }
}