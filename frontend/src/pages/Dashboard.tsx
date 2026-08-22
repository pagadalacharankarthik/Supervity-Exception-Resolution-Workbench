import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';
import type { Exception, DashboardStats, DashboardTrend, DashboardAnalytics, PaginatedExceptions } from '../types';
import { StatusBadge } from '../components/StatusBadge';
import { 
  FileText, ShieldAlert, Zap, CheckCircle2, 
  Search, ArrowUpDown, Play, ChevronLeft, ChevronRight, Layers, BarChart3, PieChart
} from 'lucide-react';

interface DashboardProps {
  onSelectException: (id: string) => void;
  refreshStatsTrigger: number;
}

export const Dashboard: React.FC<DashboardProps> = ({ onSelectException, refreshStatsTrigger }) => {
  const { user } = useAuth();
  
  // States
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [analytics, setAnalytics] = useState<DashboardAnalytics | null>(null);
  const [paginatedData, setPaginatedData] = useState<PaginatedExceptions | null>(null);
  const [loading, setLoading] = useState(true);
  const [detecting, setDetecting] = useState(false);
  const [detectResult, setDetectResult] = useState<any>(null);
  
  // Search, Filters & Pagination
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [severityFilter, setSeverityFilter] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [page, setPage] = useState(1);
  const [pageSize] = useState(10);
  const [sortBy, setSortBy] = useState<string>('severity');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  // Load stats and analytics
  const loadMetrics = async () => {
    try {
      const statsData = await api.getStats();
      setStats(statsData);
      
      const analyticsData = await api.getAnalytics();
      setAnalytics(analyticsData);
    } catch (err) {
      console.error("Failed to load dashboard metrics", err);
    }
  };

  // Load exceptions queue with pagination
  const loadQueue = async () => {
    setLoading(true);
    try {
      const data = await api.listExceptions({
        page,
        page_size: pageSize,
        search: search || undefined,
        status: statusFilter || undefined,
        severity: severityFilter || undefined,
        type: typeFilter || undefined,
        sort_by: sortBy,
        sort_order: sortOrder
      });
      setPaginatedData(data);
    } catch (err) {
      console.error("Failed to load queue", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadMetrics();
  }, [refreshStatsTrigger]);

  useEffect(() => {
    loadQueue();
  }, [page, search, statusFilter, severityFilter, typeFilter, sortBy, sortOrder, refreshStatsTrigger]);

  // Run Exception Detection Engine
  const handleRunDetection = async () => {
    setDetecting(true);
    setDetectResult(null);
    try {
      const res = await api.triggerDetection();
      setDetectResult(res);
      await loadMetrics();
      await loadQueue();
    } catch (err: any) {
      alert(`Detection run failed: ${err.message}`);
    } finally {
      setDetecting(false);
    }
  };

  // Sort handler
  const handleSort = (field: string) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(field);
      setSortOrder('desc');
    }
  };

  return (
    <div className="space-y-6 font-sans">
      {/* Top Bar / Header */}
      <div className="bg-slate-900 border border-slate-800 text-slate-300 rounded-xl p-4 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <h2 className="text-base font-extrabold text-white tracking-tight">Supervity Exception Resolution Workbench</h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Evidence-Driven AI Exception Resolution • Assessment Prototype
          </p>
        </div>
        
        <div className="flex items-center space-x-3">
          <button
            onClick={handleRunDetection}
            disabled={detecting}
            className="flex items-center px-3.5 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold uppercase tracking-wider transition-all disabled:opacity-50 shadow-md shadow-indigo-600/20 cursor-pointer"
          >
            <Play className="mr-2 h-3.5 w-3.5" />
            {detecting ? 'Running Engine...' : 'Run Detection Engine'}
          </button>
        </div>
      </div>

      {detectResult && (
        <div className="p-3.5 bg-indigo-950/40 border border-indigo-800/60 rounded-xl text-xs text-indigo-200 flex items-center justify-between">
          <div>
            <span className="font-bold">Detection Run Completed:</span> Scanned transactions and evaluated deterministic rules. Detected <span className="font-mono font-bold text-white">{detectResult.detected}</span> issues (<span className="text-emerald-400 font-bold">{detectResult.new_exceptions} new persistent exceptions</span>, {detectResult.existing_exceptions} existing skipped via idempotency).
          </div>
          <button onClick={() => setDetectResult(null)} className="text-slate-400 hover:text-white font-bold text-xs">Dismiss</button>
        </div>
      )}

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        {/* Total Card */}
        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Total Exceptions</p>
            <p className="text-2xl font-black text-slate-800 mt-1 leading-none">{stats?.total_exceptions ?? '...'}</p>
          </div>
          <div className="bg-slate-50 p-2.5 rounded-lg border border-slate-200 text-slate-500">
            <FileText className="h-5 w-5" />
          </div>
        </div>

        {/* Open Card */}
        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Open Exceptions</p>
            <p className="text-2xl font-black text-amber-600 mt-1 leading-none">{stats?.open_exceptions ?? '...'}</p>
          </div>
          <div className="bg-amber-50 p-2.5 rounded-lg border border-amber-200 text-amber-500">
            <ShieldAlert className="h-5 w-5" />
          </div>
        </div>

        {/* High Risk Card */}
        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">High-Risk Exceptions</p>
            <p className="text-2xl font-black text-rose-600 mt-1 leading-none">{stats?.high_risk_exceptions ?? '...'}</p>
          </div>
          <div className="bg-rose-50 p-2.5 rounded-lg border border-rose-200 text-rose-500">
            <ShieldAlert className="h-5 w-5" />
          </div>
        </div>

        {/* AI-Resolvable Card */}
        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Pending AI Assessment</p>
            <p className="text-2xl font-black text-indigo-600 mt-1 leading-none">{stats?.ai_resolvable_exceptions ?? '...'}</p>
          </div>
          <div className="bg-indigo-50 p-2.5 rounded-lg border border-indigo-200 text-indigo-500">
            <Zap className="h-5 w-5" />
          </div>
        </div>

        {/* Resolved Card */}
        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Resolved Exceptions</p>
            <p className="text-2xl font-black text-emerald-600 mt-1 leading-none">{stats?.resolved_exceptions ?? '...'}</p>
          </div>
          <div className="bg-emerald-50 p-2.5 rounded-lg border border-emerald-200 text-emerald-500">
            <CheckCircle2 className="h-5 w-5" />
          </div>
        </div>
      </div>

      {/* Analytics Visual Summaries */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Exception Type Distribution */}
        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
          <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center mb-3">
            <PieChart className="mr-2 h-4 w-4 text-indigo-500" />
            Exception Type Distribution
          </h3>
          <div className="space-y-2.5">
            {analytics?.type_distribution && Object.keys(analytics.type_distribution).length > 0 ? (
              Object.entries(analytics.type_distribution).map(([type, count]) => (
                <div key={type} className="text-xs">
                  <div className="flex justify-between font-medium text-slate-700 mb-1">
                    <span>{type.replace(/_/g, ' ')}</span>
                    <span className="font-mono font-bold text-slate-900">{count}</span>
                  </div>
                  <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
                    <div 
                      className="bg-indigo-500 h-1.5 rounded-full" 
                      style={{ width: `${Math.min(100, (count / (stats?.total_exceptions || 1)) * 100)}%` }}
                    ></div>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-xs text-slate-400 py-4 text-center">No type aggregations</div>
            )}
          </div>
        </div>

        {/* Severity Distribution */}
        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
          <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center mb-3">
            <BarChart3 className="mr-2 h-4 w-4 text-indigo-500" />
            Severity Distribution
          </h3>
          <div className="space-y-2.5">
            {['HIGH', 'MEDIUM', 'LOW'].map((sev) => {
              const count = analytics?.severity_distribution[sev] || 0;
              const colorClass = sev === 'HIGH' ? 'bg-rose-500' : sev === 'MEDIUM' ? 'bg-amber-500' : 'bg-slate-400';
              return (
                <div key={sev} className="text-xs">
                  <div className="flex justify-between font-medium text-slate-700 mb-1">
                    <span>{sev} Severity</span>
                    <span className="font-mono font-bold text-slate-900">{count}</span>
                  </div>
                  <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
                    <div 
                      className={`${colorClass} h-1.5 rounded-full`} 
                      style={{ width: `${Math.min(100, (count / (stats?.total_exceptions || 1)) * 100)}%` }}
                    ></div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Status Distribution */}
        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
          <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center mb-3">
            <Layers className="mr-2 h-4 w-4 text-indigo-500" />
            Status Distribution
          </h3>
          <div className="space-y-2.5">
            {analytics?.status_distribution && Object.keys(analytics.status_distribution).length > 0 ? (
              Object.entries(analytics.status_distribution).map(([st, count]) => (
                <div key={st} className="text-xs">
                  <div className="flex justify-between font-medium text-slate-700 mb-1">
                    <span>{st.replace(/_/g, ' ')}</span>
                    <span className="font-mono font-bold text-slate-900">{count}</span>
                  </div>
                  <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
                    <div 
                      className="bg-emerald-500 h-1.5 rounded-full" 
                      style={{ width: `${Math.min(100, (count / (stats?.total_exceptions || 1)) * 100)}%` }}
                    ></div>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-xs text-slate-400 py-4 text-center">No status aggregations</div>
            )}
          </div>
        </div>
      </div>

      {/* Exception Queue Panel */}
      <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
        {/* Header and filters */}
        <div className="p-5 border-b border-slate-200 bg-slate-50/50 flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center">
            <Search className="mr-2 h-4 w-4 text-indigo-500" />
            Exception Queue
          </h3>
          
          <div className="flex flex-wrap items-center gap-2.5">
            {/* Search Input */}
            <div className="relative">
              <input
                type="text"
                placeholder="Search ID, Vendor, PO, Invoice..."
                value={search}
                onChange={(e) => { setSearch(e.target.value); setPage(1); }}
                className="bg-white border border-slate-200 text-xs text-slate-800 placeholder-slate-400 px-3 py-1.5 pl-8 rounded-lg outline-none focus:ring-1 focus:ring-indigo-500 w-56 font-medium"
              />
              <Search className="absolute left-2.5 top-2 h-3.5 w-3.5 text-slate-400" />
            </div>

            {/* Type Filter */}
            <select
              value={typeFilter}
              onChange={(e) => { setTypeFilter(e.target.value); setPage(1); }}
              className="bg-white border border-slate-200 text-xs font-semibold text-slate-700 px-3 py-1.5 rounded-lg outline-none focus:ring-1 focus:ring-indigo-500 cursor-pointer"
            >
              <option value="">All Types</option>
              <option value="DUPLICATE_INVOICE">Duplicate Invoice</option>
              <option value="AMOUNT_PRICE_MISMATCH">Amount/Price Mismatch</option>
              <option value="MISSING_PO">Missing PO</option>
              <option value="TAX_ANOMALY">Tax Anomaly</option>
            </select>

            {/* Severity Filter */}
            <select
              value={severityFilter}
              onChange={(e) => { setSeverityFilter(e.target.value); setPage(1); }}
              className="bg-white border border-slate-200 text-xs font-semibold text-slate-700 px-3 py-1.5 rounded-lg outline-none focus:ring-1 focus:ring-indigo-500 cursor-pointer"
            >
              <option value="">All Severities</option>
              <option value="HIGH">High Severity</option>
              <option value="MEDIUM">Medium Severity</option>
              <option value="LOW">Low Severity</option>
            </select>

            {/* Status Filter */}
            <select
              value={statusFilter}
              onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
              className="bg-white border border-slate-200 text-xs font-semibold text-slate-700 px-3 py-1.5 rounded-lg outline-none focus:ring-1 focus:ring-indigo-500 cursor-pointer"
            >
              <option value="">All Statuses</option>
              <option value="OPEN">Open</option>
              <option value="UNDER_REVIEW">Under Review</option>
              <option value="RESOLVED">Resolved</option>
              <option value="REJECTED">Rejected</option>
              <option value="ESCALATED">Escalated</option>
              <option value="FALSE_POSITIVE">False Positive</option>
            </select>
          </div>
        </div>

        {/* Table */}
        <div className="overflow-x-auto">
          {loading ? (
            <div className="py-20 text-center text-slate-400 text-xs">
              <span className="h-3 w-3 rounded-full bg-indigo-500 inline-block animate-ping mr-2"></span>
              Loading exceptions queue...
            </div>
          ) : !paginatedData || paginatedData.items.length === 0 ? (
            <div className="py-20 text-center text-slate-400 text-xs">
              No exceptions match the selected filters.
            </div>
          ) : (
            <table className="min-w-full divide-y divide-slate-200 text-left">
              <thead className="bg-slate-50/50 text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                <tr>
                  <th className="px-6 py-3.5 cursor-pointer hover:bg-slate-100" onClick={() => handleSort('id')}>
                    Exception ID <ArrowUpDown className="inline-block ml-1 h-3 w-3" />
                  </th>
                  <th className="px-6 py-3.5 cursor-pointer hover:bg-slate-100" onClick={() => handleSort('type')}>
                    Exception Type <ArrowUpDown className="inline-block ml-1 h-3 w-3" />
                  </th>
                  <th className="px-6 py-3.5 cursor-pointer hover:bg-slate-100" onClick={() => handleSort('vendor_name')}>
                    Vendor <ArrowUpDown className="inline-block ml-1 h-3 w-3" />
                  </th>
                  <th className="px-6 py-3.5 cursor-pointer hover:bg-slate-100" onClick={() => handleSort('amount')}>
                    Financial Impact <ArrowUpDown className="inline-block ml-1 h-3 w-3" />
                  </th>
                  <th className="px-6 py-3.5 cursor-pointer hover:bg-slate-100" onClick={() => handleSort('severity')}>
                    Severity <ArrowUpDown className="inline-block ml-1 h-3 w-3" />
                  </th>
                  <th className="px-6 py-3.5">
                    AI Assessment
                  </th>
                  <th className="px-6 py-3.5 cursor-pointer hover:bg-slate-100" onClick={() => handleSort('status')}>
                    Status <ArrowUpDown className="inline-block ml-1 h-3 w-3" />
                  </th>
                  <th className="px-6 py-3.5 cursor-pointer hover:bg-slate-100" onClick={() => handleSort('created_at')}>
                    Created At <ArrowUpDown className="inline-block ml-1 h-3 w-3" />
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-xs text-slate-700 bg-white">
                {paginatedData.items.map((exc) => (
                  <tr 
                    key={exc.id} 
                    onClick={() => onSelectException(exc.id)}
                    className="hover:bg-slate-50/70 cursor-pointer border-l-2 border-transparent hover:border-indigo-500 transition-all"
                  >
                    <td className="px-6 py-4 font-mono font-bold text-slate-500 text-[11px]">
                      EX-{exc.id.slice(0, 8).toUpperCase()}
                    </td>
                    <td className="px-6 py-4">
                      <StatusBadge value={exc.type} type="type" />
                    </td>
                    <td className="px-6 py-4 font-semibold text-slate-800">{exc.vendor_name}</td>
                    <td className="px-6 py-4 font-mono font-bold text-slate-900">${exc.amount.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}</td>
                    <td className="px-6 py-4">
                      <StatusBadge value={exc.severity} type="severity" />
                    </td>
                    <td className="px-6 py-4">
                      {exc.confidence > 0 ? (
                        <div className="flex items-center space-x-1.5">
                          <span className={`h-1.5 w-1.5 rounded-full inline-block ${
                            exc.risk === 'HIGH' ? 'bg-rose-500 animate-pulse' : exc.risk === 'MEDIUM' ? 'bg-amber-500' : 'bg-emerald-500'
                          }`}></span>
                          <span className="font-semibold text-slate-800">{(exc.confidence * 100).toFixed(0)}% ({exc.risk})</span>
                        </div>
                      ) : (
                        <span className="text-[10px] font-bold text-slate-400 bg-slate-100 px-2 py-0.5 rounded uppercase">
                          Not Assessed
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      <StatusBadge value={exc.status} type="status" />
                    </td>
                    <td className="px-6 py-4 text-slate-400 font-medium">
                      {new Date(exc.created_at).toLocaleDateString()} {new Date(exc.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* Pagination Footer */}
        {paginatedData && (
          <div className="p-4 border-t border-slate-200 bg-slate-50/50 flex items-center justify-between text-xs text-slate-500">
            <div>
              Showing Page <span className="font-bold text-slate-800">{paginatedData.page}</span> of <span className="font-bold text-slate-800">{paginatedData.total_pages}</span> ({paginatedData.total} total exceptions)
            </div>
            
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page <= 1}
                className="p-1.5 rounded border border-slate-200 bg-white hover:bg-slate-100 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
              >
                <ChevronLeft className="h-4 w-4" />
              </button>
              <button
                onClick={() => setPage(p => Math.min(paginatedData.total_pages, p + 1))}
                disabled={page >= paginatedData.total_pages}
                className="p-1.5 rounded border border-slate-200 bg-white hover:bg-slate-100 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
              >
                <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
