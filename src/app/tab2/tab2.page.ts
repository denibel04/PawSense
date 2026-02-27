import { Component, ViewChild, ElementRef, OnDestroy } from '@angular/core';
import { 
  IonHeader, IonToolbar, IonTitle, IonContent, IonButton, 
  IonIcon, IonLabel, ToastController 
} from '@ionic/angular/standalone';
import { CommonModule } from '@angular/common';
import { API_CONFIG } from '../core/constants/api.constants';
import { addIcons } from 'ionicons';
import { camera, stopCircle, playCircle, cameraOutline, paw } from 'ionicons/icons';
import { HeaderComponent } from '../components/header/header.component';

@Component({
  selector: 'app-tab2',
  templateUrl: 'tab2.page.html',
  styleUrls: ['tab2.page.scss'],
  standalone: true,
  imports: [CommonModule, IonHeader, IonToolbar, IonTitle, IonContent, IonButton, IonIcon, IonLabel, HeaderComponent]
})
export class Tab2Page implements OnDestroy {
  @ViewChild('videoElement') videoElement!: ElementRef<HTMLVideoElement>;
  @ViewChild('canvasElement') canvasElement!: ElementRef<HTMLCanvasElement>;

  isRealTime = false;
  ws: WebSocket | null = null;
  stream: MediaStream | null = null;
  realTimeResult: any = null;
  private intervalId: any;

  constructor(private toastController: ToastController) {
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
        if (data.found) {
          this.realTimeResult = data.top3.map((item: any) => ({
            breed: item.breed,
            confidence: item.confidence.toString().includes('%') ? item.confidence : item.confidence + '%'
          }));
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