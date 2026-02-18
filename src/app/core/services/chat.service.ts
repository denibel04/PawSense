import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { API_CONFIG } from '../constants/api.constants';
import { Observable } from 'rxjs';

@Injectable({
    providedIn: 'root'
})
export class ChatService {

    constructor(private http: HttpClient) { }

    getBreedInfo(breedName: string): Observable<any> {
        return this.http.get(`${API_CONFIG.localBaseUrl}${API_CONFIG.endpoints.chatInfo}?breed_name=${breedName}`);
    }

    sendMessage(question: string, context: string, history: any[]): Promise<Response> {
        return fetch(`${API_CONFIG.localBaseUrl}${API_CONFIG.endpoints.chatAsk}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify({
                question: question,
                context: context,
                history: history
            })
        });
    }
}
