/**
 * Configuration for PAX App
 * Environment-specific settings for local, staging, and production
 */

const CONFIG = {
  // API endpoints
  API_BASE_URL: process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000',
  WEBSOCKET_URL: process.env.REACT_APP_WEBSOCKET_URL || 'ws://localhost:8000/ws',
  
  // Environment detection
  isProduction: () => process.env.NODE_ENV === 'production',
  isStaging: () => process.env.NODE_ENV === 'staging',
  isLocal: () => process.env.NODE_ENV === 'development',
  isDebug: () => process.env.NODE_ENV === 'development',
  
  // Get API URL for endpoint
  getApiUrl: (endpoint = '') => {
    const baseUrl = CONFIG.API_BASE_URL;
    return `${baseUrl}${endpoint}`;
  },
  
  // Get WebSocket URL
  getWebsocketUrl: () => {
    return CONFIG.WEBSOCKET_URL;
  },
  
  // Get WebSocket URL for specific booking
  getWebsocketUrlForBooking: (bookingCode) => {
    const baseUrl = CONFIG.WEBSOCKET_URL;
    // For production, use API Gateway WebSocket endpoint
    if (CONFIG.isProduction()) {
      return `${baseUrl}?booking_code=${bookingCode}`;
    }
    // For local, use MCP server WebSocket
    return `${baseUrl}/${bookingCode}`;
  }
};

// API endpoints
const API_ENDPOINTS = {
  AI_AGENT: CONFIG.getApiUrl('/api/v1/ai_agent'),
  SEND_MESSAGE: CONFIG.getApiUrl('/api/v1/send_message'),
  MAKE_CALL: CONFIG.getApiUrl('/api/v1/make_call'),
  GET_MESSAGES: CONFIG.getApiUrl('/api/v1/get_message'),
};

export { CONFIG, API_ENDPOINTS };

// Feature flags
export const FEATURES = {
  voiceRecognition: true,
  realTimeUpdates: true,
  analytics: CONFIG.isProduction()
};

// Debug logging
if (CONFIG.isDebug()) {
  console.log('🚀 NavieTakieSimulation - PAX App');
  console.log('🔧 Environment:', process.env.NODE_ENV);
  console.log('🌐 API Base URL:', CONFIG.API_BASE_URL);
  console.log('🔌 WebSocket URL:', CONFIG.WEBSOCKET_URL);
  console.log('🚀 Features:', FEATURES);
} 