import { Component, OnInit, ViewChild, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
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

  // Clave para localStorage
  private STORAGE_KEY = 'pawsense_chat_history';
  private http = inject(HttpClient);
  private apiUrl = 'http://127.0.0.1:8000/api/v1/chat/ask';
  isLoading = false;

  constructor() {
    addIcons({ send });
  }

  ngOnInit() {
    this.loadChat();
  }

  loadChat() {
    const savedChat = localStorage.getItem(this.STORAGE_KEY);
    if (savedChat) {
      this.messages = JSON.parse(savedChat);
    } else {
      // Mensaje de bienvenida inicial
      this.messages = [
        { role: 'assistant', content: '¡Hola! Soy tu asistente canino. ¿En qué puedo ayudarte hoy?' }
      ];
    }
  }

  saveChat() {
    localStorage.setItem(this.STORAGE_KEY, JSON.stringify(this.messages));
  }

  sendMessage() {
    if (!this.newMessage.trim()) return;

    // 1. Añadir mensaje del usuario
    const userMsg = { role: 'user', content: this.newMessage };
    this.messages.push(userMsg);

    // 2. Llamar al backend
    this.isLoading = true;
    this.http.post<any>(this.apiUrl, { question: this.newMessage, context: '' })
      .subscribe({
        next: (response) => {
          const botMsg = { role: 'assistant', content: response.answer };
          this.messages.push(botMsg);
          this.saveChat();
          this.isLoading = false;
        },
        error: (error) => {
          console.error('Error calling chat API:', error);
          const errorMsg = { role: 'assistant', content: 'Lo siento, hubo un error al conectar con el servidor.' };
          this.messages.push(errorMsg);
          this.saveChat();
          this.isLoading = false;
        }
      });

    // 3. Limpiar y guardar (el mensaje del usuario)
    this.newMessage = '';
    this.saveChat();
  }
}
