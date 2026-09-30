import React, { useState, useEffect, useCallback } from 'react';
import { ShieldAlert } from 'lucide-react';
import Header from './components/Header';
import MetricsCards from './components/MetricsCards';
import TransactionTable from './components/TransactionTable';
import TransactionModal from './components/TransactionModal';
import TransactionSimulator from './components/TransactionSimulator';
import RulesManager from './components/RulesManager';
import NotificationInbox from './components/NotificationInbox';

const apiFetch = (url, options = {}) => {
  const apiKey = import.meta.env.VITE_API_KEY;
  const headers = new Headers(options.headers || {});
  if (apiKey) headers.set('X-API-Key', apiKey);
  return fetch(url, { ...options, headers });
};

export default function App() {
  const [activeTab, setActiveTab] = useState('console'); // console, rules, notifications
  const [stats, setStats] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [rules, setRules] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [filterStatus, setFilterStatus] = useState('FLAGGED');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTransaction, setSelectedTransaction] = useState(null);
  const [isSimulatorOpen, setIsSimulatorOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [isInitialLoading, setIsInitialLoading] = useState(true);
  const [apiError, setApiError] = useState(null);
  const [toastMessage, setToastMessage] = useState(null);

  const showToast = (msg, type = 'info') => {
    setToastMessage({ msg, type });
    setTimeout(() => setToastMessage(null), 4000);
  };

  // Fetch dashboard stats
  const fetchStats = useCallback(async () => {
    try {
      const res = await apiFetch('/api/analytics');
      if (res.ok) {
        const data = await res.json();
        setStats(data);
        setApiError(null);
      } else {
        throw new Error(`Analytics request failed (${res.status})`);
      }
    } catch (err) {
      console.error('Error fetching analytics:', err);
      setApiError('The API is not reachable. Start the FastAPI server on port 8000, then refresh.');
    }
  }, []);

  // Fetch transactions based on filter & search
  const fetchTransactions = useCallback(async () => {
    try {
      let url = '/api/transactions?limit=100';
      if (filterStatus === 'FLAGGED') {
        url += '&flagged_only=true';
      } else if (filterStatus !== 'ALL') {
        url += `&status=${filterStatus}`;
      }
      if (searchQuery.trim()) {
        url += `&search=${encodeURIComponent(searchQuery.trim())}`;
      }

      const res = await apiFetch(url);
      if (res.ok) {
        const data = await res.json();
        setTransactions(data);
      } else {
        throw new Error(`Transactions request failed (${res.status})`);
      }
    } catch (err) {
      console.error('Error fetching transactions:', err);
      setApiError('Unable to load transactions. Check that the backend is running on port 8000.');
    }
  }, [filterStatus, searchQuery]);

  // Fetch rules
  const fetchRules = useCallback(async () => {
    try {
      const res = await apiFetch('/api/rules');
      if (res.ok) {
        const data = await res.json();
        setRules(data);
      } else {
        throw new Error(`Rules request failed (${res.status})`);
      }
    } catch (err) {
      console.error('Error fetching rules:', err);
      setApiError('Unable to load the rule registry. Check that the backend is running on port 8000.');
    }
  }, []);

  // Fetch notifications
  const fetchNotifications = useCallback(async () => {
    try {
      const res = await apiFetch('/api/notifications?limit=50');
      if (res.ok) {
        const data = await res.json();
        setNotifications(data);
      } else {
        throw new Error(`Notifications request failed (${res.status})`);
      }
    } catch (err) {
      console.error('Error fetching notifications:', err);
      setApiError('Unable to load notification history. Check that the backend is running on port 8000.');
    }
  }, []);

  // Initial load
  useEffect(() => {
    let isMounted = true;
    const initialize = async () => {
      await Promise.all([fetchStats(), fetchTransactions(), fetchRules(), fetchNotifications()]);
      if (isMounted) {
        setIsInitialLoading(false);
      }
    };
    initialize();
    return () => {
      isMounted = false;
    };
  }, [fetchStats, fetchTransactions, fetchRules, fetchNotifications]);

  // Handle Quick Review Action from Table
  const handleQuickReview = async (transactionId, newStatus) => {
    try {
      const res = await apiFetch(`/api/transactions/${transactionId}/review`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          status: newStatus,
          reviewer: 'Compliance Officer (Quick Action)',
          notes: 'Marked legitimate via rapid console clearance'
        })
      });
      if (res.ok) {
        showToast(`Transaction ${transactionId} marked as ${newStatus}`, 'success');
        fetchTransactions();
        fetchStats();
      }
    } catch (err) {
      showToast(`Error updating transaction: ${err}`, 'error');
    }
  };

  // Handle Detailed Review Action from Modal
  const handleUpdateStatus = async (transactionId, newStatus, reviewer, notes) => {
    try {
      const res = await apiFetch(`/api/transactions/${transactionId}/review`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: newStatus, reviewer, notes })
      });
      if (res.ok) {
        const updated = await res.json();
        setSelectedTransaction(updated);
        showToast(`Transaction ${transactionId} updated to ${newStatus}`, 'success');
        fetchTransactions();
        fetchStats();
      }
    } catch (err) {
      showToast(`Error updating transaction: ${err}`, 'error');
    }
  };

  // Handle Toggle Rule
  const handleToggleRule = async (ruleId) => {
    try {
      const res = await apiFetch(`/api/rules/${ruleId}/toggle`, { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        showToast(`Rule ${ruleId} is now ${data.enabled ? 'ACTIVE' : 'DISABLED'}`, 'info');
        fetchRules();
      }
    } catch (err) {
      showToast(`Error toggling rule: ${err}`, 'error');
    }
  };

  // Handle Simulate Transaction
  const handleSimulateTransaction = async (formData) => {
    const res = await apiFetch('/api/transactions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(formData)
    });
    if (!res.ok) {
      throw new Error('Simulation failed');
    }
    const data = await res.json();
    fetchTransactions();
    fetchStats();
    fetchNotifications();
    showToast(`Transaction ${data.transaction_id} evaluated (Risk Score: ${data.risk_score})`, 'success');
    return data;
  };

  // Handle Reseed Demo Data
  const handleReseed = async () => {
    setLoading(true);
    try {
      const res = await apiFetch('/api/seed', { method: 'POST' });
      if (res.ok) {
        showToast('Database reseeded with realistic demo fraud scenarios!', 'success');
        await fetchStats();
        await fetchTransactions();
        await fetchNotifications();
      }
    } catch (err) {
      showToast(`Error reseeding: ${err}`, 'error');
    } finally {
      setLoading(false);
    }
  };

  // Handle selecting a transaction ID from notification log
  const handleSelectTxnId = async (txnId) => {
    try {
      const res = await apiFetch(`/api/transactions/${txnId}`);
      if (res.ok) {
        const data = await res.json();
        setSelectedTransaction(data);
      }
    } catch (err) {
      console.error('Error fetching single transaction:', err);
    }
  };

  return (
    <div className="app-container">
      {apiError && (
        <div className="api-error" role="alert">
          <ShieldAlert size={18} />
          <span>{apiError}</span>
          <button className="api-error-dismiss" onClick={() => setApiError(null)} aria-label="Dismiss API error">Dismiss</button>
        </div>
      )}

      {/* Toast Notification */}
      {toastMessage && (
        <div
          style={{
            position: 'fixed',
            bottom: '24px',
            right: '24px',
            zIndex: 9999,
            background: toastMessage.type === 'error' ? '#ef4444' : '#10b981',
            color: '#ffffff',
            padding: '12px 20px',
            borderRadius: '8px',
            boxShadow: '0 10px 25px rgba(0,0,0,0.5)',
            fontWeight: 600,
            fontSize: '14px',
            animation: 'fadeIn 0.2s ease-out'
          }}
        >
          {toastMessage.msg}
        </div>
      )}

      {/* Header */}
      <Header
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        onOpenSimulator={() => setIsSimulatorOpen(true)}
        onReseed={handleReseed}
        loading={loading}
        rulesCount={rules.length}
      />

      {/* KPI Stats Metrics */}
      {isInitialLoading ? (
        <div className="loading-panel glass-panel" aria-live="polite">
          <div className="loading-orb" />
          <div>
            <strong>Connecting to SentinEx Guard</strong>
            <p>Loading transactions, rules, and notification history...</p>
          </div>
        </div>
      ) : <MetricsCards stats={stats} />}

      {/* Main Tab Content */}
      <main>
        {activeTab === 'console' && (
          <TransactionTable
            transactions={transactions}
            onSelectTransaction={(tx) => setSelectedTransaction(tx)}
            onQuickReview={handleQuickReview}
            filterStatus={filterStatus}
            setFilterStatus={setFilterStatus}
            searchQuery={searchQuery}
            setSearchQuery={setSearchQuery}
          />
        )}

        {activeTab === 'rules' && (
          <RulesManager rules={rules} onToggleRule={handleToggleRule} />
        )}

        {activeTab === 'notifications' && (
          <NotificationInbox
            notifications={notifications}
            onSelectTxnId={handleSelectTxnId}
          />
        )}
      </main>

      {/* Detailed Transaction Investigation Modal */}
      {selectedTransaction && (
        <TransactionModal
          transaction={selectedTransaction}
          onClose={() => setSelectedTransaction(null)}
          onUpdateStatus={handleUpdateStatus}
        />
      )}

      {/* Live Transaction Risk Simulator Modal */}
      <TransactionSimulator
        isOpen={isSimulatorOpen}
        onClose={() => setIsSimulatorOpen(false)}
        onSimulate={handleSimulateTransaction}
      />
    </div>
  );
}
