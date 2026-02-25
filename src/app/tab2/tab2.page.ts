import { Component } from '@angular/core';
import { IonHeader, IonToolbar, IonTitle, IonContent, IonIcon } from '@ionic/angular/standalone';
import { addIcons } from 'ionicons';
import { paw } from 'ionicons/icons';
import { ExploreContainerComponent } from '../shared/components/explore-container/explore-container.component';

@Component({
  selector: 'app-tab2',
  templateUrl: 'tab2.page.html',
  styleUrls: ['tab2.page.scss'],
  imports: [IonHeader, IonToolbar, IonTitle, IonContent, IonIcon, ExploreContainerComponent]
})
export class Tab2Page {
  constructor() {
    addIcons({ paw });
  }
}
