import { Component } from '@angular/core';
import {
  IonHeader, IonToolbar, IonTitle, IonContent, IonButton,
  IonLabel, IonLoading, IonIcon, IonCard, IonCardContent,
  IonGrid, IonRow, IonCol, IonProgressBar, IonBadge, ToastController, 
  IonSpinner, ModalController
} from '@ionic/angular/standalone';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { DogService } from '../core/services/dog.service';
import { addIcons } from 'ionicons';
import {
  sparklesOutline, paw, alertCircleOutline, cloudUpload, sparkles, alertCircle, trash, closeCircleOutline
} from 'ionicons/icons';
import { HeaderComponent } from '../shared/components/header/header.component';
import { PredictionModalComponent } from '../shared/components/prediction-modal/prediction-modal.component';

@Component({
  selector: 'app-tab1',
  templateUrl: 'tab1.page.html',
  styleUrls: ['tab1.page.scss'],
  standalone: true,
  imports: [
    CommonModule, FormsModule, IonHeader, IonToolbar, IonTitle,
    IonContent, IonButton, IonLabel, IonLoading, IonIcon,
    IonCard, IonCardContent, IonGrid, IonRow, IonCol,
    IonProgressBar, IonBadge, HeaderComponent, IonSpinner,
    PredictionModalComponent
  ],
})
export class Tab1Page {
  selectedFile: File | null = null;
  isLoading = false;
  imagePreview: string | null = null;
  videoPreview: string | null = null;
  fileType: 'image' | 'video' | null = null;

  constructor(
    private dogService: DogService, 
    private toastController: ToastController,
    private modalCtrl: ModalController
  ) {
    addIcons({
      cloudUpload, sparklesOutline, paw, alertCircleOutline, sparkles, alertCircle, trash, closeCircleOutline
    });
  }

  // --- GESTIÓN DE ARCHIVOS ---

  onFileSelected(event: Event) {
    const file = (event.target as HTMLInputElement).files?.[0];
    if (!file) return;

    this.resetState();
    this.selectedFile = file;

    if (this.isMediaVideo(file)) {
      this.handleVideoSelection(file);
    } else {
      this.handleImageSelection(file);
    }
  }

  private isMediaVideo(file: File): boolean {
    return file.type === 'image/gif' || file.type.startsWith('video/');
  }

  private handleVideoSelection(file: File) {
    this.fileType = 'video';
    this.videoPreview = URL.createObjectURL(file);
  }

  private handleImageSelection(file: File) {
    this.fileType = 'image';
    const reader = new FileReader();
    reader.onload = () => this.imagePreview = reader.result as string;
    reader.readAsDataURL(file);
  }

  // --- LÓGICA DE PREDICCIÓN ---

  uploadAndPredict() {
    if (!this.selectedFile) return;

    this.isLoading = true;

    const prediction$ = this.fileType === 'video'
      ? this.dogService.predictVideo(this.selectedFile)
      : this.dogService.predictBreed(this.selectedFile);

    prediction$.subscribe({
      next: (response) => this.handleSuccess(response),
      error: (err) => this.handleError(err)
    });
  }

  private handleSuccess(response: any) {
    this.isLoading = false;
    
    console.log('Respuesta cruda del servidor:', response);

    if (!response || response.success === false) {
      this.presentErrorToast(response?.message || 'No se detectó ningún perro');
      return;
    }

    this.openPredictionModal(response);
  }

  async openPredictionModal(rawResponse: any) {
    const modal = await this.modalCtrl.create({
      component: PredictionModalComponent,
      componentProps: {
        data: rawResponse,
        type: this.fileType
      }, 
      handle: true
    });

    return await modal.present();
  }

  // --- UTILIDADES ---

  private handleError(err: any) {
    this.isLoading = false;
    console.error('Error en la petición:', err);
    const msg = err.error?.detail || 'Error de conexión con el servidor';
    this.presentErrorToast(msg);
  }

  async presentErrorToast(message: string) {
    const toast = await this.toastController.create({
      message,
      duration: 3000,
      position: 'bottom',
      color: 'danger',
      icon: 'alert-circle-outline'
    });
    toast.present();
  }

  resetState() {
    this.selectedFile = null;
    this.imagePreview = null;
    this.videoPreview = null;
    this.fileType = null;
  }

  clearPreview() {
    this.resetState();
  }
}