import { Component } from '@angular/core';
import { 
  IonHeader, IonToolbar, IonTitle, IonContent, IonButton, 
  IonItem, IonLabel, IonCard, IonCardContent, IonLoading,
  IonGrid, IonRow, IonCol, IonProgressBar, IonBadge 
} from '@ionic/angular/standalone';
import { ExploreContainerComponent } from '../explore-container/explore-container.component';
import { HttpClient } from '@angular/common/http';
import { CommonModule } from '@angular/common'; 

@Component({
  selector: 'app-tab1',
  templateUrl: 'tab1.page.html',
  styleUrls: ['tab1.page.scss'],
  standalone: true,
  imports: [
    IonHeader, IonToolbar, IonTitle, IonContent, IonButton, 
    IonItem, IonLabel, IonCard, IonCardContent, IonLoading,
    IonGrid, IonRow, IonCol, IonProgressBar, IonBadge,
    ExploreContainerComponent, CommonModule
  ],
})
export class Tab1Page {
  selectedFile: File | null = null;
  resultado: any = null;
  cargando = false;
  imagePreview: string | null = null; // Para mostrar la foto que vas a subir

  // IP de tu instancia EC2 de AWS
  private readonly URL_API = 'http://51.20.108.18:8000/predict';

  constructor(private http: HttpClient) {}

  onFileSelected(event: any) {
    const file = event.target.files[0];
    if (file) {
      this.selectedFile = file;
      
      // Crear una vista previa de la imagen
      const reader = new FileReader();
      reader.onload = () => {
        this.imagePreview = reader.result as string;
      };
      reader.readAsDataURL(file);
    }
  }

  subirYPredecir() {
    if (!this.selectedFile) return;

    this.cargando = true;
    this.resultado = null; // Limpiar resultado anterior

    const formData = new FormData();
    formData.append('file', this.selectedFile);

    this.http.post(this.URL_API, formData).subscribe({
      next: (res: any) => {
        this.resultado = res;
        this.cargando = false;
        console.log('Respuesta de AWS:', res);
      },
      error: (err) => {
        console.error('Error de conexión:', err);
        alert('Error: No se pudo conectar con el servidor. Verifica que el backend esté corriendo y el puerto 8000 esté abierto en AWS.');
        this.cargando = false;
      }
    });
  }
}