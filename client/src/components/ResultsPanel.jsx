import React, { useContext, useState } from 'react';
import { DBClientContext } from '../contexts/DBClientContext';

export function ResultsPanel() {
  const {
    activeTab, setActiveTab,
    resultsData, resultsColumns,
    walEntries,
    consoleLog,
    resultsMessage,
    resultsMessageType,
  } = useContext(DBClientContext);

  const [walFilter, setWalFilter] = useState('');
  const tabs = ['Resultados', 'Bitácora (WAL)', 'Consola'];

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
            className={`px-4 py-3 text-sm font-medium transition-colors ${activeTab === tab
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
          <div className="overflow-x-auto space-y-4">
            {resultsMessage && (
              <div className={`p-4 rounded-lg flex items-center gap-3 border shadow-sm transition-all duration-300 ${
                resultsMessageType === 'success'
                  ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
                  : 'bg-rose-50 border-rose-200 text-rose-800'
              }`}>
                {resultsMessageType === 'success' ? (
                  <svg className="w-5 h-5 text-emerald-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                ) : (
                  <svg className="w-5 h-5 text-rose-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                )}
                <span className="font-medium text-sm">{resultsMessage}</span>
              </div>
            )}
            {resultsColumns.length === 0 ? (
              !resultsMessage && (
                <p className="text-gray-400 text-sm italic">No hay resultados aún. Ejecuta una consulta.</p>
              )
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
                        <span className={`px-1.5 py-0.5 rounded text-xs font-bold ${entry.op === 'COMMIT' ? 'bg-green-100 text-green-800' :
                            entry.op === 'ABORT' ? 'bg-red-100 text-red-800' :
                              entry.op === 'BEGIN' ? 'bg-blue-100 text-blue-800' :
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
