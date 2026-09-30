import React from 'react';
import { Bell, CheckCircle2, Mail, MessageSquare } from 'lucide-react';

export default function NotificationInbox({ notifications, onSelectTxnId }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Overview Card */}
      <div
        className="glass-panel"
        style={{
          padding: '24px',
          borderLeft: '4px solid #06b6d4',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '16px'
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
            <Bell size={20} color="#06b6d4" />
            <h2 style={{ fontSize: '18px', fontWeight: 800 }}>AWS SES & SNS High-Risk Alert Logs</h2>
          </div>
          <p style={{ fontSize: '13px', color: 'var(--text-secondary)', maxWidth: '800px', lineHeight: 1.5 }}>
            Every transaction that crosses the high-risk score threshold (&ge; 60/100) automatically dispatches
            instant security alerts via <strong>AWS Simple Email Service (SES)</strong> and <strong>AWS Simple Notification Service (SNS)</strong> using boto3.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '8px' }}>
          <span className="badge" style={{ background: 'rgba(6, 182, 212, 0.15)', color: '#06b6d4', padding: '6px 12px', fontSize: '12px' }}>
            <CheckCircle2 size={14} /> {notifications.length} Alerts Dispatched
          </span>
        </div>
      </div>

      {/* Notification Logs List */}
      <div className="glass-panel" style={{ padding: '20px' }}>
        {notifications.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
            No high-risk notifications dispatched yet. Use the Simulator to trigger a high-risk transaction!
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {notifications.map((notif) => {
              const isEmail = notif.channel === 'AWS_SES';
              return (
                <div
                  key={notif.id}
                  id={`notif-card-${notif.id}`}
                  style={{
                    background: 'rgba(15, 23, 42, 0.6)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: '10px',
                    padding: '16px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '10px'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <span
                        className="badge"
                        style={{
                          background: isEmail ? 'rgba(59, 130, 246, 0.15)' : 'rgba(168, 85, 247, 0.15)',
                          color: isEmail ? '#60a5fa' : '#c084fc',
                          border: `1px solid ${isEmail ? 'rgba(59, 130, 246, 0.3)' : 'rgba(168, 85, 247, 0.3)'}`
                        }}
                      >
                        {isEmail ? <Mail size={12} /> : <MessageSquare size={12} />}
                        {notif.channel}
                      </span>

                      <button
                        className="font-mono"
                        style={{
                          background: 'rgba(56, 189, 248, 0.1)',
                          border: 'none',
                          color: '#38bdf8',
                          padding: '3px 8px',
                          borderRadius: '4px',
                          cursor: 'pointer',
                          fontSize: '12px',
                          fontWeight: 600
                        }}
                        onClick={() => onSelectTxnId(notif.transaction_id)}
                        title="View Transaction Details"
                      >
                        {notif.transaction_id}
                      </button>

                      <span style={{ fontSize: '13px', fontWeight: 600 }}>
                        {notif.subject}
                      </span>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                      <span className="badge badge-low" style={{ fontSize: '11px' }}>
                        {notif.status}
                      </span>
                      <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                        {new Date(notif.created_at).toLocaleString()}
                      </span>
                    </div>
                  </div>

                  <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                    <strong>Recipient:</strong> <span className="font-mono">{notif.recipient}</span>
                  </div>

                  <div
                    style={{
                      background: 'rgba(0, 0, 0, 0.35)',
                      borderRadius: '6px',
                      padding: '10px 14px',
                      fontSize: '12px',
                      fontFamily: 'var(--font-mono)',
                      color: '#cbd5e1',
                      whiteSpace: 'pre-wrap',
                      maxHeight: '120px',
                      overflowY: 'auto'
                    }}
                  >
                    {notif.message}
                  </div>

                  <div style={{ fontSize: '11px', color: 'var(--text-muted)', display: 'flex', justifyContent: 'space-between' }}>
                    <span>AWS Region: us-east-1</span>
                    <span className="font-mono">AWS Message ID: {notif.message_id || 'N/A'}</span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
