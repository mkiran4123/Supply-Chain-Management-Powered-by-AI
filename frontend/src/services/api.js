import axios from 'axios';

const API_BASE_URL = 'http://127.0.0.1:8000';

// Create axios instance with base configuration
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add response interceptor to handle authentication errors
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    // Handle 401 Unauthorized errors
    if (error.response && error.response.status === 401) {
      console.log('Authentication error detected, redirecting to login');
      // Clear auth token
      localStorage.removeItem('authToken');
      // Redirect to login page
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  login: async (email, password) => {
    try {
      console.log('Attempting login with email:', email);
      const response = await api.post('/token', 
        `username=${encodeURIComponent(email)}&password=${encodeURIComponent(password)}`,
        {
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          },
        }
      );
      console.log('Login response received:', response);
      
      // Validate that the response contains the expected access_token
      if (!response.data || !response.data.access_token) {
        console.error('Invalid response format - missing access_token:', response.data);
        throw new Error('Invalid response format from server');
      }
      
      return response.data;
    } catch (error) {
      console.error('Login API error details:', error);
      throw error;
    }
  },
  getCurrentUser: async () => {
    const response = await api.get('/users/me');
    return response.data;
  },
};

// Inventory API
export const inventoryAPI = {
  getAll: async () => {
    const response = await api.get('/inventory/');
    return response.data;
  },
  getById: async (id) => {
    const response = await api.get(`/inventory/${id}`);
    return response.data;
  },
  create: async (data) => {
    const response = await api.post('/inventory/', data);
    return response.data;
  },
  update: async (id, data) => {
    const response = await api.put(`/inventory/${id}`, data);
    return response.data;
  },
  delete: async (id) => {
    await api.delete(`/inventory/${id}`);
  },
};

// Supplier API
export const supplierAPI = {
  getAll: async () => {
    const response = await api.get('/suppliers/');
    return response.data;
  },
  getById: async (id) => {
    const response = await api.get(`/suppliers/${id}`);
    return response.data;
  },
  create: async (data) => {
    const response = await api.post('/suppliers/', data);
    return response.data;
  },
  update: async (id, data) => {
    const response = await api.put(`/suppliers/${id}`, data);
    return response.data;
  },
  delete: async (id) => {
    await api.delete(`/suppliers/${id}`);
  },
};

// Order API
export const orderAPI = {
  getAll: async () => {
    const response = await api.get('/orders/');
    return response.data;
  },
  getById: async (id) => {
    const response = await api.get(`/orders/${id}`);
    return response.data;
  },
  create: async (data) => {
    const response = await api.post('/orders/', data);
    return response.data;
  },
  update: async (id, data) => {
    const response = await api.put(`/orders/${id}`, data);
    return response.data;
  },
};