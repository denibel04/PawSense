import { Injectable } from '@angular/core';
import { ApiService } from './api.service';
import { Observable } from 'rxjs';
import { API_CONFIG } from '../constants/api.constants';

export interface SSEEvent {
    status: 'Transcripción' | 'Extracción' | 'Revisión' | 'Informe Final' | 'completed' | 'error';
    message: string;
    percent: number;
    completed?: boolean;
    extractedData?: any;
    htmlReport?: string;
    pdfPath?: string;
    pdfBase64?: string;
    error?: boolean;
}

export interface ReportGenerationResponse {
    transcript: string;
    data: any;
}

@Injectable({
    providedIn: 'root'
})
export class ReportService {

    constructor(private api: ApiService) { }

    /**
     * Envia un archivo de audio al backend para transcribirlo y generar un informe JSON.
     * Usa Server-Sent Events (SSE) para streaming de progreso en tiempo real.
     */
    generateReportFromAudio(file: Blob, filename: string, reportType: 'veterinario' | 'adiestramiento'): Observable<SSEEvent> {
        return new Observable(observer => {
            const formData = new FormData();
            formData.append('file', file, filename);
            formData.append('report_type', reportType);

            // Usar fetch para SSE ya que HttpClient no lo soporta bien
            const apiUrl = this.getApiUrl('/report/generate/audio');

            fetch(apiUrl, {
                method: 'POST',
                body: formData
            })
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }

                    const reader = response.body?.getReader();
                    const decoder = new TextDecoder();

                    if (!reader) {
                        throw new Error('Response body is not readable');
                    }

                    let buffer = '';
                    let eventCount = 0;

                    const processChunk = async () => {
                        try {
                            const { done, value } = await reader.read();

                            if (done) {
                                observer.complete();
                                return;
                            }

                            const chunk = decoder.decode(value, { stream: true });
                            buffer += chunk;

                            // Procesar líneas completas
                            const lines = buffer.split('\n');
                            buffer = lines.pop() || ''; // Mantener última línea incompleta en buffer

                            lines.forEach(line => {
                                if (line.startsWith('data: ')) {
                                    try {
                                        eventCount++;
                                        const eventData = JSON.parse(line.slice(6));

                                        observer.next(eventData);

                                        // Si está completado o hay error, completar observable
                                        if (eventData.completed === true) {
                                            setTimeout(() => {
                                                observer.complete();
                                            }, 100);
                                        } else if (eventData.error === true) {
                                            setTimeout(() => {
                                                observer.error(new Error(eventData.message));
                                            }, 100);
                                        }
                                    } catch (e) {
                                        // No fallar si hay un evento malformado, intentar el siguiente
                                    }
                                }
                            });

                            // Continuar leyendo
                            await processChunk();
                        } catch (error) {
                            console.error('[ERROR] Error processing chunk:', error);
                            observer.error(error);
                        }
                    };

                    processChunk();
                })
                .catch(error => {
                    console.error('[ERROR] Fetch error:', error);
                    observer.error(error);
                });

            // Retornar función para limpiar recurso
            return () => {
                // Nada que limpiar en este caso
            };
        });
    }

    /**
     * Obtiene la URL completa de la API
     */
    private getApiUrl(endpoint: string): string {
        // Usar API_CONFIG.localBaseUrl si está disponible
        const baseUrl = API_CONFIG.localBaseUrl || 'http://localhost:8000/api/v1';
        return baseUrl + endpoint;
    }

    /**
     * Obtiene detalles de un reporte previamente generado
     */
    getReportDetails(reportId: string): Observable<any> {
        return this.api.get(`/report/details/${reportId}`);
    }

    /**
     * Descarga un reporte en PDF
     */
    downloadReport(reportId: string): void {
        const url = this.getApiUrl(`/report/download/${reportId}`);
        window.open(url, '_blank');
    }

    /**
     * Lista todos los reportes generados
     */
    listReports(reportType?: string, limit: number = 50, offset: number = 0): Observable<any> {
        let url = `/report/list?limit=${limit}&offset=${offset}`;
        if (reportType) {
            url += `&report_type=${reportType}`;
        }
        return this.api.get(url);
    }

    /**
     * Obtiene estadísticas de reportes
     */
    getStatistics(): Observable<any> {
        return this.api.get('/report/stats');
    }

    /**
     * Valida datos de un reporte
     */
    validateReportData(data: any, reportType: string): Observable<any> {
        return this.api.post('/report/validate', { data, report_type: reportType });
    }
}
