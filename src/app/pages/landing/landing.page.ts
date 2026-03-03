import { Component, OnInit, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { IonContent, IonHeader, IonTitle, IonToolbar, IonGrid, IonRow, IonCol, IonButton, IonIcon, IonText } from '@ionic/angular/standalone';
import { Router } from '@angular/router';
import { addIcons } from 'ionicons';
import { paw, searchOutline, chatbubbleEllipses, documentText } from 'ionicons/icons';

@Component({
  selector: 'app-landing',
  templateUrl: './landing.page.html',
  styleUrls: ['./landing.page.scss'],
  standalone: true,
  imports: [IonContent, IonGrid, IonRow, IonCol, IonButton, IonIcon, CommonModule, FormsModule]
})
export class LandingPage implements OnInit {
  @ViewChild(IonContent) content!: IonContent;

  constructor(private router: Router) {
    addIcons({ paw, searchOutline, chatbubbleEllipses, documentText });
  }

  ngOnInit() {
  }

  navigateToApp() {
    this.router.navigate(['/tabs/tab1']);
  }

  navigateTo(route: string) {
    this.router.navigate([route]);
  }

  scrollToFeatures() {
    const el = document.getElementById('features-section');
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' });
    }
  }
}
