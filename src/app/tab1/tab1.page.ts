import { Component } from '@angular/core';
import { 
  IonHeader, IonToolbar, IonContent, IonButton, 
  IonItem, IonLabel, IonCard, IonCardContent, IonLoading,
  IonGrid, IonRow, IonCol, IonProgressBar, IonBadge, IonIcon,
  ToastController 
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
  selectedFile: File | null = null;
  predictionResult: any = null;
  isLoading = false;
  imagePreview: string | null = null;

  constructor(
    private dogService: DogService,
    private toastController: ToastController
  ) {
    addIcons({ paw });
  }

  onFileSelected(event: Event) {
    const element = event.currentTarget as HTMLInputElement;
    const file = element.files?.[0];

    if (file) {
      this.selectedFile = file;
      this.predictionResult = null; // Limpiamos resultados previos
      const reader = new FileReader();
      reader.onload = () => this.imagePreview = reader.result as string;
      reader.readAsDataURL(file);
    }
  }

  async presentErrorToast(message: string) {
    const toast = await this.toastController.create({
      message: message,
      duration: 4000,
      position: 'bottom',
      color: 'danger',
      buttons: [{ text: 'OK', role: 'cancel' }]
    });
    await toast.present();
  }

  uploadAndPredict() {
  if (!this.selectedFile) return;

  this.isLoading = true;
  this.predictionResult = null; // Limpiar resultados anteriores

  this.dogService.predictBreed(this.selectedFile).subscribe({
    next: (response: any) => {
      // 🔴 VALIDACIÓN: Si el backend devuelve un error o no trae datos
      if (!response || response.error || !response.mobile) {
        this.isLoading = false;
        this.presentErrorToast(response?.error || 'No se detectó ningún perro');
        return;
      }

      try {
        const models = [
          { data: response.mobile[0], name: 'MobileNetV2' },
          { data: response.pytorch[0], name: 'PyTorch' },
          { data: response.keras[0], name: 'Keras V1' }
        ];

        // Filtramos por si alguno llegara vacío y buscamos el de mayor confianza
        const topModel = models.reduce((prev, current) => {
          return (current.data?.confidence > prev.data?.confidence) ? current : prev;
        });

        this.predictionResult = {
          winner: {
            breed: topModel.data?.breed || 'Desconocido',
            confidence: (topModel.data?.confidence || 0) + '%',
            source: topModel.name
          },
          details: {
            pytorch: response.pytorch || [],
            mobile: response.mobile || [],
            keras: response.keras || []
          }
        };
      } catch (e) {
        console.error("Error al calcular el ganador:", e);
        this.presentErrorToast("Error al procesar las probabilidades");
      }
      
      this.isLoading = false;
    },
    error: (err) => {
      this.isLoading = false;
      console.error('Prediction failed:', err);
      
      // Capturamos el mensaje de error de YOLO que viene del backend
      const msg = err.error?.detail || 'Error al analizar la imagen';
      this.presentErrorToast(msg);
    }
  });
}
}