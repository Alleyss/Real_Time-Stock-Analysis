// src/services/api.ts
import axios from 'axios';

// Retrieve the API base URL from environment variables
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

if (!API_BASE_URL) {
  console.error(
    'VITE_API_BASE_URL is not defined. Please check your .env file.'
  );
}

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Optional: Interceptor to add JWT token to requests if available
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('accessToken'); // Or wherever you store your token
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Optional: Interceptor to handle common responses or errors (e.g., 401 for logout)
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      // Example: Handle unauthorized access - perhaps redirect to login
      console.error('Unauthorized access - 401');
      localStorage.removeItem('accessToken'); // Clear token
      // Potentially redirect to login page:
      // window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default apiClient;