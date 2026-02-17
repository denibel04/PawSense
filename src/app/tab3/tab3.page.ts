import { Component, OnInit, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import {
  IonHeader, IonToolbar, IonTitle, IonContent,
  IonList, IonItem, IonLabel, IonFooter, IonButton,
  IonTextarea, IonIcon, IonButtons, IonSpinner
} from '@ionic/angular/standalone';
import { addIcons } from 'ionicons';
import { send } from 'ionicons/icons';

@Component({
  selector: 'app-tab3',
  templateUrl: 'tab3.page.html',
  styleUrls: ['tab3.page.scss'],
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    IonHeader, IonToolbar, IonTitle, IonContent,
    IonList, IonItem, IonLabel, IonFooter, IonButton,
    IonTextarea, IonIcon, IonButtons, IonSpinner
  ],
})
export class Tab3Page implements OnInit {
  messages: { role: string; content: string }[] = [];
  newMessage: string = '';
  isLoading: boolean = false;

  constructor() {
    addIcons({ send });
  }

  ngOnInit() {
    // Mensaje de bienvenida inicial (sin cargar de localStorage)
    this.messages = [
      { role: 'assistant', content: '¡Hola! Soy tu asistente canino. ¿En qué puedo ayudarte hoy?' }
    ];
  }

  async sendMessage() {
    if (!this.newMessage.trim()) return;

    // 1. Añadir mensaje del usuario
    const userMsg = { role: 'user', content: this.newMessage };
    this.messages.push(userMsg);

    const question = this.newMessage;
    this.newMessage = ''; // Limpiar input
    this.isLoading = true;

    // 2. Llamar al backend usando fetch (Streaming)
    try {
      const response = await fetch('http://127.0.0.1:8000/api/v1/chat/ask', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({
          question: question,
          context: 'Usuario desde App', // TODO: Obtener del servicio de predicción
          history: this.messages
        })
      });

      if (!response.ok) throw new Error('Error en la petición');
      if (!response.body) throw new Error('No body in response');

      // Crear mensaje vacío del bot para ir rellenando
      const botMsg = { role: 'assistant', content: '' };
      this.messages.push(botMsg);

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        botMsg.content += chunk;
        // Forzar detección de cambios si fuera necesario, aunque en Ionic suele ser auto
      }

    } catch (error) {
      console.error('Error:', error);
      const errorMsg = { role: 'assistant', content: 'Lo siento, hubo un error al conectar con el servidor.' };
      this.messages.push(errorMsg);
    } finally {
      this.isLoading = false;
    }
  }
}
