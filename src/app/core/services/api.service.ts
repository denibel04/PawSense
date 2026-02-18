import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { API_CONFIG } from '../constants/api.constants';

@Injectable({
  providedIn: 'root'
})
export class ApiService {

  constructor(private http: HttpClient) { }

  /**
   *  Método para hacer una solicitud POST a un endpoint específico con datos
   * @param endpoint  - El endpoint al que se desea hacer la solicitud
   * @param data  - Los datos que se desean enviar en la solicitud POST
   * @returns  Observable con la respuesta del servidor
   */
  post(endpoint: string, data: any) {
    return this.http.post(`${API_CONFIG.baseUrl}${endpoint}`, data);
  }

  /** 
   * Método para hacer una solicitud GET a un endpoint específico 
   * @param endpoint - El endpoint al que se desea hacer la solicitud
   * @returns Observable con la respuesta del servidor 
   **/
  get(endpoint: string) {
    return this.http.get(`${API_CONFIG.baseUrl}${endpoint}`);
  }
}