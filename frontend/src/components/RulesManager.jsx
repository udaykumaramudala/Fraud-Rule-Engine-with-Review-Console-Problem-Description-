import React from 'react';
import { ToggleLeft, ToggleRight, CheckCircle2, Cpu } from 'lucide-react';

export default function RulesManager({ rules, onToggleRule }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Pluggable Architecture Info Box */}
      <div
        className="glass-panel"
        style={{
          padding: '24px',
          borderLeft: '4px solid #6366f1',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '16px'
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
            <Cpu size={20} color="#818cf8" />
            <h2 style={{ fontSize: '18px', fontWeight: 800 }}>Pluggable Rule Engine Architecture</h2>
          </div>
          <p style={{ fontSize: '13px', color: 'var(--text-secondary)', maxWidth: '800px', lineHeight: 1.5 }}>
            Built strictly on the <strong>Open-Closed Principle</strong>. The engine evaluates rules through an abstract{' '}
            <code className="font-mono" style={{ background: 'rgba(255,255,255,0.08)', padding: '2px 6px', borderRadius: '4px' }}>BaseRule</code> interface and dynamic{' '}
            <code className="font-mono" style={{ background: 'rgba(255,255,255,0.08)', padding: '2px 6px', borderRadius: '4px' }}>RuleRegistry</code>.
            New fraud rules can be added as standalone modules in <code className="font-mono">backend/app/engine/rules/</code> and are discovered automatically at runtime without touching core engine logic.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '8px' }}>
          <span className="badge badge-low" style={{ padding: '6px 12px', fontSize: '12px' }}>
            <CheckCircle2 size={14} /> {rules.filter(r => r.enabled).length} Rules Active
          </span>
        </div>
      </div>

      {/* Rules Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '16px' }}>
        {rules.map((rule) => (
          <div
            key={rule.rule_id}
            id={`rule-card-${rule.rule_id}`}
            className="glass-panel"
            style={{
              padding: '20px',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              gap: '16px',
              borderColor: rule.enabled ? 'rgba(99, 102, 241, 0.3)' : 'var(--border-subtle)',
              opacity: rule.enabled ? 1 : 0.65
            }}
          >
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
                <div>
                  <h3 style={{ fontSize: '16px', fontWeight: 700 }}>{rule.rule_name}</h3>
                  <span className="font-mono" style={{ fontSize: '11px', color: '#38bdf8' }}>
                    ID: {rule.rule_id}
                  </span>
                </div>
                <button
                  id={`toggle-rule-${rule.rule_id}`}
                  className="btn btn-secondary btn-sm"
                  onClick={() => onToggleRule(rule.rule_id)}
                  style={{
                    color: rule.enabled ? '#10b981' : '#94a3b8',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px'
                  }}
                >
                  {rule.enabled ? <ToggleRight size={20} color="#10b981" /> : <ToggleLeft size={20} />}
                  {rule.enabled ? 'Active' : 'Disabled'}
                </button>
              </div>

              <p style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: 1.4, marginBottom: '14px' }}>
                {rule.description}
              </p>

              {/* Parameters / Thresholds */}
              <div
                style={{
                  background: 'rgba(0, 0, 0, 0.3)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: '8px',
                  padding: '12px'
                }}
              >
                <div style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: '8px', fontWeight: 600 }}>
                  Active Configured Parameters
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  {Object.entries(rule.parameters || {}).map(([key, val]) => (
                    <div key={key} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px' }}>
                      <span className="font-mono" style={{ color: '#94a3b8' }}>{key}:</span>
                      <strong className="font-mono" style={{ color: '#f8fafc' }}>
                        {Array.isArray(val) ? `[${val.length} items]` : String(val)}
                      </strong>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: '1px solid var(--border-subtle)', paddingTop: '12px', fontSize: '12px' }}>
              <span style={{ color: 'var(--text-muted)' }}>Score Multiplier Weight:</span>
              <strong className="font-mono" style={{ color: '#818cf8' }}>{rule.weight}x</strong>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
