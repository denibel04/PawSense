import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { API_CONFIG } from '../constants/api.constants';
import { Observable } from 'rxjs';

export interface ChatReportSSEEvent {
    status: 'Análisis IA' | 'Extracción' | 'Revisión' | 'Informe Final' | 'completed' | 'error';
    message: string;
    percent: number;
    completed?: boolean;
    extractedData?: any;
    htmlReport?: string;
    pdfBase64?: string;
    reportType?: string;
    error?: boolean;
}

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

    /**
     * Genera un informe desde la conversación del chat usando SSE.
     */
    generateReportFromChat(
        reportType: string,
        dogInfo: Record<string, string>,
        conversation: { role: string; content: string }[]
    ): Observable<ChatReportSSEEvent> {
        return new Observable(observer => {
            const apiUrl = `${API_CONFIG.localBaseUrl}${API_CONFIG.endpoints.chatGenerateReport}`;

            fetch(apiUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    report_type: reportType,
                    dog_info: dogInfo,
                    conversation: conversation
                })
            })
                .then(response => {
                    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
                    const reader = response.body?.getReader();
                    const decoder = new TextDecoder();
                    if (!reader) throw new Error('Response body is not readable');

                    let buffer = '';

                    const processChunk = async () => {
                        try {
                            const { done, value } = await reader.read();
                            if (done) { observer.complete(); return; }

                            buffer += decoder.decode(value, { stream: true });
                            const lines = buffer.split('\n');
                            buffer = lines.pop() || '';

                            lines.forEach(line => {
                                if (line.startsWith('data: ')) {
                                    try {
                                        const eventData = JSON.parse(line.slice(6));
                                        observer.next(eventData);
                                        if (eventData.completed === true) {
                                            setTimeout(() => observer.complete(), 100);
                                        } else if (eventData.error === true) {
                                            setTimeout(() => observer.error(new Error(eventData.message)), 100);
                                        }
                                    } catch (e) { /* skip malformed events */ }
                                }
                            });
                            await processChunk();
                        } catch (error) { observer.error(error); }
                    };
                    processChunk();
                })
                .catch(error => observer.error(error));
        });
    }
}
