import React from 'react';
import './StatusBadge.css';

export default function StatusBadge({ status, label }) {
  // Mapping statuses to semantic colors
  const getTheme = () => {
    const s = status?.toLowerCase();
    if (['available', 'active', 'resolved', 'approved', 'committed'].includes(s)) return 'success';
    if (['occupied', 'full', 'error', 'critical', 'danger'].includes(s)) return 'critical';
    if (['maintenance', 'pending', 'partial', 'warning'].includes(s)) return 'warning';
    if (['in review', 'info'].includes(s)) return 'info';
    return 'neutral';
  };

  const theme = getTheme();
  const displayLabel = label || status || 'UNKNOWN';

  return (
    <span className={`status-badge-premium badge-${theme}`}>
      <span className="badge-dot"></span>
      {displayLabel}
    </span>
  );
}
