export interface User {
  id: string;
  email: string;
  name: string;
  role: 'reviewer' | 'manager';
  organization_id: string;
  created_at: string;
}

export interface Evidence {
  id: string;
  source: string;
  field: string;
  value: string;
  explanation: string;
  fact_type: 'VERIFIED_FACT' | 'EXTRACTED_FACT' | 'AI_INTERPRETATION';
  created_at: string;
}

export interface EvaluatedCondition {
  condition: string;
  result: 'PASS' | 'FAIL';
  detail: string;
}

export interface Investigation {
  id: string;
  finding: string;
  recommendation: 'AUTO_RESOLVE' | 'APPROVE' | 'REJECT' | 'ESCALATE' | 'HUMAN_REVIEW';
  confidence: number;
  risk: 'LOW' | 'MEDIUM' | 'HIGH';
  reason: string;
  grounding?: 'GROUNDED' | 'PARTIALLY_GROUNDED' | 'INVALID';
  raw_ai_response?: Record<string, any>;
  created_at: string;
}

export interface PolicyDecision {
  id: string;
  exception_id: string;
  decision: 'AUTO_RESOLVE' | 'HUMAN_REVIEW' | 'ESCALATE';
  policy_name: string;
  policy_version: number;
  ai_confidence: number;
  risk_level: string;
  financial_impact: number;
  evaluated_conditions: EvaluatedCondition[];
  reasons: string[];
  created_at: string;
}

export interface Resolution {
  id: string;
  action: 'RESOLVE' | 'AUTO_RESOLVE' | 'REJECT' | 'ESCALATE' | 'FALSE_POSITIVE';
  actor_type?: 'USER' | 'SYSTEM';
  actor_id?: string;
  actor_name?: string;
  new_status?: string;
  previous_status?: string;
  comments?: string;
  policy_decision_id?: string;
  created_at: string;
}

export interface AuditEvent {
  id: string;
  actor_id?: string;
  actor_name: string;
  event: string;
  previous_status?: string;
  new_status?: string;
  reason?: string;
  meta_data?: Record<string, any>;
  timestamp: string;
}

export type ExceptionStatus = 'OPEN' | 'UNDER_REVIEW' | 'RESOLVED' | 'REJECTED' | 'ESCALATED' | 'FALSE_POSITIVE';
export type ExceptionType = 'DUPLICATE_INVOICE' | 'AMOUNT_PRICE_MISMATCH' | 'MISSING_PO' | 'TAX_ANOMALY';
export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH';
export type SeverityLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

export interface Exception {
  id: string;
  type: ExceptionType;
  status: ExceptionStatus;
  severity: SeverityLevel;
  confidence: number;
  risk: RiskLevel;
  amount: number;
  vendor_name: string;
  invoice_number?: string;
  created_at: string;
  updated_at: string;
}

export interface ExceptionDetail {
  id: string;
  type: ExceptionType;
  status: ExceptionStatus;
  severity: SeverityLevel;
  confidence: number;
  risk: RiskLevel;
  invoice_id?: string;
  invoice_number?: string;
  po_id?: string;
  po_number?: string;
  vendor_id?: string;
  vendor_name: string;
  amount: number;
  tax_amount: number;
  items: Array<{
    description: string;
    quantity: number;
    unit_price: number;
  }>;
  created_at: string;
  updated_at: string;
  evidence: Evidence[];
  investigations: Investigation[];
  policy_decisions: PolicyDecision[];
  resolutions: Resolution[];
  audit_events: AuditEvent[];
}

export interface DashboardStats {
  total_exceptions: number;
  open_exceptions: number;
  under_review: number;
  escalated: number;
  resolved: number;
  auto_resolved: number;
  false_positives: number;
  high_risk_exceptions: number;
}

export interface TrendPoint {
  date: string;
  count: number;
}

export interface DashboardTrend {
  points: TrendPoint[];
}

export interface DashboardAnalytics {
  type_distribution: Record<string, number>;
  severity_distribution: Record<string, number>;
  status_distribution: Record<string, number>;
}

export interface PaginatedExceptions {
  items: Exception[];
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
}

export interface Policy {
  id: string;
  name: string;
  version: number;
  priority: number;
  is_active: boolean;
  decision: string;
  rules: {
    auto_resolve_confidence_min: number;
    human_review_confidence_min: number;
    high_risk_amount_threshold: number;
    [key: string]: any;
  };
  description?: string;
  created_at: string;
  updated_at: string;
}

export interface DocumentField {
  id: string;
  document_id: string;
  field_name: string;
  extracted_value?: string;
  normalized_value?: string;
  confidence: number;
  confidence_level: 'HIGH' | 'MEDIUM' | 'LOW';
  page_number: number;
  bounding_box?: number[];
  verification_status: 'UNVERIFIED' | 'VERIFIED' | 'EDITED' | 'FLAGGED';
  created_at: string;
  history: DocumentFieldHistory[];
}

export interface DocumentFieldHistory {
  id: string;
  field_id: string;
  old_value?: string;
  new_value?: string;
  action: 'VERIFY' | 'EDIT' | 'FLAG';
  actor_id?: string;
  reason?: string;
  timestamp: string;
}

export interface Document {
  id: string;
  file_name: string;
  content_type: string;
  file_size: number;
  storage_reference: string;
  document_type: string;
  classification_confidence: number;
  processing_status: 'UPLOADED' | 'PROCESSING' | 'EXTRACTED' | 'NEEDS_REVIEW' | 'VERIFIED' | 'FAILED';
  uploaded_by_id?: string;
  raw_text?: string;
  created_at: string;
  fields: DocumentField[];
}
