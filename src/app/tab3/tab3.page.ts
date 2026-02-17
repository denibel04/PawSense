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

    // 2. Llamar al backend usando fetch
    try {
      const response = await fetch('http://127.0.0.1:8000/api/v1/chat/ask', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({
          question: question,
          context: 'Usuario desde App',
          history: this.messages
        })
      });

      if (!response.ok) throw new Error('Error en la petición');

      const data = await response.json();
      const botMsg = { role: 'assistant', content: data.answer || 'Sin respuesta' };
      this.messages.push(botMsg);
    } catch (error) {
      console.error('Error:', error);
      const errorMsg = { role: 'assistant', content: 'Error al conectar con el servidor (Verifica CORS y que el backend esté corriendo).' };
      this.messages.push(errorMsg);
    } finally {
      this.isLoading = false;
    }
  }
}
