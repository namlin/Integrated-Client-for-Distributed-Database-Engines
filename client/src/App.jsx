import { DBClientProvider } from './contexts/DBClientContext';
import { Dashboard } from './components/Dashboard';
import './App.css';

function App() {
  return (
    <DBClientProvider>
      <Dashboard />
    </DBClientProvider>
  );
}

export default App;
