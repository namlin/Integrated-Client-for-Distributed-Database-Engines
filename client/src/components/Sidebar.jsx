import React, { useContext, useState } from 'react';
import { DBClientContext } from '../contexts/DBClientContext';
import { NewConnectionModal } from './NewConnectionModal';

function ConnectionBadge({ status, color }) {
  const colorMap = {
    green: 'bg-green-100 text-green-800',
    gray: 'bg-gray-100 text-gray-800',
    red: 'bg-red-100 text-red-800',
  };
  return (
    <span className={`px-2 py-1 rounded text-xs font-medium ${colorMap[color] ?? colorMap.gray}`}>
      {status}
    </span>
  );
}

function TransactionBadge({ status, badge }) {
  const badgeMap = {
    green: 'bg-green-100 text-green-800',
    orange: 'bg-orange-100 text-orange-800',
    red: 'bg-red-100 text-red-800',
    gray: 'bg-gray-100 text-gray-800',
  };
  return (
    <span className={`px-2 py-1 rounded text-xs font-bold ${badgeMap[badge] ?? badgeMap.gray}`}>
      {status}
    </span>
  );
}

export function Sidebar() {
  const {
    activeEngine,
    activeConnectionId,
    connections,
    transactions,
    setShowConnectionModal,
    disconnectConnection,
    reconnectConnection,
    deleteConnection,
    selectConnection,
    isLoadingConnection,
  } = useContext(DBClientContext);

  const [pendingDeleteConnection, setPendingDeleteConnection] = useState(null);

  return (
    <aside className="w-64 bg-gray-50 border-r border-gray-200 flex flex-col overflow-hidden">
      <div className="flex-1 overflow-y-auto">

        {/* Connections */}
        <div className="p-4 border-b border-gray-200">
          <h2 className="text-sm font-bold text-gray-900 mb-3">CONEXIONES</h2>
          <div className="space-y-2">
            {connections.map((conn) => (
              <div
                key={conn.id}
                className={`overflow-hidden rounded-lg transition-colors ${
                  activeConnectionId === conn.id
                    ? 'bg-blue-100 border-2 border-blue-400'
                    : 'bg-white border border-gray-200'
                }`}
              >
                <button
                  type="button"
                  onClick={() => selectConnection(conn)}
                  className="w-full px-3 py-3 text-left"
                >
                  <div className="flex items-start justify-between gap-2 mb-1">
                    <span className="font-medium text-sm text-gray-900">{conn.name}</span>
                    <ConnectionBadge status={conn.status} color={conn.color} />
                  </div>
                  <div className="text-xs text-gray-600">
                    {conn.address}{conn.node ? ` — ${conn.node}` : ''}
                  </div>
                </button>
                <div className="border-t border-gray-200 bg-gray-50 p-2 space-y-2">
                  {conn.status === 'connected' ? (
                    <button
                      type="button"
                      onClick={() => disconnectConnection(conn.id)}
                      disabled={isLoadingConnection}
                      className="w-full rounded-md bg-red-100 px-3 py-2 text-sm font-semibold text-red-700 transition-colors hover:bg-red-200 disabled:cursor-not-allowed disabled:opacity-50"
                      title={`Desconectar ${conn.name}`}
                      aria-label={`Desconectar ${conn.name}`}
                    >
                      Desconectar
                    </button>
                  ) : (
                    <button
                      type="button"
                      onClick={() => reconnectConnection(conn.id)}
                      disabled={isLoadingConnection}
                      className="w-full rounded-md bg-green-100 px-3 py-2 text-sm font-semibold text-green-700 transition-colors hover:bg-green-200 disabled:cursor-not-allowed disabled:opacity-50"
                      title={`Reconectar ${conn.name}`}
                      aria-label={`Reconectar ${conn.name}`}
                    >
                      Reconectar
                    </button>
                  )}
                  <button
                    type="button"
                    onClick={() => setPendingDeleteConnection(conn)}
                    disabled={isLoadingConnection}
                    className="w-full rounded-md border border-red-300 bg-white px-3 py-2 text-sm font-semibold text-red-700 transition-colors hover:bg-red-50 disabled:cursor-not-allowed disabled:opacity-50"
                    title={`Eliminar ${conn.name}`}
                    aria-label={`Eliminar ${conn.name}`}
                  >
                    Eliminar
                  </button>
                </div>
              </div>
            ))}
            {connections.length === 0 && (
              <p className="text-xs text-gray-400 italic">Sin conexiones. Agrega una.</p>
            )}
          </div>
          <button
            onClick={() => setShowConnectionModal(true)}
            disabled={isLoadingConnection}
            className="w-full mt-3 py-2 px-3 rounded-lg bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 disabled:bg-blue-400 disabled:cursor-not-allowed transition-colors"
          >
            + Nueva conexión
          </button>
        </div>

        {/* Transactions */}
        <div className="p-4">
          <h2 className="text-sm font-bold text-gray-900 mb-3">TRANSACCIONES</h2>
          <div className="space-y-2">
            {transactions.slice(0, 10).map((txn) => (
              <div
                key={txn.id}
                className="p-3 rounded-lg bg-white border border-gray-200 flex items-center justify-between"
              >
                <div>
                  <span className="text-sm font-medium text-gray-900">{txn.id}</span>
                  {txn.protocol && (
                    <p className="text-xs text-gray-400 truncate max-w-[120px]">{txn.protocol}</p>
                  )}
                </div>
                <TransactionBadge status={txn.status} badge={txn.badge} />
              </div>
            ))}
            {transactions.length === 0 && (
              <p className="text-xs text-gray-400 italic">Sin transacciones.</p>
            )}
          </div>
        </div>
      </div>

      <NewConnectionModal />

      {pendingDeleteConnection && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-4">
          <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-xl">
            <h3 className="text-lg font-bold text-gray-900">Eliminar conexión</h3>
            <p className="mt-2 text-sm text-gray-600">
              ¿Seguro que quieres eliminar <span className="font-semibold">{pendingDeleteConnection.name}</span>?
              Esta acción no se puede deshacer.
            </p>

            <div className="mt-6 flex gap-3">
              <button
                type="button"
                onClick={() => setPendingDeleteConnection(null)}
                disabled={isLoadingConnection}
                className="flex-1 rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
              >
                Cancelar
              </button>
              <button
                type="button"
                onClick={async () => {
                  const connectionToDelete = pendingDeleteConnection;
                  setPendingDeleteConnection(null);
                  await deleteConnection(connectionToDelete.id);
                }}
                disabled={isLoadingConnection}
                className="flex-1 rounded-md bg-red-600 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-red-700 disabled:cursor-not-allowed disabled:opacity-50"
              >
                Eliminar
              </button>
            </div>
          </div>
        </div>
      )}
    </aside>
  );
}