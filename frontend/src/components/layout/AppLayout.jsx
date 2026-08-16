import React, { useState } from 'react';
import Sidebar from './Sidebar';
import TopHeader from './TopHeader';
import './AppLayout.css';

export default function AppLayout({ children }) {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  const toggleSidebar = () => {
    setIsSidebarOpen(!isSidebarOpen);
  };

  return (
    <div className="premium-app-container">
      <Sidebar isOpen={isSidebarOpen} toggleSidebar={toggleSidebar} />
      <div className="premium-main-wrapper">
        <TopHeader toggleSidebar={toggleSidebar} />
        <main className="premium-main-content">
          {children}
        </main>
      </div>
    </div>
  );
}
