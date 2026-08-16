import React, { useState, useEffect } from 'react';
import api from '../api';
import { useAuth } from '../context/AuthContext';
import { Link, useNavigate } from 'react-router-dom';
import './Dashboard.css'; // Reuse layout styles
import './Allocations.css';

function Allocations() {
  const [batches, setBatches] = useState([]);
  const [runs, setRuns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [drafting, setDrafting] = useState(false);
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [batchesRes, runsRes] = await Promise.all([
          api.get('allocations/batches/'),
          api.get('allocations/runs/')
        ]);
        setBatches(batchesRes.data);
        setRuns(runsRes.data);
      } catch (e) {
        console.error("Allocations error", e);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const handleCreateDraft = async (batchId) => {
    if (!window.confirm("Are you sure you want to run the optimizer to create a new draft?")) return;
    setDrafting(true);
    try {
      const res = await api.post('allocations/runs/draft/', { batch_id: batchId });
      navigate(`/allocations/${res.data.id}`);
    } catch (e) {
      alert("Error creating draft: " + (e.response?.data?.error || e.message));
    } finally {
      setDrafting(false);
    }
  };

  if (loading) return <div className="loader">Loading Allocations...</div>;

  return (
    <div className="premium-dashboard-container">
      <header className="page-header" style={{marginBottom: '24px'}}>
        <h2>Allocation Management</h2>
        <p className="text-secondary">View and manage hostel application batches and OR-Tools optimization runs.</p>
      </header>

      <section className="section" style={{marginBottom: '32px'}}>
        <h3>Application Batches</h3>
        <div className="premium-kpi-grid" style={{gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))'}}>
          {batches.map(batch => (
            <div key={batch.id} className="side-panel-card" style={{padding: '20px'}}>
              <div>
                <strong style={{fontSize: '1.1rem'}}>{batch.name}</strong>
                <div style={{fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '4px'}}>{batch.start_date} to {batch.end_date}</div>
              </div>
              {user?.role === 'ADMIN' && (
                <button 
                  className="btn-run-allocator" 
                  onClick={() => handleCreateDraft(batch.id)}
                  disabled={drafting}
                  style={{marginTop: '16px'}}
                >
                  {drafting ? 'Optimizing...' : 'Run Optimizer'}
                </button>
              )}
            </div>
          ))}
          {batches.length === 0 && <div className="empty-state-premium">No active batches found.</div>}
        </div>
      </section>

      <section className="section">
        <h3>Recent Allocation Runs</h3>
        <div className="side-panel-card" style={{padding: 0, overflow: 'hidden'}}>
          <table className="data-table" style={{width: '100%', borderCollapse: 'collapse', textAlign: 'left'}}>
            <thead>
              <tr style={{backgroundColor: 'var(--bg-panel)', borderBottom: '1px solid var(--border-subtle)'}}>
                <th style={{padding: '12px 16px', color: 'var(--text-secondary)'}}>ID</th>
                <th style={{padding: '12px 16px', color: 'var(--text-secondary)'}}>Run Date</th>
                <th style={{padding: '12px 16px', color: 'var(--text-secondary)'}}>Status</th>
                <th style={{padding: '12px 16px', color: 'var(--text-secondary)'}}>Fairness</th>
                <th style={{padding: '12px 16px', color: 'var(--text-secondary)'}}>Action</th>
              </tr>
            </thead>
            <tbody>
              {runs.map(run => (
                <tr key={run.id} style={{borderBottom: '1px solid var(--border-subtle)'}}>
                  <td style={{padding: '12px 16px'}}>#{run.id}</td>
                  <td style={{padding: '12px 16px'}}>{new Date(run.run_date).toLocaleString()}</td>
                  <td style={{padding: '12px 16px'}}>
                    <span className={`status-indicator dot-${run.status === 'COMMITTED' ? 'success' : run.status === 'APPROVED' ? 'info' : 'warning'}`}></span>
                    <span style={{marginLeft: '8px', fontSize: '0.85rem', fontWeight: 600}}>{run.status}</span>
                  </td>
                  <td style={{padding: '12px 16px'}}>{run.fairness_score.toFixed(2)}</td>
                  <td style={{padding: '12px 16px'}}>
                    <Link to={`/allocations/${run.id}`} className="btn-run-allocator" style={{padding: '6px 12px', fontSize: '0.8rem', width: 'auto', display: 'inline-block', margin: 0, background: 'transparent', border: '1px solid var(--color-primary)', color: 'var(--color-primary)', boxShadow: 'none'}}>View Details</Link>
                  </td>
                </tr>
              ))}
              {runs.length === 0 && (
                <tr>
                  <td colSpan="5" className="empty-state-premium" style={{border: 'none'}}>No allocation runs exist yet.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

export default Allocations;
