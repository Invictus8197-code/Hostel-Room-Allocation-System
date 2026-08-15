import React, { createContext, useState, useEffect, useContext } from 'react';
import api, { setAccessToken } from '../api';
import { jwtDecode } from 'jwt-decode';

const AuthContext = createContext();

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const parseToken = (token) => {
    try {
      return jwtDecode(token);
    } catch (e) {
      return null;
    }
  };

  const login = async (username, password) => {
    try {
      const res = await api.post('auth/token/', { username, password });
      if (res.data.access) {
        setAccessToken(res.data.access);
        const decoded = parseToken(res.data.access);
        setUser(decoded);
        return true;
      }
      return false;
    } catch (error) {
      console.error("Login failed:", error);
      return false;
    }
  };

  const logout = async () => {
    try {
      await api.post('auth/logout/');
    } catch (e) {
      console.error('Logout error', e);
    } finally {
      setAccessToken(null);
      setUser(null);
    }
  };

  useEffect(() => {
    const handleForceLogout = () => {
      setAccessToken(null);
      setUser(null);
    };

    window.addEventListener('auth_logout', handleForceLogout);
    
    // Attempt to silently refresh token on initial load
    const initAuth = async () => {
      try {
        const res = await api.post('auth/token/refresh/');
        if (res.data.access) {
          setAccessToken(res.data.access);
          setUser(parseToken(res.data.access));
        }
      } catch (e) {
        // Ignored, user is just not logged in
      } finally {
        setLoading(false);
      }
    };
    initAuth();

    return () => window.removeEventListener('auth_logout', handleForceLogout);
  }, []);

  return (
    <AuthContext.Provider value={{ user, login, logout, loading }}>
      {!loading && children}
    </AuthContext.Provider>
  );
};
