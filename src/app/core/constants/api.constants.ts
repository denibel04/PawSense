export const API_CONFIG = {
  baseUrl: 'https://pawsense-backend-468538482279.europe-west1.run.app/api/v1',
  localBaseUrl: 'http://localhost:8000/api/v1',
  wsUrl: 'wss://pawsense-backend-468538482279.europe-west1.run.app/api/v1/predict/ws',
  endpoints: {
    predict: '/predict/',
    status: '/',
    chatAsk: '/chat/ask',
    chatInfo: '/chat/info',
    chatGenerateReport: '/chat/generate-report'
  }
};
