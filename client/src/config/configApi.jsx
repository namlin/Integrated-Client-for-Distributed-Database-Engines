// Base API URL - Update this with your actual backend URL
const API_BASE_URL = 'http://localhost:8000/api';

/**
 * Generic fetch wrapper with error handling
 * @param {string} endpoint - API endpoint (without base URL)
 * @param {string} method - HTTP method (GET, POST, PUT, DELETE)
 * @param {object} data - Request body data (optional)
 * @returns {Promise<object>} - Parsed JSON response
 * @throws {Error} - Throws error with message from backend or fetch error
 */
const apiFetch = async (endpoint, method = 'GET', data = null) => {
  const url = `${API_BASE_URL}${endpoint}`;
  const options = {
    method,
    headers: {
      'Content-Type': 'application/json',
    },
  };

  if (data && (method === 'POST' || method === 'PUT')) {
    options.body = JSON.stringify(data);
  }

  try {
    const response = await fetch(url, options);

    if (!response.ok) {
      let errorMessage = `HTTP Error: ${response.status}`;
      try {
        const errorData = await response.json();
        errorMessage = errorData.message || errorData.error || errorMessage;
      } catch (e) {
        // If response is not JSON, use default error message
      }
      throw new Error(errorMessage);
    }

    const responseData = await response.json();
    return responseData;
  } catch (error) {
    console.error(`API Error [${method} ${url}]:`, error);
    throw error;
  }
};

/**
 * Connection API calls
 */
export const connectionAPI = {
  /**
   * Create a new database connection
   * @param {object} connectionData - {name, engine, host, port, username, password, database}
   * @returns {Promise<object>} - New connection object with id and status
   */
  createConnection: async (connectionData) => {
    return apiFetch('/connections', 'POST', connectionData);
  },

  /**
   * Disconnect an existing connection (mark as disconnected)
   * @param {string} connectionId - Connection ID
   * @returns {Promise<object>} - Updated connection object with status 'disconnected'
   */
  disconnectConnection: async (connectionId) => {
    return apiFetch(`/connections/${connectionId}/disconnect`, 'PUT');
  },

  /**
   * Delete a connection permanently
   * @param {string} connectionId - Connection ID
   * @returns {Promise<object>} - Confirmation response
   */
  deleteConnection: async (connectionId) => {
    return apiFetch(`/connections/${connectionId}`, 'DELETE');
  },

  /**
   * Get all connections
   * @returns {Promise<array>} - Array of connection objects
   */
  getConnections: async () => {
    return apiFetch('/connections', 'GET');
  },
};

/**
 * Query execution API calls
 */
export const queryAPI = {
  /**
   * Execute a query on a specific connection
   * @param {string} connectionId - Connection ID
   * @param {string} queryContent - SQL/query string
   * @returns {Promise<object>} - Query execution result
   */
  executeQuery: async (connectionId, queryContent) => {
    return apiFetch('/queries/execute', 'POST', {
      connectionId,
      query: queryContent,
    });
  },
};

/**
 * Transaction API calls
 */
export const transactionAPI = {
  /**
   * Commit a transaction
   * @param {string} transactionId - Transaction ID
   * @returns {Promise<object>} - Transaction confirmation
   */
  commitTransaction: async (transactionId) => {
    return apiFetch(`/transactions/${transactionId}/commit`, 'PUT');
  },

  /**
   * Rollback a transaction
   * @param {string} transactionId - Transaction ID
   * @returns {Promise<object>} - Rollback confirmation
   */
  rollbackTransaction: async (transactionId) => {
    return apiFetch(`/transactions/${transactionId}/rollback`, 'PUT');
  },
};

/**
 * WAL (Write-Ahead Log) API calls
 */
export const walAPI = {
  /**
   * Get WAL entries for a transaction
   * @param {string} transactionId - Transaction ID
   * @returns {Promise<array>} - Array of WAL entries
   */
  getWalEntries: async (transactionId) => {
    return apiFetch(`/wal/entries/${transactionId}`, 'GET');
  },
};

export default {
  connectionAPI,
  queryAPI,
  transactionAPI,
  walAPI,
};