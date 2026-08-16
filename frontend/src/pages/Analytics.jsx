import React, { useState, useEffect } from 'react';
import api from '../api';
import { useAuth } from '../context/AuthContext';
import { Link } from 'react-router-dom';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Bar } from 'react-chartjs-2';
import './Dashboard.css';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
);

function Analytics() {
  const [startDate, setStartDate] = useState('2026-09-01');
  const [endDate, setEndDate] = useState('2027-05-31');
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const { user, logout } = useAuth();

  const fetchAnalytics = async () => {
    setLoading(true);
    try {
      const res = await api.get(`analytics/hostels/?start_date=${startDate}&end_date=${endDate}`);
      setData(res.data);
    } catch (e) {
      console.error("Analytics error", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, []);

  const handleApply = (e) => {
    e.preventDefault();
    fetchAnalytics();
  };

  const chartData = {
    labels: data.map(d => d.hostel_name),
    datasets: [
      {
        label: 'Occupied Beds',
        data: data.map(d => d.occupied_beds),
        backgroundColor: 'rgba(37, 99, 235, 0.8)',
      },
      {
        label: 'Vacant Beds',
        data: data.map(d => d.vacant_beds),
        backgroundColor: 'rgba(148, 163, 184, 0.5)',
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    scales: {
      x: { 
        stacked: true,
        ticks: { color: '#94A3B8' },
        grid: { color: '#334155' }
      },
      y: { 
        stacked: true,
        ticks: { color: '#94A3B8' },
        grid: { color: '#334155' }
      },
    },
    plugins: {
      legend: { 
        position: 'top',
        labels: { color: '#F8FAFC' }
      },
      title: { 
        display: true, 
        text: 'Hostel Occupancy & Vacancy',
        color: '#F8FAFC'
      },
    },
  };

  return (
    <div className="premium-dashboard-container">
      <header className="page-header" style={{marginBottom: '24px'}}>
        <h2>Analytics</h2>
        <p className="text-secondary">Hostel Occupancy & Vacancy Breakdown</p>
      </header>

      <section className="section" style={{marginBottom: '32px'}}>
        <div className="side-panel-card" style={{padding: '20px'}}>
          <h3 style={{marginBottom: '16px', color: 'var(--text-secondary)'}}>Analysis Period</h3>
          <form onSubmit={handleApply} style={{display: 'flex', gap: '15px', alignItems: 'flex-end', flexWrap: 'wrap'}}>
            <div className="form-group" style={{marginBottom: 0, flex: 1, minWidth: '200px'}}>
              <label style={{color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '8px', display: 'block'}}>Start Date</label>
              <input type="date" value={startDate} onChange={e => setStartDate(e.target.value)} required style={{width: '100%', padding: '10px 12px', borderRadius: '8px', border: '1px solid var(--border-subtle)', backgroundColor: 'var(--bg-base)', color: 'var(--text-primary)'}} />
            </div>
            <div className="form-group" style={{marginBottom: 0, flex: 1, minWidth: '200px'}}>
              <label style={{color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '8px', display: 'block'}}>End Date</label>
              <input type="date" value={endDate} onChange={e => setEndDate(e.target.value)} required style={{width: '100%', padding: '10px 12px', borderRadius: '8px', border: '1px solid var(--border-subtle)', backgroundColor: 'var(--bg-base)', color: 'var(--text-primary)'}} />
            </div>
            <button type="submit" className="btn-run-allocator" style={{height: '42px', marginTop: 0, width: 'auto', padding: '0 24px'}}>Apply Filter</button>
          </form>
        </div>
      </section>

      {loading ? (
        <div className="loader premium-loader">Loading Analytics...</div>
      ) : (
        <>
          <section className="section" style={{marginBottom: '32px'}}>
            <h3>Utilization Chart</h3>
            <div className="side-panel-card" style={{padding: '24px', height: '450px'}}>
              {data.length > 0 ? (
                <Bar options={chartOptions} data={chartData} />
              ) : (
                <div className="empty-state-premium">No data available for this period.</div>
              )}
            </div>
          </section>
          
          <section className="section">
            <h3>Detailed Breakdown</h3>
            <div className="side-panel-card" style={{padding: 0, overflow: 'hidden'}}>
              <table className="data-table" style={{width: '100%', borderCollapse: 'collapse', textAlign: 'left'}}>
                <thead>
                  <tr style={{backgroundColor: 'var(--bg-panel)', borderBottom: '1px solid var(--border-subtle)'}}>
                    <th style={{padding: '12px 16px', color: 'var(--text-secondary)'}}>Hostel</th>
                    <th style={{padding: '12px 16px', color: 'var(--text-secondary)'}}>Total Rooms</th>
                    <th style={{padding: '12px 16px', color: 'var(--text-secondary)'}}>Total Beds</th>
                    <th style={{padding: '12px 16px', color: 'var(--text-secondary)'}}>Occupied</th>
                    <th style={{padding: '12px 16px', color: 'var(--text-secondary)'}}>Vacant</th>
                    <th style={{padding: '12px 16px', color: 'var(--text-secondary)'}}>Utilization</th>
                    <th style={{padding: '12px 16px', color: 'var(--text-secondary)'}}>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {data.map(h => (
                    <tr key={h.hostel_id} style={{borderBottom: '1px solid var(--border-subtle)'}}>
                      <td style={{padding: '12px 16px'}}><strong>{h.hostel_name}</strong></td>
                      <td style={{padding: '12px 16px'}}>{h.total_rooms}</td>
                      <td style={{padding: '12px 16px'}}>{h.total_beds}</td>
                      <td style={{padding: '12px 16px'}} className="text-green">{h.occupied_beds}</td>
                      <td style={{padding: '12px 16px'}} className="text-blue">{h.vacant_beds}</td>
                      <td style={{padding: '12px 16px'}}>{(h.utilization_rate * 100).toFixed(1)}%</td>
                      <td style={{padding: '12px 16px'}}>
                        {h.underutilized ? (
                          <span style={{fontSize: '0.8rem', padding: '4px 8px', borderRadius: '4px', backgroundColor: 'var(--color-warning-bg)', color: 'var(--color-warning)'}}>Underutilized</span>
                        ) : (
                          <span style={{fontSize: '0.8rem', padding: '4px 8px', borderRadius: '4px', backgroundColor: 'var(--color-success-bg)', color: 'var(--color-success)'}}>Optimal</span>
                        )}
                      </td>
                    </tr>
                  ))}
                  {data.length === 0 && (
                    <tr>
                      <td colSpan="7" className="empty-state-premium" style={{border: 'none'}}>No breakdown available.</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </section>
        </>
      )}
    </div>
  );
}

export default Analytics;
