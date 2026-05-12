import React, { createContext, useState } from 'react';

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

  const [connections] = useState([
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

  const [resultsData] = useState([
    {
      carne: 'B12345',
      nombre: 'Fernández López, Ana',
      nota_ant: 88,
      nota_nueva: 95,
    },
  ]);

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
