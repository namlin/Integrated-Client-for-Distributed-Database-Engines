import React, { useContext, useState } from 'react';
import { DBClientContext } from '../contexts/DBClientContext';

export function ResultsPanel() {
  const {
    activeTab, setActiveTab,
    resultsData, resultsColumns,
    walEntries,
    transactions,
    recoveryResult, runRecovery,
    activeTransaction,
    consoleLog,
    recoveryProtocol,
  } = useContext(DBClientContext);

  const [walFilter, setWalFilter] = useState('');
  const tabs = ['Resultados', 'Bitácora (WAL)', 'Recuperación', 'Consola'];

  const filteredWal = walFilter
    ? walEntries.filter(
        (e) =>
          e.tid.includes(walFilter) ||
          e.op.toLowerCase().includes(walFilter.toLowerCase()) ||
          e.tabla.toLowerCase().includes(walFilter.toLowerCase())
      )
    : walEntries;

  return (
    <div className="bg-white border-t border-gray-200 flex flex-col h-1/3">
      {/* Tab Navigation */}
      <div className="flex border-b border-gray-200 bg-gray-50">
        {tabs.map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-3 text-sm font-medium transition-colors ${
              activeTab === tab
                ? 'border-b-2 border-blue-500 text-blue-600 bg-white'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="flex-1 overflow-auto p-4">

        {/* ── RESULTS ── */}
        {activeTab === 'Resultados' && (
          <div className="overflow-x-auto">
            {resultsColumns.length === 0 ? (
              <p className="text-gray-400 text-sm italic">No hay resultados aún. Ejecuta una consulta.</p>
            ) : (
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-300 bg-gray-100">
                    {resultsColumns.map((col) => (
                      <th key={col} className="px-4 py-2 text-left font-semibold text-gray-900">
                        {col}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {resultsData.length === 0 ? (
                    <tr>
                      <td colSpan={resultsColumns.length} className="text-center py-6 text-gray-400 text-sm italic">
                        No hay filas (tabla vacía)
                      </td>
                    </tr>
                  ) : (
                    resultsData.map((row, idx) => (
                      <tr key={idx} className="border-b border-gray-200 hover:bg-gray-50">
                        {resultsColumns.map((col) => (
                          <td key={col} className="px-4 py-2 text-gray-900">
                            {row[col] === null ? <span className="text-gray-400">NULL</span> : String(row[col])}
                          </td>
                        ))}
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            )}
          </div>
        )}

        {/* ── WAL ── */}
        {activeTab === 'Bitácora (WAL)' && (
          <div>
            <div className="flex gap-2 mb-3 items-center">
              <input
                type="text"
                placeholder="Filtrar por TID, operación o tabla…"
                value={walFilter}
                onChange={(e) => setWalFilter(e.target.value)}
                className="px-3 py-1 border border-gray-300 rounded text-xs w-64"
              />
              <span className="text-xs text-gray-500">{filteredWal.length} entrada(s)</span>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-300 bg-gray-100">
                    {['TID', 'Op', 'Tabla', 'Before image', 'After image', 'Timestamp'].map((h) => (
                      <th key={h} className="px-4 py-2 text-left font-semibold text-gray-900">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {filteredWal.map((entry, idx) => (
                    <tr key={idx} className="border-b border-gray-200 hover:bg-gray-50">
                      <td className="px-4 py-2 text-gray-900 font-mono">{entry.tid}</td>
                      <td className="px-4 py-2">
                        <span className={`px-1.5 py-0.5 rounded text-xs font-bold ${
                          entry.op === 'COMMIT' ? 'bg-green-100 text-green-800' :
                          entry.op === 'ABORT'  ? 'bg-red-100 text-red-800' :
                          entry.op === 'BEGIN'  ? 'bg-blue-100 text-blue-800' :
                          'bg-gray-100 text-gray-800'
                        }`}>{entry.op}</span>
                      </td>
                      <td className="px-4 py-2 text-gray-900">{entry.tabla}</td>
                      <td className="px-4 py-2 text-gray-600 text-xs font-mono max-w-xs truncate">{entry.before}</td>
                      <td className="px-4 py-2 text-gray-600 text-xs font-mono max-w-xs truncate">{entry.after}</td>
                      <td className="px-4 py-2 text-gray-600 text-xs">{entry.timestamp?.slice(0, 19)}</td>
                    </tr>
                  ))}
                  {filteredWal.length === 0 && (
                    <tr>
                      <td colSpan={6} className="text-center py-6 text-gray-400 text-sm italic">
                        No hay entradas en la bitácora.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* ── RECOVERY ── */}
        {activeTab === 'Recuperación' && (
          <div className="space-y-4">
            {/* Protocol Info */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
              <div className="flex gap-4 items-start">
                <div className="flex-1">
                  <p className="text-sm font-semibold text-blue-900 mb-2">Protocolo de recuperación activo:</p>
                  <p className="text-lg font-bold text-blue-700 mb-3">{recoveryProtocol}</p>
                  <p className="text-xs text-blue-800 leading-relaxed mb-2">
                    {recoveryProtocol === 'Undo/Redo' && 
                      'Este protocolo utiliza UNDO (deshacer cambios) para transacciones abortadas y REDO (rehacer cambios) para transacciones comprometidas que se perdieron durante un fallo.'
                    }
                    {recoveryProtocol === 'No-Undo/Redo' && 
                      'Este protocolo utiliza solo REDO (rehacer cambios). Las escrituras se diferían hasta el commit, evitando la necesidad de UNDO.'
                    }
                    {recoveryProtocol === 'Undo/No-Redo' && 
                      'Este protocolo utiliza solo UNDO (deshacer cambios). Las transacciones se escribían inmediatamente, pero los cambios no comprometidos se revierten.'
                    }
                    {recoveryProtocol === 'No-Undo/No-Redo' && 
                      'Este protocolo no utiliza ni UNDO ni REDO. Las operaciones se bufferean hasta el commit y se aplican atómicamente.'
                    }
                  </p>
                  <p className="text-xs text-blue-700 mt-2">
                    <strong>Qué ocurrirá:</strong> Se analizará el registro de transacciones y se aplicarán las acciones de recuperación necesarias.
                  </p>
                </div>
              </div>
            </div>

            {/* Run recovery on a past transaction */}
            <div className="flex gap-3 items-center">
              <span className="text-sm text-gray-700 font-medium">Ejecutar recuperación:</span>
              {transactions.filter((t) => ['FAILED', 'ABORTED', 'COMMITTED'].includes(t.status)).slice(0, 5).map((t) => (
                <button
                  key={t.id}
                  onClick={() => runRecovery(t.id, recoveryProtocol)}
                  className="px-3 py-1 text-xs font-medium border border-blue-400 text-blue-600 rounded hover:bg-blue-50 transition-colors"
                >
                  {t.id} ({t.status})
                </button>
              ))}
              {transactions.filter((t) => ['FAILED', 'ABORTED', 'COMMITTED'].includes(t.status)).length === 0 && (
                <span className="text-xs text-gray-400 italic">Sin transacciones para recuperar. Simula un fallo primero.</span>
              )}
            </div>

            {/* Recovery result */}
            {recoveryResult && (
              <div className="border border-gray-200 rounded-lg p-4 bg-gray-50">
                <div className="flex gap-4 text-xs text-gray-600 mb-3">
                  <span><strong>TID:</strong> {recoveryResult.tid}</span>
                  <span><strong>Protocolo:</strong> {recoveryResult.protocol}</span>
                  <span><strong>Estado:</strong>{' '}
                    <span className="text-green-700 font-semibold">{recoveryResult.status}</span>
                  </span>
                </div>
                <p className="text-xs text-gray-500 mb-1"><strong>Antes:</strong> {recoveryResult.before_state}</p>
                <p className="text-xs text-gray-500 mb-3"><strong>Después:</strong> {recoveryResult.after_state}</p>
                <div className="bg-gray-900 text-green-400 rounded p-3 font-mono text-xs space-y-1 max-h-48 overflow-y-auto">
                  {recoveryResult.recovery_actions.map((action, i) => (
                    <div key={i}>{action}</div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* ── CONSOLE ── */}
        {activeTab === 'Consola' && (
          <div className="bg-gray-900 text-green-400 rounded p-3 font-mono text-xs space-y-1 h-full overflow-y-auto">
            {consoleLog.length === 0 ? (
              <span className="text-gray-500">La consola está vacía.</span>
            ) : (
              consoleLog.map((line, i) => <div key={i}>{line}</div>)
            )}
          </div>
        )}
      </div>
    </div>
  );
}
