import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import {
    IonGrid, IonRow, IonCol, IonItem, IonLabel, IonInput, IonTextarea, IonList, IonButton, IonIcon
} from '@ionic/angular/standalone';

@Component({
    selector: 'app-training-report',
    templateUrl: './training-report.component.html',
    styleUrls: ['./training-report.component.scss'],
    standalone: true,
    imports: [
        CommonModule,
        FormsModule,
        IonItem,
        IonLabel,
        IonInput,
        IonButton,
        IonTextarea,
        IonList,
        IonIcon
    ]
})
export class TrainingReportComponent {
    @Input() isEditing = false;
    currentDate: Date = new Date();

    today: string = new Date().toISOString().slice(0, 10);

    // Local mutable copy – updated via setter when parent pushes new data
    data: any = {
        behavior_observed: '',
        corrections: [],
        homework: '',
        notes: '',
        paciente: {},
        recomendaciones: '',
        fechaConsulta: ''
    };

    @Input() set trainingData(value: any) {
        if (value) {
            this.data = {
                behavior_observed: value.behavior_observed ?? '',
                corrections: Array.isArray(value.corrections) ? [...value.corrections] : [],
                homework: value.homework ?? '',
                notes: value.notes ?? '',
                paciente: value.paciente ?? {},
                recomendaciones: value.recomendaciones ?? '',
                fechaConsulta: value.fechaConsulta ?? ''
            };
        }
    }

    trackByIndex(index: number): number {
        return index;
    }
}

