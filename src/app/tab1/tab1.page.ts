import { Component } from '@angular/core';
import { 
  IonHeader, IonToolbar, IonTitle, IonContent, IonButton, 
  IonItem, IonLabel, IonCard, IonCardContent, IonLoading,
  IonGrid, IonRow, IonCol, IonProgressBar, IonBadge 
} from '@ionic/angular/standalone';
import { CommonModule } from '@angular/common'; 
import { DogService } from '../core/services/dog.service';

@Component({
  selector: 'app-tab1',
  templateUrl: 'tab1.page.html',
  styleUrls: ['tab1.page.scss'],
  standalone: true,
  imports: [
    IonHeader, IonToolbar, IonTitle, IonContent, IonButton, 
    IonItem, IonLabel, IonCard, IonCardContent, IonLoading,
    IonGrid, IonRow, IonCol, IonProgressBar, IonBadge,
    CommonModule
  ],
})
export class Tab1Page {
  selectedFile: File | null = null;
  predictionResult: any = null;
  isLoading = false;
  imagePreview: string | null = null;

  constructor(private dogService: DogService) {} 

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
      next: (response) => {
        this.predictionResult = response;
        this.isLoading = false;
      },
      error: (err) => {
        console.error('Prediction failed:', err);
        this.isLoading = false;
      }
    });
  }
}