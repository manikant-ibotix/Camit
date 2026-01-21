import axios from 'axios';

const API_BASE_URL = 'http://localhost:8001/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Camera API
export const cameraAPI = {
  getAll: () => api.get('/cameras/'),
  getById: (id) => api.get(`/cameras/${id}`),
  create: (data) => api.post('/cameras/', data),
  update: (id, data) => api.put(`/cameras/${id}`, data),
  delete: (id) => api.delete(`/cameras/${id}`),
  start: (id) => api.post(`/cameras/${id}/start`),
  stop: (id) => api.post(`/cameras/${id}/stop`),
};

// Alert API
export const alertAPI = {
  getAll: (params) => api.get('/alerts/', { params }),
  getById: (id) => api.get(`/alerts/${id}`),
  acknowledge: (id) => api.put(`/alerts/${id}/acknowledge`),
  delete: (id) => api.delete(`/alerts/${id}`),
  getStats: (days = 7) => api.get('/alerts/stats/summary', { params: { days } }),
};

// Stream API
export const streamAPI = {
  getMjpegUrl: (cameraId) => `${API_BASE_URL}/streams/${cameraId}/mjpeg`,
  getSnapshotUrl: (cameraId) => `${API_BASE_URL}/streams/${cameraId}/snapshot`,
};

// Video Analysis API
export const analysisAPI = {
  upload: (formData, onUploadProgress) => 
    api.post('/analysis/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress,
    }),
  getResults: (analysisId) => api.get(`/analysis/results/${analysisId}`),
  getStatistics: (analysisId) => api.get(`/analysis/statistics/${analysisId}`),
  list: () => api.get('/analysis/list'),
  delete: (analysisId) => api.delete(`/analysis/${analysisId}`),
};

// WebSocket
export const getWebSocketUrl = () => {
  return 'ws://localhost:8001/api/ws/live';
};

export default api;
