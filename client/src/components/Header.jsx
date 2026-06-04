import React, { useContext, useState, useEffect } from 'react';
import { DBClientContext } from '../contexts/DBClientContext';

export function Header() {
  const {
    recoveryProtocol, setRecoveryProtocol,
    sessionActive,
    activeTransaction,
    transactions,
    simulateFailure,
    postCommitTids,
    simulatePostCommitFailure,
    dismissPostCommitWindow,
  } = useContext(DBClientContext);

  const protocols = ['No-Undo/No-Redo', 'No-Undo/Redo', 'Undo/No-Redo', 'Undo/Redo'];

  // Countdown timer for the post-commit window
  const [countdown, setCountdown] = useState(15);
  useEffect(() => {
    if (postCommitTids.length === 0) {
      setCountdown(15);
      return;
    }
    setCountdown(15);
    const interval = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          clearInterval(interval);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(interval);
  }, [postCommitTids]);

  return (
    <>
      <header className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
        {/* Left: Title and Session */}
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-bold text-gray-900">DBClient UCR</h1>
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${sessionActive ? 'bg-green-500' : 'bg-gray-400'}`} />
            <span className="text-sm text-gray-600">
              {sessionActive ? 'Sesión activa' : 'Sesión inactiva'}
            </span>
          </div>
        </div>

        {/* Center: Protocol Selector */}
        <div className="flex gap-2 bg-gray-100 p-1 rounded-full">
          {protocols.map((p) => (
            <button
              key={p}
              onClick={() => setRecoveryProtocol(p)}
              className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${
                recoveryProtocol === p
                  ? 'bg-white text-blue-600 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              {p}
            </button>
          ))}
        </div>

        {/* Right: Simulate Failure */}
        <button
          onClick={simulateFailure}
          disabled={!activeTransaction && !transactions.some((t) => t.status === 'ACTIVE')}
          className="px-4 py-2 border-2 border-amber-400 text-amber-600 font-medium rounded-lg hover:bg-amber-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          title={activeTransaction || transactions.some((t) => t.status === 'ACTIVE') ? `Simular fallo en transacción activa` : 'Sin transacción activa'}
        >
          Simular fallo
        </button>
      </header>

      {/* Post-commit failure notification banner */}
      {postCommitTids.length > 0 && (
        <div className="bg-amber-50 border-b-2 border-amber-300 px-6 py-3 flex items-center justify-between animate-slide-down">
          <div className="flex items-center gap-3">
            <span className="text-amber-600 text-lg">⚠️</span>
            <div>
              <p className="text-sm font-semibold text-amber-900">
                Transacción comprometida — Ventana para simular fallo post-commit
              </p>
              <p className="text-xs text-amber-700">
                Simula un fallo ahora para probar la recuperación con REDO ({recoveryProtocol}).
                Se revertirán los cambios en disco como si las páginas no se hubieran escrito.
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            {postCommitTids.map((tid) => (
              <button
                key={tid}
                onClick={() => simulatePostCommitFailure(tid)}
                className="px-4 py-2 bg-amber-500 text-white font-medium rounded-lg hover:bg-amber-600 transition-colors text-sm shadow-sm"
              >
                Simular fallo en {tid}
              </button>
            ))}
            <span className="text-xs text-amber-600 font-mono tabular-nums w-8 text-center">
              {countdown}s
            </span>
            <button
              onClick={dismissPostCommitWindow}
              className="text-amber-400 hover:text-amber-600 transition-colors text-lg leading-none"
              title="Cerrar"
            >
              ✕
            </button>
          </div>
        </div>
      )}
    </>
  );
}
