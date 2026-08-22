import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import type { Policy } from '../types';
import { Settings, ShieldCheck, CheckCircle2, ShieldAlert, Sparkles } from 'lucide-react';

export const Policies: React.FC = () => {
  const [policies, setPolicies] = useState<Policy[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  // Policy rules local inputs
  const [autoResolveConfidence, setAutoResolveConfidence] = useState(0.90);
  const [humanReviewConfidence, setHumanReviewConfidence] = useState(0.70);
  const [highRiskAmount, setHighRiskAmount] = useState(50000);

  const loadPolicies = async () => {
    setLoading(true);
    try {
      const data = await api.listPolicies();
      setPolicies(data);
      if (data.length > 0) {
        const rules = data[0].rules;
        setAutoResolveConfidence(rules.auto_resolve_confidence_min ?? 0.90);
        setHumanReviewConfidence(rules.human_review_confidence_min ?? 0.70);
        setHighRiskAmount(rules.high_risk_amount_threshold ?? 50000);
      }
    } catch (err) {
      console.error("Failed to load policies", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPolicies();
  }, []);

  const handleSavePolicy = async (policyId: string) => {
    setSaving(true);
    setSaveSuccess(false);
    try {
      const updatedRules = {
        auto_resolve_confidence_min: Number(autoResolveConfidence),
        human_review_confidence_min: Number(humanReviewConfidence),
        high_risk_amount_threshold: Number(highRiskAmount),
      };
      
      await api.updatePolicy(policyId, updatedRules);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 4000);
    } catch (err: any) {
      alert(`Save failed: ${err.message}`);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="h-[70vh] flex flex-col items-center justify-center text-slate-400 text-xs">
        <span className="h-6 w-6 rounded-full border-2 border-indigo-500 border-t-transparent animate-spin mb-3"></span>
        Loading compliance policy settings...
      </div>
    );
  }

  if (policies.length === 0) {
    return (
      <div className="bg-white border border-slate-200 rounded-xl p-8 text-center text-slate-400 text-xs">
        No compliance policies discovered in data tables.
      </div>
    );
  }

  const activePolicy = policies[0];

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      
      {/* Banner */}
      <div className="bg-slate-900 border border-slate-800 text-slate-300 rounded-xl p-5 shadow-sm">
        <h2 className="text-sm font-bold text-white tracking-wide flex items-center">
          <Settings className="mr-2 h-4 w-4 text-indigo-400" />
          Enterprise Compliance Thresholds Manager
        </h2>
        <p className="text-xs text-slate-400 mt-1 leading-relaxed">
          Configure the deterministic bounds that sit on top of the structured AI output model. This dictates how anomaly cases are automatically routed to decline/accept transactions, review queues, or escalated senior managers.
        </p>
      </div>

      {saveSuccess && (
        <div className="bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl p-4 flex items-start space-x-3 text-xs shadow-sm">
          <CheckCircle2 className="h-4.5 w-4.5 text-emerald-500 mt-0.5 flex-shrink-0" />
          <div>
            <p className="font-bold">Configuration Persisted</p>
            <p className="text-slate-500 mt-0.5">Policy thresholds updated successfully in the system database. A permanent change trail event has been appended to the audit logs.</p>
          </div>
        </div>
      )}

      {/* Main Settings Panel */}
      <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
        {/* Header */}
        <div className="p-4 bg-slate-50/50 border-b border-slate-200 flex items-center justify-between">
          <div>
            <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider">{activePolicy.name}</h3>
            <p className="text-[10px] text-slate-400 mt-0.5 truncate">{activePolicy.description || 'System policy configurations'}</p>
          </div>
          <span className="bg-emerald-100 text-emerald-800 border border-emerald-200 px-2 py-0.5 text-[9px] font-bold rounded uppercase">
            Active
          </span>
        </div>

        {/* Form Body */}
        <div className="p-6 space-y-6 divide-y divide-slate-100">
          
          {/* Setting 1: Auto-Resolve Confidence */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-1">
            <div className="md:col-span-2 space-y-1">
              <h4 className="text-xs font-bold text-slate-800 flex items-center">
                <Sparkles className="mr-1.5 h-3.5 w-3.5 text-indigo-500" />
                Auto-Resolution Confidence Threshold
              </h4>
              <p className="text-[11px] text-slate-500 leading-snug">
                The minimum decision confidence score (0.00 to 1.00) required to bypass reviewer eyes and auto-resolve low-risk transactions. 
                Default is <span className="font-bold font-mono">0.90</span>.
              </p>
            </div>
            <div className="flex items-center">
              <div className="relative w-full">
                <input
                  type="number"
                  min="0.50"
                  max="1.00"
                  step="0.05"
                  value={autoResolveConfidence}
                  onChange={(e) => setAutoResolveConfidence(parseFloat(e.target.value))}
                  className="w-full text-xs font-bold font-mono border border-slate-200 focus:ring-1 focus:ring-indigo-500 outline-none rounded-lg px-3.5 py-2"
                />
                <span className="absolute right-3.5 top-2 text-[10px] font-bold text-slate-400 font-mono">%</span>
              </div>
            </div>
          </div>

          {/* Setting 2: Human Review Confidence */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-6">
            <div className="md:col-span-2 space-y-1">
              <h4 className="text-xs font-bold text-slate-800 flex items-center">
                <ShieldCheck className="mr-1.5 h-3.5 w-3.5 text-indigo-500" />
                Human Review Confidence Minimum
              </h4>
              <p className="text-[11px] text-slate-500 leading-snug">
                Cases with confidence scores below this minimum limit are immediately escalated to managers, bypassing the standard Reviewer approvals queue. Default is <span className="font-bold font-mono">0.70</span>.
              </p>
            </div>
            <div className="flex items-center">
              <div className="relative w-full">
                <input
                  type="number"
                  min="0.10"
                  max="0.89"
                  step="0.05"
                  value={humanReviewConfidence}
                  onChange={(e) => setHumanReviewConfidence(parseFloat(e.target.value))}
                  className="w-full text-xs font-bold font-mono border border-slate-200 focus:ring-1 focus:ring-indigo-500 outline-none rounded-lg px-3.5 py-2"
                />
                <span className="absolute right-3.5 top-2 text-[10px] font-bold text-slate-400 font-mono">%</span>
              </div>
            </div>
          </div>

          {/* Setting 3: High Risk Financial Threshold */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-6">
            <div className="md:col-span-2 space-y-1">
              <h4 className="text-xs font-bold text-slate-800 flex items-center">
                <ShieldAlert className="mr-1.5 h-3.5 w-3.5 text-indigo-500" />
                High-Risk Financial Limit ($)
              </h4>
              <p className="text-[11px] text-slate-500 leading-snug">
                Transactions with total billing amounts matching or exceeding this value are blocked from auto-resolution and require manual approval or senior manager review regardless of confidence scores. Default is <span className="font-bold font-mono">$50,000.00</span>.
              </p>
            </div>
            <div className="flex items-center">
              <div className="relative w-full">
                <span className="absolute left-3.5 top-2.5 text-[10px] font-bold text-slate-400 font-mono">$</span>
                <input
                  type="number"
                  min="1000"
                  step="1000"
                  value={highRiskAmount}
                  onChange={(e) => setHighRiskAmount(parseInt(e.target.value))}
                  className="w-full text-xs font-bold font-mono border border-slate-200 focus:ring-1 focus:ring-indigo-500 outline-none rounded-lg pl-6.5 pr-3.5 py-2"
                />
              </div>
            </div>
          </div>

        </div>

        {/* Footer Actions */}
        <div className="px-6 py-4 border-t border-slate-100 bg-slate-50 flex items-center justify-between">
          <div className="text-[10px] text-slate-400 font-medium leading-snug max-w-md">
            Editing values updates active criteria fields. Changes apply immediately to new transaction exceptions.
          </div>
          <button
            onClick={() => handleSavePolicy(activePolicy.id)}
            disabled={saving}
            className="px-5 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold rounded-lg transition-all shadow-md shadow-indigo-600/10 uppercase tracking-wider disabled:bg-slate-100 disabled:text-slate-400"
          >
            {saving ? 'Saving changes...' : 'Save Settings'}
          </button>
        </div>
      </div>
      
    </div>
  );
};
