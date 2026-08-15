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
        <header className="page-header">
          <h1>Allocation Management</h1>
        </header>

        <section className="section">
          <h2>Application Batches</h2>
          <div className="card-list">
            {batches.map(batch => (
              <div key={batch.id} className="list-card">
                <div>
                  <strong>{batch.name}</strong>
                  <div className="text-sm text-gray">{batch.start_date} to {batch.end_date}</div>
                </div>
                {user?.role === 'ADMIN' && (
                  <button 
                    className="btn btn-primary" 
                    onClick={() => handleCreateDraft(batch.id)}
                    disabled={drafting}
                  >
                    Run Optimizer
                  </button>
                )}
              </div>
            ))}
            {batches.length === 0 && <div className="empty-msg">No active batches found.</div>}
          </div>
        </section>

        <section className="section mt-40">
          <h2>Recent Allocation Runs</h2>
          <table className="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Run Date</th>
                <th>Status</th>
                <th>Fairness</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {runs.map(run => (
                <tr key={run.id}>
                  <td>#{run.id}</td>
                  <td>{new Date(run.run_date).toLocaleString()}</td>
                  <td>
                    <span className={`status-badge status-${run.status.toLowerCase()}`}>
                      {run.status}
                    </span>
                  </td>
                  <td>{run.fairness_score.toFixed(2)}</td>
                  <td>
                    <Link to={`/allocations/${run.id}`} className="btn btn-secondary btn-sm">View Details</Link>
                  </td>
                </tr>
              ))}
              {runs.length === 0 && (
                <tr>
                  <td colSpan="5" className="empty-msg">No allocation runs exist yet.</td>
                </tr>
              )}
            </tbody>
          </table>
        </section>
      </main>
    </div>
  );
}

export default Allocations;
