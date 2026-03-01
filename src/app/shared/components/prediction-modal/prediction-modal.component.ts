import { Component, Input, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { 
  IonHeader, IonToolbar, IonTitle, IonContent, IonButton, 
  IonButtons, IonIcon, ModalController 
} from '@ionic/angular/standalone';
import { addIcons } from 'ionicons';
import { closeCircleOutline, trophyOutline, analyticsOutline } from 'ionicons/icons';
import { ChatService } from 'src/app/core/services/chat.service';

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

  constructor(
    private modalCtrl: ModalController,
    private chatService: ChatService
  ) {
    addIcons({ closeCircleOutline, trophyOutline, analyticsOutline });
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
    // Si es imagen, buscamos el modelo con mayor confianza absoluta
    if (this.type === 'image') {
      const candidates = [
        { ...this.data.pytorch?.[0], source: 'PyTorch' },
        { ...this.data.keras?.[0], source: 'Keras' },
        { ...this.data.mobile?.[0], source: 'MobileNetV2' }
      ];

      this.winner = candidates.reduce((prev, curr) => 
        (curr.confidence > (prev.confidence || 0)) ? curr : prev
      );
    } else {
      // Si es video, priorizamos el promedio de Keras (como estaba en tu lógica)
      this.winner = {
        ...this.data.keras?.[0],
        source: 'Análisis de Video',
        confidence: this.data.keras?.[0]?.confidence || 0
      };
    }
  }

  private async loadBreedInfo(nombreIngles: string) {
    this.loadingInfo = true;
    this.chatService.getBreedInfo(nombreIngles).subscribe({
      next: (res) => {
        this.breedInfo = res;
        this.loadingInfo = false;
        console.log('Información extra recibida:', res);
      },
      error: (err) => {
        console.error('Error al traer info extra', err);
        this.loadingInfo = false;
      }
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
}