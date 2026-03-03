import { Component, ViewChild, ElementRef, OnDestroy, NgZone } from '@angular/core';
import {
  IonHeader, IonToolbar, IonTitle, IonContent, IonButton,
  IonIcon, IonLabel, ToastController, ModalController
} from '@ionic/angular/standalone';
import { CommonModule } from '@angular/common';
import { API_CONFIG } from '../core/constants/api.constants';
import { addIcons } from 'ionicons';
import { camera, stopCircle, playCircle, cameraOutline, paw } from 'ionicons/icons';
import { HeaderComponent } from '../shared/components/header/header.component';
import { PredictionModalComponent } from '../shared/components/prediction-modal/prediction-modal.component';

@Component({
  selector: 'app-tab2',
  templateUrl: 'tab2.page.html',
  styleUrls: ['tab2.page.scss'],
  standalone: true,
  imports: [
    CommonModule,
    IonContent, IonButton,
    IonIcon, HeaderComponent,
  ]
})
export class Tab2Page implements OnDestroy {
  @ViewChild('videoElement') videoElement!: ElementRef<HTMLVideoElement>;
  @ViewChild('canvasElement') canvasElement!: ElementRef<HTMLCanvasElement>;

  isRealTime = false;
  ws: WebSocket | null = null;
  stream: MediaStream | null = null;
  realTimeResult: any = null;
  private intervalId: any;

  async handleHighConfidenceMatch(match: any, image: string, allResults: any[]) {
    // 1. Paramos la cámara
    this.stopRealTime();

    // 2. Preparamos el objeto de respuesta para que sea igual al de la Tab 1
    // El WebSocket devuelve { breed_en, breed_es, confidence }
    const formattedResults = allResults.map(res => ({
      breed_en: res.breed_en,
      breed_es: res.breed_es,
      confidence: res.confidence
    }));

    const fakeResponse = {
      success: true,
      pytorch: formattedResults,
      keras: formattedResults,
      mobile: formattedResults
    };

    console.log('Tab2 - Enviando fakeResponse al modal:', fakeResponse);

    // 3. Abrimos el modal nativo
    const modal = await this.modalCtrl.create({
      component: PredictionModalComponent,
      componentProps: {
        data: fakeResponse,
        imagePreview: image, // Le pasamos la captura del canvas
        type: 'image'
      }
    });

    await modal.present();

    // Opcional: Cuando se cierre el modal, reiniciar la cámara
    await modal.onDidDismiss();
    // this.startRealTime(); // Descomenta si quieres que vuelva a empezar solo
  }

  constructor(
    private toastController: ToastController,
    private modalCtrl: ModalController,
    private ngZone: NgZone
  ) {
    addIcons({ camera, stopCircle, playCircle, cameraOutline, paw });
  }

  ngOnDestroy() {
    this.stopRealTime();
  }

  async toggleRealTime() {
    if (this.isRealTime) {
      this.stopRealTime();
    } else {
      await this.startRealTime();
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
        if (data.found && data.top3 && data.top3.length > 0) {
          const bestMatch = data.top3[0];
          const confidence = parseFloat(bestMatch.confidence)

          // Si la confianza es mayor al 80% muestra el popup
          if (confidence >= 80) {

            //"Coge los píxeles que hay ahora mismo dibujados en el cuadro del canvas y conviértelos en una foto real con formato JPEG".
            const capturedImage = this.canvasElement.nativeElement.toDataURL('image/jpeg')

            // Forzamos a Angular a detectar el cambio (WebSocket corre fuera de la Zona)
            this.ngZone.run(() => {
              this.handleHighConfidenceMatch(bestMatch, capturedImage, data.top3);
            });
          }
          else {
            // Si es menor seguimos actualizando la lista en tiempo real
            this.realTimeResult = data.top3.map((item: any) => ({
              breed: item.breed_es,
              confidence: item.confidence.toString().includes('%') ? item.confidence : item.confidence + '%'
            }));
          }
        }
      };

      this.intervalId = setInterval(() => this.sendFrame(), 200);
    } catch (err) {
      console.error("Error al acceder a la cámara:", err);
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
}