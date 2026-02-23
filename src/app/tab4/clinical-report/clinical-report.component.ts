import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import {
    IonGrid, IonRow, IonCol, IonButton, IonIcon
} from '@ionic/angular/standalone';
import { addIcons } from 'ionicons';
import { downloadOutline, createOutline } from 'ionicons/icons';

@Component({
    selector: 'app-clinical-report',
    templateUrl: './clinical-report.component.html',
    styleUrls: ['./clinical-report.component.scss'],
    standalone: true,
    imports: [
        CommonModule,
        IonGrid,
        IonRow,
        IonCol,
        IonButton,
        IonIcon
    ]
})
export class ClinicalReportComponent {
    /**
     * Mock clinical data for preview visualization
     * In production, this would be populated from backend/parent component
     */
    clinicalData = {
        symptoms: 'Prurito, Enrojecimiento',
        duration: '14 días',
        appetite: 'Normal',
        urgency: 'No Urgente',
        redFlags: 'Ninguno detectado'
    };

    constructor() {
        addIcons({ downloadOutline, createOutline });
    }

    /**
     * Handle download PDF action
     * TODO: Integrate with ReportService for actual PDF generation
     */
    onDownloadPdf() {
        console.log('Descargando PDF del informe...');
        // this.reportService.exportPdf(this.clinicalData).subscribe(...)
    }

    /**
     * Handle edit report action
     * TODO: Emit event to parent component to switch to edit mode
     */
    onEditReport() {
        console.log('Abriendo editor de informe...');
        // This would typically emit an event to parent (Tab4Page)
    }
}
