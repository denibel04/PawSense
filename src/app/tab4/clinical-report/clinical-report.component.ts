import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import {
    IonCard, IonCardHeader, IonCardTitle, IonCardContent,
    IonItem, IonLabel, IonInput, IonTextarea, IonIcon, IonButton,
    IonDatetime, IonDatetimeButton, IonModal, IonSelect, IonSelectOption
} from '@ionic/angular/standalone';
import { addIcons } from 'ionicons';
import { mic } from 'ionicons/icons';

@Component({
    selector: 'app-clinical-report',
    templateUrl: './clinical-report.component.html',
    styleUrls: ['./clinical-report.component.scss'],
    standalone: true,
    imports: [
        CommonModule, FormsModule,
        IonCard, IonCardHeader, IonCardTitle, IonCardContent,
        IonItem, IonLabel, IonInput, IonTextarea, IonIcon, IonButton,
        IonDatetime, IonDatetimeButton, IonModal
    ]
})
export class ClinicalReportComponent {
    clinicalData = {
        dogName: '',
        visitDate: new Date().toISOString(),
        weight: '',
        symptoms: '',
        diagnosis: '',
        treatment: '',
        notes: ''
    };

    isDictating = false;

    constructor() {
        addIcons({ mic });
    }

    toggleDictation(field: string) {
        this.isDictating = !this.isDictating;
        console.log(`Toggling dictation for ${field}: ${this.isDictating}`);
    }
}
