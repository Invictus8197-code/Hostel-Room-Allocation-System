import React, { useState } from 'react';
import MetricCard from '../components/common/MetricCard';
import './Dashboard.css';

function StudentDashboard() {
  const [swapRequested, setSwapRequested] = useState(false);

  return (
    <div className="premium-dashboard-container">
      <div className="premium-kpi-grid">
        <MetricCard 
          title="My Allocation" 
          value="B-Block, 204" 
          subtitle="Allocated for Fall 2026" 
          icon={<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path></svg>} 
          theme="success" 
        />
        <MetricCard 
          title="Active Complaints" 
          value="0" 
          subtitle="All issues resolved" 
          icon={<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>} 
          theme="primary" 
        />
      </div>

      <div className="dashboard-main-grid" style={{ gridTemplateColumns: '1fr 1fr' }}>
        <div className="side-panel-card">
          <div className="panel-header">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="17 1 21 5 17 9"></polyline><path d="M3 11V9a4 4 0 0 1 4-4h14"></path><polyline points="7 23 3 19 7 15"></polyline><path d="M21 13v2a4 4 0 0 1-4 4H3"></path></svg>
            <h3>Intelligent Room Swap System</h3>
          </div>
          <div className="panel-body">
            <p style={{fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '24px'}}>
              Request a room swap with another student. If they accept, the AI Optimizer will automatically execute the cycle without Warden intervention.
            </p>
            {!swapRequested ? (
              <div style={{display: 'flex', gap: '12px'}}>
                <input type="text" placeholder="Target Registration Number" style={{flex: 1, padding: '12px', borderRadius: '8px', border: '1px solid var(--border-subtle)', backgroundColor: 'var(--bg-panel)', color: 'var(--text-primary)'}} />
                <button className="btn-run-allocator" style={{marginTop: 0, padding: '0 24px', width: 'auto'}} onClick={() => setSwapRequested(true)}>Initiate</button>
              </div>
            ) : (
              <div className="conflict-alert warning">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
                <div>
                  <strong>Swap Request Pending</strong>
                  <p>Waiting for the other student to approve the mutual cycle.</p>
                  <button onClick={() => setSwapRequested(false)} style={{marginTop: '12px', background: 'none', border: '1px solid var(--color-warning)', color: 'var(--color-warning)', padding: '6px 12px', borderRadius: '6px', cursor: 'pointer', fontSize: '0.75rem'}}>Cancel Request</button>
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="side-panel-card">
          <div className="panel-header">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>
            <h3>Mutual Roommate Pairing</h3>
          </div>
          <div className="panel-body">
            <p style={{fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '24px'}}>
              Lock in a mutual request. If you both request each other before the next Allocation Batch, the OR-Tools AI will guarantee you are placed in the same room.
            </p>
            <div style={{display: 'flex', gap: '12px'}}>
              <input type="text" placeholder="Friend's Registration Number" style={{flex: 1, padding: '12px', borderRadius: '8px', border: '1px solid var(--border-subtle)', backgroundColor: 'var(--bg-panel)', color: 'var(--text-primary)'}} />
              <button className="btn-run-allocator" style={{marginTop: 0, padding: '0 24px', width: 'auto', background: 'transparent', border: '1px solid var(--color-primary)', color: 'var(--color-primary)', boxShadow: 'none'}}>Send Request</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default StudentDashboard;
