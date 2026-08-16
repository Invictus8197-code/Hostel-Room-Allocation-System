import React from 'react';
import './TopHeader.css';

export default function TopHeader({ toggleSidebar }) {
  // Can add breadcrumbs or specific context later
  return (
    <header className="premium-header">
      <div className="header-left">
        <button className="mobile-menu-btn" onClick={toggleSidebar}>
          ☰
        </button>
        <div className="header-title-block">
          <h1>Smart Hostel Room Allocation Optimizer</h1>
          <p>Real-time room availability, student affinity matching & conflict resolution system</p>
        </div>
      </div>
      <div className="header-right">
        <div className="theme-toggle">
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="5"></circle>
            <line x1="12" y1="1" x2="12" y2="3"></line>
            <line x1="12" y1="21" x2="12" y2="23"></line>
            <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line>
            <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line>
            <line x1="1" y1="12" x2="3" y2="12"></line>
            <line x1="21" y1="12" x2="23" y2="12"></line>
            <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line>
            <line x1="18.36" y1="4.22" x2="19.78" y2="5.64"></line>
          </svg>
        </div>
        <div className="last-run-badge">
          Last Run: Never
        </div>
      </div>
    </header>
  );
}
