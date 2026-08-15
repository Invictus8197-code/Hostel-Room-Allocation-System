import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';

import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Allocations from './pages/Allocations';
import AllocationDetail from './pages/AllocationDetail';
import Analytics from './pages/Analytics';
import Simulation from './pages/Simulation';

function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/login" element={<Login />} />
          
          <Route path="/dashboard" element={
            <ProtectedRoute roles={['ADMIN', 'WARDEN']}>
              <Dashboard />
            </ProtectedRoute>
          } />
          
          <Route path="/allocations" element={
            <ProtectedRoute roles={['ADMIN', 'WARDEN']}>
              <Allocations />
            </ProtectedRoute>
          } />
          
          <Route path="/allocations/:id" element={
            <ProtectedRoute roles={['ADMIN', 'WARDEN']}>
              <AllocationDetail />
            </ProtectedRoute>
          } />
          
          <Route path="/analytics" element={
            <ProtectedRoute roles={['ADMIN', 'WARDEN']}>
              <Analytics />
            </ProtectedRoute>
          } />
          
          <Route path="/simulation" element={
            <ProtectedRoute roles={['ADMIN', 'WARDEN']}>
              <Simulation />
            </ProtectedRoute>
          } />
          
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;
