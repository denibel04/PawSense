export const API_CONFIG = {
  baseUrl: 'http://127.0.0.1:8000/api/v1', // Ajustado a local para desarrollo
  localBaseUrl: 'http://127.0.0.1:8000/api/v1',
  wsUrl: 'ws://127.0.0.1:8000/api/v1/predict/ws',
  endpoints: {
    predict: '/predict',
    status: '/',
    chatAsk: '/chat/ask',
    chatInfo: '/chat/info',
    chatGenerateReport: '/chat/generate-report'
  }
};
