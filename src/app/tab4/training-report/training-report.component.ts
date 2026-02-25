import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import {
    IonGrid, IonRow, IonCol
} from '@ionic/angular/standalone';

@Component({
    selector: 'app-training-report',
    templateUrl: './training-report.component.html',
    styleUrls: ['./training-report.component.scss'],
    standalone: true,
    imports: [
        CommonModule,
        IonGrid,
        IonRow,
        IonCol
    ]
})
export class TrainingReportComponent {
    /**
     * Training data for preview visualization.
     * Populated via @Input() — will be updated dynamically by Whisper + agent.
     */
    @Input() trainingData = {
        dogName: '',
        sessionDate: new Date().toISOString(),
        duration: '',
        commandsWorkingOn: '',
        behaviorNotes: '',
        trainerComments: ''
    };
}

