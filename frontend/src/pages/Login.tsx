import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { ShieldCheck, UserCheck, ShieldAlert, ArrowRight } from 'lucide-react';

export const Login: React.FC = () => {
  const { login, error, clearError } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) return;
    setLoading(true);
    try {
      await login(email, password);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleQuickLogin = async (demoEmail: string) => {
    clearError();
    setEmail(demoEmail);
    setPassword('supervity123');
    setLoading(true);
    try {
      await login(demoEmail, 'supervity123');
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col justify-center py-12 sm:px-6 lg:px-8 relative overflow-hidden font-sans">
      {/* Background glowing effects */}
      <div className="absolute top-0 left-1/4 w-96 h-96 bg-indigo-600/10 rounded-full filter blur-3xl"></div>
      <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-indigo-900/10 rounded-full filter blur-3xl"></div>

      <div className="sm:mx-auto sm:w-full sm:max-w-md relative z-10">
        <div className="flex justify-center items-center space-x-3">
          <ShieldCheck className="h-10 w-10 text-indigo-400" />
          <span className="text-2xl font-black text-white tracking-tight">Supervity</span>
        </div>
        <h2 className="mt-4 text-center text-xl font-extrabold tracking-tight text-slate-100">
          Supervity Exception Resolution Workbench
        </h2>
        <p className="mt-1.5 text-center text-xs font-medium text-slate-400">
          Evidence-Driven AI Exception Resolution
        </p>
        <p className="mt-2.5 text-center text-[10px] font-bold text-slate-500 uppercase tracking-widest">
          Assessment Prototype • Synthetic Data
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md relative z-10 px-4">
        <div className="bg-slate-900/80 backdrop-blur-md py-8 px-6 shadow-2xl rounded-xl border border-slate-800/80">
          {error && (
            <div className="mb-4 bg-red-950/40 border border-red-900/40 text-red-300 rounded-lg p-3.5 flex items-start space-x-3 text-xs">
              <ShieldAlert className="h-4.5 w-4.5 text-red-400 flex-shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          <form className="space-y-4.5" onSubmit={handleSubmit}>
            <div>
              <label htmlFor="email" className="block text-xs font-bold uppercase tracking-wider text-slate-400">
                Email Address
              </label>
              <div className="mt-1.5">
                <input
                  id="email"
                  name="email"
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="reviewer@supervity-demo.com"
                  className="block w-full rounded-lg bg-slate-950/60 border border-slate-800 text-slate-200 placeholder-slate-600 px-4 py-2.5 text-xs font-medium focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all outline-none"
                />
              </div>
            </div>

            <div>
              <label htmlFor="password" className="block text-xs font-bold uppercase tracking-wider text-slate-400">
                Password
              </label>
              <div className="mt-1.5">
                <input
                  id="password"
                  name="password"
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="block w-full rounded-lg bg-slate-950/60 border border-slate-800 text-slate-200 placeholder-slate-600 px-4 py-2.5 text-xs font-medium focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all outline-none"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center py-2.5 px-4 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold tracking-wider uppercase transition-all duration-200 shadow-md shadow-indigo-600/20 disabled:bg-slate-800 disabled:text-slate-500 disabled:cursor-not-allowed"
            >
              {loading ? 'Authenticating...' : 'Sign In'}
              <ArrowRight className="ml-2 h-4 w-4" />
            </button>
          </form>

          {/* Quick Demo Logins Section */}
          <div className="mt-6 border-t border-slate-800/80 pt-6">
            <h3 className="text-[10px] font-bold tracking-widest text-slate-500 uppercase mb-3 flex items-center justify-center">
              <UserCheck className="mr-1.5 h-3.5 w-3.5" />
              Quick Demo Identities
            </h3>
            
            <div className="space-y-2">
              <button
                type="button"
                onClick={() => handleQuickLogin('reviewer@supervity-demo.com')}
                className="w-full flex items-center justify-between p-3 rounded-lg bg-slate-950/40 hover:bg-slate-800/50 border border-slate-800 hover:border-slate-700 transition-all group"
              >
                <div className="text-left">
                  <p className="text-xs font-semibold text-slate-200">Alex Audit</p>
                  <p className="text-[10px] text-slate-500 font-mono">reviewer@supervity-demo.com</p>
                </div>
                <span className="text-[9px] font-bold uppercase tracking-wider bg-slate-800 text-slate-400 group-hover:bg-indigo-950 group-hover:text-indigo-400 px-2 py-0.5 rounded transition-all">
                  Reviewer
                </span>
              </button>

              <button
                type="button"
                onClick={() => handleQuickLogin('manager@supervity-demo.com')}
                className="w-full flex items-center justify-between p-3 rounded-lg bg-slate-950/40 hover:bg-slate-800/50 border border-slate-800 hover:border-slate-700 transition-all group"
              >
                <div className="text-left">
                  <p className="text-xs font-semibold text-slate-200">Sarah Manager</p>
                  <p className="text-[10px] text-slate-500 font-mono">manager@supervity-demo.com</p>
                </div>
                <span className="text-[9px] font-bold uppercase tracking-wider bg-slate-800 text-slate-400 group-hover:bg-indigo-950 group-hover:text-indigo-400 px-2 py-0.5 rounded transition-all">
                  Manager
                </span>
              </button>
            </div>
            
            <p className="mt-4 text-center text-[10px] text-slate-600 leading-snug">
              This system is for technical evaluation. Credentials and data are synthetic mock files.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
