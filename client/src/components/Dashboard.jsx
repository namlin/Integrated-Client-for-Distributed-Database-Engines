import React from 'react';
import { Header } from './Header';
import { Sidebar } from './Sidebar';
import { EditorPanel } from './EditorPanel';
import { ResultsPanel } from './ResultsPanel';
import { StatusBar } from './StatusBar';

export function Dashboard() {
  return (
    <div className="h-screen flex flex-col bg-white overflow-hidden">
      {/* Header */}
      <Header />

      {/* Main Content Area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar */}
        <Sidebar />

        {/* Center + Right Content */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Editor Panel */}
          <EditorPanel />

          {/* Results Tabs Panel */}
          <ResultsPanel />
        </div>
      </div>

      {/* Status Bar Footer */}
      <StatusBar />
    </div>
  );
}
