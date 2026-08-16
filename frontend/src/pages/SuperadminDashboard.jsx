import React, { useState, useEffect } from 'react';
import api from '../api';
import MetricCard from '../components/common/MetricCard';
import './Dashboard.css';

function SuperadminDashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [optimizerStrictness, setOptimizerStrictness] = useState(50);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await api.get('dashboard/summary/');
        setData(res.data);
      } catch (e) {
        console.error("Superadmin Dashboard error", e);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) return <div className="loader premium-loader">Loading system data...</div>;
  if (!data) return <div className="loader premium-loader" style={{color: 'var(--color-critical)'}}>Failed to load dashboard data. Check API logs.</div>;

  return (
    <div className="premium-dashboard-container">
      {/* Top KPI Cards */}
      <div className="premium-kpi-grid">
        <MetricCard 
          title="System Occupancy" 
          value={`${(data.utilization * 100).toFixed(0)}%`} 
          icon={<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path><polyline points="9 22 9 12 15 12 15 22"></polyline></svg>} 
          theme="primary" 
        />
        <MetricCard 
          title="Global Students" 
          value={data.total_students} 
          subtitle={`${data.allocated_students} allocated`} 
          icon={<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>} 
          theme="info" 
        />
        <MetricCard 
          title="Total System Beds" 
          value={data.total_beds} 
          subtitle={`${data.vacant_beds} vacant globally`}
          icon={<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"></path><line x1="7" y1="7" x2="7.01" y2="7"></line></svg>} 
          theme="success" 
        />
        <MetricCard 
          title="Global Conflicts" 
          value={data.unallocated_students} 
          subtitle="Require override" 
          icon={<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>} 
          theme="critical" 
        />
      </div>

      <div className="dashboard-main-grid">
        {/* Warden Access Control */}
        <div className="floorplan-section">
          <div className="section-header">
            <div className="section-title">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>
              <h2>Warden Access Control</h2>
            </div>
            <p style={{fontSize: '0.85rem', color: 'var(--text-secondary)', margin: 0}}>Enforce strict 5-hostel limits for regional Wardens.</p>
          </div>
          
          <div className="warden-list-placeholder" style={{display: 'flex', flexDirection: 'column', gap: '16px', marginTop: '16px'}}>
            <div className="side-panel-card" style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
              <div>
                <strong style={{display: 'block', marginBottom: '4px'}}>Warden: admin</strong>
                <span style={{fontSize: '0.8rem', color: 'var(--text-muted)'}}>Hostel A • Hostel C • Hostel D</span>
              </div>
              <div style={{display: 'flex', alignItems: 'center', gap: '16px'}}>
                <span className="badge-premium badge-success" style={{padding: '4px 10px', borderRadius: '12px', fontSize: '0.75rem', backgroundColor: 'var(--color-success-bg)', color: 'var(--color-success)'}}>3/5 Hostels Assigned</span>
                <button className="btn-run-allocator" style={{marginTop: 0, padding: '8px 16px', width: 'auto'}}>Manage</button>
              </div>
            </div>
          </div>
        </div>

        {/* Right Side Panel - Optimizer */}
        <div className="side-panel-section">
          <div className="side-panel-card optimizer-card">
            <div className="panel-header">
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="4 14 10 14 10 20"></polyline><polyline points="20 10 14 10 14 4"></polyline><line x1="14" y1="10" x2="21" y2="3"></line><line x1="3" y1="21" x2="10" y2="14"></line></svg>
              <h3>Global AI Configuration</h3>
            </div>
            <div className="panel-body">
              <p style={{fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '24px'}}>Adjust the constraints and preference weightings of the Google OR-Tools engine for all hostels.</p>
              
              <div className="slider-container" style={{marginBottom: '24px'}}>
                <label style={{display: 'block', fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '12px'}}>Preference Priority vs. Capacity Strictness</label>
                <input 
                  type="range" 
                  min="1" 
                  max="100" 
                  value={optimizerStrictness} 
                  onChange={(e) => setOptimizerStrictness(e.target.value)} 
                  style={{width: '100%', cursor: 'pointer', accentColor: 'var(--color-primary)'}}
                />
                <div style={{display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '8px', fontWeight: 600}}>
                  <span>Max Happiness</span>
                  <span>Max Capacity</span>
                </div>
              </div>
              
              <button className="btn-run-allocator">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>
                Update AI Engine Parameters
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default SuperadminDashboard;
