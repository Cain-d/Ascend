import { useState } from 'react';
import Dashboard from "./dashboard.jsx";
import AnalyticsDashboard from "./components/Analytics/AnalyticsDashboard.jsx";
import './App.css';
import './index.css';

function App() {
  const [currentView, setCurrentView] = useState('dashboard');

  const renderNavigation = () => (
    <nav className="bg-white shadow-sm border-b">
      <div className="max-w-6xl mx-auto px-6">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center space-x-8">
            <h1 className="text-xl font-bold text-gray-800">Ascend</h1>
            <div className="flex space-x-4">
              <button
                onClick={() => setCurrentView('dashboard')}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  currentView === 'dashboard'
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-gray-600 hover:text-gray-800 hover:bg-gray-100'
                }`}
              >
                Dashboard
              </button>
              <button
                onClick={() => setCurrentView('analytics')}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  currentView === 'analytics'
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-gray-600 hover:text-gray-800 hover:bg-gray-100'
                }`}
              >
                Analytics
              </button>
            </div>
          </div>
        </div>
      </div>
    </nav>
  );

  const renderCurrentView = () => {
    switch (currentView) {
      case 'analytics':
        return <AnalyticsDashboard />;
      case 'dashboard':
      default:
        return <Dashboard />;
    }
  };

  return (
    <div className="App min-h-screen bg-gray-50">
      {renderNavigation()}
      {renderCurrentView()}
    </div>
  );
}

export default App;


