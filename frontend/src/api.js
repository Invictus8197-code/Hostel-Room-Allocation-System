import axios from 'axios';

const api = axios.create({
  baseURL: '/api/',
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

let _accessToken = null;

export const setAccessToken = (token) => {
  _accessToken = token;
};

export const getAccessToken = () => _accessToken;

api.interceptors.request.use(
  (config) => {
    if (_accessToken) {
      config.headers.Authorization = `Bearer ${_accessToken}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    // Ignore 401 on login and refresh endpoints to prevent loops
    if (originalRequest.url === 'auth/token/' || originalRequest.url === 'auth/token/refresh/') {
      return Promise.reject(error);
    }
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      try {
        const resp = await axios.post('http://localhost:8000/api/auth/token/refresh/', {}, { withCredentials: true });
        if (resp.status === 200) {
          setAccessToken(resp.data.access);
          originalRequest.headers.Authorization = `Bearer ${resp.data.access}`;
          return api(originalRequest);
        }
      } catch (refreshError) {
        // Refresh failed (e.g. cookie expired)
        setAccessToken(null);
        // Dispatch custom event to trigger logout in AuthContext
        window.dispatchEvent(new Event('auth_logout'));
        return Promise.reject(refreshError);
      }
    }
    return Promise.reject(error);
  }
);

export default api;
