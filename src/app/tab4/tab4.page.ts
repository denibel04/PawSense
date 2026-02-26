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
import { documentText, cloudDownload, time, micOutline, folderOutline, checkmarkCircle, checkmarkOutline, ellipseOutline, timeOutline, createOutline, downloadOutline, closeOutline, closeCircleOutline, paw, pauseCircleOutline, playCircleOutline, stopCircleOutline, refreshOutline } from 'ionicons/icons';
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
  isPaused = false;
  isSpeaking = false;
  audioBase64: string | null = null;
  audioMimeType: string | null = null;
  audioProcessing = false;
  transcriptText: string = '';
  clinicalData: any = null;
  trainingData: any = null;
  pdfBase64: string | null = null;

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
    addIcons({ documentText, cloudDownload, time, micOutline, folderOutline, checkmarkCircle, checkmarkOutline, ellipseOutline, timeOutline, createOutline, downloadOutline, closeOutline, closeCircleOutline, paw, stopCircleOutline, pauseCircleOutline, playCircleOutline, refreshOutline });
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

  async startNewRecording() {
    if (!this.isRecording) {
      // Reset state for new recording
      this.isPaused = false;
      this.transcriptText = '';
      this.finalTranscript = '';
      await this.startRecording();
    }
  }

  async pauseRecording() {
    try {
      this.isPaused = true;
      this.isSpeaking = false;
      if (this.recognition) {
        try { this.recognition.stop(); } catch (e) { }
      }
      // Note: capacitor-voice-recorder may not have a pause method, 
      // but we'll pause the speech recognition
      this.cdr.detectChanges();
    } catch (error) {
      console.error('Error pausing recording', error);
    }
  }

  async resumeRecording() {
    try {
      this.isPaused = false;
      this.isSpeaking = true;
      if (this.recognition) {
        try { this.recognition.start(); } catch (e) { }
      }
      this.cdr.detectChanges();
    } catch (error) {
      console.error('Error resuming recording', error);
    }
  }

  async finalizeRecording() {
    if (this.isRecording || this.isPaused) {
      await this.stopRecording();
    }
  }

  async restartRecording() {
    this.isRecording = false;
    this.isPaused = false;
    this.isSpeaking = false;
    if (this.recognition) {
      try { this.recognition.stop(); } catch (e) { }
    }
    try {
      await VoiceRecorder.stopRecording();
    } catch (e) {
      console.error('Error stopping voice recorder on restart', e);
    }
    this.transcriptText = '';
    this.finalTranscript = '';
    this.audioBase64 = null;
    this.cdr.detectChanges();
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
      this.isPaused = false;
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
      this.isPaused = false;
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
    this.pdfBase64 = null;
    this.progress.transcription = 'process';
    this.progress.clinicalExtraction = 'pending';
    this.progress.revision = 'pending';
    this.progress.finalReport = 'pending';

    const reportType: 'veterinario' | 'adiestramiento' = this.selectedSegment === 'adiestramiento' ? 'adiestramiento' : 'veterinario';

    this.reportService.generateReportFromAudio(file, filename, reportType).subscribe({
      next: (event) => {
        // Actualizar progreso según estado
        switch (event.status) {
          case 'Transcripción':
            this.progress.transcription = 'process';
            break;

          case 'Extracción':
            this.progress.transcription = 'done';
            this.progress.clinicalExtraction = 'process';
            // Si hay datos extraídos, mostrarlos
            if (event.extractedData) {
              if (reportType === 'veterinario') {
                this.clinicalData = this.transformVeterinaryData(event.extractedData);
              } else {
                this.trainingData = this.transformTrainingData(event.extractedData);
              }
            } else {
              console.warn(`[WARN] No hay extractedData en evento de Extracción`);
            }
            break;

          case 'Revisión':
            this.progress.clinicalExtraction = 'done';
            this.progress.revision = 'process';
            break;

          case 'Informe Final':
            this.progress.revision = 'done';
            this.progress.finalReport = 'process';
            break;

          case 'completed':
            this.progress.transcription = 'done';
            this.progress.clinicalExtraction = 'done';
            this.progress.revision = 'done';
            this.progress.finalReport = 'done';
            this.audioProcessing = false;

            // Mostrar datos finales
            if (event.extractedData) {
              if (reportType === 'veterinario') {
                this.clinicalData = this.transformVeterinaryData(event.extractedData);
              } else {
                this.trainingData = this.transformTrainingData(event.extractedData);
              }
            }

            // Guardar PDF base64 para descarga
            if (event.pdfBase64) {
              this.pdfBase64 = event.pdfBase64;
            }
            break;

          case 'error':
            console.error(`[ERROR] Error en reporte:`, event.message);
            this.progress.transcription = 'pending';
            this.progress.clinicalExtraction = 'pending';
            this.progress.revision = 'pending';
            this.progress.finalReport = 'pending';
            this.audioProcessing = false;
            break;
        }

        this.cdr.detectChanges();
      },
      error: (err) => {
        console.error('[ERROR] Error al generar reporte:', err);
        this.progress.transcription = 'pending';
        this.progress.clinicalExtraction = 'pending';
        this.progress.revision = 'pending';
        this.progress.finalReport = 'pending';
        this.audioProcessing = false;
        this.cdr.detectChanges();
      },
      complete: () => {
        this.audioProcessing = false;
        this.cdr.detectChanges();
      }
    });
  }

  /**
   * Transforma datos extraídos de Gemini al formato esperado por clinical-report component
   */
  private transformVeterinaryData(data: any): any {
    // El backend retorna 'sintomas' (array), 'diagnostico', 'tratamiento', etc.
    const transformed = {
      symptoms: data.sintomas || [],  // Cambio clave: es 'sintomas' (no 'signos')
      diagnosis: data.diagnostico || '',
      treatment: data.tratamiento || data.receta_detallada || '',
      notes: data.notas || '',
      paciente: data.paciente || {},
      antecedentes: data.antecedentes_patologicos || '',
      examen_fisico: data.examen_fisico || '',
      recomendaciones: data.recomendaciones || '',
      fechaConsulta: data.fechaConsulta || ''
    };

    return transformed;
  }

  /**
   * Transforma datos extraídos de Gemini al formato esperado por training-report component
   */
  private transformTrainingData(data: any): any {
    // El backend retorna los campos directamente del schema
    const transformed = {
      behavior_observed: data.comportamiento_observado || '',
      corrections: Array.isArray(data.correcciones) ? data.correcciones : [],
      homework: Array.isArray(data.tareas_casa) ? data.tareas_casa.join(', ') : data.tareas_casa || '',
      notes: data.notas || data.recomendaciones || '',
      paciente: data.paciente || {},
      recomendaciones: data.recomendaciones || '',
      fechaConsulta: data.fechaConsulta || ''
    };

    return transformed;
  }

  downloadReport() {
    if (!this.pdfBase64) {
      console.warn('[WARN] No hay PDF disponible para descargar');
      return;
    }

    try {
      // Convertir base64 a blob
      const byteCharacters = atob(this.pdfBase64);
      const byteNumbers = new Array(byteCharacters.length);
      for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i);
      }
      const byteArray = new Uint8Array(byteNumbers);
      const blob = new Blob([byteArray], { type: 'application/pdf' });

      // Crear enlace de descarga
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `PawSense_${this.selectedSegment}_${new Date().toISOString().slice(0, 10)}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('[ERROR] Error al descargar PDF:', error);
    }
  }
}

