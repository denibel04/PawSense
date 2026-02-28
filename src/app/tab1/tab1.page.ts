import { Component } from '@angular/core';
import {
  IonHeader, IonToolbar, IonTitle, IonContent, IonButton,
  IonLabel, IonLoading, IonIcon, IonCard, IonCardContent,
  IonGrid, IonRow, IonCol, IonProgressBar, IonBadge, ToastController, IonSpinner
} from '@ionic/angular/standalone';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { DogService } from '../core/services/dog.service';
import { addIcons } from 'ionicons';
import {
  sparklesOutline, paw, alertCircleOutline, cloudUpload, sparkles, alertCircle
} from 'ionicons/icons';
import { HeaderComponent } from '../shared/components/header/header.component';

@Component({
  selector: 'app-tab1',
  templateUrl: 'tab1.page.html',
  styleUrls: ['tab1.page.scss'],
  standalone: true,
  imports: [
    CommonModule, FormsModule, IonHeader, IonToolbar, IonTitle,
    IonContent, IonButton, IonLabel, IonLoading, IonIcon,
    IonCard, IonCardContent, IonGrid, IonRow, IonCol,
    IonProgressBar, IonBadge, HeaderComponent, IonSpinner
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
      cloudUpload, sparklesOutline, paw, alertCircleOutline
    });
  }

  /**
   * Gestiona la selección de archivos, detectando si es imagen estática,
   * un GIF animado o un video.
   */
  onFileSelected(event: Event) {
    const file = (event.target as HTMLInputElement).files?.[0];
    if (!file) return;

    this.selectedFile = file;
    this.predictionResult = null;

    // CASO 1: Es un GIF o un Video (Los tratamos como flujo de frames)
    if (file.type === 'image/gif' || file.type.startsWith('video/')) {
      this.fileType = 'video';
      this.imagePreview = null;
      this.videoPreview = URL.createObjectURL(file);
    }
    // CASO 2: Es una imagen estática (JPG, PNG, WebP...)
    else if (file.type.startsWith('image/')) {
      this.fileType = 'image';
      this.videoPreview = null;
      const reader = new FileReader();
      reader.onload = () => this.imagePreview = reader.result as string;
      reader.readAsDataURL(file);
    }
  }

  /**
   * Sube el archivo al endpoint correspondiente y procesa la respuesta triple.
   */
  uploadAndPredict() {
    if (!this.selectedFile) return;

    this.isLoading = true;
    this.predictionResult = null;

    // Elegimos el servicio según el tipo detectado
    const call = this.fileType === 'video'
      ? this.dogService.predictVideo(this.selectedFile)
      : this.dogService.predictBreed(this.selectedFile);

    call.subscribe({
      next: (response: any) => {
        console.log('Respuesta cruda del servidor:', response);

        if (!response || response.success === false) {
          this.isLoading = false;
          this.presentErrorToast(response?.message || 'No se detectó ningún perro');
          return;
        }

        try {
          // PROCESAMIENTO PARA IMÁGENES ESTÁTICAS
          if (this.fileType === 'image') {
            const models = [
              { data: response.mobile?.[0], name: 'MobileNetV2' },
              { data: response.pytorch?.[0], name: 'PyTorch' },
              { data: response.keras?.[0], name: 'Keras V1' }
            ];

            const topModel = models.reduce((prev, current) => {
              const currentConf = current.data?.confidence || 0;
              const prevConf = prev.data?.confidence || 0;
              return (currentConf > prevConf) ? current : prev;
            });

            this.predictionResult = {
              winner: {
                breed: topModel.data?.breed || 'Desconocido',
                confidence: topModel.data?.confidence + '%',
                source: topModel.name
              },
              details: {
                pytorch: response.pytorch || [],
                mobile: response.mobile || [],
                keras: response.keras || []
              }
            };
          }
          // PROCESAMIENTO PARA VIDEOS / GIFS
          else {
            // Buscamos el ganador promediado (usamos Keras como referencia principal)
            const videoWinner = response.keras && response.keras.length > 0
              ? response.keras[0]
              : { breed: 'Desconocido', confidence: 0 };

            this.predictionResult = {
              winner: {
                breed: videoWinner.breed,
                confidence: videoWinner.confidence + '%',
                source: 'Análisis Multiframe (Promedio)'
              },
              details: {
                pytorch: response.pytorch || [],
                mobile: response.mobile || [],
                keras: response.keras || []
              }
            };
          }
        } catch (e) {
          console.error('Error parseando resultados:', e);
          this.presentErrorToast("Error al procesar los datos de la IA");
        }
        this.isLoading = false;
      },
      error: (err) => {
        this.isLoading = false;
        console.error('Error en la petición:', err);
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

  clearPreview() {
    this.selectedFile = null;
    this.predictionResult = null;
    this.imagePreview = null;
    this.videoPreview = null;
  }
}