import React, { createContext, useState, useEffect, useCallback } from 'react';
import {
  connectionAPI,
  queryAPI,
  transactionAPI,
  walAPI,
  recoveryAPI,
  healthAPI,
} from '../config/configApi';

export const DBClientContext = createContext();

export function DBClientProvider({ children }) {
  const [activeEngine, setActiveEngine] = useState(null);
  const [activeConnectionId, setActiveConnectionId] = useState(null);
  const [activeTransaction, setActiveTransaction] = useState(null);
  const [recoveryProtocol, setRecoveryProtocol] = useState('No-Undo/Redo');
  const [queryContent, setQueryContent] = useState(
    `BEGIN;\nUPDATE students\nSET grade = 95\nWHERE id = 1;\n-- Click COMMIT or ROLLBACK`
  );
  const [activeTab, setActiveTab] = useState('Resultados');
  const [sessionActive, setSessionActive] = useState(true);

  const [connections, setConnections] = useState([]);
  const [transactions, setTransactions] = useState([]);
  const [resultsData, setResultsData] = useState([]);
  const [resultsColumns, setResultsColumns] = useState([]);
  const [walEntries, setWalEntries] = useState([]);
  const [consoleLog, setConsoleLog] = useState([]);
  const [recoveryResult, setRecoveryResult] = useState(null);
  const [health, setHealth] = useState(null);

  const [showConnectionModal, setShowConnectionModal] = useState(false);
  const [isLoadingConnection, setIsLoadingConnection] = useState(false);
  const [connectionError, setConnectionError] = useState(null);
  const [editingConnection, setEditingConnection] = useState(null);

  const [isExecuting, setIsExecuting] = useState(false);
  const [queryError, setQueryError] = useState(null);

  // ── Helpers ───────────────────────────────────────────────────────────────

  const appendLog = (msg) =>
    setConsoleLog((prev) => [`[${new Date().toLocaleTimeString()}] ${msg}`, ...prev].slice(0, 100));

  const refreshTransactions = useCallback(async () => {
    try {
      const data = await transactionAPI.getTransactions();
      setTransactions(data);
    } catch (_) {}
  }, []);

  const refreshWal = useCallback(async () => {
    try {
      const data = await walAPI.getAllWalEntries({});
      setWalEntries(data);
    } catch (_) {}
  }, []);

  const refreshHealth = useCallback(async () => {
    try {
      const data = await healthAPI.getHealth();
      setHealth(data);
    } catch (_) {}
  }, []);

  // ── Boot: load connections + health ───────────────────────────────────────

  useEffect(() => {
    if (!localStorage.getItem('db_client_session_id')) {
      localStorage.setItem('db_client_session_id', crypto.randomUUID());
    }
    (async () => {
      try {
        const conns = await connectionAPI.getConnections();
        setConnections(conns);
        const first = conns.find((c) => c.status === 'connected');
        if (first) {
          setActiveEngine(first.name);
          setActiveConnectionId(first.id);
        }
      } catch (_) {}
      refreshTransactions();
      refreshWal();
      refreshHealth();
    })();
  }, []);

  // ── Connection management ─────────────────────────────────────────────────

  const addConnection = async (connectionData) => {
    setIsLoadingConnection(true);
    setConnectionError(null);
    try {
      const newConn = await connectionAPI.createConnection(connectionData);
      setConnections((prev) => [...prev, newConn]);
      setShowConnectionModal(false);
      setEditingConnection(null);
      if (!activeConnectionId) {
        setActiveEngine(newConn.name);
        setActiveConnectionId(newConn.id);
      }
      appendLog(`Connected to ${newConn.name} (${newConn.address})`);
    } catch (error) {
      setConnectionError(error.message);
    } finally {
      setIsLoadingConnection(false);
    }
  };

  const disconnectConnection = async (connectionId) => {
    setIsLoadingConnection(true);
    setConnectionError(null);
    try {
      const updated = await connectionAPI.disconnectConnection(connectionId);
      setConnections((prev) => prev.map((c) => (c.id === connectionId ? updated : c)));
      if (activeConnectionId === connectionId) {
        const next = connections.find((c) => c.id !== connectionId && c.status === 'connected');
        setActiveEngine(next?.name ?? null);
        setActiveConnectionId(next?.id ?? null);
      }
      appendLog(`Disconnected from ${updated.name}`);
    } catch (error) {
      setConnectionError(error.message);
    } finally {
      setIsLoadingConnection(false);
    }
  };

  const reconnectConnection = async (connectionId) => {
    setIsLoadingConnection(true);
    setConnectionError(null);
    try {
      const updated = await connectionAPI.reconnectConnection(connectionId);
      setConnections((prev) => prev.map((c) => (c.id === connectionId ? updated : c)));
      if (!activeConnectionId || activeConnectionId === connectionId) {
        setActiveEngine(updated.name);
        setActiveConnectionId(updated.id);
      }
      appendLog(`Reconnected to ${updated.name}`);
    } catch (error) {
      setConnectionError(error.message);
    } finally {
      setIsLoadingConnection(false);
    }
  };

  const deleteConnection = async (connectionId) => {
    setIsLoadingConnection(true);
    setConnectionError(null);
    try {
      await connectionAPI.deleteConnection(connectionId);
      setConnections((prev) => prev.filter((c) => c.id !== connectionId));
      if (activeConnectionId === connectionId) {
        const next = connections.find((c) => c.id !== connectionId && c.status === 'connected');
        setActiveEngine(next?.name ?? null);
        setActiveConnectionId(next?.id ?? null);
      }
      appendLog(`Deleted connection`);
    } catch (error) {
      setConnectionError(error.message);
    } finally {
      setIsLoadingConnection(false);
    }
  };

  const selectConnection = (conn) => {
    setActiveEngine(conn.name);
    setActiveConnectionId(conn.id);
  };

  // ── Query execution ───────────────────────────────────────────────────────

  const executeQuery = async () => {
    if (!activeConnectionId) {
      setQueryError('No active connection. Add one in the sidebar.');
      return;
    }
    setIsExecuting(true);
    setQueryError(null);
    try {
      const result = await queryAPI.executeQuery(
        activeConnectionId,
        queryContent,
        recoveryProtocol,
        activeTransaction
      );
      setResultsData(result.results || []);
      setResultsColumns(result.columns || []);
      if (result.txn_id) setActiveTransaction(result.txn_id);
      appendLog(
        result.message ||
          `Query OK — ${result.rowsAffected} row(s) affected`
      );
      setActiveTab('Resultados');
      await refreshTransactions();
      await refreshWal();
      await refreshHealth();
    } catch (error) {
      setQueryError(error.message);
      appendLog(`ERROR: ${error.message}`);
      setActiveTab('Consola');
    } finally {
      setIsExecuting(false);
    }
  };

  // ── Transaction controls ──────────────────────────────────────────────────

  const commitTransaction = async () => {
    const activeTransactions = transactions.filter((txn) => txn.status === 'ACTIVE');
    if (activeTransactions.length === 0) return;
    
    try {
      // Commit all active transactions
      for (const txn of activeTransactions) {
        await transactionAPI.commitTransaction(txn.id);
        appendLog(`Transaction ${txn.id} committed`);
      }
      setActiveTransaction(null);
      await refreshTransactions();
      await refreshWal();
    } catch (error) {
      appendLog(`COMMIT ERROR: ${error.message}`);
    }
  };

  const rollbackTransaction = async () => {
    const activeTransactions = transactions.filter((txn) => txn.status === 'ACTIVE');
    if (activeTransactions.length === 0) return;
    
    try {
      // Rollback all active transactions
      for (const txn of activeTransactions) {
        await transactionAPI.rollbackTransaction(txn.id);
        appendLog(`Transaction ${txn.id} rolled back`);
      }
      setActiveTransaction(null);
      await refreshTransactions();
      await refreshWal();
    } catch (error) {
      appendLog(`ROLLBACK ERROR: ${error.message}`);
    }
  };

  // ── Recovery ──────────────────────────────────────────────────────────────

  const simulateFailure = async () => {
    if (!activeTransaction) {
      appendLog('No active transaction to simulate failure on.');
      return;
    }
    try {
      const result = await recoveryAPI.simulateFailure(activeTransaction);
      appendLog(`Failure simulated on ${result.tid}`);
      setActiveTransaction(null);
      await refreshTransactions();
      setActiveTab('Recuperación');
    } catch (error) {
      appendLog(`SIMULATE FAILURE ERROR: ${error.message}`);
    }
  };

  const runRecovery = async (tid, protocol) => {
    try {
      const result = await recoveryAPI.runRecovery(tid, protocol || recoveryProtocol);
      setRecoveryResult(result);
      appendLog(`Recovery (${result.protocol}) on ${tid}: ${result.after_state}`);
      await refreshTransactions();
      await refreshWal();
      setActiveTab('Recuperación');
    } catch (error) {
      appendLog(`RECOVERY ERROR: ${error.message}`);
    }
  };

  const value = {
    // Connection state
    activeEngine, setActiveEngine,
    activeConnectionId, setActiveConnectionId,
    connections, setConnections,
    selectConnection,
    showConnectionModal, setShowConnectionModal,
    isLoadingConnection,
    connectionError,
    editingConnection, setEditingConnection,
    addConnection, disconnectConnection, reconnectConnection, deleteConnection,

    // Transaction state
    activeTransaction, setActiveTransaction,
    transactions,
    recoveryProtocol, setRecoveryProtocol,
    commitTransaction, rollbackTransaction,

    // Query state
    queryContent, setQueryContent,
    resultsData, resultsColumns,
    isExecuting, queryError,
    executeQuery,

    // WAL
    walEntries,

    // Recovery
    recoveryResult,
    simulateFailure,
    runRecovery,

    // UI
    activeTab, setActiveTab,
    sessionActive, setSessionActive,
    consoleLog,
    health,
    refreshWal, refreshTransactions, refreshHealth,
  };

  return (
    <DBClientContext.Provider value={value}>
      {children}
    </DBClientContext.Provider>
  );
}
