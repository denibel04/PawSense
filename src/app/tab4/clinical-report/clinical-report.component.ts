import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import {
    IonGrid, IonRow, IonCol
} from '@ionic/angular/standalone';

@Component({
    selector: 'app-clinical-report',
    templateUrl: './clinical-report.component.html',
    styleUrls: ['./clinical-report.component.scss'],
    standalone: true,
    imports: [
        CommonModule,
        IonGrid,
        IonRow,
        IonCol
    ]
})
export class ClinicalReportComponent {
    /**
     * Clinical data for preview visualization.
     * Populated via @Input() — will be updated dynamically by Whisper + agent.
     */
    @Input() clinicalData = {
        symptoms: 'Prurito, Enrojecimiento',
        duration: '14 días',
        appetite: 'Normal',
        urgency: 'No Urgente',
        redFlags: 'Ninguno detectado'
    };
}
