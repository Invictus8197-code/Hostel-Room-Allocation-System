import React, { useState, useEffect } from 'react';
import api from '../api';
import { useAuth } from '../context/AuthContext';
import { Link } from 'react-router-dom';
import './Dashboard.css';
import './Allocations.css';

function Simulation() {
  const [batches, setBatches] = useState([]);
  const [selectedBatchId, setSelectedBatchId] = useState('');
  const [unavailableBedIds, setUnavailableBedIds] = useState('');
  const [subsetStudentIds, setSubsetStudentIds] = useState('');
  
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const { user, logout } = useAuth();

  useEffect(() => {
    const fetchBatches = async () => {
      try {
        const res = await api.get('allocations/batches/');
        setBatches(res.data);
        if (res.data.length > 0) {
          setSelectedBatchId(res.data[0].id);
        }
      } catch (e) {
        console.error("Simulation batches error", e);
      }
    };
    fetchBatches();
  }, []);

  const handleSimulate = async (e) => {
    e.preventDefault();
    if (!selectedBatchId) return;
    
    setLoading(true);
    setError('');
    setResult(null);
    
    // Parse scenario
    const scenario = {};
    if (unavailableBedIds.trim()) {
      scenario.unavailable_bed_ids = unavailableBedIds.split(',').map(s => parseInt(s.trim())).filter(n => !isNaN(n));
    }
    if (subsetStudentIds.trim()) {
      scenario.subset_student_ids = subsetStudentIds.split(',').map(s => parseInt(s.trim())).filter(n => !isNaN(n));
    }

    try {
      const res = await api.post('simulations/run/', { batch_id: selectedBatchId, scenario });
      setResult(res.data);
    } catch (e) {
      setError(e.response?.data?.error || e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="layout">
      <aside className="sidebar">
        <h2 className="brand">Smart Hostel</h2>
        <nav className="nav-menu">
          <Link to="/dashboard" className="nav-item">Dashboard</Link>
          <Link to="/allocations" className="nav-item">Allocations</Link>
          <Link to="/analytics" className="nav-item">Analytics</Link>
          <Link to="/simulation" className="nav-item active">Simulation</Link>
        </nav>
        <div className="user-profile">
          <div>{user?.username} ({user?.role})</div>
          <button onClick={logout} className="logout-btn">Logout</button>
        </div>
      </aside>
      
      <main className="main-content">
        <header className="page-header">
          <h1>What-If Simulation Engine</h1>
          <p className="text-gray" style={{marginTop: '5px'}}>
            Evaluate hypothetical scenarios without modifying production allocations.
          </p>
        </header>

        <div style={{display: 'flex', gap: '30px', alignItems: 'flex-start'}}>
          <section className="section" style={{flex: '0 0 350px'}}>
            <h2>Configure Scenario</h2>
            <form onSubmit={handleSimulate}>
              <div className="form-group">
                <label>Target Batch</label>
                <select 
                  className="form-control" 
                  style={{width: '100%', padding: '10px', borderRadius: '6px', border: '1px solid #d1d5db'}}
                  value={selectedBatchId} 
                  onChange={e => setSelectedBatchId(e.target.value)}
                  required
                >
                  <option value="">Select a batch...</option>
                  {batches.map(b => (
                    <option key={b.id} value={b.id}>{b.name} ({b.start_date})</option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label>Unavailable Bed IDs (comma separated)</label>
                <input 
                  type="text" 
                  placeholder="e.g. 1, 4, 15"
                  value={unavailableBedIds} 
                  onChange={e => setUnavailableBedIds(e.target.value)} 
                />
                <small className="text-gray" style={{display: 'block', marginTop: '5px'}}>Simulate beds under maintenance.</small>
              </div>

              <div className="form-group">
                <label>Subset Student IDs (comma separated)</label>
                <input 
                  type="text" 
                  placeholder="e.g. 101, 102"
                  value={subsetStudentIds} 
                  onChange={e => setSubsetStudentIds(e.target.value)} 
                />
                <small className="text-gray" style={{display: 'block', marginTop: '5px'}}>Simulate allocation for a specific subset.</small>
              </div>

              <button type="submit" className="btn btn-primary" style={{width: '100%', marginTop: '10px'}} disabled={loading}>
                {loading ? 'Running Simulation...' : 'Run Simulation'}
              </button>
            </form>
            {error && <div className="conflict-alert" style={{marginTop: '20px'}}>{error}</div>}
          </section>

          {result && (
            <section className="section" style={{flex: '1'}}>
              <h2 style={{color: '#ea580c'}}>Simulation Results <span className="status-badge status-draft">HYPOTHETICAL</span></h2>
              <div style={{background: '#fef3c7', color: '#92400e', padding: '12px', borderRadius: '6px', marginBottom: '20px', fontSize: '0.9rem'}}>
                <strong>Note:</strong> These results are strictly hypothetical and have not modified any real allocation data.
              </div>

              <table className="data-table" style={{marginBottom: '30px'}}>
                <thead>
                  <tr>
                    <th>Metric</th>
                    <th>Current Baseline</th>
                    <th>Simulated</th>
                    <th>Difference</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td><strong>Fairness Score</strong></td>
                    <td>{result.current?.fairness_score?.toFixed(2) || 'N/A'}</td>
                    <td>{result.simulated?.fairness_score?.toFixed(2) || 'N/A'}</td>
                    <td>
                      {result.difference?.fairness_score > 0 ? (
                        <span className="text-green">+{result.difference.fairness_score.toFixed(2)}</span>
                      ) : (
                        <span className="text-red">{result.difference?.fairness_score?.toFixed(2) || 0}</span>
                      )}
                    </td>
                  </tr>
                  <tr>
                    <td><strong>Allocated Students</strong></td>
                    <td>{result.current?.allocated || 0}</td>
                    <td>{result.simulated?.allocated || 0}</td>
                    <td>
                      {result.difference?.allocated > 0 ? (
                        <span className="text-green">+{result.difference.allocated}</span>
                      ) : (
                        <span className="text-red">{result.difference?.allocated || 0}</span>
                      )}
                    </td>
                  </tr>
                  <tr>
                    <td><strong>Unallocated Students</strong></td>
                    <td>{result.current?.unallocated || 0}</td>
                    <td>{result.simulated?.unallocated || 0}</td>
                    <td>
                      {result.difference?.unallocated > 0 ? (
                        <span className="text-red">+{result.difference.unallocated}</span>
                      ) : (
                        <span className="text-green">{result.difference?.unallocated || 0}</span>
                      )}
                    </td>
                  </tr>
                </tbody>
              </table>

              <h3>Simulated Allocations Output</h3>
              <div style={{maxHeight: '300px', overflowY: 'auto', background: '#f8fafc', padding: '15px', borderRadius: '6px', border: '1px solid #e2e8f0'}}>
                <pre style={{margin: 0, fontSize: '0.85rem', color: '#334155'}}>
                  {JSON.stringify(result.allocation?.student_bed_assignments, null, 2)}
                </pre>
              </div>
            </section>
          )}
        </div>
      </main>
    </div>
  );
}

export default Simulation;
