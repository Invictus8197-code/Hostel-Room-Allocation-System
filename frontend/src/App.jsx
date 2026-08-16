import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import AppLayout from './components/layout/AppLayout';

import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Allocations from './pages/Allocations';
import AllocationDetail from './pages/AllocationDetail';
import Analytics from './pages/Analytics';
import Simulation from './pages/Simulation';
import SmartHome from './pages/SmartHome';
import StudentDashboard from './pages/StudentDashboard';
import SuperadminDashboard from './pages/SuperadminDashboard';

// A dynamic router that redirects users to their appropriate dashboard based on their role
function RoleBasedDashboardRedirect() {
  const { user } = useAuth();
  
  if (!user) return <Navigate to="/login" replace />;
  
  switch(user.role) {
    case 'STUDENT': return <Navigate to="/student-dashboard" replace />;
    case 'SUPERADMIN': return <Navigate to="/superadmin-dashboard" replace />;
    case 'ADMIN': return <Navigate to="/dashboard" replace />;
    case 'WARDEN': return <Navigate to="/dashboard" replace />;
    default: return <Navigate to="/login" replace />;
  }
}

function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/" element={<SmartHome />} />
          <Route path="/login" element={<Login />} />
          
          {/* Main Redirect Route */}
          <Route path="/redirect-dashboard" element={<RoleBasedDashboardRedirect />} />
          
          <Route path="/student-dashboard" element={
            <ProtectedRoute roles={['STUDENT']}>
              <AppLayout><StudentDashboard /></AppLayout>
            </ProtectedRoute>
          } />
          
          <Route path="/superadmin-dashboard" element={
            <ProtectedRoute roles={['SUPERADMIN']}>
              <AppLayout><SuperadminDashboard /></AppLayout>
            </ProtectedRoute>
          } />
          
          <Route path="/dashboard" element={
            <ProtectedRoute roles={['ADMIN', 'WARDEN']}>
              <AppLayout><Dashboard /></AppLayout>
            </ProtectedRoute>
          } />
          
          <Route path="/allocations" element={
            <ProtectedRoute roles={['ADMIN', 'WARDEN', 'SUPERADMIN']}>
              <AppLayout><Allocations /></AppLayout>
            </ProtectedRoute>
          } />
          
          <Route path="/allocations/:id" element={
            <ProtectedRoute roles={['ADMIN', 'WARDEN', 'SUPERADMIN']}>
              <AppLayout><AllocationDetail /></AppLayout>
            </ProtectedRoute>
          } />
          
          <Route path="/analytics" element={
            <ProtectedRoute roles={['ADMIN', 'WARDEN', 'SUPERADMIN']}>
              <AppLayout><Analytics /></AppLayout>
            </ProtectedRoute>
          } />
          
          <Route path="/simulation" element={
            <ProtectedRoute roles={['ADMIN', 'WARDEN', 'SUPERADMIN']}>
              <AppLayout><Simulation /></AppLayout>
            </ProtectedRoute>
          } />
          
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;
