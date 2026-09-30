import React from 'react';
import { Search, Eye, CheckCircle2, AlertOctagon, ShieldAlert, MapPin, Clock } from 'lucide-react';

export default function TransactionTable({
  transactions,
  onSelectTransaction,
  onQuickReview,
  filterStatus,
  setFilterStatus,
  searchQuery,
  setSearchQuery
}) {
  const getRiskBadge = (level, score) => {
    switch (level) {
      case 'CRITICAL':
        return <span className="badge badge-critical font-mono">CRITICAL {score}</span>;
      case 'HIGH':
        return <span className="badge badge-high font-mono">HIGH {score}</span>;
      case 'MEDIUM':
        return <span className="badge badge-medium font-mono">MED {score}</span>;
      default:
        return <span className="badge badge-low font-mono">LOW {score}</span>;
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'FLAGGED':
        return (
          <span className="badge" style={{ background: 'rgba(239, 68, 68, 0.15)', color: '#ef4444', border: '1px solid rgba(239, 68, 68, 0.3)' }}>
            <AlertOctagon size={12} /> FLAGGED
          </span>
        );
      case 'UNDER_REVIEW':
        return (
          <span className="badge" style={{ background: 'rgba(245, 158, 11, 0.15)', color: '#f59e0b', border: '1px solid rgba(245, 158, 11, 0.3)' }}>
            <Clock size={12} /> IN REVIEW
          </span>
        );
      case 'CLEARED':
        return (
          <span className="badge" style={{ background: 'rgba(16, 185, 129, 0.15)', color: '#10b981', border: '1px solid rgba(16, 185, 129, 0.3)' }}>
            <CheckCircle2 size={12} /> CLEARED
          </span>
        );
      case 'CONFIRMED_FRAUD':
        return (
          <span className="badge" style={{ background: 'rgba(153, 27, 27, 0.3)', color: '#f87171', border: '1px solid #dc2626' }}>
            <ShieldAlert size={12} /> FRAUD
          </span>
        );
      default:
        return <span className="badge badge-low">{status}</span>;
    }
  };

  const formatTime = (ts) => {
    if (!ts) return 'Just now';
    try {
      const d = new Date(ts);
      return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }) + ' ' + d.toLocaleDateString([], { month: 'short', day: 'numeric' });
    } catch {
      return ts;
    }
  };

  return (
    <div className="table-panel glass-panel">
      <div className="table-controls">
        {/* Status Filters */}
        <div className="table-filters" role="group" aria-label="Filter Transactions">
          {[
            { id: 'FLAGGED', label: 'Action Required (Flagged)' },
            { id: 'ALL', label: 'All Transactions' },
            { id: 'UNDER_REVIEW', label: 'Under Review' },
            { id: 'CLEARED', label: 'Cleared' },
            { id: 'CONFIRMED_FRAUD', label: 'Confirmed Fraud' }
          ].map((tab) => (
            <button
              key={tab.id}
              id={`filter-${tab.id.toLowerCase()}`}
              className={`filter-btn ${filterStatus === tab.id ? 'active' : ''}`}
              onClick={() => setFilterStatus(tab.id)}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Search */}
        <div className="search-input-wrapper">
          <Search size={16} className="search-icon" />
          <input
            id="search-transactions-input"
            type="text"
            className="input"
            placeholder="Search by ID, User, Merchant, City..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
      </div>

      {/* Table */}
      <div className="table-responsive">
        <table className="data-table" id="transactions-table">
          <thead>
            <tr>
              <th>Txn ID</th>
              <th>User Account</th>
              <th>Amount</th>
              <th>Merchant & Category</th>
              <th>Location</th>
              <th>Timestamp</th>
              <th>Risk Score</th>
              <th>Status</th>
              <th>Rules Triggered</th>
              <th>Review Actions</th>
            </tr>
          </thead>
          <tbody>
            {transactions.length === 0 ? (
              <tr>
                <td colSpan={10} style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
                  No transactions match the current filter criteria.
                </td>
              </tr>
            ) : (
              transactions.map((tx) => {
                const flaggedEvals = (tx.rule_evaluations || []).filter((r) => r.is_flagged);
                return (
                  <tr key={tx.transaction_id} id={`txn-row-${tx.transaction_id}`}>
                    <td className="font-mono" style={{ fontWeight: 600, color: '#38bdf8' }}>
                      {tx.transaction_id}
                    </td>
                    <td>
                      <span className="font-mono" style={{ background: 'rgba(255,255,255,0.05)', padding: '2px 6px', borderRadius: '4px' }}>
                        {tx.user_id}
                      </span>
                    </td>
                    <td className="font-mono" style={{ fontWeight: 700, fontSize: '14px', color: tx.amount > 3000 ? '#f87171' : 'var(--text-primary)' }}>
                      {tx.currency || '$'} {tx.amount.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </td>
                    <td>
                      <div style={{ fontWeight: 600 }}>{tx.merchant}</div>
                      <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{tx.category}</div>
                    </td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '12px' }}>
                        <MapPin size={12} color="#94a3b8" />
                        <span>{tx.location_name}</span>
                      </div>
                    </td>
                    <td style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                      {formatTime(tx.timestamp)}
                    </td>
                    <td>
                      <div className="risk-meter">
                        {getRiskBadge(tx.risk_level, tx.risk_score)}
                        <div className="risk-bar">
                          <div
                            className="risk-bar-fill"
                            style={{
                              width: `${Math.min(100, tx.risk_score)}%`,
                              background:
                                tx.risk_score >= 80 ? '#ef4444' :
                                tx.risk_score >= 60 ? '#f97316' :
                                tx.risk_score >= 30 ? '#f59e0b' : '#10b981'
                            }}
                          />
                        </div>
                      </div>
                    </td>
                    <td>{getStatusBadge(tx.status)}</td>
                    <td>
                      {flaggedEvals.length > 0 ? (
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                          {flaggedEvals.map((e, idx) => (
                            <span
                              key={idx}
                              style={{
                                fontSize: '11px',
                                background: 'rgba(239, 68, 68, 0.12)',
                                color: '#f87171',
                                border: '1px solid rgba(239, 68, 68, 0.25)',
                                padding: '2px 6px',
                                borderRadius: '4px'
                              }}
                              title={e.reason}
                            >
                              {e.rule_name || e.rule_id}
                            </span>
                          ))}
                        </div>
                      ) : (
                        <span style={{ fontSize: '12px', color: '#10b981' }}>0 (Normal)</span>
                      )}
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: '6px' }}>
                        <button
                          id={`inspect-btn-${tx.transaction_id}`}
                          className="btn btn-secondary btn-sm"
                          onClick={() => onSelectTransaction(tx)}
                          title="Inspect Telemetry & Evidence"
                        >
                          <Eye size={14} />
                          Inspect
                        </button>

                        {tx.status !== 'CLEARED' && (
                          <button
                            id={`quick-clear-btn-${tx.transaction_id}`}
                            className="btn btn-success btn-sm"
                            onClick={() => onQuickReview(tx.transaction_id, 'CLEARED')}
                            title="Quick Clear (Mark as Legitimate)"
                          >
                            <CheckCircle2 size={13} />
                            Clear
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
