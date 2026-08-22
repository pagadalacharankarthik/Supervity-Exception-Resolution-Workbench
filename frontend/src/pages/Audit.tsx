import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import type { AuditEvent } from '../types';
import { ClipboardList, RotateCw, History, User } from 'lucide-react';

export const Audit: React.FC = () => {
  const [logs, setLogs] = useState<AuditEvent[]>([]);
  const [loading, setLoading] = useState(true);

  const loadLogs = async () => {
    setLoading(true);
    try {
      const data = await api.getGlobalAuditLogs();
      setLogs(data);
    } catch (err) {
      console.error("Failed to load audit logs", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadLogs();
  }, []);

  if (loading) {
    return (
      <div className="h-[70vh] flex flex-col items-center justify-center text-slate-400 text-xs">
        <span className="h-6 w-6 rounded-full border-2 border-indigo-500 border-t-transparent animate-spin mb-3"></span>
        Loading system audit trail logs...
      </div>
    );
  }

  return (
    <div className="space-y-6">
      
      {/* Header Panel */}
      <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm flex items-center justify-between">
        <div>
          <h2 className="text-sm font-bold text-slate-800 tracking-wide flex items-center">
            <ClipboardList className="mr-2 h-5 w-5 text-indigo-500" />
            Enterprise Audit Logs Ledger
          </h2>
          <p className="text-xs text-slate-500 mt-1 leading-snug">
            Permanent, immutable ledger tracking all AI scan triggers, automated system decisions, policy changes, and manual reviewer override actions.
          </p>
        </div>
        
        <button
          onClick={loadLogs}
          className="flex items-center px-3 py-1.5 border border-slate-200 hover:bg-slate-50 text-slate-500 hover:text-slate-700 text-xs font-bold rounded-lg transition-all uppercase tracking-wider"
        >
          <RotateCw className="mr-1.5 h-3.5 w-3.5" />
          Refresh Ledger
        </button>
      </div>

      {/* Logs Table */}
      <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          {logs.length === 0 ? (
            <div className="py-20 text-center text-slate-400 text-xs">
              No audit logs recorded in system ledger.
            </div>
          ) : (
            <table className="min-w-full divide-y divide-slate-200 text-left">
              <thead className="bg-slate-50/50 text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                <tr>
                  <th className="px-6 py-3.5">Timestamp</th>
                  <th className="px-6 py-3.5">Actor</th>
                  <th className="px-6 py-3.5">Event Type</th>
                  <th className="px-6 py-3.5">Status Delta</th>
                  <th className="px-6 py-3.5">Reason / Comments</th>
                  <th className="px-6 py-3.5">Related Case Reference</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-xs text-slate-700 bg-white">
                {logs.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-50/40">
                    <td className="px-6 py-4 text-slate-400 font-mono">
                      {new Date(log.timestamp).toLocaleDateString()}{' '}
                      {new Date(log.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit', second:'2-digit'})}
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center space-x-1.5">
                        <User className="h-3.5 w-3.5 text-slate-400" />
                        <span className="font-bold text-slate-800">{log.actor_name}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span className="inline-flex items-center px-2 py-0.5 rounded bg-slate-100 text-slate-800 border border-slate-200 font-mono text-[10px] font-semibold uppercase tracking-wide">
                        {log.event}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      {log.previous_status || log.new_status ? (
                        <div className="flex items-center space-x-1 font-mono text-[10px] font-bold">
                          <span className="text-slate-400">{log.previous_status || 'NULL'}</span>
                          <span className="text-slate-400">→</span>
                          <span className="text-indigo-600">{log.new_status || 'NULL'}</span>
                        </div>
                      ) : (
                        <span className="text-slate-400">-</span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-slate-600 leading-relaxed max-w-sm truncate" title={log.reason}>
                      {log.reason || '-'}
                    </td>
                    <td className="px-6 py-4">
                      {log.exception_id ? (
                        <span className="font-mono font-bold text-slate-500 uppercase text-[10px]">
                          CASE: {log.exception_id.slice(0, 8).toUpperCase()}...
                        </span>
                      ) : (
                        <span className="text-slate-400 bg-slate-50 border border-slate-100 px-1.5 py-0.5 rounded text-[9px] font-semibold uppercase">
                          System Setting
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

    </div>
  );
};
