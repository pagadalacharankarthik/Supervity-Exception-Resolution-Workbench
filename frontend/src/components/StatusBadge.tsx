import React from 'react';

interface StatusBadgeProps {
  value: string;
  type?: 'status' | 'severity' | 'risk' | 'confidence' | 'type';
}

const STATUS_STYLES: Record<string, string> = {
  // Statuses
  OPEN:           'bg-blue-50 text-blue-700 border-blue-200',
  UNDER_REVIEW:   'bg-indigo-50 text-indigo-700 border-indigo-200',
  RESOLVED:       'bg-emerald-50 text-emerald-700 border-emerald-200',
  REJECTED:       'bg-slate-100 text-slate-600 border-slate-300',
  ESCALATED:      'bg-orange-50 text-orange-700 border-orange-200',
  FALSE_POSITIVE: 'bg-purple-50 text-purple-700 border-purple-200',
  // Legacy status aliases
  NEW:            'bg-blue-50 text-blue-700 border-blue-200',
  INVESTIGATING:  'bg-indigo-50 text-indigo-700 border-indigo-200',
  AUTO_RESOLVED:  'bg-emerald-50 text-emerald-700 border-emerald-200',
  // Severity
  CRITICAL:       'bg-red-100 text-red-800 border-red-300',
  HIGH:           'bg-rose-50 text-rose-700 border-rose-200',
  MEDIUM:         'bg-amber-50 text-amber-700 border-amber-200',
  LOW:            'bg-slate-50 text-slate-600 border-slate-200',
};

const STATUS_LABELS: Record<string, string> = {
  OPEN:           'Open',
  UNDER_REVIEW:   'Under Review',
  RESOLVED:       'Resolved',
  REJECTED:       'Rejected',
  ESCALATED:      'Escalated',
  FALSE_POSITIVE: 'False Positive',
  NEW:            'Open',
  INVESTIGATING:  'Under Review',
  AUTO_RESOLVED:  'Auto Resolved',
  CRITICAL:       'Critical',
  HIGH:           'High',
  MEDIUM:         'Medium',
  LOW:            'Low',
};

export const StatusBadge: React.FC<StatusBadgeProps> = ({ value, type }) => {
  if (!value) return null;
  const key = value.toUpperCase();
  const style = STATUS_STYLES[key] || 'bg-slate-100 text-slate-600 border-slate-200';
  const label = STATUS_LABELS[key] || value.replace(/_/g, ' ');

  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded border text-[10px] font-bold uppercase tracking-wide ${style}`}>
      {label}
    </span>
  );
};
