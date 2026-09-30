import React from 'react';
import { ShieldAlert, RefreshCw, PlusCircle, Activity, Bell, Sliders } from 'lucide-react';

export default function Header({ activeTab, setActiveTab, onOpenSimulator, onReseed, loading, rulesCount }) {
  return (
    <header className="app-header glass-panel">
      <div className="brand-wrapper">
        <div className="brand-icon">
          <ShieldAlert size={26} />
        </div>
        <div className="brand-text">
          <h1>SentinEx Guard</h1>
          <div className="brand-subtitle">
            Enterprise Fraud Rule Engine & Real-Time Review Console
          </div>
        </div>
      </div>

      <nav className="nav-tabs" aria-label="Main Navigation">
        <button
          id="nav-console"
          className={`nav-tab ${activeTab === 'console' ? 'active' : ''}`}
          onClick={() => setActiveTab('console')}
        >
          <Activity size={16} />
          Review Console
        </button>
        <button
          id="nav-rules"
          className={`nav-tab ${activeTab === 'rules' ? 'active' : ''}`}
          onClick={() => setActiveTab('rules')}
        >
          <Sliders size={16} />
          Pluggable Rules ({rulesCount || 4})
        </button>
        <button
          id="nav-notifications"
          className={`nav-tab ${activeTab === 'notifications' ? 'active' : ''}`}
          onClick={() => setActiveTab('notifications')}
        >
          <Bell size={16} />
          AWS SES / SNS Logs
        </button>
      </nav>

      <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
        <button
          id="btn-reseed-data"
          className="btn btn-secondary btn-sm"
          onClick={onReseed}
          disabled={loading}
          title="Reseed database with realistic demo fraud scenarios"
        >
          <RefreshCw size={14} className={loading ? 'spin' : ''} />
          Reseed Demo
        </button>

        <button
          id="btn-simulate-txn"
          className="btn btn-primary"
          onClick={onOpenSimulator}
        >
          <PlusCircle size={16} />
          Simulate Transaction
        </button>
      </div>
    </header>
  );
}
