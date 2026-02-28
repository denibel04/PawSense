import { Component, EnvironmentInjector, inject } from '@angular/core';
import { IonTabs, IonTabBar, IonTabButton, IonIcon, IonLabel } from '@ionic/angular/standalone';
import { addIcons } from 'ionicons';
import { 
  images, imagesOutline, 
  camera, cameraOutline, 
  chatbubble, chatbubbleOutline, 
  documentText, documentTextOutline 
} from 'ionicons/icons';

@Component({
  selector: 'app-tabs',
  templateUrl: 'tabs.page.html',
  styleUrls: ['tabs.page.scss'],
  imports: [IonTabs, IonTabBar, IonTabButton, IonIcon, IonLabel],
})
export class TabsPage {
  public environmentInjector = inject(EnvironmentInjector);

  constructor() {
    addIcons({ 
      images, imagesOutline, 
      camera, cameraOutline, 
      chatbubble, chatbubbleOutline, 
      documentText, documentTextOutline 
    });
  }
}