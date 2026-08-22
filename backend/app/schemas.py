from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any

# Auth Schemas
class LoginRequest(BaseModel):
    email: str
    password: str

class LoginUserResponse(BaseModel):
    id: str
    email: str
    role: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: LoginUserResponse

class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None
    user_id: Optional[str] = None

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    role: str
    organization_id: str
    created_at: datetime

    class Config:
        from_attributes = True

# Evidence Schemas
class EvidenceResponse(BaseModel):
    id: str
    source: str
    field: str
    value: str
    explanation: str
    fact_type: str
    created_at: datetime

    class Config:
        from_attributes = True

# Investigation Schemas
class InvestigationResponse(BaseModel):
    id: str
    finding: str
    recommendation: str
    confidence: float
    risk: str
    reason: str
    raw_ai_response: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True

# Resolution Schemas
class ResolutionCreate(BaseModel):
    action: str  # "RESOLVED", "REJECTED", "ESCALATED", "FALSE_POSITIVE"
    comments: Optional[str] = None

class ResolutionResponse(BaseModel):
    id: str
    action: str
    actor_id: str
    actor_name: str
    comments: Optional[str] = None
    created_at: datetime

# Audit Event Schemas
class AuditEventResponse(BaseModel):
    id: str
    actor_id: Optional[str] = None
    actor_name: Optional[str] = "System"
    event: str
    previous_status: Optional[str] = None
    new_status: Optional[str] = None
    reason: Optional[str] = None
    meta_data: Optional[Dict[str, Any]] = None
    timestamp: datetime

    class Config:
        from_attributes = True

# Exception Queue / Details Schemas
class ExceptionResponse(BaseModel):
    id: str
    type: str
    status: str
    severity: str
    confidence: float
    risk: str
    amount: Decimal = Decimal("0.00")
    vendor_name: str = ""
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class PaginatedExceptionResponse(BaseModel):
    items: List[ExceptionResponse]
    page: int
    page_size: int
    total: int
    total_pages: int

class DashboardAnalytics(BaseModel):
    type_distribution: Dict[str, int]
    severity_distribution: Dict[str, int]
    status_distribution: Dict[str, int]

# Line Item Schemas for Response
class InvoiceLineResponse(BaseModel):
    id: str
    description: str
    quantity: int
    unit_price: Decimal
    tax_rate: Decimal
    tax_amount: Decimal
    total_amount: Decimal

    class Config:
        from_attributes = True

class ExceptionDetailResponse(BaseModel):
    id: str
    type: str
    status: str
    severity: str
    confidence: float
    risk: str
    invoice_id: Optional[str] = None
    invoice_number: Optional[str] = None
    po_id: Optional[str] = None
    po_number: Optional[str] = None
    vendor_id: Optional[str] = None
    vendor_name: str = ""
    amount: Decimal = Decimal("0.00")
    items: List[InvoiceLineResponse] = []
    tax_amount: Decimal = Decimal("0.00")
    created_at: datetime
    updated_at: datetime
    evidence: List[EvidenceResponse] = []
    investigations: List[InvestigationResponse] = []
    resolutions: List[ResolutionResponse] = []
    audit_events: List[AuditEventResponse] = []

    class Config:
        from_attributes = True

# Policy Schemas
class PolicyUpdate(BaseModel):
    rules: Dict[str, Any]
    is_active: Optional[bool] = None

class PolicyResponse(BaseModel):
    id: str
    name: str
    is_active: bool
    rules: Dict[str, Any]
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Dashboard Schemas
class DashboardStats(BaseModel):
    total_exceptions: int
    open_exceptions: int
    high_risk_exceptions: int
    ai_resolvable_exceptions: int
    resolved_exceptions: int

class TrendPoint(BaseModel):
    date: str
    count: int

class DashboardTrend(BaseModel):
    points: List[TrendPoint]

# Verify Endpoints Response Schemas
class VendorResponse(BaseModel):
    id: str
    name: str
    vendor_code: str
    created_at: datetime

    class Config:
        from_attributes = True

class PurchaseOrderLineResponse(BaseModel):
    id: str
    description: str
    quantity: int
    unit_price: Decimal
    tax_rate: Decimal
    tax_amount: Decimal
    total_amount: Decimal

    class Config:
        from_attributes = True

class PurchaseOrderResponse(BaseModel):
    id: str
    po_number: str
    vendor_id: str
    total_amount: Decimal
    currency: str
    status: str
    order_date: datetime
    created_at: datetime
    lines: List[PurchaseOrderLineResponse] = []

    class Config:
        from_attributes = True

class InvoiceResponse(BaseModel):
    id: str
    invoice_number: str
    po_id: Optional[str] = None
    vendor_id: str
    subtotal: Decimal
    tax: Decimal
    total: Decimal
    status: str
    invoice_date: datetime
    due_date: datetime
    received_at: datetime
    lines: List[InvoiceLineResponse] = []

    class Config:
        from_attributes = True

class TransactionResponse(BaseModel):
    id: str
    invoice_id: Optional[str] = None
    po_id: Optional[str] = None
    amount: Decimal
    currency: str
    status: str
    transaction_date: datetime

    class Config:
        from_attributes = True

class EvaluatedCondition(BaseModel):
    condition: str
    actual_value: Any
    passed: bool

class PolicyDecisionResponse(BaseModel):
    id: str
    exception_id: str
    investigation_id: Optional[str] = None
    policy_id: Optional[str] = None
    policy_name: str
    policy_version: int = 1
    decision: str  # "AUTO_RESOLVE", "HUMAN_REVIEW", "ESCALATE"
    ai_confidence: float
    risk: str
    financial_impact: Decimal
    evidence_complete: bool
    evaluated_conditions: List[EvaluatedCondition]
    reasons: List[str]
    created_at: datetime

    class Config:
        from_attributes = True

class PolicyResponse(BaseModel):
    id: str
    name: str
    version: int = 1
    priority: int = 10
    is_active: bool
    decision: str = "HUMAN_REVIEW"
    rules: Dict[str, Any]
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class DocumentFieldHistoryResponse(BaseModel):
    id: str
    field_id: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    action: str
    actor_id: Optional[str] = None
    reason: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True

class DocumentFieldResponse(BaseModel):
    id: str
    document_id: str
    field_name: str
    extracted_value: Optional[str] = None
    normalized_value: Optional[str] = None
    confidence: float
    confidence_level: str
    page_number: int = 1
    bounding_box: Optional[Any] = None
    verification_status: str
    created_at: datetime
    history: List[DocumentFieldHistoryResponse] = []

    class Config:
        from_attributes = True

class DocumentResponse(BaseModel):
    id: str
    file_name: str
    content_type: str
    file_size: int
    storage_reference: str
    document_type: str
    classification_confidence: float
    processing_status: str
    uploaded_by_id: Optional[str] = None
    raw_text: Optional[str] = None
    created_at: datetime
    fields: List[DocumentFieldResponse] = []

    class Config:
        from_attributes = True

class DocumentFieldEditRequest(BaseModel):
    new_value: str
    reason: Optional[str] = "Manual reviewer correction"
