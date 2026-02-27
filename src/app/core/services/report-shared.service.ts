import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

/**
 * Shared service for passing report data between tabs (e.g., from chat to reports tab).
 * Uses BehaviorSubject so tab4 can pick up data whenever it is navigated to.
 */

export interface SharedReportData {
    reportType: 'veterinario' | 'adiestramiento';
    extractedData: any; // Raw extracted data from Gemini (backend format)
    timestamp: number;
}

@Injectable({
    providedIn: 'root'
})
export class ReportSharedService {

    private pendingReport$ = new BehaviorSubject<SharedReportData | null>(null);

    /**
     * Observable that tab4 subscribes to. Emits null when no pending report.
     */
    get pendingReport() {
        return this.pendingReport$.asObservable();
    }

    /**
     * Set report data (called by tab3/chat after generating a report).
     */
    setReportData(data: SharedReportData) {
        this.pendingReport$.next(data);
    }

    /**
     * Consume and clear the pending report (called by tab4 after loading the data).
     */
    consumeReportData(): SharedReportData | null {
        const current = this.pendingReport$.getValue();
        this.pendingReport$.next(null);
        return current;
    }

    /**
     * Check if there is pending report data without consuming it.
     */
    hasPendingReport(): boolean {
        return this.pendingReport$.getValue() !== null;
    }
}
