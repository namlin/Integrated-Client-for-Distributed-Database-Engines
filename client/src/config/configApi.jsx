const API_BASE_URL = 'http://localhost:8000/api';

const getSessionId = () => localStorage.getItem('db_client_session_id') || '';

const apiFetch = async (endpoint, method = 'GET', data = null) => {
  const url = `${API_BASE_URL}${endpoint}`;
  const options = {
    method,
    headers: {
      'Content-Type': 'application/json',
      'X-Client-Session-Id': getSessionId(),
    },
  };
  if (data && (method === 'POST' || method === 'PUT')) {
    options.body = JSON.stringify(data);
  }
  const response = await fetch(url, options);
  if (!response.ok) {
    let errorMessage = `HTTP Error: ${response.status}`;
    try {
      const err = await response.json();
      errorMessage = err.detail || err.message || err.error || errorMessage;
    } catch (_) {}
    throw new Error(errorMessage);
  }
  return response.json();
};

export const connectionAPI = {
  getConnections: () => apiFetch('/connections', 'GET'),
  createConnection: (data) => apiFetch('/connections', 'POST', data),
  disconnectConnection: (id) => apiFetch(`/connections/${id}/disconnect`, 'PUT'),
  reconnectConnection: (id) => apiFetch(`/connections/${id}/reconnect`, 'PUT'),
  deleteConnection: (id) => apiFetch(`/connections/${id}`, 'DELETE'),
};

export const queryAPI = {
  executeQuery: (connectionId, query, protocol = 'Undo/Redo', tid = null) =>
    apiFetch('/queries/execute', 'POST', { connectionId, query, protocol, tid }),
};

export const transactionAPI = {
  beginTransaction: (connectionId, protocol) =>
    apiFetch('/transactions/begin', 'POST', { connectionId, protocol }),
  getTransactions: () => apiFetch('/transactions', 'GET'),
  commitTransaction: (tid) => apiFetch(`/transactions/${tid}/commit`, 'PUT'),
  rollbackTransaction: (tid) => apiFetch(`/transactions/${tid}/rollback`, 'PUT'),
};

export const walAPI = {
  getWalEntries: (tid) => apiFetch(`/wal/entries/${tid}`, 'GET'),
  getAllWalEntries: ({ tid, op, start_ts, end_ts } = {}) => {
    const params = new URLSearchParams();
    if (tid) params.append('tid', tid);
    if (op) params.append('op', op);
    if (start_ts) params.append('start_ts', start_ts);
    if (end_ts) params.append('end_ts', end_ts);
    const qs = params.toString();
    return apiFetch(`/wal${qs ? '?' + qs : ''}`, 'GET');
  },
};

export const recoveryAPI = {
  simulateFailure: (tid) => apiFetch(`/recovery/simulate-failure/${tid}`, 'POST'),
  simulatePostCommitFailure: (tid) => apiFetch(`/recovery/simulate-post-commit-failure/${tid}`, 'POST'),
  runRecovery: (tid, protocol) => apiFetch(`/recovery/run/${tid}`, 'POST', { protocol }),
  getRecoveryStatus: (tid) => apiFetch(`/recovery/status/${tid}`, 'GET'),
};

export const healthAPI = {
  getHealth: () => apiFetch('/health', 'GET'),
};

export default { connectionAPI, queryAPI, transactionAPI, walAPI, recoveryAPI, healthAPI };
