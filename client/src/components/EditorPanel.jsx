import React, { useContext } from 'react';
import { DBClientContext } from '../contexts/DBClientContext';

export function EditorPanel() {
  const {
    activeEngine,
    activeTransaction,
    queryContent, setQueryContent,
    executeQuery, commitTransaction, rollbackTransaction,
    isExecuting,
    queryError,
  } = useContext(DBClientContext);

  return (
    <div className="flex-1 flex flex-col bg-white border-r border-gray-200">
      {/* Context Bar */}
      <div className="border-b border-gray-200 px-4 py-3 flex items-center justify-between bg-gray-50">
        <span className="text-sm text-gray-700">
          <span className="font-semibold">Motor activo:</span>{' '}
          {activeEngine ?? <span className="text-gray-400 italic">sin conexión</span>}
        </span>
        <span className="text-sm text-gray-700">
          {activeTransaction ? (
            <>
              <span className="font-semibold">{activeTransaction}</span> en curso
            </>
          ) : (
            <span className="text-gray-400 italic">sin transacción activa</span>
          )}
        </span>
      </div>

      {/* Query Error */}
      {queryError && (
        <div className="mx-4 mt-3 p-3 bg-red-50 border border-red-300 rounded text-sm text-red-700">
          {queryError}
        </div>
      )}

      {/* Query Editor */}
      <div className="flex-1 flex flex-col p-4">
        <textarea
          value={queryContent}
          onChange={(e) => setQueryContent(e.target.value)}
          className="flex-1 p-3 border border-gray-300 rounded-lg font-mono text-sm text-gray-900 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          placeholder="Escribe tu consulta aquí…"
          disabled={isExecuting}
        />
      </div>

      {/* Action Buttons */}
      <div className="border-t border-gray-200 px-4 py-3 flex gap-3 bg-gray-50">
        <button
          onClick={executeQuery}
          disabled={isExecuting || !activeEngine}
          className="px-6 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 disabled:bg-blue-300 disabled:cursor-not-allowed transition-colors"
        >
          {isExecuting ? 'Ejecutando…' : 'Ejecutar'}
        </button>
        <button
          onClick={rollbackTransaction}
          disabled={!activeTransaction || isExecuting}
          className="px-6 py-2 border-2 border-gray-300 text-gray-700 font-medium rounded-lg hover:bg-gray-100 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >
          ROLLBACK
        </button>
        <button
          onClick={commitTransaction}
          disabled={!activeTransaction || isExecuting}
          className="px-6 py-2 border-2 border-gray-300 text-gray-700 font-medium rounded-lg hover:bg-gray-100 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >
          COMMIT
        </button>
      </div>
    </div>
  );
}
