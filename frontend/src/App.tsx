import React, { useState } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { Layout } from './components/Layout';
import { Login } from './pages/Login';
import { Dashboard } from './pages/Dashboard';
import { Workspace } from './pages/Workspace';
import { Documents } from './pages/Documents';
import { Policies } from './pages/Policies';
import { Audit } from './pages/Audit';

const AppContent: React.FC = () => {
  const { isAuthenticated, loading } = useAuth();
  
  const [activeTab, setActiveTab] = useState('dashboard');
  const [selectedExceptionId, setSelectedExceptionId] = useState<string | null>(null);
  const [refreshStatsTrigger, setRefreshStatsTrigger] = useState(0);

  const handleSelectException = (id: string) => {
    setSelectedExceptionId(id);
    setActiveTab('workspace');
  };

  const handleBackToQueue = () => {
    setActiveTab('dashboard');
  };

  const handleStateChange = () => {
    setRefreshStatsTrigger(prev => prev + 1);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center text-slate-400 text-xs">
        <span className="h-6 w-6 rounded-full border-2 border-indigo-500 border-t-transparent animate-spin mb-3" />
        Loading Supervity Exception Resolution Workbench...
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Login />;
  }

  return (
    <Layout 
      activeTab={activeTab} 
      setActiveTab={setActiveTab} 
      selectedExceptionId={selectedExceptionId}
    >
      {activeTab === 'dashboard' && (
        <Dashboard 
          onSelectException={handleSelectException} 
          refreshStatsTrigger={refreshStatsTrigger}
        />
      )}
      
      {activeTab === 'workspace' && selectedExceptionId && (
        <Workspace 
          exceptionId={selectedExceptionId} 
          onBackToQueue={handleBackToQueue}
          onStateChange={handleStateChange}
        />
      )}

      {activeTab === 'workspace' && !selectedExceptionId && (
        <div className="flex flex-col items-center justify-center h-[60vh] text-slate-400 space-y-3">
          <p className="text-sm font-bold">No exception selected.</p>
          <button onClick={() => setActiveTab('dashboard')} className="text-xs text-indigo-600 font-bold hover:underline">
            ← Return to Exceptions Queue
          </button>
        </div>
      )}
      
      {activeTab === 'documents' && <Documents />}
      {activeTab === 'policies' && <Policies />}
      {activeTab === 'audit' && <Audit />}
    </Layout>
  );
};

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App;
