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
    selector: 'app-training-report',
    templateUrl: './training-report.component.html',
    styleUrls: ['./training-report.component.scss'],
    standalone: true,
    imports: [
        CommonModule, FormsModule,
        IonCard, IonCardHeader, IonCardTitle, IonCardContent,
        IonItem, IonLabel, IonInput, IonTextarea, IonIcon, IonButton,
        IonDatetime, IonDatetimeButton, IonModal
    ]
})
export class TrainingReportComponent {
    trainingData = {
        dogName: '',
        sessionDate: new Date().toISOString(),
        duration: '',
        commandsWorkingOn: '',
        behaviorNotes: '',
        trainerComments: ''
    };

    isDictating = false;

    constructor() {
        addIcons({ mic });
    }

    toggleDictation(field: string) {
        // Placeholder for actual dictation logic
        this.isDictating = !this.isDictating;
        console.log(`Toggling dictation for ${field}: ${this.isDictating}`);
    }
}
