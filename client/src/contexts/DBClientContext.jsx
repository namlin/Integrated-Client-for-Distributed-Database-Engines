import React, { createContext, useState } from 'react';
import { connectionAPI } from '../config/configApi';

export const DBClientContext = createContext();

export function DBClientProvider({ children }) {
  const [activeEngine, setActiveEngine] = useState('PostgreSQL');
  const [activeTransaction, setActiveTransaction] = useState('TXN-0043');
  const [recoveryProtocol, setRecoveryProtocol] = useState('No-Undo/Redo');
  const [queryContent, setQueryContent] = useState(
    `BEGIN;
UPDATE estudiantes
SET nota = 95
WHERE carne = 'B12345';
-- COMMIT / ROLLBACK`
  );
  const [activeTab, setActiveTab] = useState('Resultados');
  const [sessionActive, setSessionActive] = useState(true);

  // Modal and connection management state
  const [showConnectionModal, setShowConnectionModal] = useState(false);
  const [isLoadingConnection, setIsLoadingConnection] = useState(false);
  const [connectionError, setConnectionError] = useState(null);
  const [editingConnection, setEditingConnection] = useState(null);

  // The conections with the nodes will be asked on the backend here, but for now we will hardcode them
  const [connections, setConnections] = useState([
    {
      id: 'pg',
      name: 'PostgreSQL',
      status: 'connected',
      color: 'green',
      address: 'localhost:5432',
      node: 'nodo-1',
    },
    {
      id: 'mongo',
      name: 'MongoDB',
      status: 'connected',
      color: 'green',
      address: 'localhost:27017',
      node: 'nodo-2',
    },
    {
      id: 'mysql',
      name: 'MySQL',
      status: 'desconectado',
      color: 'gray',
      address: '192.168.1.5',
      node: '',
    },
    {
      id: 'redis',
      name: 'Redis',
      status: 'error',
      color: 'red',
      address: 'localhost:6379',
      node: '',
    },
  ]);

  // The transactions will be asked on the backend here, but for now we will hardcode them
  // BITACORA
  const [transactions] = useState([
    {
      id: 'TXN-0042',
      status: 'COMMIT',
      badge: 'green',
    },
    {
      id: 'TXN-0043',
      status: 'ACTIVA',
      badge: 'orange',
    },
    {
      id: 'TXN-0041',
      status: 'ABORT',
      badge: 'gray',
    },
  ]);

  // The results and the wal entries will be asked on the backend here, but for now we will hardcode them
  // BITACORA
  const [resultsData] = useState([
    {
      carne: 'B12345',
      nombre: 'Fernández López, Ana',
      nota_ant: 88,
      nota_nueva: 95,
    },
  ]);

  // BITACORA
  const [walEntries] = useState([
    {
      tid: '0043',
      op: 'BEGIN',
      tabla: '-',
      before: '-',
      after: '-',
      timestamp: '2026-05-11 14:22:00',
    },
    {
      tid: '0043',
      op: 'UPDATE',
      tabla: 'estudiantes',
      before: "{'nota': 88, 'carne': 'B12345'}",
      after: "{'nota': 95, 'carne': 'B12345'}",
      timestamp: '2026-05-11 14:22:05',
    },
  ]);

  // Connection management functions
  const addConnection = async (connectionData) => {
    setIsLoadingConnection(true);
    setConnectionError(null);
    try {
      const newConnection = await connectionAPI.createConnection(connectionData);
      // Add the new connection to the local state
      setConnections([...connections, newConnection]);
      setShowConnectionModal(false);
      setEditingConnection(null);
    } catch (error) {
      setConnectionError(error.message);
      console.error('Error adding connection:', error);
    } finally {
      setIsLoadingConnection(false);
    }
  };

  const disconnectConnection = async (connectionId) => {
    setIsLoadingConnection(true);
    setConnectionError(null);
    try {
      const updatedConnection = await connectionAPI.disconnectConnection(connectionId);
      // Update the connection status in local state
      setConnections(
        connections.map((conn) =>
          conn.id === connectionId ? updatedConnection : conn
        )
      );

      // If the disconnected connection was active, switch to another
      if (activeEngine === connectionId) {
        const availableConnection = connections.find((conn) => conn.id !== connectionId);
        if (availableConnection) {
          setActiveEngine(availableConnection.name);
        }
      }
    } catch (error) {
      setConnectionError(error.message);
      console.error('Error disconnecting connection:', error);
    } finally {
      setIsLoadingConnection(false);
    }
  };

  const deleteConnection = async (connectionId) => {
    setIsLoadingConnection(true);
    setConnectionError(null);
    try {
      await connectionAPI.deleteConnection(connectionId);
      // Remove the connection from local state
      setConnections(connections.filter((conn) => conn.id !== connectionId));

      // If the deleted connection was active, switch to another
      if (activeEngine === connectionId) {
        const availableConnection = connections.find((conn) => conn.id !== connectionId);
        if (availableConnection) {
          setActiveEngine(availableConnection.name);
        }
      }
    } catch (error) {
      setConnectionError(error.message);
      console.error('Error deleting connection:', error);
    } finally {
      setIsLoadingConnection(false);
    }
  };

  const value = {
    activeEngine,
    setActiveEngine,
    activeTransaction,
    setActiveTransaction,
    recoveryProtocol,
    setRecoveryProtocol,
    queryContent,
    setQueryContent,
    activeTab,
    setActiveTab,
    sessionActive,
    setSessionActive,
    connections,
    setConnections,
    showConnectionModal,
    setShowConnectionModal,
    isLoadingConnection,
    connectionError,
    editingConnection,
    setEditingConnection,
    addConnection,
    disconnectConnection,
    deleteConnection,
    transactions,
    resultsData,
    walEntries,
  };

  return (
    <DBClientContext.Provider value={value}>
      {children}
    </DBClientContext.Provider>
  );
}