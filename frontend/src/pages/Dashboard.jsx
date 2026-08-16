import React, { useState, useEffect } from 'react';
import api from '../api';
import MetricCard from '../components/common/MetricCard';
import RoomCard from '../components/common/RoomCard';
import StatusBadge from '../components/common/StatusBadge';
import './Dashboard.css';

function Dashboard() {
  const [data, setData] = useState(null);
  const [floorplan, setFloorplan] = useState([]);
  const [loading, setLoading] = useState(true);
  const [optimizerStrictness, setOptimizerStrictness] = useState(50);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [summaryRes, floorplanRes] = await Promise.all([
          api.get('dashboard/summary/'),
          api.get('dashboard/floorplan/')
        ]);
        setData(summaryRes.data);
        setFloorplan(floorplanRes.data);
      } catch (e) {
        console.error("Dashboard error", e);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) return <div className="loader premium-loader">Loading operations data...</div>;
  if (!data) return <div className="loader premium-loader" style={{color: 'var(--color-critical)'}}>Failed to load dashboard data. Check API logs.</div>;

  // Group floorplan data by block and floor
  const floorGrouped = floorplan.reduce((acc, room) => {
    const blockName = room.block_name;
    const floorNum = room.floor_number;
    if (!acc[blockName]) acc[blockName] = {};
    if (!acc[blockName][floorNum]) acc[blockName][floorNum] = [];
    acc[blockName][floorNum].push(room);
    return acc;
  }, {});

  const satisfactionRate = data.total_beds > 0 ? ((data.occupied_beds / data.total_beds) * 100).toFixed(0) : 0;

  return (
    <div className="premium-dashboard-container">
      {/* Top KPI Cards */}
      <div className="premium-kpi-grid">
        <MetricCard 
          title="Occupancy Rate" 
          value={`${(data.utilization * 100).toFixed(0)}%`} 
          icon={<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path><polyline points="9 22 9 12 15 12 15 22"></polyline></svg>} 
          theme="primary" 
        />
        <MetricCard 
          title="Allocated Students" 
          value={`${data.occupied_beds}/${data.total_students}`} 
          subtitle={`${data.unallocated_students} unassigned`} 
          icon={<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>} 
          theme="success" 
        />
        <MetricCard 
          title="System Capacity" 
          value={`${data.total_beds}`} 
          subtitle={`${data.vacant_beds} vacant beds`}
          icon={<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"></path><line x1="7" y1="7" x2="7.01" y2="7"></line></svg>} 
          theme="warning" 
        />
        <MetricCard 
          title="Allocation Conflicts" 
          value={data.unallocated_students} 
          subtitle="Unsatisfied rules" 
          icon={<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>} 
          theme="critical" 
        />
      </div>

      <div className="dashboard-main-grid">
        {/* Visual Hostel Layout */}
        <div className="floorplan-section">
          <div className="section-header">
            <div className="section-title">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="3" width="7" height="7"></rect><rect x="14" y="3" width="7" height="7"></rect><rect x="14" y="14" width="7" height="7"></rect><rect x="3" y="14" width="7" height="7"></rect></svg>
              <h2>Visual Hostel Layout</h2>
            </div>
            <div className="floorplan-controls">
              <div className="status-legend">
                <span className="legend-item"><span className="dot dot-success"></span> Vacant</span>
                <span className="legend-item"><span className="dot dot-warning"></span> Partial/Maintenance</span>
                <span className="legend-item"><span className="dot dot-critical"></span> Full</span>
              </div>
            </div>
          </div>
          
          <div className="floorplan-blocks">
            {Object.keys(floorGrouped).length > 0 ? (
              Object.keys(floorGrouped).map(blockName => (
                <div key={blockName} className="block-container">
                  <h3 className="block-title">Block {blockName}</h3>
                  {Object.keys(floorGrouped[blockName]).sort().reverse().map(floorNum => (
                    <div key={floorNum} className="floor-container">
                      <div className="floor-label">FLOOR {floorNum}</div>
                      <div className="rooms-grid">
                        {floorGrouped[blockName][floorNum].map(room => (
                          <RoomCard key={room.id} room={room} />
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              ))
            ) : (
              <div className="empty-state-premium">No rooms found in assigned hostels.</div>
            )}
          </div>
        </div>

        {/* Right Side Panel */}
        <div className="side-panel-section">
          <div className="side-panel-card">
            <div className="panel-header">
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>
              <h3>Active Conflicts</h3>
              <span className="badge badge-critical">{data.unallocated_students}</span>
            </div>
            <div className="panel-body">
              {data.unallocated_students > 0 ? (
                <div className="conflict-alert warning">
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>
                  <div>
                    <strong>Unassigned Students</strong>
                    <p>There are {data.unallocated_students} students left unallocated due to strict room constraints or capacity limits.</p>
                  </div>
                </div>
              ) : (
                <div className="empty-state-premium small">No active conflicts found.</div>
              )}
            </div>
          </div>

          <div className="side-panel-card optimizer-card">
            <div className="panel-header">
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="4 14 10 14 10 20"></polyline><polyline points="20 10 14 10 14 4"></polyline><line x1="14" y1="10" x2="21" y2="3"></line><line x1="3" y1="21" x2="10" y2="14"></line></svg>
              <h3>Optimizer Engine</h3>
            </div>
            <div className="panel-body">
              <div className="optimizer-weight">
                <div className="weight-label">
                  <span>Gender Segregation</span>
                  <span className="text-success">Strict</span>
                </div>
                <div className="progress-bar-bg"><div className="progress-bar-fill success" style={{width: '100%'}}></div></div>
              </div>
              <div className="optimizer-weight">
                <div className="weight-label">
                  <span>Year/Course Alignment</span>
                  <span>80%</span>
                </div>
                <div className="progress-bar-bg"><div className="progress-bar-fill primary" style={{width: '80%'}}></div></div>
              </div>
              <div className="optimizer-weight">
                <div className="weight-label">
                  <span>Roommate Preference</span>
                  <span>90%</span>
                </div>
                <div className="progress-bar-bg"><div className="progress-bar-fill primary" style={{width: '90%'}}></div></div>
              </div>
              
              <button className="btn-run-allocator">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
                Run Allocator Engine
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
