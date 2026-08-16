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
    <div className="premium-dashboard-container">
      <header className="page-header" style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px'}}>
        <div>
          <Link to="/allocations" className="text-secondary" style={{textDecoration: 'none', marginBottom: '10px', display: 'inline-block'}}>← Back to Allocations</Link>
          <h2>Run #{run.id} Details</h2>
        </div>
        <div style={{display: 'flex', gap: '12px', alignItems: 'center'}}>
          <span className={`status-indicator dot-${run.status === 'COMMITTED' ? 'success' : run.status === 'APPROVED' ? 'info' : 'warning'}`}></span>
          <span style={{fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-primary)'}}>{run.status}</span>
          {user?.role === 'ADMIN' && run.status === 'DRAFT' && (
            <button className="btn-run-allocator" onClick={() => handleAction('approve')} disabled={actionLoading} style={{marginTop: 0, width: 'auto', padding: '8px 16px', background: 'var(--color-info)'}}>
              Approve Run
            </button>
          )}
          {user?.role === 'ADMIN' && run.status === 'APPROVED' && (
            <button className="btn-run-allocator" onClick={() => handleAction('commit')} disabled={actionLoading} style={{marginTop: 0, width: 'auto', padding: '8px 16px', background: 'var(--color-success)'}}>
              Commit Allocations
            </button>
          )}
        </div>
      </header>

      {conflictError && (
        <div className="conflict-alert" style={{backgroundColor: 'var(--color-critical-bg)', borderLeft: '4px solid var(--color-critical)', color: 'var(--color-critical)', padding: '16px', marginBottom: '24px', borderRadius: '4px'}}>
          <strong>Conflict Error:</strong> {conflictError}
          <button className="btn-run-allocator" style={{marginLeft: '15px', padding: '4px 12px', width: 'auto', background: 'transparent', border: '1px solid var(--color-critical)', color: 'var(--color-critical)', boxShadow: 'none', fontSize: '0.8rem'}} onClick={fetchRun}>Refresh Data</button>
        </div>
      )}

      <div className="premium-kpi-grid">
        <div className="side-panel-card" style={{padding: '24px'}}>
          <h3 style={{color: 'var(--text-secondary)', fontSize: '0.9rem', textTransform: 'uppercase', letterSpacing: '0.05em'}}>Fairness Score</h3>
          <div style={{fontSize: '2rem', fontWeight: 700, color: 'var(--text-primary)', marginTop: '8px'}}>{run.fairness_score.toFixed(2)}</div>
        </div>
        <div className="side-panel-card" style={{padding: '24px'}}>
          <h3 style={{color: 'var(--text-secondary)', fontSize: '0.9rem', textTransform: 'uppercase', letterSpacing: '0.05em'}}>Total Allocated</h3>
          <div style={{fontSize: '2rem', fontWeight: 700, color: 'var(--color-success)', marginTop: '8px'}}>{run.summary_data.totals?.allocated || 0}</div>
        </div>
        <div className="side-panel-card" style={{padding: '24px'}}>
          <h3 style={{color: 'var(--text-secondary)', fontSize: '0.9rem', textTransform: 'uppercase', letterSpacing: '0.05em'}}>Unallocated</h3>
          <div style={{fontSize: '2rem', fontWeight: 700, color: 'var(--color-critical)', marginTop: '8px'}}>{run.summary_data.totals?.unallocated || 0}</div>
        </div>
      </div>

      <section className="section" style={{marginTop: '32px'}}>
        <h3>Student Allocations ({run.allocations?.length || 0})</h3>
        <div className="side-panel-card" style={{padding: 0, overflow: 'hidden'}}>
          <table className="data-table" style={{width: '100%', borderCollapse: 'collapse', textAlign: 'left'}}>
            <thead>
              <tr style={{backgroundColor: 'var(--bg-panel)', borderBottom: '1px solid var(--border-subtle)'}}>
                <th style={{padding: '12px 16px', color: 'var(--text-secondary)'}}>Reg No</th>
                <th style={{padding: '12px 16px', color: 'var(--text-secondary)'}}>Name</th>
                <th style={{padding: '12px 16px', color: 'var(--text-secondary)'}}>Hostel</th>
                <th style={{padding: '12px 16px', color: 'var(--text-secondary)'}}>Room</th>
                <th style={{padding: '12px 16px', color: 'var(--text-secondary)'}}>Bed</th>
                <th style={{padding: '12px 16px', color: 'var(--text-secondary)'}}>Gender</th>
              </tr>
            </thead>
            <tbody>
              {run.allocations?.map(alloc => (
                <tr key={alloc.id} style={{borderBottom: '1px solid var(--border-subtle)'}}>
                  <td style={{padding: '12px 16px'}}>{alloc.student.registration_number}</td>
                  <td style={{padding: '12px 16px'}}>{alloc.student.full_name || alloc.student.username}</td>
                  <td style={{padding: '12px 16px'}}>{alloc.hostel_name}</td>
                  <td style={{padding: '12px 16px'}}>{alloc.room_number}</td>
                  <td style={{padding: '12px 16px'}}>{alloc.bed_number}</td>
                  <td style={{padding: '12px 16px'}}>{alloc.student.gender}</td>
                </tr>
              ))}
              {(!run.allocations || run.allocations.length === 0) && (
                <tr>
                  <td colSpan="6" className="empty-state-premium" style={{border: 'none'}}>No allocations in this run.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

export default AllocationDetail;
