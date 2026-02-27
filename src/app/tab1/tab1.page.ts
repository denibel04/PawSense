import { Component } from '@angular/core';
import { 
  IonHeader, IonToolbar, IonTitle, IonContent, IonButton, 
  IonItem, IonLabel, IonCard, IonCardContent, IonLoading,
  IonGrid, IonRow, IonCol, IonProgressBar, IonBadge, IonIcon
} from '@ionic/angular/standalone';
import { CommonModule } from '@angular/common';
import { addIcons } from 'ionicons';
import { paw } from 'ionicons/icons';
import { DogService } from '../core/services/dog.service';

@Component({
  selector: 'app-tab1',
  templateUrl: 'tab1.page.html',
  styleUrls: ['tab1.page.scss'],
  standalone: true,
  imports: [
    IonHeader, IonToolbar, IonContent, IonButton, 
    IonItem, IonLabel, IonCard, IonCardContent, IonLoading,
    IonGrid, IonRow, IonCol, IonProgressBar, IonBadge, IonIcon,
    CommonModule
  ],
})
export class Tab1Page {
  constructor(private dogService: DogService) {
    addIcons({ paw });
  }
  selectedFile: File | null = null;
  predictionResult: any = null;
  isLoading = false;
  imagePreview: string | null = null;

  onFileSelected(event: Event) {
    const element = event.currentTarget as HTMLInputElement;
    const file = element.files?.[0];

    if (file) {
      this.selectedFile = file;
      const reader = new FileReader();
      reader.onload = () => this.imagePreview = reader.result as string;
      reader.readAsDataURL(file);
    }
  }

 uploadAndPredict() {
  if (!this.selectedFile) return;

  this.isLoading = true;
  this.dogService.predictBreed(this.selectedFile).subscribe({
    next: (response: any) => {
      // Mapeamos la respuesta para que encaje con tu HTML
      this.predictionResult = {
        winner: {
          // Elegimos el de mayor confianza de MobileNet (que suele ser el más robusto)
          breed: response.mobile[0].breed,
          confidence: response.mobile[0].confidence + '%',
          source: 'MobileNetV2'
        },
        details: {
          pytorch: response.pytorch,
          mobile: response.mobile,
          keras: response.keras
        }
      };
      this.isLoading = false;
    },
    error: (err) => {
      console.error('Prediction failed:', err);
      this.isLoading = false;
    }
  });
}
}