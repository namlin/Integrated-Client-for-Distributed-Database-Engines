import React, { useContext } from 'react';
import { DBClientContext } from '../contexts/DBClientContext';

export function Header() {
  const { recoveryProtocol, setRecoveryProtocol, sessionActive } =
    useContext(DBClientContext);

  const protocols = ['No-Undo/No-Redo', 'No-Undo/Redo', 'Undo/No-Redo', 'Undo/Redo'];

  return (
    <header className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
      {/* Left: Title and Session */}
      <div className="flex items-center gap-3">
        <h1 className="text-2xl font-bold text-gray-900">DBClient UCR</h1>
        <div className="flex items-center gap-2">
          <div
            className={`w-2 h-2 rounded-full ${
              sessionActive ? 'bg-green-500' : 'bg-gray-400'
            }`}
          />
          <span className="text-sm text-gray-600">
            {sessionActive ? 'Sesión activa' : 'Sesión inactiva'}
          </span>
        </div>
      </div>

      {/* Center: Protocol Selector */}
      <div className="flex gap-2 bg-gray-100 p-1 rounded-full">
        {protocols.map((protocol) => (
          <button
            key={protocol}
            onClick={() => setRecoveryProtocol(protocol)}
            className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${
              recoveryProtocol === protocol
                ? 'bg-white text-blue-600 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            {protocol}
          </button>
        ))}
      </div>

      {/* Right: Simulate Failure Button */}
      <button className="px-4 py-2 border-2 border-amber-400 text-amber-600 font-medium rounded-lg hover:bg-amber-50 transition-colors">
        Simular fallo
      </button>
    </header>
  );
}
