import React, { useState, useEffect, useCallback } from 'react';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';
import type { ExceptionDetail, Investigation, PolicyDecision } from '../types';
import { StatusBadge } from '../components/StatusBadge';
import {
  FileText, ShieldCheck, ArrowLeft, AlertCircle,
  History, UserCheck, Layers, FileCheck, Brain,
  Gavel, CheckCircle2, XCircle, TrendingUp, AlertTriangle,
  MessageSquare, Send, Loader2, ChevronDown, ChevronUp,
  Bot, Shield
} from 'lucide-react';

interface WorkspaceProps {
  exceptionId: string;
  onBackToQueue: () => void;
  onStateChange: () => void;
}

const CLOSED_STATUSES = new Set(['RESOLVED', 'REJECTED', 'FALSE_POSITIVE']);
const OPEN_STATUSES = new Set(['OPEN', 'UNDER_REVIEW']);

export const Workspace: React.FC<WorkspaceProps> = ({ exceptionId, onBackToQueue, onStateChange }) => {
  const { user } = useAuth();
  const [detail, setDetail] = useState<ExceptionDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // AI Investigation state
  const [investigation, setInvestigation] = useState<Investigation | null>(null);
  const [investigating, setInvestigating] = useState(false);
  const [investigationError, setInvestigationError] = useState<string | null>(null);

  // Policy Decision state
  const [policyDecision, setPolicyDecision] = useState<PolicyDecision | null>(null);
  const [evaluating, setEvaluating] = useState(false);
  const [policyError, setPolicyError] = useState<string | null>(null);

  // Resolution state
  const [resolveComment, setResolveComment] = useState('');
  const [rejectReason, setRejectReason] = useState('');
  const [escalateReason, setEscalateReason] = useState('');
  const [resolving, setResolving] = useState(false);
  const [resolutionError, setResolutionError] = useState<string | null>(null);
  const [showResolveForm, setShowResolveForm] = useState(false);
  const [showRejectForm, setShowRejectForm] = useState(false);
  const [showEscalateForm, setShowEscalateForm] = useState(false);

  // Chat state
  const [chatMessages, setChatMessages] = useState<Array<{ sender: string; text: string }>>([]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const [showChat, setShowChat] = useState(false);

  const reload = useCallback(async () => {
    try {
      const data = await api.getException(exceptionId);
      setDetail(data);
      // Sync latest investigation and policy decision from loaded data
      if (data.investigations?.length > 0) {
        setInvestigation(data.investigations[data.investigations.length - 1]);
      }
      if (data.policy_decisions?.length > 0) {
        setPolicyDecision(data.policy_decisions[data.policy_decisions.length - 1]);
      }
    } catch (err: any) {
      setError(err.message);
    }
  }, [exceptionId]);

  useEffect(() => {
    setLoading(true);
    setError(null);
    reload().finally(() => setLoading(false));
  }, [reload]);

  const handleInvestigate = async () => {
    setInvestigating(true);
    setInvestigationError(null);
    try {
      const inv = await api.runInvestigation(exceptionId);
      setInvestigation(inv);
      await reload();
      onStateChange();
    } catch (err: any) {
      setInvestigationError(err.message || 'AI investigation failed. Please try again.');
    } finally {
      setInvestigating(false);
    }
  };

  const handleEvaluatePolicy = async () => {
    setEvaluating(true);
    setPolicyError(null);
    try {
      const decision = await api.evaluatePolicy(exceptionId);
      setPolicyDecision(decision);
      await reload();
      onStateChange();
    } catch (err: any) {
      setPolicyError(err.message || 'Policy evaluation failed.');
    } finally {
      setEvaluating(false);
    }
  };

  const handleResolve = async () => {
    if (!resolveComment.trim()) {
      setResolutionError('A resolution comment is required.');
      return;
    }
    setResolving(true);
    setResolutionError(null);
    try {
      await api.resolveException(exceptionId, resolveComment);
      await reload();
      onStateChange();
      setShowResolveForm(false);
      setResolveComment('');
    } catch (err: any) {
      setResolutionError(err.message || 'Resolution failed.');
    } finally {
      setResolving(false);
    }
  };

  const handleReject = async () => {
    if (!rejectReason.trim()) {
      setResolutionError('A rejection reason is required.');
      return;
    }
    setResolving(true);
    setResolutionError(null);
    try {
      await api.rejectException(exceptionId, rejectReason);
      await reload();
      onStateChange();
      setShowRejectForm(false);
      setRejectReason('');
    } catch (err: any) {
      setResolutionError(err.message || 'Rejection failed.');
    } finally {
      setResolving(false);
    }
  };

  const handleEscalate = async () => {
    if (!escalateReason.trim()) {
      setResolutionError('An escalation reason is required.');
      return;
    }
    setResolving(true);
    setResolutionError(null);
    try {
      await api.escalateException(exceptionId, escalateReason);
      await reload();
      onStateChange();
      setShowEscalateForm(false);
      setEscalateReason('');
    } catch (err: any) {
      setResolutionError(err.message || 'Escalation failed.');
    } finally {
      setResolving(false);
    }
  };

  const handleFalsePositive = async () => {
    if (!window.confirm('Mark this exception as a False Positive? This cannot be undone.')) return;
    setResolving(true);
    setResolutionError(null);
    try {
      await api.markFalsePositive(exceptionId, 'Marked as false positive by reviewer.');
      await reload();
      onStateChange();
    } catch (err: any) {
      setResolutionError(err.message || 'Failed to mark as false positive.');
    } finally {
      setResolving(false);
    }
  };

  const handleAutoResolve = async () => {
    if (!window.confirm('Execute System Controlled Auto-Resolution? This will be logged with actor type SYSTEM.')) return;
    setResolving(true);
    setResolutionError(null);
    try {
      await api.autoResolveException(exceptionId);
      await reload();
      onStateChange();
    } catch (err: any) {
      setResolutionError(err.message || 'Auto-resolution failed.');
    } finally {
      setResolving(false);
    }
  };

  const handleSendChat = async () => {
    if (!chatInput.trim()) return;
    const userMsg = { sender: 'user', text: chatInput };
    const newMessages = [...chatMessages, userMsg];
    setChatMessages(newMessages);
    setChatInput('');
    setChatLoading(true);
    try {
      const response = await api.sendChat(exceptionId, newMessages, chatInput);
      setChatMessages(prev => [...prev, { sender: 'assistant', text: response.reply }]);
    } catch (err: any) {
      setChatMessages(prev => [...prev, { sender: 'assistant', text: `Error: ${err.message}` }]);
    } finally {
      setChatLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="h-[70vh] flex flex-col items-center justify-center text-slate-400 text-xs">
        <Loader2 className="h-6 w-6 animate-spin text-indigo-500 mb-3" />
        Loading exception case...
      </div>
    );
  }

  if (error || !detail) {
    return (
      <div className="h-[70vh] flex flex-col items-center justify-center space-y-3">
        <AlertCircle className="h-8 w-8 text-rose-500" />
        <p className="text-sm font-semibold text-slate-700">{error || 'Exception not found.'}</p>
        <button onClick={onBackToQueue} className="text-xs text-indigo-600 font-bold hover:underline">← Back to Queue</button>
      </div>
    );
  }

  const isClosed = CLOSED_STATUSES.has(detail.status);
  const isOpen = OPEN_STATUSES.has(detail.status);
  const isEscalated = detail.status === 'ESCALATED';
  const latestDecision = policyDecision?.decision;
  const canAutoResolve = latestDecision === 'AUTO_RESOLVE';
  const isManager = user?.role === 'manager';

  // Get PO amount from evidence for display
  const poEvidenceItem = detail.evidence?.find(e => e.field === 'po_total' || e.source?.includes('PO'));
  const invEvidenceItem = detail.evidence?.find(e => e.field === 'invoice_total' || e.source?.includes('INV'));

  const getDecisionColor = (dec?: string) => {
    if (dec === 'AUTO_RESOLVE') return 'text-emerald-700 bg-emerald-50 border-emerald-200';
    if (dec === 'ESCALATE') return 'text-red-700 bg-red-50 border-red-200';
    return 'text-amber-700 bg-amber-50 border-amber-200';
  };

  const getConfidenceBar = (conf: number) => {
    const pct = Math.round(conf * 100);
    const color = pct >= 90 ? 'bg-emerald-500' : pct >= 70 ? 'bg-amber-500' : 'bg-red-500';
    return (
      <div className="flex items-center gap-2">
        <div className="flex-1 h-1.5 bg-slate-200 rounded-full overflow-hidden">
          <div className={`h-full ${color} rounded-full`} style={{ width: `${pct}%` }} />
        </div>
        <span className="font-mono font-bold text-xs">{pct}%</span>
      </div>
    );
  };

  return (
    <div className="space-y-5 font-sans pb-12">
      {/* Navigation Header */}
      <div className="flex items-center justify-between">
        <button
          onClick={onBackToQueue}
          className="flex items-center text-xs font-bold text-slate-500 hover:text-indigo-600 transition-all cursor-pointer group"
        >
          <ArrowLeft className="mr-1.5 h-4 w-4 group-hover:-translate-x-0.5 transition-transform" />
          Back to Exception Queue
        </button>
        <span className="font-mono text-[10px] font-bold uppercase tracking-widest text-slate-400 bg-slate-100 px-3 py-1 rounded border border-slate-200">
          Case Investigation Workspace
        </span>
      </div>

      {/* ── Exception Header ─────────────────────────────────────────────── */}
      <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-100 pb-4 mb-4">
          <div className="flex items-center space-x-3">
            <span className="font-mono text-sm font-black text-slate-400 bg-slate-100 px-2.5 py-1 rounded border border-slate-200">
              EX-{detail.id.slice(0, 8).toUpperCase()}
            </span>
            <div>
              <h1 className="text-base font-black text-slate-900 tracking-tight">
                {detail.type.replace(/_/g, ' ')}
              </h1>
              <p className="text-xs text-slate-500 font-semibold mt-0.5">
                Vendor: <span className="text-slate-800 font-bold">{detail.vendor_name}</span>
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <StatusBadge value={detail.severity} type="severity" />
            <StatusBadge value={detail.status} type="status" />
            {detail.risk && <StatusBadge value={detail.risk} type="risk" />}
          </div>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
          <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Financial Impact</p>
            <p className="text-base font-black text-slate-900 font-mono mt-1">
              ${detail.amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}
            </p>
          </div>
          <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Invoice</p>
            <p className="text-sm font-bold text-slate-800 font-mono mt-1">{detail.invoice_number || 'N/A'}</p>
          </div>
          <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Purchase Order</p>
            <p className="text-sm font-bold text-indigo-600 font-mono mt-1">{detail.po_number || '— None —'}</p>
          </div>
          <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Detection Confidence</p>
            <div className="mt-1.5">{getConfidenceBar(detail.confidence || 0)}</div>
          </div>
        </div>
      </div>

      {/* ── Main Grid ────────────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">

        {/* LEFT: Evidence + AI + Policy ─────────────────────────────────── */}
        <div className="lg:col-span-7 space-y-5">

          {/* Source Evidence Panel */}
          <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center">
                <FileCheck className="mr-2 h-4 w-4 text-emerald-600" />
                Verified Source Evidence
              </h3>
              <span className="text-[10px] font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200 uppercase">
                Ground Truth
              </span>
            </div>
            {detail.evidence && detail.evidence.length > 0 ? (
              <div className="space-y-2">
                {detail.evidence.map((ev) => (
                  <div key={ev.id} className={`p-3 rounded-lg border text-xs space-y-1 ${
                    ev.fact_type === 'VERIFIED_FACT' ? 'bg-emerald-50 border-emerald-200' :
                    ev.fact_type === 'AI_INTERPRETATION' ? 'bg-violet-50 border-violet-200' :
                    'bg-slate-50 border-slate-200'
                  }`}>
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex items-center gap-1.5">
                        <span className={`text-[9px] font-bold uppercase px-1.5 py-0.5 rounded ${
                          ev.fact_type === 'VERIFIED_FACT' ? 'text-emerald-700 bg-emerald-100' :
                          ev.fact_type === 'AI_INTERPRETATION' ? 'text-violet-700 bg-violet-100' :
                          'text-slate-600 bg-slate-200'
                        }`}>{ev.fact_type.replace(/_/g,' ')}</span>
                        <span className="font-bold text-slate-700">{ev.source} • {ev.field}</span>
                      </div>
                      <span className="font-mono font-bold text-slate-900 bg-white px-2 py-0.5 rounded border border-slate-200 whitespace-nowrap">
                        {ev.value}
                      </span>
                    </div>
                    <p className="text-slate-600 text-[11px] leading-relaxed">{ev.explanation}</p>
                  </div>
                ))}
              </div>
            ) : (
              <div className="py-6 text-center text-xs text-slate-400">
                No evidence records. Run exception detection to populate evidence.
              </div>
            )}
          </div>

          {/* AI Investigation Panel */}
          <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center">
                <Brain className="mr-2 h-4 w-4 text-violet-500" />
                AI Investigation
              </h3>
              <div className="flex items-center gap-2">
                <span className="text-[9px] font-bold text-violet-700 bg-violet-50 px-2 py-0.5 rounded border border-violet-200 uppercase">
                  Advisory Only
                </span>
                {!isClosed && (
                  <button
                    onClick={handleInvestigate}
                    disabled={investigating}
                    className="flex items-center gap-1.5 px-3 py-1.5 bg-violet-600 hover:bg-violet-700 text-white text-[10px] font-bold rounded-lg transition-all disabled:opacity-60 disabled:cursor-not-allowed"
                  >
                    {investigating ? <Loader2 className="h-3 w-3 animate-spin" /> : <Brain className="h-3 w-3" />}
                    {investigating ? 'Investigating...' : investigation ? 'Re-Investigate' : 'Run AI Investigation'}
                  </button>
                )}
              </div>
            </div>

            {investigationError && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-xs text-red-700 flex items-start gap-2">
                <AlertCircle className="h-4 w-4 flex-shrink-0 mt-0.5" />
                <span>{investigationError}</span>
              </div>
            )}

            {investigation ? (
              <div className="space-y-3">
                {/* Grounding Badge */}
                {investigation.grounding && (
                  <div className={`inline-flex items-center gap-1.5 text-[10px] font-bold px-2 py-1 rounded border uppercase tracking-wide ${
                    investigation.grounding === 'GROUNDED' ? 'text-emerald-700 bg-emerald-50 border-emerald-200' :
                    investigation.grounding === 'PARTIALLY_GROUNDED' ? 'text-amber-700 bg-amber-50 border-amber-200' :
                    'text-red-700 bg-red-50 border-red-200'
                  }`}>
                    <Shield className="h-3 w-3" />
                    Evidence: {investigation.grounding.replace(/_/g,' ')}
                  </div>
                )}

                {/* Finding */}
                <div className="p-4 bg-violet-50 border border-violet-200 rounded-lg text-xs">
                  <p className="text-[10px] font-bold text-violet-500 uppercase tracking-widest mb-1.5">AI Finding</p>
                  <p className="text-slate-800 font-medium leading-relaxed">{investigation.finding}</p>
                </div>

                {/* Recommendation & Risk */}
                <div className="grid grid-cols-3 gap-3 text-xs">
                  <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg">
                    <p className="text-[9px] font-bold text-slate-400 uppercase mb-1">AI Recommendation</p>
                    <p className="font-bold text-slate-800">{investigation.recommendation?.replace(/_/g,' ')}</p>
                  </div>
                  <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg">
                    <p className="text-[9px] font-bold text-slate-400 uppercase mb-1">AI Confidence</p>
                    {getConfidenceBar(investigation.confidence || 0)}
                  </div>
                  <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg">
                    <p className="text-[9px] font-bold text-slate-400 uppercase mb-1">Risk Level</p>
                    <StatusBadge value={investigation.risk} type="risk" />
                  </div>
                </div>

                {investigation.reason && (
                  <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-600 leading-relaxed">
                    <span className="font-bold text-slate-500 block mb-1 text-[10px] uppercase tracking-wide">AI Reasoning</span>
                    {investigation.reason}
                  </div>
                )}

                {/* Evidence Chat Toggle */}
                <button
                  onClick={() => setShowChat(v => !v)}
                  className="flex items-center gap-1.5 text-[10px] font-bold text-violet-600 hover:text-violet-700 transition-colors"
                >
                  <MessageSquare className="h-3.5 w-3.5" />
                  {showChat ? 'Hide' : 'Ask AI about this case'}
                  {showChat ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
                </button>

                {showChat && (
                  <div className="border border-slate-200 rounded-lg overflow-hidden">
                    <div className="h-40 overflow-y-auto p-3 space-y-2 bg-slate-50 text-xs">
                      {chatMessages.length === 0 && (
                        <p className="text-slate-400 text-center pt-4">Ask a question about this exception case...</p>
                      )}
                      {chatMessages.map((m, i) => (
                        <div key={i} className={`flex ${m.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                          <div className={`max-w-[85%] px-3 py-2 rounded-lg ${
                            m.sender === 'user'
                              ? 'bg-indigo-600 text-white'
                              : 'bg-white border border-slate-200 text-slate-700'
                          }`}>
                            {m.sender === 'assistant' && <Bot className="h-3 w-3 inline mr-1 text-violet-500" />}
                            {m.text}
                          </div>
                        </div>
                      ))}
                      {chatLoading && (
                        <div className="flex justify-start">
                          <div className="bg-white border border-slate-200 px-3 py-2 rounded-lg">
                            <Loader2 className="h-3 w-3 animate-spin text-violet-500 inline mr-1" />
                            <span className="text-slate-400 text-[10px]">Analyzing...</span>
                          </div>
                        </div>
                      )}
                    </div>
                    <div className="flex border-t border-slate-200">
                      <input
                        type="text"
                        value={chatInput}
                        onChange={e => setChatInput(e.target.value)}
                        onKeyDown={e => e.key === 'Enter' && !chatLoading && handleSendChat()}
                        placeholder="e.g. What does the invoice say about the total?"
                        className="flex-1 px-3 py-2 text-xs bg-white outline-none text-slate-700 placeholder-slate-400"
                      />
                      <button
                        onClick={handleSendChat}
                        disabled={chatLoading || !chatInput.trim()}
                        className="px-3 py-2 bg-violet-600 hover:bg-violet-700 text-white disabled:opacity-50 transition-colors"
                      >
                        <Send className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="py-6 text-center text-xs text-slate-400">
                {isClosed
                  ? 'Case is closed. Investigation complete.'
                  : 'No investigation yet. Click "Run AI Investigation" to analyze this case with grounded evidence.'}
              </div>
            )}
          </div>

          {/* Policy Decision Panel */}
          <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center">
                <Gavel className="mr-2 h-4 w-4 text-amber-600" />
                Deterministic Policy Decision
              </h3>
              <div className="flex items-center gap-2">
                <span className="text-[9px] font-bold text-amber-700 bg-amber-50 px-2 py-0.5 rounded border border-amber-200 uppercase">
                  Not AI
                </span>
                {!isClosed && investigation && (
                  <button
                    onClick={handleEvaluatePolicy}
                    disabled={evaluating}
                    className="flex items-center gap-1.5 px-3 py-1.5 bg-amber-600 hover:bg-amber-700 text-white text-[10px] font-bold rounded-lg transition-all disabled:opacity-60 disabled:cursor-not-allowed"
                  >
                    {evaluating ? <Loader2 className="h-3 w-3 animate-spin" /> : <Gavel className="h-3 w-3" />}
                    {evaluating ? 'Evaluating...' : policyDecision ? 'Re-Evaluate' : 'Evaluate Policy'}
                  </button>
                )}
              </div>
            </div>

            {policyError && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-xs text-red-700">{policyError}</div>
            )}

            {policyDecision ? (
              <div className="space-y-3">
                <div className={`p-4 border rounded-lg ${getDecisionColor(policyDecision.decision)}`}>
                  <p className="text-[10px] font-bold uppercase tracking-widest mb-1">Policy Decision</p>
                  <p className="text-lg font-black">{policyDecision.decision.replace(/_/g, ' ')}</p>
                  <p className="text-[10px] mt-0.5 opacity-80">Policy: {policyDecision.policy_name} v{policyDecision.policy_version}</p>
                </div>

                {/* Evaluated Conditions */}
                {policyDecision.evaluated_conditions?.length > 0 && (
                  <div className="space-y-1.5">
                    <p className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Evaluated Conditions</p>
                    {policyDecision.evaluated_conditions.map((cond, i) => (
                      <div key={i} className={`flex items-start gap-2 p-2 rounded border text-xs ${
                        cond.result === 'PASS' ? 'bg-emerald-50 border-emerald-200' : 'bg-red-50 border-red-200'
                      }`}>
                        {cond.result === 'PASS'
                          ? <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600 flex-shrink-0 mt-0.5" />
                          : <XCircle className="h-3.5 w-3.5 text-red-500 flex-shrink-0 mt-0.5" />}
                        <div>
                          <span className="font-bold text-slate-700">{cond.condition}</span>
                          <p className="text-[10px] text-slate-500 mt-0.5">{cond.detail}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {/* Reasons */}
                {policyDecision.reasons?.length > 0 && (
                  <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg space-y-1">
                    <p className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Decision Rationale</p>
                    {policyDecision.reasons.map((r, i) => (
                      <p key={i} className="text-xs text-slate-600">• {r}</p>
                    ))}
                  </div>
                )}
              </div>
            ) : (
              <div className="py-6 text-center text-xs text-slate-400">
                {!investigation
                  ? 'Run AI investigation first, then evaluate policy.'
                  : isClosed
                    ? 'Case is closed.'
                    : 'Click "Evaluate Policy" to run deterministic policy rules against the AI investigation output.'}
              </div>
            )}
          </div>

          {/* Invoice Line Items */}
          {detail.items && detail.items.length > 0 && (
            <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-3">
              <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center">
                <FileText className="mr-2 h-4 w-4 text-indigo-500" />
                Invoice Line Items
              </h3>
              <div className="border border-slate-200 rounded-lg overflow-hidden">
                <table className="min-w-full text-left text-xs">
                  <thead className="bg-slate-50 text-[10px] font-bold text-slate-400 uppercase border-b border-slate-200">
                    <tr>
                      <th className="px-4 py-2.5">Description</th>
                      <th className="px-4 py-2.5 text-right">Qty</th>
                      <th className="px-4 py-2.5 text-right">Unit Price</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 font-medium text-slate-700">
                    {detail.items.map((item, idx) => (
                      <tr key={idx}>
                        <td className="px-4 py-2.5">{item.description}</td>
                        <td className="px-4 py-2.5 text-right font-mono">{item.quantity}</td>
                        <td className="px-4 py-2.5 text-right font-mono font-bold">${item.unit_price.toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>

        {/* RIGHT: Resolution + Audit ─────────────────────────────────────── */}
        <div className="lg:col-span-5 space-y-5">

          {/* Resolution Workflow */}
          <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-4">
            <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center border-b border-slate-100 pb-3">
              <UserCheck className="mr-2 h-4 w-4 text-indigo-500" />
              Resolution Workflow
            </h3>

            {resolutionError && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-xs text-red-700 flex items-start gap-2">
                <AlertCircle className="h-4 w-4 flex-shrink-0 mt-0.5" />
                {resolutionError}
              </div>
            )}

            {/* Closed State */}
            {isClosed && (
              <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-lg space-y-2">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-5 w-5 text-emerald-600" />
                  <p className="text-sm font-black text-emerald-800">Case Closed</p>
                </div>
                <StatusBadge value={detail.status} type="status" />
                {detail.resolutions?.[0] && (
                  <div className="text-xs text-emerald-700 mt-2 space-y-0.5">
                    <p><span className="font-bold">Action:</span> {detail.resolutions[0].action}</p>
                    {detail.resolutions[0].actor_type === 'SYSTEM' && (
                      <p className="text-[10px] font-bold uppercase text-emerald-600">System Auto-Resolution</p>
                    )}
                    {detail.resolutions[0].comments && (
                      <p className="text-slate-600 italic">"{detail.resolutions[0].comments}"</p>
                    )}
                  </div>
                )}
              </div>
            )}

            {/* Escalated - manager action */}
            {isEscalated && isManager && (
              <div className="p-3 bg-orange-50 border border-orange-200 rounded-lg text-xs text-orange-800 space-y-2">
                <div className="flex items-center gap-2">
                  <AlertTriangle className="h-4 w-4 text-orange-600" />
                  <p className="font-bold">Escalated — Manager Action Required</p>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    onClick={() => { setShowResolveForm(true); setShowRejectForm(false); setShowEscalateForm(false); }}
                    disabled={resolving}
                    className="px-3 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-[10px] font-bold uppercase transition-all disabled:opacity-60"
                  >
                    Resolve
                  </button>
                  <button
                    onClick={() => { setShowRejectForm(true); setShowResolveForm(false); setShowEscalateForm(false); }}
                    disabled={resolving}
                    className="px-3 py-2 bg-slate-700 hover:bg-slate-800 text-white rounded-lg text-[10px] font-bold uppercase transition-all disabled:opacity-60"
                  >
                    Reject
                  </button>
                </div>
              </div>
            )}

            {/* Open / Under Review Actions */}
            {isOpen && (
              <div className="space-y-3">
                {/* Policy guidance banner */}
                {policyDecision && (
                  <div className={`p-3 rounded-lg border text-xs ${getDecisionColor(policyDecision.decision)}`}>
                    <p className="font-bold text-[10px] uppercase tracking-wide mb-0.5">Policy Recommends</p>
                    <p className="font-black text-sm">{policyDecision.decision.replace(/_/g, ' ')}</p>
                  </div>
                )}

                {/* Auto-Resolve button */}
                {canAutoResolve && (
                  <button
                    onClick={handleAutoResolve}
                    disabled={resolving}
                    className="w-full flex items-center justify-center gap-2 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-bold transition-all disabled:opacity-60"
                  >
                    {resolving ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <CheckCircle2 className="h-3.5 w-3.5" />}
                    System Auto-Resolve
                  </button>
                )}

                {/* Human action buttons */}
                <div className="grid grid-cols-2 gap-2">
                  <button
                    onClick={() => { setShowResolveForm(v => !v); setShowRejectForm(false); setShowEscalateForm(false); }}
                    disabled={resolving}
                    className="py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-[10px] font-bold uppercase transition-all disabled:opacity-60"
                  >
                    ✓ Resolve
                  </button>
                  <button
                    onClick={() => { setShowRejectForm(v => !v); setShowResolveForm(false); setShowEscalateForm(false); }}
                    disabled={resolving}
                    className="py-2 bg-slate-700 hover:bg-slate-800 text-white rounded-lg text-[10px] font-bold uppercase transition-all disabled:opacity-60"
                  >
                    ✕ Reject
                  </button>
                  <button
                    onClick={() => { setShowEscalateForm(v => !v); setShowResolveForm(false); setShowRejectForm(false); }}
                    disabled={resolving}
                    className="py-2 bg-orange-600 hover:bg-orange-700 text-white rounded-lg text-[10px] font-bold uppercase transition-all disabled:opacity-60"
                  >
                    ↑ Escalate
                  </button>
                  <button
                    onClick={handleFalsePositive}
                    disabled={resolving}
                    className="py-2 bg-slate-200 hover:bg-slate-300 text-slate-700 rounded-lg text-[10px] font-bold uppercase transition-all disabled:opacity-60"
                  >
                    ⚑ False Positive
                  </button>
                </div>

                {/* Resolve Form */}
                {showResolveForm && (
                  <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg space-y-2">
                    <p className="text-[10px] font-bold text-emerald-700 uppercase">Resolution Comment (required)</p>
                    <textarea
                      rows={3}
                      value={resolveComment}
                      onChange={e => setResolveComment(e.target.value)}
                      placeholder="Describe the resolution action taken..."
                      className="w-full text-xs border border-emerald-300 rounded-lg p-2 resize-none outline-none focus:ring-1 focus:ring-emerald-500 bg-white"
                    />
                    <div className="flex gap-2">
                      <button
                        onClick={handleResolve}
                        disabled={resolving || !resolveComment.trim()}
                        className="flex-1 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-[10px] font-bold rounded-lg disabled:opacity-60"
                      >
                        {resolving ? 'Saving...' : 'Confirm Resolution'}
                      </button>
                      <button onClick={() => setShowResolveForm(false)} className="px-3 py-2 text-[10px] font-bold text-slate-600 bg-white border border-slate-300 rounded-lg hover:bg-slate-50">
                        Cancel
                      </button>
                    </div>
                  </div>
                )}

                {/* Reject Form */}
                {showRejectForm && (
                  <div className="p-3 bg-slate-50 border border-slate-300 rounded-lg space-y-2">
                    <p className="text-[10px] font-bold text-slate-600 uppercase">Rejection Reason (required)</p>
                    <textarea
                      rows={2}
                      value={rejectReason}
                      onChange={e => setRejectReason(e.target.value)}
                      placeholder="State the reason for rejection..."
                      className="w-full text-xs border border-slate-300 rounded-lg p-2 resize-none outline-none focus:ring-1 focus:ring-slate-500"
                    />
                    <div className="flex gap-2">
                      <button
                        onClick={handleReject}
                        disabled={resolving || !rejectReason.trim()}
                        className="flex-1 py-2 bg-slate-700 hover:bg-slate-800 text-white text-[10px] font-bold rounded-lg disabled:opacity-60"
                      >
                        {resolving ? 'Saving...' : 'Confirm Rejection'}
                      </button>
                      <button onClick={() => setShowRejectForm(false)} className="px-3 py-2 text-[10px] font-bold text-slate-600 bg-white border border-slate-300 rounded-lg hover:bg-slate-50">
                        Cancel
                      </button>
                    </div>
                  </div>
                )}

                {/* Escalate Form */}
                {showEscalateForm && (
                  <div className="p-3 bg-orange-50 border border-orange-200 rounded-lg space-y-2">
                    <p className="text-[10px] font-bold text-orange-700 uppercase">Escalation Reason (required)</p>
                    <textarea
                      rows={2}
                      value={escalateReason}
                      onChange={e => setEscalateReason(e.target.value)}
                      placeholder="Why is this being escalated to a manager?..."
                      className="w-full text-xs border border-orange-300 rounded-lg p-2 resize-none outline-none focus:ring-1 focus:ring-orange-500"
                    />
                    <div className="flex gap-2">
                      <button
                        onClick={handleEscalate}
                        disabled={resolving || !escalateReason.trim()}
                        className="flex-1 py-2 bg-orange-600 hover:bg-orange-700 text-white text-[10px] font-bold rounded-lg disabled:opacity-60"
                      >
                        {resolving ? 'Saving...' : 'Confirm Escalation'}
                      </button>
                      <button onClick={() => setShowEscalateForm(false)} className="px-3 py-2 text-[10px] font-bold text-slate-600 bg-white border border-slate-300 rounded-lg hover:bg-slate-50">
                        Cancel
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Escalated - non-manager view */}
            {isEscalated && !isManager && (
              <div className="p-4 bg-orange-50 border border-orange-200 rounded-lg text-xs text-orange-800">
                <div className="flex items-center gap-2 mb-1">
                  <AlertTriangle className="h-4 w-4 text-orange-600" />
                  <p className="font-bold">Escalated to Manager</p>
                </div>
                <p className="text-[11px] text-orange-700">This case requires manager-level authorization to proceed.</p>
              </div>
            )}
          </div>

          {/* Related Entities */}
          <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-3">
            <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center">
              <ShieldCheck className="mr-2 h-4 w-4 text-indigo-500" />
              Related Database Records
            </h3>
            <div className="space-y-1.5 text-xs">
              {[
                { label: 'Vendor', value: detail.vendor_name },
                { label: 'Invoice Total', value: `$${detail.amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}` },
                { label: 'Tax Amount', value: `$${(detail.tax_amount || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}` },
                { label: 'Net Subtotal', value: `$${((detail.amount || 0) - (detail.tax_amount || 0)).toLocaleString(undefined, { minimumFractionDigits: 2 })}` },
              ].map(({ label, value }) => (
                <div key={label} className="p-2.5 bg-slate-50 border border-slate-100 rounded-lg flex justify-between">
                  <span className="text-slate-500 font-bold uppercase text-[10px] tracking-wide">{label}</span>
                  <span className="font-semibold text-slate-800 font-mono">{value}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Audit Timeline */}
          <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-3">
            <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center">
              <History className="mr-2 h-4 w-4 text-indigo-500" />
              Audit Timeline
            </h3>
            <div className="relative border-l border-slate-200 pl-4 space-y-4">
              {detail.audit_events && detail.audit_events.length > 0 ? (
                detail.audit_events.map((audit) => (
                  <div key={audit.id} className="relative">
                    <span className="absolute -left-[21px] top-1 bg-white border-2 border-indigo-400 rounded-full h-3 w-3" />
                    <div className="text-xs">
                      <div className="flex items-center justify-between gap-2">
                        <span className="font-bold text-slate-800 text-[11px]">{audit.event.replace(/_/g, ' ')}</span>
                        <span className="text-[9px] text-slate-400 font-mono flex-shrink-0">
                          {new Date(audit.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </span>
                      </div>
                      {audit.reason && (
                        <p className="text-slate-500 text-[11px] mt-0.5 leading-normal">{audit.reason}</p>
                      )}
                      <p className="text-[9px] text-slate-400 font-bold mt-0.5 uppercase tracking-wider">
                        Actor: {audit.actor_name}
                      </p>
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-xs text-slate-400 py-2">No audit events recorded yet.</div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
