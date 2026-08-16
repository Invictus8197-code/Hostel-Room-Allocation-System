import React from 'react';
import './MetricCard.css';

export default function MetricCard({ title, value, subtitle, icon, theme = 'primary' }) {
  return (
    <div className={`metric-card-premium theme-${theme}`}>
      <div className="metric-header">
        <div className={`metric-icon-box bg-${theme}`}>
          {icon}
        </div>
        <div className="metric-title">{title}</div>
      </div>
      <div className="metric-body">
        <div className="metric-value">{value}</div>
        {subtitle && <div className="metric-subtitle">{subtitle}</div>}
      </div>
    </div>
  );
}
