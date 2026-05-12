import React, { useContext } from 'react';
import { DBClientContext } from '../contexts/DBClientContext';

export function ResultsPanel() {
  const { activeTab, setActiveTab, resultsData, walEntries, activeTransaction } =
    useContext(DBClientContext);

  const tabs = ['Resultados', 'Bitácora (WAL)', 'Recuperación', 'Consola'];

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
        {activeTab === 'Resultados' && (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-300 bg-gray-100">
                  <th className="px-4 py-2 text-left font-semibold text-gray-900">
                    carne
                  </th>
                  <th className="px-4 py-2 text-left font-semibold text-gray-900">
                    nombre
                  </th>
                  <th className="px-4 py-2 text-left font-semibold text-gray-900">
                    nota_ant
                  </th>
                  <th className="px-4 py-2 text-left font-semibold text-gray-900">
                    nota_nueva
                  </th>
                </tr>
              </thead>
              <tbody>
                {resultsData.map((row, idx) => (
                  <tr key={idx} className="border-b border-gray-200 hover:bg-gray-50">
                    <td className="px-4 py-2 text-gray-900">{row.carne}</td>
                    <td className="px-4 py-2 text-gray-900">{row.nombre}</td>
                    <td className="px-4 py-2 text-gray-900">{row.nota_ant}</td>
                    <td className="px-4 py-2 text-gray-900">{row.nota_nueva}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {activeTab === 'Bitácora (WAL)' && (
          <div>
            <div className="flex gap-2 mb-4">
              <span className="px-3 py-1 rounded-full bg-blue-100 text-blue-800 text-xs font-medium">
                Filtrar: {activeTransaction}
              </span>
              <span className="px-3 py-1 rounded-full bg-gray-100 text-gray-800 text-xs font-medium">
                Todas las ops
              </span>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-300 bg-gray-100">
                    <th className="px-4 py-2 text-left font-semibold text-gray-900">
                      TID
                    </th>
                    <th className="px-4 py-2 text-left font-semibold text-gray-900">
                      Op
                    </th>
                    <th className="px-4 py-2 text-left font-semibold text-gray-900">
                      Tabla
                    </th>
                    <th className="px-4 py-2 text-left font-semibold text-gray-900">
                      Before image
                    </th>
                    <th className="px-4 py-2 text-left font-semibold text-gray-900">
                      After image
                    </th>
                    <th className="px-4 py-2 text-left font-semibold text-gray-900">
                      Timestamp
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {walEntries.map((entry, idx) => (
                    <tr key={idx} className="border-b border-gray-200 hover:bg-gray-50">
                      <td className="px-4 py-2 text-gray-900 font-mono">
                        {entry.tid}
                      </td>
                      <td className="px-4 py-2 text-gray-900">{entry.op}</td>
                      <td className="px-4 py-2 text-gray-900">{entry.tabla}</td>
                      <td className="px-4 py-2 text-gray-600 text-xs font-mono">
                        {entry.before}
                      </td>
                      <td className="px-4 py-2 text-gray-600 text-xs font-mono">
                        {entry.after}
                      </td>
                      <td className="px-4 py-2 text-gray-600 text-xs">
                        {entry.timestamp}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {activeTab === 'Recuperación' && (
          <div className="text-center py-8 text-gray-500">
            <p>Funcionalidad de recuperación disponible próximamente</p>
          </div>
        )}

        {activeTab === 'Consola' && (
          <div className="text-center py-8 text-gray-500">
            <p>Consola disponible próximamente</p>
          </div>
        )}
      </div>
    </div>
  );
}
