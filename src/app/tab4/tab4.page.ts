import { Component, ViewChild, ElementRef, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import {
  IonHeader, IonToolbar, IonTitle, IonContent,
  IonList, IonItem, IonLabel, IonIcon, IonBadge, IonButton,
  IonSegment, IonSegmentButton, IonGrid, IonRow, IonCol,
  IonCard, IonCardHeader, IonCardTitle, IonCardContent, IonCardSubtitle, IonTextarea,
  AlertController, ToastController
} from '@ionic/angular/standalone';
import { addIcons } from 'ionicons';
import { documentText, cloudDownload, time, micOutline, folderOutline, checkmarkCircle, checkmarkOutline, ellipseOutline, timeOutline, createOutline, downloadOutline, closeOutline, closeCircleOutline, paw } from 'ionicons/icons';
import { TrainingReportComponent } from './training-report/training-report.component';
import { ClinicalReportComponent } from './clinical-report/clinical-report.component';
import { VoiceRecorder } from 'capacitor-voice-recorder';
import { ReportService } from '../core/services/report.service';
@Component({
  selector: 'app-tab4',
  templateUrl: './tab4.page.html',
  styleUrls: ['./tab4.page.scss'],
  standalone: true,
  imports: [
    CommonModule,
    IonHeader, IonToolbar, IonContent,
    IonList, IonItem, IonLabel, IonIcon, IonButton,
    IonSegment, IonSegmentButton, IonGrid, IonRow, IonCol,
    IonCard, IonCardHeader, IonCardTitle, IonCardContent, IonTextarea,
    TrainingReportComponent, ClinicalReportComponent
  ]
})
export class Tab4Page {
  @ViewChild('fileInput', { static: false }) fileInput!: ElementRef;

  selectedSegment = 'veterinario';
  isEditing = false; // Toggles between read-only preview and edit mode
  isDragging = false; // Drag & drop state

  // Audio state
  isRecording = false;
  isSpeaking = false;
  audioBase64: string | null = null;
  audioMimeType: string | null = null;
  audioProcessing = false;
  transcriptText: string = '';
  clinicalData: any = null;
  trainingData: any = null;

  recognition: any;
  finalTranscript = '';

  // Mock progression states
  progress = {
    transcription: 'pending', // done, pending, process
    clinicalExtraction: 'pending',
    revision: 'pending',
    finalReport: 'pending'
  };

  reports = [
    { id: 1, breed: 'Golden Retriever', date: '2024-02-23', status: 'Completado' },
    { id: 2, breed: 'Husky Siberiano', date: '2024-02-22', status: 'Completado' },
    { id: 3, breed: 'Beagle', date: '2024-02-20', status: 'Completado' }
  ];

  constructor(
    private cdr: ChangeDetectorRef,
    private reportService: ReportService,
    private alertController: AlertController,
    private toastController: ToastController
  ) {
    addIcons({ documentText, cloudDownload, time, micOutline, folderOutline, checkmarkCircle, checkmarkOutline, ellipseOutline, timeOutline, createOutline, downloadOutline, closeOutline, closeCircleOutline, paw, stopCircleOutline: 'stop-circle-outline' });
    this.initSpeechRecognition();
  }

  initSpeechRecognition() {
    const { webkitSpeechRecognition, SpeechRecognition }: any = window as any;
    const SpeechRec = SpeechRecognition || webkitSpeechRecognition;
    if (SpeechRec) {
      this.recognition = new SpeechRec();
      this.recognition.continuous = true;
      this.recognition.interimResults = true;
      this.recognition.lang = 'es-ES';

      this.recognition.onresult = (event: any) => {
        let interimTranscript = '';
        for (let i = event.resultIndex; i < event.results.length; ++i) {
          if (event.results[i].isFinal) {
            this.finalTranscript += event.results[i][0].transcript + ' ';
          } else {
            interimTranscript += event.results[i][0].transcript;
          }
        }
        this.transcriptText = this.finalTranscript + interimTranscript;
        this.cdr.detectChanges();
      };

      this.recognition.onerror = (event: any) => {
        console.error('[DEBUG] Speech recognition error', event.error);
      };
    } else {
      console.warn('SpeechRecognition API no soportada en este navegador.');
    }
  }

  toggleEditMode() {
    this.isEditing = !this.isEditing;
  }

  async toggleRecording() {
    if (this.isRecording) {
      await this.stopRecording();
    } else {
      await this.startRecording();
    }
  }

  async startRecording() {
    try {
      const permission = await VoiceRecorder.requestAudioRecordingPermission();
      if (permission.value) {
        this.isRecording = true;
        this.isSpeaking = true;
        await VoiceRecorder.startRecording();
        if (this.recognition) {
          this.finalTranscript = '';
          this.transcriptText = '';
          try { this.recognition.start(); } catch (e) { }
        }
        this.cdr.detectChanges();
      }
    } catch (error) {
      console.error('Error starting recording', error);
    }
  }

  async stopRecording() {
    try {
      this.isRecording = false;
      this.isSpeaking = false;
      if (this.recognition) {
        try { this.recognition.stop(); } catch (e) { }
      }
      this.cdr.detectChanges();

      const result = await VoiceRecorder.stopRecording();
      if (result && result.value && result.value.recordDataBase64) {
        this.audioBase64 = result.value.recordDataBase64;
        this.audioMimeType = result.value.mimeType;
        const byteCharacters = atob(this.audioBase64);
        const byteNumbers = new Array(byteCharacters.length);
        for (let i = 0; i < byteCharacters.length; i++) {
          byteNumbers[i] = byteCharacters.charCodeAt(i);
        }
        const byteArray = new Uint8Array(byteNumbers);
        const audioBlob = new Blob([byteArray], { type: this.audioMimeType || 'audio/aac' });
        const filename = `recording_${new Date().getTime()}.aac`;
        this.processAudio(audioBlob, filename);
      }
    } catch (error) {
      console.error('Error stopping recording', error);
      this.isRecording = false;
      this.isSpeaking = false;
      this.cdr.detectChanges();
    }
  }

  triggerFileInput() {
    if (this.fileInput && this.fileInput.nativeElement) {
      this.fileInput.nativeElement.click();
    }
  }

  onDragOver(event: DragEvent) {
    event.preventDefault();
    event.stopPropagation();
    this.isDragging = true;
  }

  onDragLeave(event: DragEvent) {
    event.preventDefault();
    event.stopPropagation();
    this.isDragging = false;
  }

  onDrop(event: DragEvent) {
    event.preventDefault();
    event.stopPropagation();
    this.isDragging = false;

    if (event.dataTransfer && event.dataTransfer.files.length > 0) {
      const file = event.dataTransfer.files[0];
      this.handleFileUpload(file);
    }
  }

  onFileSelected(event: any) {
    const file = event.target.files[0];
    if (file) {
      this.handleFileUpload(file);
    }
    // Clear input value to allow selecting the same file again
    event.target.value = '';
  }

  async handleFileUpload(file: File) {
    if (!file.type.startsWith('audio/')) {
      const alert = await this.alertController.create({
        header: 'Formato no soportado',
        message: 'Por favor, selecciona un archivo de audio válido (mp3, wav, m4a, etc).',
        buttons: ['OK']
      });
      await alert.present();
      return;
    }
    this.processAudio(file, file.name);
  }

  processAudio(file: Blob, filename: string) {
    this.audioProcessing = true;
    this.progress.transcription = 'process';
    this.progress.clinicalExtraction = 'pending';

    const reportType: 'veterinario' | 'adiestramiento' = this.selectedSegment === 'adiestramiento' ? 'adiestramiento' : 'veterinario';

    this.reportService.generateReportFromAudio(file, filename, reportType).subscribe({
      next: (response) => {
        this.progress.transcription = 'done';
        this.progress.clinicalExtraction = 'done';
        this.progress.revision = 'pending';
        this.audioProcessing = false;
        this.transcriptText = response.transcript;
        if (reportType === 'veterinario') {
          this.clinicalData = response.data;
        } else {
          this.trainingData = response.data;
        }
        this.cdr.detectChanges();
      },
      error: async (err) => {
        console.error('Error al generar reporte:', err);

        const toast = await this.toastController.create({
          message: 'Error al subir u procesar el audio. Asegúrate de que es un formato válido.',
          duration: 3000,
          color: 'danger',
          position: 'top',
          icon: 'close-circle-outline'
        });
        await toast.present();

        this.progress.transcription = 'pending';
        this.audioProcessing = false;
        this.cdr.detectChanges();
      }
    });
  }

  downloadReport() {
    // TODO: Integrar con PDFReportService
  }

  downloadOldReport(id: number) {
    // TODO: Integrar con PDFReportService
  }
}

