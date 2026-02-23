import { Component, ViewChild, ElementRef, OnDestroy } from '@angular/core';
import {
  IonHeader, IonToolbar, IonTitle, IonContent, IonButton,
  IonItem, IonLabel, IonCard, IonCardContent, IonLoading,
  IonGrid, IonRow, IonCol, IonProgressBar, IonBadge, IonIcon,
  IonSegment, IonSegmentButton
} from '@ionic/angular/standalone';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { DogService } from '../core/services/dog.service';
import { API_CONFIG } from '../core/constants/api.constants';
import { addIcons } from 'ionicons';
import { camera, stopCircle, playCircle, cameraOutline, cloudUploadOutline, sparklesOutline } from 'ionicons/icons';

@Component({
  selector: 'app-tab1',
  templateUrl: 'tab1.page.html',
  styleUrls: ['tab1.page.scss'],
  standalone: true,
  imports: [
    IonHeader, IonToolbar, IonTitle, IonContent, IonButton,
    IonItem, IonLabel, IonCard, IonCardContent, IonLoading,
    IonGrid, IonRow, IonCol, IonProgressBar, IonBadge, IonIcon,
    IonSegment, IonSegmentButton,
    CommonModule,
    FormsModule
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

  // Real-time variables
  isRealTime = false;
  ws: WebSocket | null = null;
  stream: MediaStream | null = null;
  realTimeResult: any = null;
  activeSegment: 'visor' | 'analizador' = 'visor';
  private intervalId: any;

  constructor(private dogService: DogService) {
    addIcons({ camera, stopCircle, playCircle, cameraOutline, cloudUploadOutline, sparklesOutline });
  }

  ngOnDestroy() {
    this.stopRealTime();
  }

  toggleRealTime() {
    if (this.isRealTime) {
      this.stopRealTime();
    } else {
      this.startRealTime();
    }
  }

  async startRealTime() {
    try {
      this.stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } });
      this.videoElement.nativeElement.srcObject = this.stream;
      this.isRealTime = true;

      // Conectar WebSocket
      console.log('Conectando a:', API_CONFIG.wsUrl);
      this.ws = new WebSocket(API_CONFIG.wsUrl);

      this.ws.onopen = () => console.log('WebSocket conectado ✅');
      this.ws.onerror = (err) => console.error('Error WebSocket ❌:', err);
      this.ws.onclose = () => console.log('WebSocket cerrado 🚪');

      // Sistema de estabilidad (Promedio Ponderado)
      let probabilityBuffer: { [breed: string]: number[] } = {};
      const MAX_SAMPLES = 8;
      let lastResultTime = 0;

      this.ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        const now = Date.now();

        if (data.found) {
          lastResultTime = now;

          // Actualizar buffer de probabilidades para cada raza en el Top 3
          data.top3.forEach((item: any) => {
            const prob = parseFloat(item.confidence) / 100;
            if (!probabilityBuffer[item.breed]) probabilityBuffer[item.breed] = [];
            probabilityBuffer[item.breed].push(prob);
          });

          // Limpiar razas que ya no aparecen
          Object.keys(probabilityBuffer).forEach(breed => {
            const foundInTop3 = data.top3.find((t: any) => t.breed === breed);
            if (!foundInTop3) {
              probabilityBuffer[breed].push(0); // Penalizar si no aparece
            }
            if (probabilityBuffer[breed].length > MAX_SAMPLES) probabilityBuffer[breed].shift();
          });

          // Calcular promedios
          const averages: any[] = Object.keys(probabilityBuffer).map(breed => {
            const sum = probabilityBuffer[breed].reduce((a, b) => a + b, 0);
            return { breed, average: sum / probabilityBuffer[breed].length };
          });

          averages.sort((a, b) => b.average - a.average);

          // Si el ganador es sólido (aunque no sea el mismo de antes), actualizamos
          if (averages[0].average > 0.3) {
            // Reconstruir el display
            this.realTimeResult = averages.slice(0, 3).map(a => ({
              breed: a.breed,
              confidence: (a.average * 100).toFixed(1) + '%'
            }));
          }
        } else {
          // Persistencia: Solo borramos si ha pasado mucho tiempo
          if (now - lastResultTime > 2000) {
            probabilityBuffer = {};
            this.realTimeResult = null;
          }
        }
      };

      // Enviar frames cada 200ms (Más fluido)
      this.intervalId = setInterval(() => {
        this.sendFrame();
      }, 200);

    } catch (err) {
      console.error('Error al acceder a la cámara:', err);
    }
  }

  stopRealTime() {
    this.isRealTime = false;
    if (this.intervalId) clearInterval(this.intervalId);
    if (this.ws) this.ws.close();
    if (this.stream) {
      this.stream.getTracks().forEach(track => track.stop());
    }
    this.realTimeResult = null;
  }

  sendFrame() {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) return;

    const canvas = this.canvasElement.nativeElement;
    const video = this.videoElement.nativeElement;
    const context = canvas.getContext('2d');

    if (context && video.videoWidth) {
      // Aumentar a 480px para mejor detección sin sacrificar demasiada velocidad
      canvas.width = 480;
      canvas.height = (video.videoHeight / video.videoWidth) * 480;
      context.drawImage(video, 0, 0, canvas.width, canvas.height);
      const dataUrl = canvas.toDataURL('image/jpeg', 0.7); // Mejor calidad para el clasificador
      this.ws.send(dataUrl);
    }
  }

  onFileSelected(event: Event) {
    const element = event.currentTarget as HTMLInputElement;
    const file = element.files?.[0];

    if (file) {
      this.selectedFile = file;
      this.predictionResult = null; // Reset results
      this.stopRealTime();

      if (file.type.startsWith('image/') && file.type !== 'image/gif') {
        this.fileType = 'image';
        this.videoPreview = null;
        const reader = new FileReader();
        reader.onload = () => {
          this.imagePreview = reader.result as string;
        };
        reader.readAsDataURL(file);
      } else if (file.type.startsWith('video/') || file.type === 'image/gif') {
        this.fileType = 'video';
        this.imagePreview = null;
        this.videoPreview = URL.createObjectURL(file);
      }
    }
  }

  uploadAndPredict() {
    if (!this.selectedFile) return;

    this.isLoading = true;

    const upload$ = this.fileType === 'video'
      ? this.dogService.predictVideo(this.selectedFile)
      : this.dogService.predictBreed(this.selectedFile);

    upload$.subscribe({
      next: (response: any) => {
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
