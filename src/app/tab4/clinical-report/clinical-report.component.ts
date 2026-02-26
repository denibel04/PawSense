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

    // Local mutable copy – updated via setter when parent pushes new data
    data: any = {
        resena: '',
        anamnesis: '',
        exploracion_fisica: '',
        exploracion_especial: '',
        diagnostico: '',
        tratamiento: [],
        recomendaciones: []
    };

    @Input() set clinicalData(value: any) {
        if (value) {
            // Deep-clone so edits don't mutate the parent directly
            this.data = {
                resena: value.resena ?? '',
                anamnesis: value.anamnesis ?? '',
                exploracion_fisica: value.exploracion_fisica ?? '',
                exploracion_especial: value.exploracion_especial ?? '',
                diagnostico: value.diagnostico ?? '',
                tratamiento: Array.isArray(value.tratamiento) ? [...value.tratamiento] : [],
                recomendaciones: Array.isArray(value.recomendaciones) ? [...value.recomendaciones] : []
            };
        }
    }

    trackByIndex(index: number): number {
        return index;
    }
}
