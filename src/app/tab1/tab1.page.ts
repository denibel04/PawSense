import { Component } from '@angular/core';
import {
  IonHeader, IonToolbar, IonTitle, IonContent, IonButton,
  IonLabel, IonLoading, IonIcon, IonCard, IonCardContent, 
  IonGrid, IonRow, IonCol, IonProgressBar, IonBadge, ToastController
} from '@ionic/angular/standalone';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { DogService } from '../core/services/dog.service';
import { addIcons } from 'ionicons';
import {
  cloudUploadOutline, sparklesOutline, paw, alertCircleOutline
} from 'ionicons/icons';
import { HeaderComponent } from '../components/header/header.component';

@Component({
  selector: 'app-tab1',
  templateUrl: 'tab1.page.html',
  styleUrls: ['tab1.page.scss'],
  standalone: true,
  imports: [
    CommonModule, FormsModule, IonHeader, IonToolbar, IonTitle, 
    IonContent, IonButton, IonLabel, IonLoading, IonIcon, 
    IonCard, IonCardContent, IonGrid, IonRow, IonCol, 
    IonProgressBar, IonBadge, HeaderComponent
  ],
})
export class Tab1Page {
  selectedFile: File | null = null;
  predictionResult: any = null;
  isLoading = false;
  imagePreview: string | null = null;
  videoPreview: string | null = null;
  fileType: 'image' | 'video' | null = null;

  constructor(private dogService: DogService, private toastController: ToastController) {
    addIcons({
      cloudUploadOutline, sparklesOutline, paw, alertCircleOutline
    });
  }

  onFileSelected(event: Event) {
    const file = (event.target as HTMLInputElement).files?.[0];
    if (file) {
      this.selectedFile = file;
      this.predictionResult = null;
      
      if (file.type.startsWith('image/')) {
        this.fileType = 'image';
        this.videoPreview = null;
        const reader = new FileReader();
        reader.onload = () => this.imagePreview = reader.result as string;
        reader.readAsDataURL(file);
      } else {
        this.fileType = 'video';
        this.imagePreview = null;
        this.videoPreview = URL.createObjectURL(file);
      }
    }
  }

  uploadAndPredict() {
    if (!this.selectedFile) return;

    this.isLoading = true;
    this.predictionResult = null;

    const call = this.fileType === 'video'
      ? this.dogService.predictVideo(this.selectedFile)
      : this.dogService.predictBreed(this.selectedFile);

    call.subscribe({
      next: (response: any) => {
        if (!response || response.error) {
          this.isLoading = false;
          this.presentErrorToast(response?.error || 'No se detectó ningún perro');
          return;
        }

        try {
          if (this.fileType === 'image' && response.mobile) {
            const models = [
              { data: response.mobile[0], name: 'MobileNetV2' },
              { data: response.pytorch[0], name: 'PyTorch' },
              { data: response.keras[0], name: 'Keras V1' }
            ];

            const topModel = models.reduce((prev, current) => {
              const currentConf = parseFloat(current.data?.confidence) || 0;
              const prevConf = parseFloat(prev.data?.confidence) || 0;
              return (currentConf > prevConf) ? current : prev;
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
          } else if (this.fileType === 'video') {
            this.predictionResult = {
              winner: {
                breed: response.winner?.breed || 'Desconocido',
                confidence: response.winner?.confidence || '0%',
                source: 'Análisis de Video'
              },
              summary: response.summary,
              details: {
                pytorch: response.details?.pytorch || []
              }
            };
          }
        } catch (e) {
          this.presentErrorToast("Error al procesar los datos de la IA");
        }
        this.isLoading = false;
      },
      error: (err) => {
        this.isLoading = false;
        const msg = err.error?.detail || 'Error de conexión con el servidor';
        this.presentErrorToast(msg);
      }
    });
  }

  async presentErrorToast(message: string) {
    const toast = await this.toastController.create({
      message: message,
      duration: 3000,
      position: 'bottom',
      color: 'danger',
      icon: 'alert-circle-outline'
    });
    toast.present();
  }
}