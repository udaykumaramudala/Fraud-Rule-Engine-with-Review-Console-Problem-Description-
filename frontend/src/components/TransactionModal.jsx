import React, { useState } from 'react';
import {
  X, ShieldAlert, CheckCircle2, AlertTriangle, ArrowRight,
  MapPin, Clock, DollarSign, User, Server, Compass, Send
} from 'lucide-react';

export default function TransactionModal({
  transaction,
  onClose,
  onUpdateStatus
}) {
  const [reviewerName, setReviewerName] = useState('Analyst Sarah Connor');
  const [reviewNotes, setReviewNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);

  if (!transaction) return null;

  const handleAction = async (status) => {
    setSubmitting(true);
    try {
      await onUpdateStatus(transaction.transaction_id, status, reviewerName, reviewNotes);
    } finally {
      setSubmitting(false);
    }
  };

  const flaggedRules = (transaction.rule_evaluations || []).filter((r) => r.is_flagged);
  const normalRules = (transaction.rule_evaluations || []).filter((r) => !r.is_flagged);

  return (
    <div className="modal-overlay" onClick={onClose} role="dialog" aria-modal="true">
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="modal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div
              style={{
                width: '38px',
                height: '38px',
                borderRadius: '8px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                background:
                  transaction.risk_score >= 60 ? 'rgba(239, 68, 68, 0.2)' : 'rgba(16, 185, 129, 0.2)',
                color: transaction.risk_score >= 60 ? '#ef4444' : '#10b981'
              }}
            >
              <ShieldAlert size={22} />
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <h2 style={{ fontSize: '18px', fontWeight: 700 }}>
                  Transaction Investigation
                </h2>
                <span className="font-mono" style={{ color: '#38bdf8', fontSize: '14px' }}>
                  {transaction.transaction_id}
                </span>
              </div>
              <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                Evaluated at {new Date(transaction.timestamp).toLocaleString()}
              </div>
            </div>
          </div>

          <button className="close-btn" onClick={onClose} id="modal-close-btn" aria-label="Close modal">
            <X size={20} />
          </button>
        </div>

        {/* Body */}
        <div className="modal-body">
          {/* Risk Level Banner */}
          <div
            style={{
              padding: '16px 20px',
              borderRadius: '12px',
              background:
                transaction.risk_level === 'CRITICAL' ? 'rgba(239, 68, 68, 0.15)' :
                transaction.risk_level === 'HIGH' ? 'rgba(249, 115, 22, 0.15)' :
                transaction.risk_level === 'MEDIUM' ? 'rgba(245, 158, 11, 0.15)' :
                'rgba(16, 185, 129, 0.15)',
              border: `1px solid ${
                transaction.risk_level === 'CRITICAL' ? 'rgba(239, 68, 68, 0.4)' :
                transaction.risk_level === 'HIGH' ? 'rgba(249, 115, 22, 0.4)' :
                transaction.risk_level === 'MEDIUM' ? 'rgba(245, 158, 11, 0.4)' :
                'rgba(16, 185, 129, 0.4)'
              }`,
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}
          >
            <div>
              <div style={{ fontSize: '12px', textTransform: 'uppercase', letterSpacing: '0.5px', color: 'var(--text-secondary)' }}>
                Calculated Risk Assessment
              </div>
              <div style={{ fontSize: '22px', fontWeight: 800 }}>
                {transaction.risk_level} RISK &bull;{' '}
                <span className="font-mono">{transaction.risk_score} / 100</span>
              </div>
            </div>

            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Current Status</div>
              <div style={{ fontSize: '15px', fontWeight: 700, color: '#38bdf8' }}>
                {transaction.status}
              </div>
            </div>
          </div>

          {/* Telemetry Grid */}
          <div className="detail-grid">
            <div className="detail-item">
              <span className="detail-label"><User size={12} style={{ display: 'inline' }} /> User Account</span>
              <span className="detail-val font-mono">{transaction.user_id}</span>
            </div>
            <div className="detail-item">
              <span className="detail-label"><DollarSign size={12} style={{ display: 'inline' }} /> Amount</span>
              <span className="detail-val font-mono" style={{ color: '#38bdf8' }}>
                {transaction.currency} {transaction.amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}
              </span>
            </div>
            <div className="detail-item">
              <span className="detail-label">Merchant</span>
              <span className="detail-val">{transaction.merchant}</span>
            </div>
            <div className="detail-item">
              <span className="detail-label">Category</span>
              <span className="detail-val" style={{ textTransform: 'capitalize' }}>
                {transaction.category.replace('_', ' ')}
              </span>
            </div>
            <div className="detail-item">
              <span className="detail-label"><MapPin size={12} style={{ display: 'inline' }} /> Geolocation</span>
              <span className="detail-val">{transaction.location_name}</span>
            </div>
            <div className="detail-item">
              <span className="detail-label">Coordinates</span>
              <span className="detail-val font-mono" style={{ fontSize: '12px' }}>
                {transaction.latitude.toFixed(4)}, {transaction.longitude.toFixed(4)}
              </span>
            </div>
            <div className="detail-item">
              <span className="detail-label"><Server size={12} style={{ display: 'inline' }} /> IP & Device</span>
              <span className="detail-val font-mono" style={{ fontSize: '12px' }}>
                {transaction.ip_address}
              </span>
            </div>
            <div className="detail-item">
              <span className="detail-label">Device Hash</span>
              <span className="detail-val font-mono" style={{ fontSize: '12px' }}>
                {transaction.device_id}
              </span>
            </div>
          </div>

          {/* Rule Engine Evaluation Breakdown */}
          <div>
            <h3 style={{ fontSize: '15px', fontWeight: 700, marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Compass size={18} color="#818cf8" />
              Independent Rules Evaluation Breakdown
            </h3>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {/* Flagged Rules */}
              {flaggedRules.map((rule, idx) => {
                let meta = {};
                try {
                  meta = JSON.parse(rule.metadata_json || '{}');
                } catch {}

                return (
                  <div key={idx} className="rule-card flagged">
                    <div className="rule-card-top">
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <AlertTriangle size={18} color="#ef4444" />
                        <span style={{ fontWeight: 700, fontSize: '14px' }}>{rule.rule_name}</span>
                      </div>
                      <span className="badge badge-critical font-mono">
                        +{rule.risk_score} pts ({rule.severity})
                      </span>
                    </div>

                    <p style={{ fontSize: '13px', color: '#e2e8f0', lineHeight: 1.4 }}>
                      {rule.reason}
                    </p>

                    {/* Specific Telemetry Evidence Visuals */}
                    {rule.rule_id === 'impossible_geographical_location' && meta.implied_speed_kmh && (
                      <div
                        style={{
                          background: 'rgba(0, 0, 0, 0.3)',
                          padding: '10px 14px',
                          borderRadius: '8px',
                          fontSize: '12px',
                          display: 'flex',
                          justifyContent: 'space-between',
                          marginTop: '4px'
                        }}
                      >
                        <div>
                          <strong>Transit Route:</strong> {meta.origin_location} <ArrowRight size={12} style={{ display: 'inline' }} /> {meta.destination_location}
                        </div>
                        <div>
                          <strong>Distance:</strong> {meta.distance_km} km in {meta.elapsed_minutes} mins
                        </div>
                        <div style={{ color: '#ef4444', fontWeight: 700 }}>
                          Speed: {meta.implied_speed_kmh} km/h (Limit: {meta.max_allowed_speed_kmh} km/h)
                        </div>
                      </div>
                    )}

                    {rule.rule_id === 'unusual_transaction_amount' && meta.historical_avg && (
                      <div
                        style={{
                          background: 'rgba(0, 0, 0, 0.3)',
                          padding: '10px 14px',
                          borderRadius: '8px',
                          fontSize: '12px',
                          display: 'flex',
                          justifyContent: 'space-between',
                          marginTop: '4px'
                        }}
                      >
                        <div>
                          <strong>Baseline Avg:</strong> ${meta.historical_avg} ({meta.historical_count} txs)
                        </div>
                        <div>
                          <strong>Current Amount:</strong> ${meta.current_amount}
                        </div>
                        <div style={{ color: '#ef4444', fontWeight: 700 }}>
                          Multiplier: {meta.amount_multiplier}x above average
                        </div>
                      </div>
                    )}

                    {rule.rule_id === 'transaction_velocity' && meta.short_window_count && (
                      <div
                        style={{
                          background: 'rgba(0, 0, 0, 0.3)',
                          padding: '10px 14px',
                          borderRadius: '8px',
                          fontSize: '12px',
                          display: 'flex',
                          justifyContent: 'space-between',
                          marginTop: '4px'
                        }}
                      >
                        <div>
                          <strong>Window:</strong> {meta.short_window_minutes} minutes
                        </div>
                        <div>
                          <strong>Burst Count:</strong> {meta.short_window_count} transactions
                        </div>
                        <div style={{ color: '#ef4444', fontWeight: 700 }}>
                          Limit: {meta.short_window_limit} transactions
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}

              {/* Passed Rules */}
              {normalRules.map((rule, idx) => (
                <div key={idx} className="rule-card" style={{ opacity: 0.75 }}>
                  <div className="rule-card-top">
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <CheckCircle2 size={16} color="#10b981" />
                      <span style={{ fontWeight: 600, fontSize: '13px' }}>{rule.rule_name}</span>
                    </div>
                    <span className="badge badge-low font-mono">0 pts (Passed)</span>
                  </div>
                  <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                    {rule.reason}
                  </p>
                </div>
              ))}
            </div>
          </div>

          {/* AWS SES / SNS Dispatched Alerts for this Transaction */}
          {transaction.notifications && transaction.notifications.length > 0 && (
            <div>
              <h3 style={{ fontSize: '14px', fontWeight: 700, marginBottom: '8px', color: '#06b6d4', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Send size={15} /> AWS SES / SNS Notifications Dispatched
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                {transaction.notifications.map((notif, idx) => (
                  <div
                    key={idx}
                    style={{
                      background: 'rgba(6, 182, 212, 0.08)',
                      border: '1px solid rgba(6, 182, 212, 0.25)',
                      borderRadius: '8px',
                      padding: '10px 14px',
                      fontSize: '12px',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center'
                    }}
                  >
                    <div>
                      <strong>[{notif.channel}]</strong> &rarr; {notif.recipient} ({notif.subject})
                    </div>
                    <span className="font-mono" style={{ color: '#06b6d4', fontSize: '11px' }}>
                      MsgID: {notif.message_id || 'simulated-ok'}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Review Audit History */}
          {transaction.audit_logs && transaction.audit_logs.length > 0 && (
            <div>
              <h3 style={{ fontSize: '14px', fontWeight: 700, marginBottom: '8px', color: 'var(--text-secondary)' }}>
                Investigation Audit Trail
              </h3>
              <div className="audit-list">
                {transaction.audit_logs.map((log) => (
                  <div key={log.id} className="audit-item">
                    <div>
                      <strong>{log.reviewer}</strong> changed status from{' '}
                      <span style={{ color: '#94a3b8' }}>{log.previous_status}</span> &rarr;{' '}
                      <span style={{ color: '#38bdf8', fontWeight: 600 }}>{log.new_status}</span>
                      {log.notes && <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '2px' }}>&ldquo;{log.notes}&rdquo;</div>}
                    </div>
                    <div className="font-mono" style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                      {new Date(log.created_at).toLocaleTimeString()}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Reviewer Action Form */}
          <div className="review-action-box">
            <h3 style={{ fontSize: '15px', fontWeight: 700 }}>
              Reviewer Disposition & Action
            </h3>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '12px' }}>
              <div>
                <label style={{ fontSize: '12px', color: 'var(--text-secondary)', display: 'block', marginBottom: '4px' }}>
                  Reviewer Name
                </label>
                <input
                  id="input-reviewer-name"
                  type="text"
                  className="input"
                  value={reviewerName}
                  onChange={(e) => setReviewerName(e.target.value)}
                  placeholder="e.g. Sarah Jenkins"
                />
              </div>

              <div>
                <label style={{ fontSize: '12px', color: 'var(--text-secondary)', display: 'block', marginBottom: '4px' }}>
                  Investigation Notes / Rationale
                </label>
                <input
                  id="input-reviewer-notes"
                  type="text"
                  className="input"
                  value={reviewNotes}
                  onChange={(e) => setReviewNotes(e.target.value)}
                  placeholder="e.g. Spoke to user, confirmed card authorized, or suspected credential stuffing"
                />
              </div>
            </div>

            <div className="action-buttons-group">
              <button
                id="btn-action-clear"
                className="btn btn-success"
                disabled={submitting}
                onClick={() => handleAction('CLEARED')}
              >
                <CheckCircle2 size={16} />
                Clear as Legitimate
              </button>

              <button
                id="btn-action-under-review"
                className="btn btn-warning"
                disabled={submitting}
                onClick={() => handleAction('UNDER_REVIEW')}
              >
                <Clock size={16} />
                Mark Under Review
              </button>

              <button
                id="btn-action-confirm-fraud"
                className="btn btn-danger"
                disabled={submitting}
                onClick={() => handleAction('CONFIRMED_FRAUD')}
              >
                <ShieldAlert size={16} />
                Confirm Fraud & Block
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
