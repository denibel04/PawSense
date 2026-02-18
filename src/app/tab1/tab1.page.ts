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
  resultado: any = null;
  cargando = false;
  imagePreview: string | null = null;

  constructor(
    private dogService: DogService
  ) {} 

  onFileSelected(event: any) {
    const file = event.target.files[0];
    if (file) {
      this.selectedFile = file;
      const reader = new FileReader();
      reader.onload = () => this.imagePreview = reader.result as string;
      reader.readAsDataURL(file);
    }
  }

  subirYPredecir() {
    if (!this.selectedFile) return;

    this.cargando = true;
    this.dogService.predictBreed(this.selectedFile).subscribe({
      next: (res) => {
        this.resultado = res;
        this.cargando = false;
      },
      error: () => this.cargando = false
    });
  }
}