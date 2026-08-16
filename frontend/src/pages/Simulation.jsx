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
    <div className="premium-dashboard-container">
      <header className="page-header" style={{marginBottom: '24px'}}>
        <h2>What-If Simulation Engine</h2>
        <p className="text-secondary" style={{marginTop: '5px'}}>
          Evaluate hypothetical scenarios without modifying production allocations.
        </p>
      </header>

      <div style={{display: 'flex', gap: '30px', alignItems: 'flex-start', flexWrap: 'wrap'}}>
        <section className="section" style={{flex: '1 1 350px'}}>
          <div className="side-panel-card" style={{padding: '24px'}}>
            <h3 style={{marginBottom: '20px'}}>Configure Scenario</h3>
            <form onSubmit={handleSimulate}>
              <div className="form-group" style={{marginBottom: '20px'}}>
                <label style={{color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '8px', display: 'block'}}>Target Batch</label>
                <select 
                  className="form-control" 
                  style={{width: '100%', padding: '10px 12px', borderRadius: '8px', border: '1px solid var(--border-subtle)', backgroundColor: 'var(--bg-base)', color: 'var(--text-primary)'}}
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

              <div className="form-group" style={{marginBottom: '20px'}}>
                <label style={{color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '8px', display: 'block'}}>Unavailable Bed IDs (comma separated)</label>
                <input 
                  type="text" 
                  placeholder="e.g. 1, 4, 15"
                  value={unavailableBedIds} 
                  onChange={e => setUnavailableBedIds(e.target.value)} 
                  style={{width: '100%', padding: '10px 12px', borderRadius: '8px', border: '1px solid var(--border-subtle)', backgroundColor: 'var(--bg-base)', color: 'var(--text-primary)'}}
                />
                <small className="text-secondary" style={{display: 'block', marginTop: '6px', fontSize: '0.75rem'}}>Simulate beds under maintenance.</small>
              </div>

              <div className="form-group" style={{marginBottom: '24px'}}>
                <label style={{color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '8px', display: 'block'}}>Subset Student IDs (comma separated)</label>
                <input 
                  type="text" 
                  placeholder="e.g. 101, 102"
                  value={subsetStudentIds} 
                  onChange={e => setSubsetStudentIds(e.target.value)} 
                  style={{width: '100%', padding: '10px 12px', borderRadius: '8px', border: '1px solid var(--border-subtle)', backgroundColor: 'var(--bg-base)', color: 'var(--text-primary)'}}
                />
                <small className="text-secondary" style={{display: 'block', marginTop: '6px', fontSize: '0.75rem'}}>Simulate allocation for a specific subset.</small>
              </div>

              <button type="submit" className="btn-run-allocator" style={{width: '100%', marginTop: '10px'}} disabled={loading}>
                {loading ? 'Running Simulation...' : 'Run Simulation'}
              </button>
            </form>
            {error && (
              <div className="conflict-alert" style={{backgroundColor: 'var(--color-critical-bg)', borderLeft: '4px solid var(--color-critical)', color: 'var(--color-critical)', padding: '12px', marginTop: '20px', borderRadius: '4px'}}>
                {error}
              </div>
            )}
          </div>
        </section>

        {result && (
          <section className="section" style={{flex: '2 1 600px'}}>
            <div className="side-panel-card" style={{padding: '24px'}}>
              <h3 style={{color: 'var(--color-warning)', display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px'}}>
                Simulation Results 
                <span style={{fontSize: '0.7rem', padding: '4px 8px', borderRadius: '4px', backgroundColor: 'var(--color-warning-bg)', color: 'var(--color-warning)', letterSpacing: '0.05em'}}>HYPOTHETICAL</span>
              </h3>
              
              <div style={{background: 'var(--color-warning-bg)', color: 'var(--color-warning)', padding: '12px 16px', borderRadius: '8px', marginBottom: '24px', fontSize: '0.85rem', border: '1px solid rgba(245, 158, 11, 0.2)'}}>
                <strong>Note:</strong> These results are strictly hypothetical and have not modified any real allocation data.
              </div>

              <table className="data-table" style={{width: '100%', borderCollapse: 'collapse', textAlign: 'left', marginBottom: '32px'}}>
                <thead>
                  <tr style={{borderBottom: '1px solid var(--border-subtle)'}}>
                    <th style={{padding: '12px 8px', color: 'var(--text-secondary)'}}>Metric</th>
                    <th style={{padding: '12px 8px', color: 'var(--text-secondary)'}}>Current Baseline</th>
                    <th style={{padding: '12px 8px', color: 'var(--text-secondary)'}}>Simulated</th>
                    <th style={{padding: '12px 8px', color: 'var(--text-secondary)'}}>Difference</th>
                  </tr>
                </thead>
                <tbody>
                  <tr style={{borderBottom: '1px solid var(--border-subtle)'}}>
                    <td style={{padding: '12px 8px'}}><strong>Fairness Score</strong></td>
                    <td style={{padding: '12px 8px'}}>{result.current?.fairness_score?.toFixed(2) || 'N/A'}</td>
                    <td style={{padding: '12px 8px'}}>{result.simulated?.fairness_score?.toFixed(2) || 'N/A'}</td>
                    <td style={{padding: '12px 8px'}}>
                      {result.difference?.fairness_score > 0 ? (
                        <span className="text-green">+{result.difference.fairness_score.toFixed(2)}</span>
                      ) : (
                        <span className="text-red">{result.difference?.fairness_score?.toFixed(2) || 0}</span>
                      )}
                    </td>
                  </tr>
                  <tr style={{borderBottom: '1px solid var(--border-subtle)'}}>
                    <td style={{padding: '12px 8px'}}><strong>Allocated Students</strong></td>
                    <td style={{padding: '12px 8px'}}>{result.current?.allocated || 0}</td>
                    <td style={{padding: '12px 8px'}}>{result.simulated?.allocated || 0}</td>
                    <td style={{padding: '12px 8px'}}>
                      {result.difference?.allocated > 0 ? (
                        <span className="text-green">+{result.difference.allocated}</span>
                      ) : (
                        <span className="text-red">{result.difference?.allocated || 0}</span>
                      )}
                    </td>
                  </tr>
                  <tr style={{borderBottom: '1px solid var(--border-subtle)'}}>
                    <td style={{padding: '12px 8px'}}><strong>Unallocated Students</strong></td>
                    <td style={{padding: '12px 8px'}}>{result.current?.unallocated || 0}</td>
                    <td style={{padding: '12px 8px'}}>{result.simulated?.unallocated || 0}</td>
                    <td style={{padding: '12px 8px'}}>
                      {result.difference?.unallocated > 0 ? (
                        <span className="text-red">+{result.difference.unallocated}</span>
                      ) : (
                        <span className="text-green">{result.difference?.unallocated || 0}</span>
                      )}
                    </td>
                  </tr>
                </tbody>
              </table>

              <h3 style={{marginBottom: '16px'}}>Simulated Allocations Output</h3>
              <div style={{maxHeight: '300px', overflowY: 'auto', background: 'var(--bg-base)', padding: '16px', borderRadius: '8px', border: '1px solid var(--border-subtle)'}}>
                <pre style={{margin: 0, fontSize: '0.85rem', color: 'var(--text-secondary)'}}>
                  {JSON.stringify(result.allocation?.student_bed_assignments, null, 2)}
                </pre>
              </div>
            </div>
          </section>
        )}
      </div>
    </div>
  );
}

export default Simulation;
