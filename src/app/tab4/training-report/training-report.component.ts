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
        IonGrid,
        IonRow,
        IonCol,
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

    // Local mutable copy – updated via setter when parent pushes new data
    data: any = {
        fecha: '',
        duracion: '',
        objetivos: [],
        conductas_resultados: '',
        tipo_refuerzo: '',
        observaciones_actitud: ''
    };

    @Input() set trainingData(value: any) {
        if (value) {
            this.data = {
                fecha: value.fecha ?? '',
                duracion: value.duracion ?? '',
                objetivos: Array.isArray(value.objetivos) ? [...value.objetivos] : [],
                conductas_resultados: value.conductas_resultados ?? '',
                tipo_refuerzo: value.tipo_refuerzo ?? '',
                observaciones_actitud: value.observaciones_actitud ?? ''
            };
        }
    }

    onFechaInput(event: any) {
        let input = event.target.value;
        if (!input) {
            this.data.fecha = '';
            return;
        }

        // Remove all non-numeric characters
        let value = input.replace(/\D/g, '');

        // Limit to 8 digits
        if (value.length > 8) {
            value = value.substring(0, 8);
        }

        let day = value.substring(0, 2);
        let month = value.substring(2, 4);
        let year = value.substring(4, 8);

        // Cap values to generic max valid dates
        if (day.length === 2 && parseInt(day) > 31) {
            day = '31';
        }
        if (month.length === 2 && parseInt(month) > 12) {
            month = '12';
        }

        let formattedValue = day;
        if (value.length >= 3) {
            formattedValue += '/' + month;
        }
        if (value.length >= 5) {
            formattedValue += '/' + year;
        }

        // Update the model and the input visual value
        this.data.fecha = formattedValue;
        event.target.value = formattedValue;
    }

    trackByIndex(index: number): number {
        return index;
    }
}

