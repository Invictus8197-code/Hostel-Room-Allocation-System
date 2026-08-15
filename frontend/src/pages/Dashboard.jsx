import React, { useState, useEffect } from 'react';
import api from '../api';
import { useAuth } from '../context/AuthContext';
import { Link } from 'react-router-dom';
import './Dashboard.css';

function Dashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const { user, logout } = useAuth();

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await api.get('dashboard/summary/');
        setData(res.data);
      } catch (e) {
        console.error("Dashboard error", e);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) return <div className="loader">Loading Dashboard...</div>;

  return (
    <div className="layout">
      <aside className="sidebar">
        <h2 className="brand">Smart Hostel</h2>
        <nav className="nav-menu">
          <Link to="/dashboard" className="nav-item active">Dashboard</Link>
          <Link to="/allocations" className="nav-item">Allocations</Link>
          <Link to="/analytics" className="nav-item">Analytics</Link>
          <Link to="/simulation" className="nav-item">Simulation</Link>
        </nav>
        <div className="user-profile">
          <div>{user?.username} ({user?.role})</div>
          <button onClick={logout} className="logout-btn">Logout</button>
        </div>
      </aside>
      
      <main className="main-content">
        <header className="page-header">
          <h1>Dashboard Overview</h1>
        </header>

        {data ? (
          <div className="metrics-grid">
            <div className="metric-card">
              <h3>Total Students</h3>
              <div className="metric-value">{data.total_students}</div>
            </div>
            <div className="metric-card">
              <h3>Allocated</h3>
              <div className="metric-value text-green">{data.allocated_students}</div>
            </div>
            <div className="metric-card">
              <h3>Unallocated</h3>
              <div className="metric-value text-red">{data.unallocated_students}</div>
            </div>
            <div className="metric-card">
              <h3>Total Beds</h3>
              <div className="metric-value">{data.total_beds}</div>
            </div>
            <div className="metric-card">
              <h3>Occupied Beds</h3>
              <div className="metric-value text-green">{data.occupied_beds}</div>
            </div>
            <div className="metric-card">
              <h3>Vacant Beds</h3>
              <div className="metric-value text-blue">{data.vacant_beds}</div>
            </div>
            <div className="metric-card">
              <h3>Utilization</h3>
              <div className="metric-value">{(data.utilization * 100).toFixed(1)}%</div>
            </div>
            <div className="metric-card">
              <h3>Underutilized Rooms</h3>
              <div className="metric-value text-orange">{data.underutilized_rooms}</div>
            </div>
          </div>
        ) : (
          <div className="empty-state">Failed to load dashboard data.</div>
        )}
      </main>
    </div>
  );
}

export default Dashboard;
