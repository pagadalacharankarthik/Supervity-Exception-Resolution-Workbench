import React from 'react';
import { useAuth } from '../context/AuthContext';
import { 
  LayoutDashboard, ShieldCheck, ClipboardList, 
  LogOut, FileText, Settings, User as UserIcon, FolderOpen
} from 'lucide-react';

interface LayoutProps {
  children: React.ReactNode;
  activeTab: string;
  setActiveTab: (tab: string) => void;
  selectedExceptionId: string | null;
}

export const Layout: React.FC<LayoutProps> = ({ 
  children, activeTab, setActiveTab, selectedExceptionId 
}) => {
  const { user, logout } = useAuth();

  const menuItems = [
    { id: 'dashboard', name: 'Exceptions Queue', icon: LayoutDashboard, role: 'all' },
    { id: 'workspace', name: 'Investigation Workspace', icon: FileText, role: 'all', disabled: !selectedExceptionId },
    { id: 'documents', name: 'Document Workbench', icon: FolderOpen, role: 'all' },
    { id: 'audit', name: 'Audit Timeline', icon: ClipboardList, role: 'all' },
    { id: 'policies', name: 'Resolution Policies', icon: Settings, role: 'manager' },
  ];

  return (
    <div className="flex h-screen bg-slate-50 overflow-hidden font-sans">
      {/* Sidebar */}
      <aside className="w-64 bg-slate-900 text-slate-100 flex flex-col flex-shrink-0 border-r border-slate-800">
        {/* Sidebar Header */}
        <div className="p-5 border-b border-slate-800 flex items-center space-x-3">
          <ShieldCheck className="h-8 w-8 text-indigo-400 flex-shrink-0" />
          <div>
            <h1 className="font-bold text-sm tracking-wide text-white leading-tight">Supervity</h1>
            <p className="text-[10px] text-slate-400 font-medium tracking-wider uppercase">Exception Workbench</p>
          </div>
        </div>

        {/* Sidebar Environment Tag */}
        <div className="px-5 py-2.5 bg-slate-950 border-b border-slate-800/50 flex flex-col">
          <span className="text-[10px] font-semibold text-indigo-400">Assessment Prototype</span>
          <span className="text-[9px] font-medium text-slate-500">Synthetic Data Only</span>
        </div>

        {/* Navigation Menu */}
        <nav className="flex-1 px-3 py-4 space-y-1.5 overflow-y-auto">
          {menuItems.map((item) => {
            const isManagerOnly = item.role === 'manager' && user?.role !== 'manager';
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            const isDisabled = item.disabled || isManagerOnly;

            return (
              <button
                key={item.id}
                disabled={isDisabled}
                onClick={() => !isDisabled && setActiveTab(item.id)}
                className={`w-full flex items-center px-4 py-2.5 rounded-lg text-xs font-semibold tracking-wide transition-all duration-200 text-left ${
                  isActive 
                    ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/20' 
                    : isDisabled
                      ? 'text-slate-600 cursor-not-allowed opacity-50'
                      : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-100 cursor-pointer'
                }`}
              >
                <Icon className={`mr-3 h-4.5 w-4.5 flex-shrink-0 ${isActive ? 'text-white' : 'text-slate-500'}`} />
                <span className="flex-1 truncate">{item.name}</span>
                {isManagerOnly && (
                  <span className="ml-1.5 text-[8px] font-bold text-slate-500 uppercase tracking-wider bg-slate-950 px-1.5 py-0.5 rounded border border-slate-800">
                    Manager Only
                  </span>
                )}
                {item.id === 'workspace' && selectedExceptionId && !isActive && (
                  <span className="ml-2 px-1.5 py-0.5 text-[9px] bg-slate-800 text-indigo-300 rounded border border-slate-700 font-mono">
                    Active
                  </span>
                )}
              </button>
            );
          })}
        </nav>

        {/* Sidebar Footer (User info & Logout) */}
        <div className="p-4 border-t border-slate-800 bg-slate-950 flex flex-col space-y-3">
          <div className="flex items-center space-x-3">
            <div className="bg-slate-800 p-2 rounded-full border border-slate-700 flex-shrink-0">
              <UserIcon className="h-4.5 w-4.5 text-slate-300" />
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-xs font-semibold text-white truncate leading-snug">{user?.name || 'Loading...'}</p>
              <p className="text-[10px] text-slate-400 truncate leading-none capitalize">{user?.role} Role</p>
            </div>
          </div>
          
          <button
            onClick={logout}
            className="w-full flex items-center justify-center px-4 py-2 bg-slate-900/60 hover:bg-red-950/20 text-slate-400 hover:text-red-400 border border-slate-800 hover:border-red-900/40 rounded-lg text-[10px] font-bold tracking-wider uppercase transition-all duration-200"
          >
            <LogOut className="mr-2 h-3.5 w-3.5" />
            Sign Out
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="h-14 bg-white border-b border-slate-200 flex items-center justify-between px-6 flex-shrink-0">
          <div className="flex items-center space-x-4">
            <span className="text-xs font-bold text-slate-700 tracking-wide">
              {activeTab === 'dashboard' && 'Exceptions Queue'}
              {activeTab === 'workspace' && 'Investigation Workspace'}
              {activeTab === 'documents' && 'Document Workbench'}
              {activeTab === 'policies' && 'Resolution Policies'}
              {activeTab === 'audit' && 'System Audit Trails'}
            </span>
          </div>

          <div className="flex items-center space-x-3">
            {/* System Status Badges */}
            <div className="hidden sm:flex items-center space-x-2 text-[10px] font-medium text-slate-500 bg-slate-50 border border-slate-200 px-3 py-1 rounded-md">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 inline-block animate-pulse"></span>
              <span>API: Online</span>
            </div>
            <div className="hidden md:flex items-center space-x-2 text-[10px] font-medium text-slate-500 bg-slate-50 border border-slate-200 px-3 py-1 rounded-md">
              <span>Tenant: <span className="font-semibold text-slate-700">Supervity Demo Org</span></span>
            </div>
          </div>
        </header>

        {/* Content Wrapper */}
        <main className="flex-1 overflow-y-auto bg-slate-50 p-6">
          {children}
        </main>
      </div>
    </div>
  );
};
