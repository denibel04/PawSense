import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import {
    IonGrid, IonRow, IonCol, IonItem, IonLabel, IonInput, IonTextarea, IonList, IonButton, IonIcon
} from '@ionic/angular/standalone';

@Component({
    selector: 'app-clinical-report',
    templateUrl: './clinical-report.component.html',
    styleUrls: ['./clinical-report.component.scss'],
    standalone: true,
    imports: [
        CommonModule,
        FormsModule,
        IonGrid,
        IonRow,
        IonCol,
        IonItem,
        IonLabel,
        IonInput,
        IonTextarea,
        IonList,
        IonButton,
        IonIcon
    ]
})
export class ClinicalReportComponent {
    @Input() isEditing = false;
    currentDate: Date = new Date();

    today: string = new Date().toLocaleDateString('es-ES', { year: 'numeric', month: 'long', day: 'numeric' });

    // Local mutable copy – updated via setter when parent pushes new data
    data: any = {
        symptoms: [],
        diagnosis: '',
        treatment: '',
        notes: '',
        paciente: {},
        antecedentes: '',
        examen_fisico: '',
        recomendaciones: '',
        fechaConsulta: ''
    };

    @Input() set clinicalData(value: any) {
        if (value) {
            // Deep-clone so edits don't mutate the parent directly
            this.data = {
                symptoms: Array.isArray(value.symptoms) ? [...value.symptoms] : [],
                diagnosis: value.diagnosis ?? '',
                treatment: value.treatment ?? '',
                notes: value.notes ?? '',
                paciente: value.paciente ?? {},
                antecedentes: value.antecedentes ?? '',
                examen_fisico: value.examen_fisico ?? '',
                recomendaciones: value.recomendaciones ?? '',
                fechaConsulta: value.fechaConsulta ?? ''
            };
        }
    }

    trackByIndex(index: number): number {
        return index;
    }
}
