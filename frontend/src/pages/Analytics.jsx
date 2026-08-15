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
      x: { stacked: true },
      y: { stacked: true },
    },
    plugins: {
      legend: { position: 'top' },
      title: { display: true, text: 'Hostel Occupancy & Vacancy' },
    },
  };

  return (
    <div className="layout">
      <aside className="sidebar">
        <h2 className="brand">Smart Hostel</h2>
        <nav className="nav-menu">
          <Link to="/dashboard" className="nav-item">Dashboard</Link>
          <Link to="/allocations" className="nav-item">Allocations</Link>
          <Link to="/analytics" className="nav-item active">Analytics</Link>
          <Link to="/simulation" className="nav-item">Simulation</Link>
        </nav>
        <div className="user-profile">
          <div>{user?.username} ({user?.role})</div>
          <button onClick={logout} className="logout-btn">Logout</button>
        </div>
      </aside>
      
      <main className="main-content">
        <header className="page-header">
          <h1>Analytics</h1>
        </header>

        <section className="section" style={{marginBottom: '30px'}}>
          <h2>Analysis Period</h2>
          <form onSubmit={handleApply} style={{display: 'flex', gap: '15px', alignItems: 'flex-end'}}>
            <div className="form-group" style={{marginBottom: 0}}>
              <label>Start Date</label>
              <input type="date" value={startDate} onChange={e => setStartDate(e.target.value)} required />
            </div>
            <div className="form-group" style={{marginBottom: 0}}>
              <label>End Date</label>
              <input type="date" value={endDate} onChange={e => setEndDate(e.target.value)} required />
            </div>
            <button type="submit" className="btn btn-primary" style={{height: '42px'}}>Apply Filter</button>
          </form>
        </section>

        {loading ? (
          <div className="loader">Loading Analytics...</div>
        ) : (
          <>
            <section className="section" style={{marginBottom: '30px'}}>
              <h2>Utilization Chart</h2>
              <div style={{height: '400px'}}>
                {data.length > 0 ? (
                  <Bar options={chartOptions} data={chartData} />
                ) : (
                  <div className="empty-msg">No data available for this period.</div>
                )}
              </div>
            </section>
            
            <section className="section">
              <h2>Detailed Breakdown</h2>
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Hostel</th>
                    <th>Total Rooms</th>
                    <th>Total Beds</th>
                    <th>Occupied</th>
                    <th>Vacant</th>
                    <th>Utilization</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {data.map(h => (
                    <tr key={h.hostel_id}>
                      <td><strong>{h.hostel_name}</strong></td>
                      <td>{h.total_rooms}</td>
                      <td>{h.total_beds}</td>
                      <td className="text-green">{h.occupied_beds}</td>
                      <td className="text-blue">{h.vacant_beds}</td>
                      <td>{(h.utilization_rate * 100).toFixed(1)}%</td>
                      <td>
                        {h.underutilized ? (
                          <span className="status-badge status-draft text-orange">Underutilized</span>
                        ) : (
                          <span className="status-badge status-committed">Optimal</span>
                        )}
                      </td>
                    </tr>
                  ))}
                  {data.length === 0 && (
                    <tr>
                      <td colSpan="7" className="empty-msg">No breakdown available.</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </section>
          </>
        )}
      </main>
    </div>
  );
}

export default Analytics;
