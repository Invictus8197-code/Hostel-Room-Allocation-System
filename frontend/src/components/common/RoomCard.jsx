import React from 'react';
import './RoomCard.css';

export default function RoomCard({ room }) {
  if (!room) return null;
  const capacity = room.capacity || 0;
  const occupancy = room.occupancy || 0;

  // Determine overall room status
  let statusClass = 'room-available';
  let statusDotClass = 'dot-success';
  
  if (room.is_under_maintenance) {
    statusClass = 'room-maintenance';
    statusDotClass = 'dot-warning';
  } else if (capacity > 0 && capacity === occupancy) {
    statusClass = 'room-full';
    statusDotClass = 'dot-critical';
  } else if (occupancy > 0) {
    statusClass = 'room-partial';
    statusDotClass = 'dot-warning';
  }

  // Render bed dots based on capacity and occupancy
  const beds = Array.from({ length: capacity }).map((_, i) => {
    let bedState = 'bed-empty';
    if (room.is_under_maintenance) bedState = 'bed-maintenance';
    else if (i < occupancy) bedState = 'bed-occupied';
    
    return <div key={i} className={`bed-dot ${bedState}`}></div>;
  });

  return (
    <div className={`room-card-premium ${statusClass}`}>
      <div className="room-card-header">
        <h4 className="room-number">{room.room_number}</h4>
        <div className="room-type-badge">
          {room.is_ac ? 'AC' : 'Non-AC'}
          <span className={`status-indicator ${statusDotClass}`}></span>
        </div>
      </div>
      <div className="room-card-body">
        <div className="bed-container">
          {beds}
        </div>
        <div className="room-occupancy-text">
          {room.occupancy}/{room.capacity} beds
        </div>
      </div>
      <div className="room-card-footer">
        <div className="occupancy-bar-bg">
          <div 
            className="occupancy-bar-fill" 
            style={{ width: `${capacity > 0 ? (occupancy / capacity) * 100 : 0}%` }}
          ></div>
        </div>
      </div>
    </div>
  );
}
