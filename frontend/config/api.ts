// API Configuration
// In production (served from backend), use relative URLs
// In development, use full localhost URL

const isDevelopment = import.meta.env.DEV;

export const API_BASE_URL = isDevelopment 
  ? 'http://localhost:8000/api'
  : '/api';

export const HEYGEN_API_URL = isDevelopment
  ? 'http://localhost:8000'
  : '';
