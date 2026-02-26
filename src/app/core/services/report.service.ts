import { Injectable } from '@angular/core';
import { ApiService } from './api.service';
import { Observable } from 'rxjs';

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
     */
    generateReportFromAudio(file: Blob, filename: string, reportType: 'veterinario' | 'adiestramiento'): Observable<ReportGenerationResponse> {
        const formData = new FormData();
        formData.append('file', file, filename);
        formData.append('report_type', reportType);

        return this.api.post<ReportGenerationResponse>('/report/generate/audio', formData);
    }
}
