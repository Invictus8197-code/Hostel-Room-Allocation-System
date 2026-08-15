import React, { useState, useEffect } from 'react';
import api from '../api';
import { useAuth } from '../context/AuthContext';
import { useParams, Link, useNavigate } from 'react-router-dom';
import './Dashboard.css'; 
import './Allocations.css';

function AllocationDetail() {
  const { id } = useParams();
  const [run, setRun] = useState(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [conflictError, setConflictError] = useState('');
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const fetchRun = async () => {
    try {
      const res = await api.get(`allocations/runs/${id}/`);
      setRun(res.data);
      setConflictError('');
    } catch (e) {
      console.error("Allocation run error", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRun();
  }, [id]);

  const handleAction = async (action) => {
    if (!window.confirm(`Are you sure you want to ${action} this run?`)) return;
    setActionLoading(true);
    setConflictError('');
    try {
      const res = await api.post(`allocations/runs/${id}/${action}/`);
      setRun(res.data);
    } catch (e) {
      if (e.response?.status === 409) {
        setConflictError(e.response.data.error || "This run is stale or a conflict occurred. Please refresh.");
      } else {
        alert(`Error: ${e.response?.data?.error || e.message}`);
      }
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) return <div className="loader">Loading Run Details...</div>;
  if (!run) return <div className="loader">Run not found.</div>;

  return (
    <div className="layout">
      <aside className="sidebar">
        <h2 className="brand">Smart Hostel</h2>
        <nav className="nav-menu">
          <Link to="/dashboard" className="nav-item">Dashboard</Link>
          <Link to="/allocations" className="nav-item active">Allocations</Link>
          <Link to="/analytics" className="nav-item">Analytics</Link>
          <Link to="/simulation" className="nav-item">Simulation</Link>
        </nav>
        <div className="user-profile">
          <div>{user?.username} ({user?.role})</div>
          <button onClick={logout} className="logout-btn">Logout</button>
        </div>
      </aside>
      
      <main className="main-content">
        <header className="page-header" style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
          <div>
            <Link to="/allocations" className="text-gray" style={{textDecoration: 'none', marginBottom: '10px', display: 'inline-block'}}>← Back to Allocations</Link>
            <h1>Run #{run.id} Details</h1>
          </div>
          <div style={{display: 'flex', gap: '10px', alignItems: 'center'}}>
            <span className={`status-badge status-${run.status.toLowerCase()}`}>{run.status}</span>
            {user?.role === 'ADMIN' && run.status === 'DRAFT' && (
              <button className="btn btn-primary" onClick={() => handleAction('approve')} disabled={actionLoading}>
                Approve Run
              </button>
            )}
            {user?.role === 'ADMIN' && run.status === 'APPROVED' && (
              <button className="btn btn-success" onClick={() => handleAction('commit')} disabled={actionLoading}>
                Commit Allocations
              </button>
            )}
          </div>
        </header>

        {conflictError && (
          <div className="conflict-alert">
            <strong>Conflict Error:</strong> {conflictError}
            <button className="btn btn-secondary btn-sm" style={{marginLeft: '15px'}} onClick={fetchRun}>Refresh Data</button>
          </div>
        )}

        <div className="metrics-grid">
          <div className="metric-card">
            <h3>Fairness Score</h3>
            <div className="metric-value">{run.fairness_score.toFixed(2)}</div>
          </div>
          <div className="metric-card">
            <h3>Total Allocated</h3>
            <div className="metric-value text-green">{run.summary_data.totals?.allocated}</div>
          </div>
          <div className="metric-card">
            <h3>Unallocated</h3>
            <div className="metric-value text-red">{run.summary_data.totals?.unallocated}</div>
          </div>
        </div>

        <section className="section mt-40">
          <h2>Student Allocations ({run.allocations?.length})</h2>
          <table className="data-table">
            <thead>
              <tr>
                <th>Reg No</th>
                <th>Name</th>
                <th>Hostel</th>
                <th>Room</th>
                <th>Bed</th>
                <th>Gender</th>
              </tr>
            </thead>
            <tbody>
              {run.allocations?.map(alloc => (
                <tr key={alloc.id}>
                  <td>{alloc.student.registration_number}</td>
                  <td>{alloc.student.full_name || alloc.student.username}</td>
                  <td>{alloc.hostel_name}</td>
                  <td>{alloc.room_number}</td>
                  <td>{alloc.bed_number}</td>
                  <td>{alloc.student.gender}</td>
                </tr>
              ))}
              {(!run.allocations || run.allocations.length === 0) && (
                <tr>
                  <td colSpan="6" className="empty-msg">No allocations in this run.</td>
                </tr>
              )}
            </tbody>
          </table>
        </section>
      </main>
    </div>
  );
}

export default AllocationDetail;
