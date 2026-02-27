import { Component, ViewChild, ElementRef, OnDestroy } from '@angular/core';
import {
  IonHeader, IonToolbar, IonTitle, IonContent, IonButton,
  IonLabel, IonLoading, IonIcon, IonSegment, IonSegmentButton,
  IonCard, IonCardContent, IonGrid, IonRow, IonCol,
  IonProgressBar, IonBadge, ToastController
} from '@ionic/angular/standalone';
import { CommonModule } from '@angular/common'; // IMPORTANTE PARA *ngIf y *ngFor
import { FormsModule } from '@angular/forms'; // IMPORTANTE PARA [(ngModel)]
import { DogService } from '../core/services/dog.service';
import { API_CONFIG } from '../core/constants/api.constants';
import { addIcons } from 'ionicons';
import {
  camera, stopCircle, playCircle, cameraOutline,
  cloudUploadOutline, sparklesOutline, paw, alertCircleOutline
} from 'ionicons/icons';

@Component({
  selector: 'app-tab1',
  templateUrl: 'tab1.page.html',
  styleUrls: ['tab1.page.scss'],
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    IonHeader, IonToolbar, IonTitle, IonContent, IonButton,
    IonLabel, IonLoading, IonIcon, IonSegment, IonSegmentButton,
    IonCard, IonCardContent, IonGrid, IonRow, IonCol,
    IonProgressBar, IonBadge
  ],
})
export class Tab1Page implements OnDestroy {
  @ViewChild('videoElement') videoElement!: ElementRef<HTMLVideoElement>;
  @ViewChild('canvasElement') canvasElement!: ElementRef<HTMLCanvasElement>;

  selectedFile: File | null = null;
  predictionResult: any = null;
  isLoading = false;
  imagePreview: string | null = null;
  videoPreview: string | null = null;
  fileType: 'image' | 'video' | null = null;

  isRealTime = false;
  ws: WebSocket | null = null;
  stream: MediaStream | null = null;
  realTimeResult: any = null;
  activeSegment: 'visor' | 'analizador' = 'visor';
  private intervalId: any;

  constructor(private dogService: DogService, private toastController: ToastController) {
    addIcons({
      camera, stopCircle, playCircle, cameraOutline,
      cloudUploadOutline, sparklesOutline, paw, alertCircleOutline
    });
  }

  ngOnDestroy() {
    this.stopRealTime();
  }

  // --- MÉTODOS DE CÁMARA ---
  toggleRealTime() {
    if (this.isRealTime) {
      this.stopRealTime();
    } else {
      this.startRealTime();
    }
  }

  async startRealTime() {
    try {
      this.stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment' }
      });
      this.videoElement.nativeElement.srcObject = this.stream;
      this.isRealTime = true;
      this.ws = new WebSocket(API_CONFIG.wsUrl);

      this.ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.found) {
          this.realTimeResult = data.top3.map((item: any) => ({
            breed: item.breed,
            confidence: item.confidence.toString().includes('%') ? item.confidence : item.confidence + '%'
          }));
        }
      };

      this.intervalId = setInterval(() => this.sendFrame(), 200);
    } catch (err) {
      console.error(err);
    }
  }

  stopRealTime() {
    this.isRealTime = false;
    if (this.intervalId) clearInterval(this.intervalId);
    if (this.ws) this.ws.close();
    if (this.stream) this.stream.getTracks().forEach(t => t.stop());
    this.realTimeResult = null;
  }

  sendFrame() {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) return;
    const canvas = this.canvasElement.nativeElement;
    const video = this.videoElement.nativeElement;
    const context = canvas.getContext('2d');
    if (context && video.videoWidth) {
      canvas.width = 480;
      canvas.height = (video.videoHeight / video.videoWidth) * 480;
      context.drawImage(video, 0, 0, canvas.width, canvas.height);
      this.ws.send(canvas.toDataURL('image/jpeg', 0.7));
    }
  }

  // --- MÉTODOS DE ARCHIVOS ---
  onFileSelected(event: Event) {
    const file = (event.target as HTMLInputElement).files?.[0];
    if (file) {
      this.selectedFile = file;
      this.predictionResult = null;
      this.stopRealTime();
      if (file.type.startsWith('image/')) {
        this.fileType = 'image';
        const reader = new FileReader();
        reader.onload = () => this.imagePreview = reader.result as string;
        reader.readAsDataURL(file);
      } else {
        this.fileType = 'video';
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
        // 1. VALIDACIÓN INICIAL
        if (!response || response.error) {
          this.isLoading = false;
          this.presentErrorToast(response?.error || 'No se detectó ningún perro');
          return;
        }

        try {
          // 2. LÓGICA PARA IMÁGENES (3 MODELOS)
          if (this.fileType === 'image' && response.mobile) {
            const models = [
              { data: response.mobile[0], name: 'MobileNetV2' },
              { data: response.pytorch[0], name: 'PyTorch' },
              { data: response.keras[0], name: 'Keras V1' }
            ];

            // Buscamos el modelo con mayor confianza
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
          }
          // 3. LÓGICA PARA VIDEO (SUMMARY)
          else if (this.fileType === 'video') {
            this.predictionResult = {
              winner: {
                breed: response.winner?.breed || 'Desconocido',
                confidence: response.winner?.confidence || '0%',
                source: 'Análisis de Video'
              },
              summary: response.summary,
              // Si el video también manda detalles por frame:
              details: {
                pytorch: response.details?.pytorch || []
              }
            };
          }
        } catch (e) {
          console.error("Error al procesar la respuesta:", e);
          this.presentErrorToast("Error al procesar los datos de la IA");
        }

        this.isLoading = false;
      },
      error: (err) => {
        this.isLoading = false;
        console.error('Petición fallida:', err);
        const msg = err.error?.detail || 'Error de conexión con el servidor';
        this.presentErrorToast(msg);
      }
    });
  }

  // Asegúrate de tener este método para que no te dé error
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