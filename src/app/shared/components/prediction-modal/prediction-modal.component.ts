import { Component, Input, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import {
  IonHeader, IonToolbar, IonTitle, IonContent, IonButton,
  IonButtons, IonIcon, ModalController
} from '@ionic/angular/standalone';
import { closeCircleOutline, trophyOutline, analyticsOutline } from 'ionicons/icons';
import { DogService } from 'src/app/core/services/dog.service';
import { ChatService } from 'src/app/core/services/chat.service';
import { addIcons } from 'ionicons';
import * as allIcons from 'ionicons/icons';
import { TEMPERAMENT_MAP } from './temperament-map';
import { Router } from '@angular/router';

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
  runnerUps: any[] = [];   // 2nd and 3rd predictions
  breedInfo: any = null;
  allBreedsInfo: any[] = []; // TheDogAPI info for top 3 breeds
  loadingInfo = false;
  formattedTemps: any[] = [];

  constructor(
    private modalCtrl: ModalController,
    private dogService: DogService,
    private chatService: ChatService,
    private router: Router
  ) {
    addIcons(allIcons);
  }

  ngOnInit() {
    if (this.data) {
      this.calculateWinner();
    }

    if (this.winner && this.winner.breed_en) {
      this.loadAllBreedsInfo();
    }
  }

  private calculateWinner() {
    // Determine which architecture's top-1 has the highest confidence
    const archResults: { name: string; predictions: any[] }[] = [
      { name: 'PyTorch', predictions: this.data.pytorch || [] },
      { name: 'Keras', predictions: this.data.keras || [] },
      { name: 'MobileNetV2', predictions: this.data.mobile || [] }
    ];

    let bestArch = archResults[0];
    for (const arch of archResults) {
      if (arch.predictions.length > 0 &&
        arch.predictions[0].confidence > (bestArch.predictions[0]?.confidence || 0)) {
        bestArch = arch;
      }
    }

    // Winner = top-1 of the best architecture
    if (bestArch.predictions.length > 0) {
      this.winner = { ...bestArch.predictions[0], source: bestArch.name };
    }

    // Runner-ups = positions 2 and 3 from the same architecture
    this.runnerUps = bestArch.predictions
      .slice(1, 3)
      .map(p => ({ ...p, source: bestArch.name }));
  }

  /**
   * Fetches TheDogAPI info for top 3 breeds (winner + runner-ups).
   * Only the winner's info is displayed in the modal, but all 3 are passed to the chat.
   */
  private loadAllBreedsInfo() {
    this.loadingInfo = true;
    const allPredictions = [this.winner, ...this.runnerUps];
    this.allBreedsInfo = new Array(allPredictions.length).fill(null);
    let completed = 0;

    const checkCompleteAndShare = () => {
      completed++;
      if (completed === allPredictions.length) {
        this.loadingInfo = false;
        this.sharePredictionContext();
      }
    };

    allPredictions.forEach((pred, index) => {
      if (!pred?.breed_en) {
        checkCompleteAndShare();
        return;
      }
      const cleanName = this.sanitizeBreedName(pred.breed_en);
      this.dogService.getPredictionDetails(cleanName).subscribe({
        next: (res) => {
          this.allBreedsInfo[index] = res.found ? res : null;
          // The winner (index 0) is also used for modal display
          if (index === 0) {
            this.breedInfo = res.found ? res : null;
            if (this.breedInfo?.temperament) {
              this.processTemperaments(this.breedInfo.temperament);
            }
          }
          checkCompleteAndShare();
        },
        error: () => checkCompleteAndShare()
      });
    });
  }

  /**
   * Submits the prediction context implicitly without user interaction.
   * Allows the Chat to know the subject even if the modal is dismissed.
   */
  private sharePredictionContext() {
    const allPredictions = [this.winner, ...this.runnerUps];
    const top3 = allPredictions.map((pred, i) => ({
      breed_en: pred?.breed_en || '',
      breed_es: pred?.breed_es || '',
      confidence: pred?.confidence || 0,
      apiInfo: this.allBreedsInfo[i] || null
    }));
    this.chatService.updatePredictionContext(top3);
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

  /**
   * Navigate to the Chat tab (tab3) passing the top 3 predicted breeds with their API info.
   */
  async askAI() {
    const allPredictions = [this.winner, ...this.runnerUps];
    const top3 = allPredictions.map((pred, i) => ({
      breed_en: pred?.breed_en || '',
      breed_es: pred?.breed_es || '',
      confidence: pred?.confidence || 0,
      apiInfo: this.allBreedsInfo[i] || null
    }));
    await this.modalCtrl.dismiss();
    this.router.navigate(['/tabs/tab3'], {
      queryParams: { top3: JSON.stringify(top3) }
    });
  }
}