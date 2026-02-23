import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import {
  IonHeader, IonToolbar, IonTitle, IonContent,
  IonList, IonItem, IonLabel, IonIcon, IonBadge, IonButton
} from '@ionic/angular/standalone';
import { addIcons } from 'ionicons';
import { documentText, cloudDownload, time } from 'ionicons/icons';

@Component({
  selector: 'app-tab4',
  templateUrl: './tab4.page.html',
  styleUrls: ['./tab4.page.scss'],
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    IonHeader, IonToolbar, IonTitle, IonContent,
    IonList, IonItem, IonLabel, IonIcon, IonBadge, IonButton
  ]
})
export class Tab4Page {
  reports = [
    { id: 1, breed: 'Golden Retriever', date: '2024-02-23', status: 'Completado' },
    { id: 2, breed: 'Husky Siberiano', date: '2024-02-22', status: 'Completado' },
    { id: 3, breed: 'Beagle', date: '2024-02-20', status: 'Completado' }
  ];

  constructor() {
    addIcons({ documentText, cloudDownload, time });
  }

  downloadReport(id: number) {
    console.log('Descargando reporte:', id);
    // TODO: Integrar con PDFReportService
  }
}

