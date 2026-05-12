import React, { useContext } from 'react';
import { DBClientContext } from '../contexts/DBClientContext';

export function StatusBar() {
  const { recoveryProtocol } = useContext(DBClientContext);

  return (
    <footer className="h-8 bg-gray-900 text-white text-xs px-6 py-1.5 flex items-center gap-6 border-t border-gray-800">
      <div className="flex items-center gap-2">
        <div className="w-2 h-2 rounded-full bg-green-500" />
        <span>PostgreSQL OK</span>
      </div>
      <span>Protocolo: {recoveryProtocol}</span>
      <span>WAL: 12 entradas</span>
      <span>TXN activas: 1</span>
    </footer>
  );
}
