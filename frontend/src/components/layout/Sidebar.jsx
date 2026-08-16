import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import './Sidebar.css';

export default function Sidebar({ isOpen, toggleSidebar }) {
  const { user, logout } = useAuth();
  const location = useLocation();

  if (!user) return null;

  // Define navigation links based on role
  let links = [];
  
  if (user.role === 'STUDENT') {
    links = [
      { path: '/student-dashboard', label: 'My Dashboard', icon: '🏠' },
    ];
  } else if (user.role === 'WARDEN' || user.role === 'ADMIN') {
    links = [
      { path: '/dashboard', label: 'Dashboard', icon: '📊' },
      { path: '/allocations', label: 'Allocations', icon: '🛏️' },
      { path: '/simulation', label: 'Optimizer Engine', icon: '🧠' },
      { path: '/analytics', label: 'Analytics', icon: '📈' },
    ];
  } else if (user.role === 'SUPERADMIN') {
    links = [
      { path: '/superadmin-dashboard', label: 'System Control', icon: '🛡️' },
      { path: '/allocations', label: 'Allocations', icon: '🛏️' },
      { path: '/simulation', label: 'Optimizer Engine', icon: '🧠' },
      { path: '/analytics', label: 'Global Analytics', icon: '🌍' },
    ];
  }

  return (
    <aside className={`premium-sidebar ${isOpen ? 'open' : ''}`}>
      <div className="sidebar-brand">
        <div className="brand-logo">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
          </svg>
        </div>
        <div className="brand-text">
          <h2>Smart Ashray.com</h2>
          <span className="brand-version">v2.4 SMART AI</span>
        </div>
      </div>

      <div className="sidebar-nav-label">MAIN NAVIGATION</div>
      <nav className="sidebar-nav">
        {links.map((link) => (
          <Link 
            key={link.path} 
            to={link.path} 
            className={`sidebar-link ${location.pathname === link.path ? 'active' : ''}`}
          >
            <span className="link-icon">{link.icon}</span>
            <span className="link-text">{link.label}</span>
          </Link>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div className="user-info">
          <div className="user-avatar">{(user.username || 'U').charAt(0).toUpperCase()}</div>
          <div className="user-details">
            <span className="user-name">{user.username || `User ${user.user_id}`}</span>
            <span className="user-role">{user.role}</span>
          </div>
        </div>
        <button onClick={logout} className="logout-btn-premium">
          Logout
        </button>
      </div>
    </aside>
  );
}
