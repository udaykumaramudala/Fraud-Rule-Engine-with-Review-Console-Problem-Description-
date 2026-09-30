import React from 'react';
import { AlertTriangle, CheckCircle, Clock, ShieldAlert, Radio, Flame } from 'lucide-react';

export default function MetricsCards({ stats }) {
  if (!stats) return null;

  return (
    <div className="metrics-grid">
      {/* Total Transactions */}
      <div className="metric-card glass-panel">
        <div className="metric-card-header">
          <span className="metric-card-title">Total Volume</span>
          <div className="metric-card-icon" style={{ background: 'rgba(99, 102, 241, 0.15)', color: '#818cf8' }}>
            <Radio size={18} />
          </div>
        </div>
        <div className="metric-card-value font-mono">{stats.total_transactions}</div>
        <div className="metric-card-subtext">
          Avg Risk Score: <strong style={{ color: stats.average_risk_score > 40 ? '#f59e0b' : '#10b981' }}>{stats.average_risk_score}/100</strong>
        </div>
      </div>

      {/* Flagged Transactions */}
      <div className="metric-card glass-panel" style={{ borderLeft: '4px solid #ef4444' }}>
        <div className="metric-card-header">
          <span className="metric-card-title">Flagged for Review</span>
          <div className="metric-card-icon" style={{ background: 'rgba(239, 68, 68, 0.15)', color: '#ef4444' }}>
            <AlertTriangle size={18} />
          </div>
        </div>
        <div className="metric-card-value font-mono" style={{ color: '#ef4444' }}>
          {stats.flagged_count}
        </div>
        <div className="metric-card-subtext">
          Requires reviewer investigation
        </div>
      </div>

      {/* High Risk Critical */}
      <div className="metric-card glass-panel">
        <div className="metric-card-header">
          <span className="metric-card-title">High Risk Incidents</span>
          <div className="metric-card-icon" style={{ background: 'rgba(249, 115, 22, 0.15)', color: '#f97316' }}>
            <Flame size={18} />
          </div>
        </div>
        <div className="metric-card-value font-mono" style={{ color: '#f97316' }}>
          {stats.high_risk_count}
        </div>
        <div className="metric-card-subtext">
          Score ≥ 60.0 (Auto-Alert threshold)
        </div>
      </div>

      {/* Under Review */}
      <div className="metric-card glass-panel">
        <div className="metric-card-header">
          <span className="metric-card-title">Under Investigation</span>
          <div className="metric-card-icon" style={{ background: 'rgba(245, 158, 11, 0.15)', color: '#f59e0b' }}>
            <Clock size={18} />
          </div>
        </div>
        <div className="metric-card-value font-mono" style={{ color: '#f59e0b' }}>
          {stats.under_review_count}
        </div>
        <div className="metric-card-subtext">
          Active analyst workflows
        </div>
      </div>

      {/* Cleared Legitimate */}
      <div className="metric-card glass-panel">
        <div className="metric-card-header">
          <span className="metric-card-title">Cleared Legitimate</span>
          <div className="metric-card-icon" style={{ background: 'rgba(16, 185, 129, 0.15)', color: '#10b981' }}>
            <CheckCircle size={18} />
          </div>
        </div>
        <div className="metric-card-value font-mono" style={{ color: '#10b981' }}>
          {stats.cleared_count}
        </div>
        <div className="metric-card-subtext">
          Approved & normal traffic
        </div>
      </div>

      {/* AWS SES & SNS Alerts Dispatched */}
      <div className="metric-card glass-panel">
        <div className="metric-card-header">
          <span className="metric-card-title">AWS SES/SNS Dispatched</span>
          <div className="metric-card-icon" style={{ background: 'rgba(6, 182, 212, 0.15)', color: '#06b6d4' }}>
            <ShieldAlert size={18} />
          </div>
        </div>
        <div className="metric-card-value font-mono" style={{ color: '#06b6d4' }}>
          {stats.notifications_sent_count}
        </div>
        <div className="metric-card-subtext">
          Instant high-risk notifications
        </div>
      </div>
    </div>
  );
}
