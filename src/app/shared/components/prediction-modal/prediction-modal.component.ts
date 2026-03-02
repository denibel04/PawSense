import { Component, Input, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import {
  IonHeader, IonToolbar, IonTitle, IonContent, IonButton,
  IonButtons, IonIcon, ModalController
} from '@ionic/angular/standalone';
import { closeCircleOutline, trophyOutline, analyticsOutline } from 'ionicons/icons';
import { DogService } from 'src/app/core/services/dog.service';
import { addIcons } from 'ionicons';
import * as allIcons from 'ionicons/icons';
import { TEMPERAMENT_MAP } from './temperament-map';

@Component({
  selector: 'app-prediction-modal',
  templateUrl: './prediction-modal.component.html',
  styleUrls: ['./prediction-modal.component.scss'],
  standalone: true,
  imports: [CommonModule, IonHeader, IonToolbar, IonTitle, IonContent, IonButton, IonButtons, IonIcon]
})
export class PredictionModalComponent implements OnInit {
  @Input() data: any; // Recibe el JSON bruto del backend
  @Input() type: 'image' | 'video' | null = null;

  winner: any = null;
  breedInfo: any = null;
  loadingInfo = false;
  formattedTemps: any[] = [];

  constructor(
    private modalCtrl: ModalController,
    private dogService: DogService
  ) {
    addIcons(allIcons);
  }

  ngOnInit() {
    if (this.data) {
      this.calculateWinner();

    }

    if (this.winner && this.winner.breed_en) {
      const cleanName = this.sanitizeBreedName(this.winner.breed_en);
      this.loadBreedInfo(cleanName);
    }
  }

  private calculateWinner() {
    const candidates = [
      { ...this.data.pytorch?.[0], source: 'PyTorch' },
      { ...this.data.keras?.[0], source: 'Keras' },
      { ...this.data.mobile?.[0], source: 'MobileNetV2' }
    ];

    this.winner = candidates.reduce((prev, curr) =>
      (curr.confidence > (prev.confidence || 0)) ? curr : prev
    );
  }

  private async loadBreedInfo(breedName: string) {
    this.loadingInfo = true;
    this.dogService.getPredictionDetails(breedName).subscribe({
      next: (res) => {
        this.breedInfo = res.found ? res : null;
        console.log('Información de la raza obtenida:', this.breedInfo);
        if (this.breedInfo?.temperament) {
          this.processTemperaments(this.breedInfo.temperament); // Usa la función que hicimos antes
        }
        this.loadingInfo = false;
      },
      error: () => this.loadingInfo = false
    });
  }

  close() {
    this.modalCtrl.dismiss();
  }

  private sanitizeBreedName(name: string): string {
    if (!name) return '';

    let clean = name.toLowerCase();

    clean = clean.replace('-dog', '').replace('_dog', '').replace(' dog', '');

    clean = clean.replace(/_/g, ' ');

    clean = clean.trim();

    console.log(`Nombre original: ${name} -> Nombre limpio para API: ${clean}`);
    return clean;
  }

  processTemperaments(tempString: string) {
    const rawList = tempString.split(',').map(t => t.trim().toLowerCase());

    this.formattedTemps = rawList.map(word => {
      return TEMPERAMENT_MAP[word] || {
        esp: word,
        group: 'default',
        icon: 'help-circle-outline'
      };
    });
  }

  formatMetric(val: string | null | undefined): string {
    if (!val) return 'N/A';

    // 1. Si viene el formato "Male: 23-24; Female: 21-22"
    if (val.includes('Male') || val.includes('Female')) {
      return val
        .split(';') // Separamos por el punto y coma
        .map(part => {
          // Para cada parte (Male/Female), buscamos el rango y ponemos espacios al guion
          return part.replace(/(\d+)-(\d+)/, '$1 - $2').trim();
        })
        .join('<br>'); // Los unimos con un salto de línea
    }

    // 2. Si es un rango simple "3-4", le ponemos espacios: "3 - 4"
    return val.replace(/(\d+)-(\d+)/, '$1 - $2');
  }


}