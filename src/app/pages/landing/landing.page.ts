import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { IonContent, IonHeader, IonTitle, IonToolbar, IonGrid, IonRow, IonCol, IonButton, IonIcon, IonText } from '@ionic/angular/standalone';
import { Router } from '@angular/router';
import { addIcons } from 'ionicons';
import { paw, heart, chatbubbleEllipses, shieldCheckmark } from 'ionicons/icons';

@Component({
  selector: 'app-landing',
  templateUrl: './landing.page.html',
  styleUrls: ['./landing.page.scss'],
  standalone: true,
  imports: [IonContent, IonGrid, IonRow, IonCol, IonButton, IonIcon, CommonModule, FormsModule]
})
export class LandingPage implements OnInit {

  constructor(private router: Router) {
    addIcons({ paw, heart, chatbubbleEllipses, shieldCheckmark });
  }

  ngOnInit() {
  }
  //
  navigateToApp() {
    this.router.navigate(['/tabs/tab1']);
  }

}
