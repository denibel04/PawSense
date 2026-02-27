import { ChangeDetectorRef, Component, NgZone, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import {
  IonHeader, IonToolbar, IonTitle, IonContent,
  IonItem, IonLabel, IonFooter, IonButton,
  IonTextarea, IonIcon, IonButtons, IonSpinner, IonRippleEffect,
  IonProgressBar
} from '@ionic/angular/standalone';
import { addIcons } from 'ionicons';
import { send, paw, documentTextOutline } from 'ionicons/icons';
import { ChatService, ChatReportSSEEvent } from '../core/services/chat.service';
import { ReportSharedService } from '../core/services/report-shared.service';
import { Router } from '@angular/router';

interface ChatMessage {
  role: string;
  content: string;
  type?: 'text' | 'report-questions' | 'report-progress' | 'report-ready';
  reportType?: string;
  reportProgress?: number;
}

@Component({
  selector: 'app-tab3',
  templateUrl: 'tab3.page.html',
  styleUrls: ['tab3.page.scss'],
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    IonHeader, IonToolbar, IonTitle, IonContent,
    IonItem, IonLabel, IonFooter, IonButton,
    IonTextarea, IonIcon, IonButtons, IonSpinner, IonRippleEffect,
    IonProgressBar
  ],
})
export class Tab3Page implements OnInit {
  messages: ChatMessage[] = [];
  newMessage: string = '';
  isLoading: boolean = false;
  contextData: string = '';
  cdr: ChangeDetectorRef;

  // Report generation state
  reportPendingType: string | null = null;  // When bot asked for dog info
  reportKnownInfo: Record<string, string> = {};  // Pre-filled info from context/conversation
  reportMissingFields: string[] = [];  // Fields still needed
  reportGenerating: boolean = false;
  reportProgress: number = 0;

  constructor(
    private chatService: ChatService,
    private reportSharedService: ReportSharedService,
    private changeDetectorRef: ChangeDetectorRef,
    private ngZone: NgZone,
    private router: Router
  ) {
    this.cdr = changeDetectorRef;
    addIcons({ send, paw, documentTextOutline });
  }

  ngOnInit() {
    this.messages = [
      { role: 'assistant', content: '¡Hola! Soy tu asistente canino. ¿En qué puedo ayudarte hoy? También puedo generar informes veterinarios o de adiestramiento basados en nuestra conversación. ¡Solo pídemelo!' }
    ];

    // Obtener contexto inicial (Hardcoded por ahora, debería venir de la navegación)
    this.getInitialContext('terrier');
  }

  getInitialContext(breed: string) {
    this.chatService.getBreedInfo(breed).subscribe({
      next: (data) => {
        if (data.found) {
          this.contextData = `
            Raza: ${data.breed}
            Temperamento: ${data.temperament}
            Vida: ${data.life_span}
            Origen: ${data.origin}
            Uso: ${data.bred_for}
          `.trim();
        }
      },
      error: (err) => {
        console.error('Error fetching breed context:', err);
        this.contextData = '';
      }
    });
  }

  async sendMessage() {
    if (!this.newMessage.trim()) return;

    const userMsg: ChatMessage = { role: 'user', content: this.newMessage };
    this.messages.push(userMsg);

    const question = this.newMessage;
    this.newMessage = '';
    this.isLoading = true;

    // Check if we are in the report-questions flow (user is answering dog info)
    if (this.reportPendingType) {
      this.handleReportAnswers(question);
      return;
    }

    try {
      const response = await this.chatService.sendMessage(question, this.contextData, this.messages);

      if (!response.ok) throw new Error('Error en la petición');
      if (!response.body) throw new Error('No body in response');

      const botMsg: ChatMessage = { role: 'assistant', content: '' };
      this.messages.push(botMsg);

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        botMsg.content += chunk;

        if (this.isLoading && botMsg.content.length > 0) {
          this.isLoading = false;
        }
      }

      // Flush any remaining bytes held in the decoder's internal buffer
      const remaining = decoder.decode();
      if (remaining) {
        botMsg.content += remaining;
      }

      // Check if the response contains the new report intent marker
      // Use (\[.*?\]) for MISSING to properly capture JSON arrays like ["nombre","edad"]
      // without the non-greedy .*? stopping at the first ] inside the array
      const reportMatch = botMsg.content.match(/\[REPORT_INTENT:(veterinario|adiestramiento)\|KNOWN:(\{.*?\})\|MISSING:(\[.*?\])\]/);
      if (reportMatch) {
        // Remove the full marker from the visible text (greedy to capture the outer ]]
        botMsg.content = botMsg.content.replace(/\[REPORT_INTENT:[^\]]*\]\]?/, '').trim();
        const reportType = reportMatch[1];
        let knownInfo: Record<string, string> = {};
        let missingFields: string[] = [];

        try { knownInfo = JSON.parse(reportMatch[2]); } catch (e) { }
        try { missingFields = JSON.parse(reportMatch[3]); } catch (e) { }

        this.reportPendingType = reportType;
        this.reportKnownInfo = knownInfo;
        this.reportMissingFields = missingFields;

        if (missingFields.length === 0) {
          // All info is known — generate report immediately
          botMsg.type = 'report-progress';
          botMsg.reportType = reportType;
          botMsg.reportProgress = 0;
          botMsg.content = 'Generando informe... Esto puede tardar unos segundos.';
          this.isLoading = false;
          this.cdr.detectChanges();
          this.generateReportFromChat(knownInfo, botMsg);
          return;
        } else {
          botMsg.type = 'report-questions';
          botMsg.reportType = reportType;
        }
      }

      this.cdr.detectChanges();

    } catch (error) {
      console.error('Error in chat:', error);

      if (this.messages.length > 0 && this.messages[this.messages.length - 1].role === 'assistant' && !this.messages[this.messages.length - 1].content) {
        this.messages.pop();
      }

      const errorMsg: ChatMessage = { role: 'assistant', content: 'Lo siento, hubo un error al conectar con el servidor.' };
      this.messages.push(errorMsg);
      this.isLoading = false;
    }
  }

  /**
   * Handles the user's response with dog info for report generation.
   * Parses the answers and triggers report generation.
   */
  private handleReportAnswers(answerText: string) {
    this.isLoading = false;

    // Parse the answers for the missing fields
    const newInfo = this.parseDogInfo(answerText, this.reportMissingFields);

    // Merge known info + new answers
    const dogInfo = { ...this.reportKnownInfo, ...newInfo };

    // Show confirmation message
    const confirmMsg: ChatMessage = {
      role: 'assistant',
      content: `Generando informe... Esto puede tardar unos segundos.`,
      type: 'report-progress',
      reportType: this.reportPendingType!,
      reportProgress: 0
    };
    this.messages.push(confirmMsg);
    this.cdr.detectChanges();

    // Trigger report generation
    this.generateReportFromChat(dogInfo, confirmMsg);
  }

  /**
   * Parses dog info from a free-text answer.
   * Uses smart extraction per field type instead of naive positional mapping.
   */
  private parseDogInfo(text: string, fields: string[]): Record<string, string> {
    const info: Record<string, string> = {};
    const lower = text.toLowerCase();

    for (const field of fields) {
      switch (field) {
        case 'nombre': {
          // Look for "se llama X", "nombre es X", or just a proper name
          const m = lower.match(/(?:se llama|nombre(?:\s+es)?)\s+(\w+)/)
            || lower.match(/^([A-Za-záéíóúñÁÉÍÓÚÑ]+)(?:,|\s|$)/);
          if (m) info['nombre'] = m[1].charAt(0).toUpperCase() + m[1].slice(1);
          break;
        }
        case 'edad': {
          // Extract "N años/meses" pattern
          const m = lower.match(/(\d+)\s*(?:años|año|meses|mes)/);
          if (m) info['edad'] = m[0].trim();
          break;
        }
        case 'peso': {
          // Extract "N kg/kilos"
          const m = lower.match(/(\d+[\.,]?\d*)\s*(?:kg|kilos|kilogramos)/);
          if (m) info['peso'] = m[1] + ' kg';
          else {
            // "pesa N"
            const m2 = lower.match(/pesa(?:\s+unos?)?\s+(\d+[\.,]?\d*)/);
            if (m2) info['peso'] = m2[1] + ' kg';
          }
          break;
        }
        case 'genero': {
          const m = lower.match(/\b(macho|hembra|male|female)\b/);
          if (m) info['genero'] = m[1] === 'macho' || m[1] === 'male' ? 'Macho' : 'Hembra';
          break;
        }
        case 'raza': {
          // If there's "raza es X" or "es un/una X", otherwise take the whole text segment
          const m = lower.match(/(?:raza(?:\s+es)?|es\s+un[a]?)\s+([a-záéíóúñ\s]+)/i);
          if (m) info['raza'] = m[1].trim();
          break;
        }
      }
    }

    // Fallback: if we have exactly one field and couldn't extract it, use the full text cleaned
    if (fields.length === 1 && !info[fields[0]]) {
      info[fields[0]] = text.replace(/^\d+[\.\)\-]\s*/, '').trim();
    }

    return info;
  }

  /**
   * Calls the backend to generate a report from the chat conversation.
   */
  private generateReportFromChat(dogInfo: Record<string, string>, progressMsg: ChatMessage) {
    this.reportGenerating = true;
    this.reportProgress = 0;

    // Build conversation history (only text messages, exclude system messages)
    const conversation = this.messages
      .filter(m => m.type !== 'report-progress' && m.type !== 'report-ready')
      .map(m => ({ role: m.role, content: m.content }));

    this.chatService.generateReportFromChat(
      this.reportPendingType!,
      dogInfo,
      conversation
    ).subscribe({
      next: (event: ChatReportSSEEvent) => {
        // Update progress
        progressMsg.reportProgress = event.percent || 0;
        this.reportProgress = event.percent || 0;

        if (event.status === 'completed' && event.completed) {
          // Report is ready! Store data in shared service for tab4
          if (event.extractedData) {
            this.reportSharedService.setReportData({
              reportType: (event.reportType || this.reportPendingType || 'veterinario') as 'veterinario' | 'adiestramiento',
              extractedData: event.extractedData,
              timestamp: Date.now()
            });
          }

          progressMsg.content = '¡Informe generado exitosamente! Puedes verlo, editarlo y descargarlo en la pestaña de Reportes.';
          progressMsg.type = 'report-ready';
          progressMsg.reportType = event.reportType || this.reportPendingType!;
          this.reportGenerating = false;
          this.reportPendingType = null;
          this.reportKnownInfo = {};
          this.reportMissingFields = [];
        } else if (event.error) {
          progressMsg.content = `Error al generar el informe: ${event.message}`;
          progressMsg.type = 'text';
          this.reportGenerating = false;
          this.reportPendingType = null;
          this.reportKnownInfo = {};
          this.reportMissingFields = [];
        } else {
          progressMsg.content = `Generando informe... ${event.message} (${event.percent}%)`;
        }

        this.cdr.detectChanges();
      },
      error: (err) => {
        console.error('Error generating report from chat:', err);
        progressMsg.content = 'Lo siento, hubo un error al generar el informe. Inténtalo de nuevo.';
        progressMsg.type = 'text';
        this.reportGenerating = false;
        this.reportPendingType = null;
        this.reportKnownInfo = {};
        this.reportMissingFields = [];
        this.cdr.detectChanges();
      },
      complete: () => {
        this.reportGenerating = false;
        this.cdr.detectChanges();
      }
    });
  }

  /**
   * Navigates to the reports tab (Tab 4).
   */
  goToReportsTab() {
    this.router.navigate(['/tabs/tab4']);
  }
}
