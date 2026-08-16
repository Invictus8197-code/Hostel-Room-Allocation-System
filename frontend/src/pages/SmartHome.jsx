import React from 'react';
import { Navigate } from 'react-router-dom';

function SmartHome() {
  // Redirect the public landing page straight to the Login page
  // since the system is now exclusively user-based authentication.
  return <Navigate to="/login" replace />;
}

export default SmartHome;
