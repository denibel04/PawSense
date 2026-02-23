import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import {
  IonHeader, IonToolbar, IonTitle, IonContent,
  IonList, IonItem, IonLabel, IonIcon, IonBadge, IonButton,
  IonSegment, IonSegmentButton, IonGrid, IonRow, IonCol,
  IonCard, IonCardHeader, IonCardTitle, IonCardContent, IonCardSubtitle
} from '@ionic/angular/standalone';
import { addIcons } from 'ionicons';
import { documentText, cloudDownload, time, micOutline, folderOutline, checkmarkCircle, ellipseOutline, timeOutline, createOutline, downloadOutline } from 'ionicons/icons';
import { TrainingReportComponent } from './training-report/training-report.component';
import { ClinicalReportComponent } from './clinical-report/clinical-report.component';

@Component({
  selector: 'app-tab4',
  templateUrl: './tab4.page.html',
  styleUrls: ['./tab4.page.scss'],
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    IonHeader, IonToolbar, IonTitle, IonContent,
    IonList, IonItem, IonLabel, IonIcon, IonBadge, IonButton,
    IonSegment, IonSegmentButton, IonGrid, IonRow, IonCol,
    IonCard, IonCardHeader, IonCardTitle, IonCardContent,
    TrainingReportComponent, ClinicalReportComponent
  ]
})
export class Tab4Page {
  selectedSegment = 'veterinario';
  isEditing = false; // Toggles between read-only preview and edit mode

  // Mock progression states
  progress = {
    transcription: 'done', // done, pending, process
    clinicalExtraction: 'done',
    revision: 'pending',
    finalReport: 'process'
  };

  reports = [
    { id: 1, breed: 'Golden Retriever', date: '2024-02-23', status: 'Completado' },
    { id: 2, breed: 'Husky Siberiano', date: '2024-02-22', status: 'Completado' },
    { id: 3, breed: 'Beagle', date: '2024-02-20', status: 'Completado' }
  ];

  constructor() {
    addIcons({ documentText, cloudDownload, time, micOutline, folderOutline, checkmarkCircle, ellipseOutline, timeOutline, createOutline, downloadOutline });
  }

  toggleEditMode() {
    this.isEditing = !this.isEditing;
  }

  downloadReport() {
    console.log('Descargando reporte actual...');
  }

  downloadOldReport(id: number) {
    console.log('Descargando reporte:', id);
    // TODO: Integrar con PDFReportService
  }
}

