import React, { useState } from 'react';
import { X, Play, Zap, Send } from 'lucide-react';

const PRESETS = [
  {
    name: 'Velocity Spike Attack',
    desc: 'Rapid card testing burst (4th tx within 2 minutes)',
    data: {
      user_id: 'USR-4099',
      amount: 4.99,
      merchant: 'Digital Gaming Voucher',
      category: 'digital_goods',
      latitude: 51.5074,
      longitude: -0.1278,
      location_name: 'London, UK',
      ip_address: '195.154.122.99',
      device_id: 'automated_script_curl'
    }
  },
  {
    name: 'Impossible Travel (Teleportation)',
    desc: 'Transaction in Singapore 15 mins after Los Angeles (speed > 5,000 km/h)',
    data: {
      user_id: 'USR-2005',
      amount: 850.00,
      merchant: 'Marina Bay Sands Luxury Mall',
      category: 'retail',
      latitude: 1.2847,
      longitude: 103.8610,
      location_name: 'Singapore, SG',
      ip_address: '118.200.15.44',
      device_id: 'unknown_mobile_android'
    }
  },
  {
    name: 'Unusual Amount ($16,500)',
    desc: 'Massive single purchase exceeding historical baseline by 300x',
    data: {
      user_id: 'USR-1001',
      amount: 16500.00,
      merchant: 'Geneva Haute Horlogerie',
      category: 'luxury_goods',
      latitude: 40.7128,
      longitude: -74.0060,
      location_name: 'New York, USA',
      ip_address: '198.51.100.12',
      device_id: 'iphone_15_alice'
    }
  },
  {
    name: 'High-Risk Crypto Merchant',
    desc: 'Unregulated crypto tumbler offshore transfer',
    data: {
      user_id: 'USR-7700',
      amount: 4800.00,
      merchant: 'Offshore Crypto Mixer & Tumbler',
      category: 'crypto_exchange',
      latitude: 25.2048,
      longitude: 55.2708,
      location_name: 'Dubai, UAE',
      ip_address: '185.120.34.8',
      device_id: 'brave_tor_browser'
    }
  },
  {
    name: 'Legitimate Low-Risk Coffee',
    desc: 'Standard local cafe purchase matching historical profile',
    data: {
      user_id: 'USR-1001',
      amount: 5.75,
      merchant: 'Blue Bottle Coffee',
      category: 'food_and_beverage',
      latitude: 40.7580,
      longitude: -73.9855,
      location_name: 'New York, USA',
      ip_address: '198.51.100.12',
      device_id: 'iphone_15_alice'
    }
  }
];

export default function TransactionSimulator({ isOpen, onClose, onSimulate }) {
  const [form, setForm] = useState(PRESETS[0].data);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  if (!isOpen) return null;

  const applyPreset = (preset) => {
    setForm(preset.data);
    setResult(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setResult(null);
    try {
      const res = await onSimulate(form);
      setResult(res);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose} role="dialog" aria-modal="true">
      <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '780px' }}>
        <div className="modal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div
              style={{
                width: '36px',
                height: '36px',
                borderRadius: '8px',
                background: 'linear-gradient(135deg, #6366f1 0%, #3b82f6 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#fff'
              }}
            >
              <Zap size={20} />
            </div>
            <div>
              <h2 style={{ fontSize: '18px', fontWeight: 700 }}>Transaction Risk Simulator</h2>
              <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                Test the pluggable rule engine and verify live AWS SES/SNS alert triggers
              </div>
            </div>
          </div>
          <button className="close-btn" onClick={onClose} id="simulator-close-btn" aria-label="Close modal">
            <X size={20} />
          </button>
        </div>

        <div className="modal-body">
          {/* Quick Presets */}
          <div>
            <div style={{ fontSize: '12px', fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-secondary)', marginBottom: '8px' }}>
              Quick Test Presets
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: '8px' }}>
              {PRESETS.map((preset, idx) => (
                <button
                  key={idx}
                  type="button"
                  id={`preset-btn-${idx}`}
                  className="filter-btn"
                  style={{ textAlign: 'left', padding: '8px 10px', height: 'auto' }}
                  onClick={() => applyPreset(preset)}
                >
                  <div style={{ fontWeight: 700, fontSize: '12px', color: '#f8fafc' }}>{preset.name}</div>
                  <div style={{ fontSize: '10px', color: 'var(--text-muted)', marginTop: '2px', lineHeight: 1.2 }}>{preset.desc}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
              <div>
                <label style={{ fontSize: '12px', color: 'var(--text-secondary)', display: 'block', marginBottom: '4px' }}>
                  User Account ID
                </label>
                <input
                  id="sim-user-id"
                  type="text"
                  className="input font-mono"
                  value={form.user_id}
                  onChange={(e) => setForm({ ...form, user_id: e.target.value })}
                  required
                />
              </div>

              <div>
                <label style={{ fontSize: '12px', color: 'var(--text-secondary)', display: 'block', marginBottom: '4px' }}>
                  Transaction Amount ($)
                </label>
                <input
                  id="sim-amount"
                  type="number"
                  step="0.01"
                  className="input font-mono"
                  value={form.amount}
                  onChange={(e) => setForm({ ...form, amount: parseFloat(e.target.value) || 0 })}
                  required
                />
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
              <div>
                <label style={{ fontSize: '12px', color: 'var(--text-secondary)', display: 'block', marginBottom: '4px' }}>
                  Merchant Name
                </label>
                <input
                  id="sim-merchant"
                  type="text"
                  className="input"
                  value={form.merchant}
                  onChange={(e) => setForm({ ...form, merchant: e.target.value })}
                  required
                />
              </div>

              <div>
                <label style={{ fontSize: '12px', color: 'var(--text-secondary)', display: 'block', marginBottom: '4px' }}>
                  Category
                </label>
                <input
                  id="sim-category"
                  type="text"
                  className="input"
                  value={form.category}
                  onChange={(e) => setForm({ ...form, category: e.target.value })}
                  required
                />
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 1fr', gap: '12px' }}>
              <div>
                <label style={{ fontSize: '12px', color: 'var(--text-secondary)', display: 'block', marginBottom: '4px' }}>
                  Location Name
                </label>
                <input
                  id="sim-location"
                  type="text"
                  className="input"
                  value={form.location_name}
                  onChange={(e) => setForm({ ...form, location_name: e.target.value })}
                  required
                />
              </div>

              <div>
                <label style={{ fontSize: '12px', color: 'var(--text-secondary)', display: 'block', marginBottom: '4px' }}>
                  Latitude
                </label>
                <input
                  id="sim-lat"
                  type="number"
                  step="0.0001"
                  className="input font-mono"
                  value={form.latitude}
                  onChange={(e) => setForm({ ...form, latitude: parseFloat(e.target.value) || 0 })}
                  required
                />
              </div>

              <div>
                <label style={{ fontSize: '12px', color: 'var(--text-secondary)', display: 'block', marginBottom: '4px' }}>
                  Longitude
                </label>
                <input
                  id="sim-lon"
                  type="number"
                  step="0.0001"
                  className="input font-mono"
                  value={form.longitude}
                  onChange={(e) => setForm({ ...form, longitude: parseFloat(e.target.value) || 0 })}
                  required
                />
              </div>
            </div>

            <button
              id="btn-run-simulation"
              type="submit"
              className="btn btn-primary"
              disabled={loading}
              style={{ padding: '12px', fontSize: '15px' }}
            >
              <Play size={16} />
              {loading ? 'Evaluating in Engine...' : 'Run Live Fraud Evaluation'}
            </button>
          </form>

          {/* Result Card */}
          {result && (
            <div
              style={{
                background: 'rgba(15, 23, 42, 0.9)',
                border: '1px solid var(--border-subtle)',
                borderRadius: '12px',
                padding: '20px',
                display: 'flex',
                flexDirection: 'column',
                gap: '12px',
                animation: 'fadeIn 0.2s ease-out'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Evaluation Result for {result.transaction_id}</div>
                  <div style={{ fontSize: '20px', fontWeight: 800 }}>
                    Risk Score: <span className="font-mono" style={{ color: result.risk_score >= 60 ? '#ef4444' : '#10b981' }}>{result.risk_score}/100</span> ({result.risk_level})
                  </div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Engine Status</div>
                  <span className={`badge ${result.status === 'FLAGGED' ? 'badge-critical' : 'badge-low'}`}>
                    {result.status}
                  </span>
                </div>
              </div>

              {/* AWS Notification Alert Banner if triggered */}
              {result.notifications && result.notifications.length > 0 && (
                <div
                  style={{
                    background: 'rgba(239, 68, 68, 0.12)',
                    border: '1px solid rgba(239, 68, 68, 0.3)',
                    borderRadius: '8px',
                    padding: '10px 14px',
                    fontSize: '13px',
                    color: '#fca5a5',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '10px'
                  }}
                >
                  <Send size={18} color="#ef4444" />
                  <div>
                    <strong>High-Risk Threshold Exceeded!</strong> Dispatched live alerts via{' '}
                    <strong>AWS SES Email</strong> and <strong>AWS SNS</strong>.
                  </div>
                </div>
              )}

              {/* Triggered Rules */}
              <div>
                <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '6px' }}>
                  Rule Findings:
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  {(result.rule_evaluations || []).map((ev, idx) => (
                    <div
                      key={idx}
                      style={{
                        padding: '8px 12px',
                        borderRadius: '6px',
                        fontSize: '12px',
                        background: ev.is_flagged ? 'rgba(239, 68, 68, 0.1)' : 'rgba(16, 185, 129, 0.08)',
                        border: `1px solid ${ev.is_flagged ? 'rgba(239, 68, 68, 0.25)' : 'rgba(16, 185, 129, 0.2)'}`,
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center'
                      }}
                    >
                      <div>
                        <strong>{ev.rule_name}:</strong> {ev.reason}
                      </div>
                      <span className="font-mono" style={{ fontWeight: 700, color: ev.is_flagged ? '#ef4444' : '#10b981' }}>
                        {ev.is_flagged ? `+${ev.risk_score}` : 'Passed'}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
