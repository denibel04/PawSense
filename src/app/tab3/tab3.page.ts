import { ChangeDetectorRef, Component, NgZone, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import {
  IonHeader, IonToolbar, IonTitle, IonContent,
  IonItem, IonLabel, IonFooter, IonButton,
  IonTextarea, IonIcon, IonButtons, IonSpinner, IonRippleEffect
} from '@ionic/angular/standalone';
import { addIcons } from 'ionicons';
import { send, paw } from 'ionicons/icons';
import { ChatService } from '../core/services/chat.service';
import { HeaderComponent } from '../shared/components/header/header.component';

@Component({
  selector: 'app-tab3',
  templateUrl: 'tab3.page.html',
  styleUrls: ['tab3.page.scss'],
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    IonHeader, IonToolbar, IonTitle, IonContent,
    IonItem, IonLabel, IonFooter, 
    IonTextarea, IonIcon, IonButtons, IonSpinner, IonRippleEffect, 
    HeaderComponent
  ],
})
export class Tab3Page implements OnInit {
  messages: { role: string; content: string }[] = [];
  newMessage: string = '';
  isLoading: boolean = false;
  contextData: string = '';
  cdr: ChangeDetectorRef;

  constructor(private chatService: ChatService, private changeDetectorRef: ChangeDetectorRef, private ngZone: NgZone) {
    this.cdr = changeDetectorRef;
    addIcons({ send, paw });
  }

  ngOnInit() {
    this.messages = [
      { role: 'assistant', content: '¡Hola! Soy tu asistente canino. ¿En qué puedo ayudarte hoy?' }
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
        // Fallback or silently fail - do not show error to user in chat
        this.contextData = '';
      }
    });
  }

  async sendMessage() {
    if (!this.newMessage.trim()) return;

    const userMsg = { role: 'user', content: this.newMessage };
    this.messages.push(userMsg);

    const question = this.newMessage;
    this.newMessage = '';
    this.isLoading = true;

    try {
      const response = await this.chatService.sendMessage(question, this.contextData, this.messages);

      if (!response.ok) throw new Error('Error en la petición');
      if (!response.body) throw new Error('No body in response');

      const botMsg = { role: 'assistant', content: '' };
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

      // Force Angular to render the final state of botMsg.content.
      // zone.js may fire its change detection cycle just before the last
      // assignment, leaving the final character(s) un-rendered.
      this.cdr.detectChanges();

    } catch (error) {
      console.error('Error in chat:', error);

      if (this.messages.length > 0 && this.messages[this.messages.length - 1].role === 'assistant' && !this.messages[this.messages.length - 1].content) {
        this.messages.pop();
      }

      const errorMsg = { role: 'assistant', content: 'Lo siento, hubo un error al conectar con el servidor.' };
      this.messages.push(errorMsg);
      this.isLoading = false;
    }
  }
}

