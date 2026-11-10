import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
});

// Attach JWT token to requests if available
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('ecosort_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const apiService = {
  // System Health
  async getHealth() {
    const res = await api.get('/health');
    return res.data;
  },

  // Authentication
  async register(userData) {
    const res = await api.post('/auth/register', userData);
    if (res.data?.access_token) {
      localStorage.setItem('ecosort_token', res.data.access_token);
      localStorage.setItem('ecosort_user', JSON.stringify(res.data.user));
    }
    return res.data;
  },

  async login(credentials) {
    const res = await api.post('/auth/login', credentials);
    if (res.data?.access_token) {
      localStorage.setItem('ecosort_token', res.data.access_token);
      localStorage.setItem('ecosort_user', JSON.stringify(res.data.user));
    }
    return res.data;
  },

  async getProfile() {
    const res = await api.get('/auth/me');
    return res.data;
  },

  logout() {
    localStorage.removeItem('ecosort_token');
    localStorage.removeItem('ecosort_user');
  },

  getCurrentUser() {
    try {
      const stored = localStorage.getItem('ecosort_user');
      return stored ? JSON.parse(stored) : null;
    } catch {
      return null;
    }
  },

  // Waste Analysis
  async analyzeImage(file, location = 'us_epa', isContaminated = false) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('location', location);
    formData.append('is_contaminated', isContaminated ? 'true' : 'false');

    const res = await api.post('/analyze', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return res.data;
  },

  // History
  async getHistory(limit = 50, skip = 0, category = null) {
    const params = { limit, skip };
    if (category) params.category = category;
    const res = await api.get('/history', { params });
    return res.data;
  },

  // Analytics
  async getAnalytics() {
    const res = await api.get('/analytics');
    return res.data;
  },
};

export default api;

