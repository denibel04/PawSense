export interface TemperamentInfo {
  esp: string;
  group: 'activity' | 'intel' | 'social' | 'character' | 'default';
  icon: string;
}

export const TEMPERAMENT_MAP: Record<string, TemperamentInfo> = {
  // --- ACTIVITY (Energía y Movimiento) ---
  'energetic': { esp: 'Enérgico', group: 'activity', icon: 'flash-outline' },
  'athletic': { esp: 'Atlético', group: 'activity', icon: 'bicycle-outline' },
  'lively': { esp: 'Vivaz', group: 'activity', icon: 'paw-outline' },
  'playful': { esp: 'Juguetón', group: 'activity', icon: 'football-outline' },
  'spirited': { esp: 'Espabilado', group: 'activity', icon: 'bonfire-outline' },
  'work-focused': { esp: 'Trabajador', group: 'activity', icon: 'briefcase-outline' },
  'mischievous': { esp: 'Travieso', group: 'activity', icon: 'ice-cream-outline' },

  // --- INTELLIGENCE (Mente y Aprendizaje) ---
  'intelligent': { esp: 'Inteligente', group: 'intel', icon: 'bulb-outline' },
  'smart': { esp: 'Listo', group: 'intel', icon: 'brain-outline' },
  'alert': { esp: 'Alerta', group: 'intel', icon: 'eye-outline' },
  'curious': { esp: 'Curioso', group: 'intel', icon: 'search-outline' },
  'eager to please': { esp: 'Dócil', group: 'intel', icon: 'star-outline' },
  'independent': { esp: 'Independiente', group: 'intel', icon: 'compass-outline' },
  'adaptable': { esp: 'Adaptable', group: 'intel', icon: 'extension-puzzle-outline' },
  'quick': { esp: 'Rápido', group: 'intel', icon: 'speedometer-outline' },

  // --- SOCIAL (Relación con otros) ---
  'affectionate': { esp: 'Cariñoso', group: 'social', icon: 'heart-outline' },
  'friendly': { esp: 'Amigable', group: 'social', icon: 'people-outline' },
  'loyal': { esp: 'Leal', group: 'social', icon: 'ribbon-outline' },
  'outgoing': { esp: 'Extrovertido', group: 'social', icon: 'chatbubbles-outline' },
  'gentle': { esp: 'Gentil', group: 'social', icon: 'leaf-outline' },
  'happy': { esp: 'Feliz', group: 'social', icon: 'happy-outline' },
  'devoted': { esp: 'Devoto', group: 'social', icon: 'infinite-outline' },
  'charming': { esp: 'Encantador', group: 'social', icon: 'sparkles-outline' },
  'cheerful': { esp: 'Alegre', group: 'social', icon: 'sunny-outline' },
  'easygoing': { esp: 'Relajado', group: 'social', icon: 'hand-thumbs-up-outline' },
  'good-natured': { esp: 'Buen carácter', group: 'social', icon: 'body-outline' },
  'loving': { esp: 'Amoroso', group: 'social', icon: 'heart-half-outline' },
  'trusting': { esp: 'Confiado', group: 'social', icon: 'accessibility-outline' },

  // --- CHARACTER (Temperamento y Temple) ---
  'confident': { esp: 'Seguro', group: 'character', icon: 'shield-checkmark-outline' },
  'courageous': { esp: 'Valiente', group: 'character', icon: 'trophy-outline' },
  'fearless': { esp: 'Intrépido', group: 'character', icon: 'flame-outline' },
  'protective': { esp: 'Protector', group: 'character', icon: 'shield-outline' },
  'calm': { esp: 'Tranquilo', group: 'character', icon: 'water-outline' },
  'docile': { esp: 'Obediente', group: 'character', icon: 'thumbs-up-outline' },
  'reserved': { esp: 'Reservado', group: 'character', icon: 'moon-outline' },
  'aloof': { esp: 'Distante', group: 'character', icon: 'ban-outline' },
  'dignified': { esp: 'Digno', group: 'character', icon: 'medal-outline' },
  'patient': { esp: 'Paciente', group: 'character', icon: 'hourglass-outline' },
  'sensitive': { esp: 'Sensible', group: 'character', icon: 'thermometer-outline' },
  'brave': { esp: 'Bravo', group: 'character', icon: 'shield-outline' },
  'composed': { esp: 'Sereno', group: 'character', icon: 'mediat-outline' },
  'watchful': { esp: 'Vigilante', group: 'character', icon: 'telescope-outline' },
  'steady': { esp: 'Estable', group: 'character', icon: 'anchor-outline' },
  'quiet': { esp: 'Silencioso', group: 'character', icon: 'volume-mute-outline' },
  'tenacious': { esp: 'Tenaz', group: 'character', icon: 'link-outline' },
  'determined': { esp: 'Decidido', group: 'character', icon: 'golf-outline' },
  'bold': { esp: 'Audaz', group: 'character', icon: 'rocket-outline' },
  'tough': { esp: 'Resistente', group: 'character', icon: 'hammer-outline' },
  'reliable': { esp: 'Fiable', group: 'character', icon: 'checkmark-done-outline' },
  'faithful': { esp: 'Fiel', group: 'character', icon: 'heart-circle-outline' },
  'wild': { esp: 'Salvaje', group: 'character', icon: 'warning-outline' },
  'hardy': { esp: 'Robusto', group: 'character', icon: 'build-outline' }
};