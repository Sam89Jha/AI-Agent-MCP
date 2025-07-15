/**
 * Configuration for DAX App
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
  
  // Get AI Intent API URL
  getAiIntentApiUrl: () => {
    // Use hosted AI Intent API for all environments
    return 'http://ai-intent-api-env.eba-7jgtzmmn.us-west-2.elasticbeanstalk.com';
  },
  
  // Get WebSocket URL
  getWebsocketUrl: () => {
    // Use hosted WebSocket API Gateway for all environments now
    return 'wss://gslu2w0885.execute-api.us-east-1.amazonaws.com/prod';
  },
  
  // Get WebSocket URL for specific booking
  getWebsocketUrlForBooking: (bookingCode) => {
    const baseUrl = 'wss://gslu2w0885.execute-api.us-east-1.amazonaws.com/prod';
    return `${baseUrl}?booking_code=${bookingCode}`;
  }
};

// API endpoints - Only AI Intent API for voice commands
const API_ENDPOINTS = {
  AI_INTENT_API: `${CONFIG.getAiIntentApiUrl()}/detect_intent`,
  HEALTH_CHECK: `${CONFIG.getAiIntentApiUrl()}/health`,
};

export { CONFIG, API_ENDPOINTS };

// Feature flags
export const FEATURES = {
  voiceRecognition: true,
  realTimeUpdates: true,
  analytics: CONFIG.isProduction()
};

export const AI_INTENT_API_URL = CONFIG.getAiIntentApiUrl();

// Debug logging
if (CONFIG.isDebug()) {
  console.log('🚀 NavieTakieSimulation - DAX App (Voice Only)');
  console.log('🔧 Environment:', process.env.NODE_ENV);
  console.log('🌐 AI Intent API URL:', CONFIG.getAiIntentApiUrl());
  console.log('🔌 WebSocket URL:', CONFIG.WEBSOCKET_URL);
  console.log('🚀 Features:', FEATURES);
} 