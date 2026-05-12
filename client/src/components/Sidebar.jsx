import React, { useContext } from 'react';
import { DBClientContext } from '../contexts/DBClientContext';

function ConnectionBadge({ status, color }) {
  const colorMap = {
    green: 'bg-green-100 text-green-800',
    gray: 'bg-gray-100 text-gray-800',
    red: 'bg-red-100 text-red-800',
  };

  return (
    <span className={`px-2 py-1 rounded text-xs font-medium ${colorMap[color]}`}>
      {status}
    </span>
  );
}

function TransactionBadge({ status, badge }) {
  const badgeMap = {
    green: 'bg-green-100 text-green-800',
    orange: 'bg-orange-100 text-orange-800',
    gray: 'bg-gray-100 text-gray-800',
  };

  return (
    <span className={`px-2 py-1 rounded text-xs font-bold ${badgeMap[badge]}`}>
      {status}
    </span>
  );
}

export function Sidebar() {
  const { activeEngine, setActiveEngine, connections, transactions } =
    useContext(DBClientContext);

  return (
    <aside className="w-64 bg-gray-50 border-r border-gray-200 flex flex-col overflow-hidden">
      {/* Connections Section */}
      <div className="flex-1 overflow-y-auto">
        <div className="p-4 border-b border-gray-200">
          <h2 className="text-sm font-bold text-gray-900 mb-3">CONEXIONES</h2>
          <div className="space-y-2">
            {connections.map((conn) => (
              <button
                key={conn.id}
                onClick={() => setActiveEngine(conn.name)}
                className={`w-full text-left p-3 rounded-lg transition-colors ${
                  activeEngine === conn.name
                    ? 'bg-blue-100 border-2 border-blue-400'
                    : 'bg-white border border-gray-200 hover:bg-gray-100'
                }`}
              >
                <div className="flex items-start justify-between mb-1">
                  <span className="font-medium text-sm text-gray-900">
                    {conn.name}
                  </span>
                  <ConnectionBadge status={conn.status} color={conn.color} />
                </div>
                <div className="text-xs text-gray-600">
                  {conn.address}
                  {conn.node && ` - ${conn.node}`}
                </div>
              </button>
            ))}
          </div>
          <button className="w-full mt-3 py-2 px-3 rounded-lg bg-gray-200 text-gray-700 text-sm font-medium hover:bg-gray-300 transition-colors">
            + Nueva conexión
          </button>
        </div>

        {/* Transactions Section */}
        <div className="p-4">
          <h2 className="text-sm font-bold text-gray-900 mb-3">TRANSACCIONES</h2>
          <div className="space-y-2">
            {transactions.map((txn) => (
              <div
                key={txn.id}
                className="p-3 rounded-lg bg-white border border-gray-200 flex items-center justify-between"
              >
                <span className="text-sm font-medium text-gray-900">
                  {txn.id}
                </span>
                <TransactionBadge status={txn.status} badge={txn.badge} />
              </div>
            ))}
          </div>
        </div>
      </div>
    </aside>
  );
}
