import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Text, JSON, Numeric, Float
from sqlalchemy.orm import relationship
from app.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class Organization(Base):
    __tablename__ = "organizations"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    users = relationship("User", back_populates="organization")

class User(Base):
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(200), nullable=False)
    name = Column(String(100), nullable=False)
    role = Column(String(20), nullable=False)  # "reviewer", "manager"
    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    organization = relationship("Organization", back_populates="users")
    resolutions = relationship("Resolution", back_populates="actor")
    audit_events = relationship("AuditEvent", back_populates="actor")

class Vendor(Base):
    __tablename__ = "vendors"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False)
    vendor_code = Column(String(50), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    purchase_orders = relationship("PurchaseOrder", back_populates="vendor")
    invoices = relationship("Invoice", back_populates="vendor")

class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    po_number = Column(String(50), unique=True, nullable=False, index=True)
    vendor_id = Column(String(36), ForeignKey("vendors.id"), nullable=False)
    total_amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(10), default="USD")
    status = Column(String(30), nullable=False)  # "open", "fully_invoiced", "closed"
    order_date = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    vendor = relationship("Vendor", back_populates="purchase_orders")
    lines = relationship("PurchaseOrderLine", back_populates="purchase_order", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="purchase_order")
    exceptions = relationship("Exception", back_populates="purchase_order")

class PurchaseOrderLine(Base):
    __tablename__ = "purchase_order_lines"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    po_id = Column(String(36), ForeignKey("purchase_orders.id"), nullable=False)
    description = Column(String(200), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(12, 2), nullable=False)
    tax_rate = Column(Numeric(5, 2), default=0.08) # e.g. 0.08 for 8%
    tax_amount = Column(Numeric(12, 2), nullable=False)
    total_amount = Column(Numeric(12, 2), nullable=False)
    
    purchase_order = relationship("PurchaseOrder", back_populates="lines")

class Invoice(Base):
    __tablename__ = "invoices"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    invoice_number = Column(String(50), nullable=False, index=True)
    po_id = Column(String(36), ForeignKey("purchase_orders.id"), nullable=True)
    vendor_id = Column(String(36), ForeignKey("vendors.id"), nullable=False)
    subtotal = Column(Numeric(12, 2), nullable=False)
    tax = Column(Numeric(12, 2), nullable=False)
    total = Column(Numeric(12, 2), nullable=False)
    status = Column(String(30), nullable=False)  # "received", "processing", "matched", "exception", "paid"
    invoice_date = Column(DateTime, default=datetime.utcnow)
    due_date = Column(DateTime, nullable=False)
    received_at = Column(DateTime, default=datetime.utcnow)
    
    vendor = relationship("Vendor", back_populates="invoices")
    purchase_order = relationship("PurchaseOrder", back_populates="invoices")
    lines = relationship("InvoiceLine", back_populates="invoice", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="invoice")
    exceptions = relationship("Exception", back_populates="invoice")

class InvoiceLine(Base):
    __tablename__ = "invoice_lines"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    invoice_id = Column(String(36), ForeignKey("invoices.id"), nullable=False)
    description = Column(String(200), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(12, 2), nullable=False)
    tax_rate = Column(Numeric(5, 2), default=0.08)
    tax_amount = Column(Numeric(12, 2), nullable=False)
    total_amount = Column(Numeric(12, 2), nullable=False)
    
    invoice = relationship("Invoice", back_populates="lines")

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    invoice_id = Column(String(36), ForeignKey("invoices.id"), nullable=True)
    po_id = Column(String(36), ForeignKey("purchase_orders.id"), nullable=True)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(10), default="USD")
    status = Column(String(30), nullable=False)  # "pending", "settled", "failed"
    transaction_date = Column(DateTime, default=datetime.utcnow)
    
    invoice = relationship("Invoice", back_populates="transactions")

class Exception(Base):
    __tablename__ = "exceptions"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    type = Column(String(50), nullable=False)  # "DUPLICATE_INVOICE", "AMOUNT_PRICE_MISMATCH", "MISSING_PO", "TAX_ANOMALY"
    status = Column(String(30), nullable=False, default="OPEN")  # "OPEN", "UNDER_REVIEW", "RESOLVED", "REJECTED", "ESCALATED", "FALSE_POSITIVE"
    severity = Column(String(20), nullable=False)  # "LOW", "MEDIUM", "HIGH"
    confidence = Column(Float, nullable=False, default=0.0)  # Calculated application confidence/decision score
    risk = Column(String(20), nullable=False)  # "LOW", "MEDIUM", "HIGH"
    invoice_id = Column(String(36), ForeignKey("invoices.id"), nullable=True)
    po_id = Column(String(36), ForeignKey("purchase_orders.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    invoice = relationship("Invoice", back_populates="exceptions")
    purchase_order = relationship("PurchaseOrder", back_populates="exceptions")
    evidence = relationship("Evidence", back_populates="exception", cascade="all, delete-orphan")
    investigations = relationship("Investigation", back_populates="exception", cascade="all, delete-orphan")
    resolutions = relationship("Resolution", back_populates="exception", cascade="all, delete-orphan")
    audit_events = relationship("AuditEvent", back_populates="exception", cascade="all, delete-orphan")
    policy_decisions = relationship("PolicyDecision", back_populates="exception", cascade="all, delete-orphan")

class Evidence(Base):
    __tablename__ = "evidence"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    exception_id = Column(String(36), ForeignKey("exceptions.id"), nullable=False)
    source = Column(String(100), nullable=False)  # e.g. "Invoice Database", "Purchase Order", "Tax API"
    field = Column(String(50), nullable=False)  # e.g. "Amount", "Vendor Code", "Tax Rate"
    value = Column(String(200), nullable=False)  # Value found
    explanation = Column(Text, nullable=False)  # Explanation of how it was determined
    fact_type = Column(String(30), nullable=False)  # "VERIFIED_FACT", "EXTRACTED_FACT", "AI_INTERPRETATION"
    created_at = Column(DateTime, default=datetime.utcnow)
    
    exception = relationship("Exception", back_populates="evidence")

class Investigation(Base):
    __tablename__ = "investigations"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    exception_id = Column(String(36), ForeignKey("exceptions.id"), nullable=False)
    finding = Column(Text, nullable=False)
    recommendation = Column(String(30), nullable=False)  # "AUTO_RESOLVE", "APPROVE", "REJECT", "ESCALATE"
    confidence = Column(Float, nullable=False)
    risk = Column(String(20), nullable=False)  # "LOW", "MEDIUM", "HIGH"
    reason = Column(Text, nullable=False)
    raw_ai_response = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    exception = relationship("Exception", back_populates="investigations")

class Resolution(Base):
    __tablename__ = "resolutions"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    exception_id = Column(String(36), ForeignKey("exceptions.id"), nullable=False)
    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=True)
    action = Column(String(30), nullable=False)  # "RESOLVE", "APPROVE", "REJECT", "ESCALATE", "FALSE_POSITIVE", "AUTO_RESOLVE"
    previous_status = Column(String(30), nullable=True)
    new_status = Column(String(30), nullable=True)
    actor_type = Column(String(20), default="USER")  # "USER" or "SYSTEM"
    actor_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    comments = Column(Text, nullable=True)
    policy_decision_id = Column(String(36), ForeignKey("policy_decisions.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    exception = relationship("Exception", back_populates="resolutions")
    actor = relationship("User", back_populates="resolutions")
    policy_decision = relationship("PolicyDecision")

class Policy(Base):
    __tablename__ = "policies"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False, unique=True)
    is_active = Column(Boolean, default=True)
    rules = Column(JSON, nullable=False)  # E.g., confidence thresholds, risk levels
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AuditEvent(Base):
    __tablename__ = "audit_events"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    exception_id = Column(String(36), ForeignKey("exceptions.id"), nullable=True)
    actor_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    event = Column(String(100), nullable=False)  # e.g., "EXCEPTION_CREATED", "AUTO_RESOLVE_RUN", "MANUAL_RESOLVE"
    previous_status = Column(String(30), nullable=True)
    new_status = Column(String(30), nullable=True)
    reason = Column(Text, nullable=True)
    meta_data = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    exception = relationship("Exception", back_populates="audit_events")
    actor = relationship("User", back_populates="audit_events")

class PolicyDecision(Base):
    __tablename__ = "policy_decisions"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    exception_id = Column(String(36), ForeignKey("exceptions.id"), nullable=False)
    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=True)
    investigation_id = Column(String(36), ForeignKey("investigations.id"), nullable=True)
    policy_id = Column(String(36), ForeignKey("policies.id"), nullable=True)
    policy_name = Column(String(100), nullable=False)
    policy_version = Column(Integer, default=1)
    decision = Column(String(30), nullable=False)  # "AUTO_RESOLVE", "HUMAN_REVIEW", "ESCALATE"
    ai_confidence = Column(Float, nullable=False, default=0.0)
    risk = Column(String(20), nullable=False)  # "LOW", "MEDIUM", "HIGH"
    financial_impact = Column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    evidence_complete = Column(Boolean, default=True)
    evaluated_conditions = Column(JSON, nullable=False)  # [{condition, actual_value, passed}]
    reasons = Column(JSON, nullable=False)  # [string reasons]
    created_at = Column(DateTime, default=datetime.utcnow)
    
    exception = relationship("Exception", back_populates="policy_decisions")
    investigation = relationship("Investigation")
    policy = relationship("Policy")

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=True)
    file_name = Column(String(255), nullable=False)
    content_type = Column(String(100), nullable=False)
    file_size = Column(Integer, nullable=False)
    storage_reference = Column(String(500), nullable=False)
    document_type = Column(String(50), default="INVOICE")
    classification_confidence = Column(Float, default=0.90)
    processing_status = Column(String(30), default="UPLOADED")
    uploaded_by_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    raw_text = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    uploader = relationship("User")
    fields = relationship("DocumentField", back_populates="document", cascade="all, delete-orphan")

class DocumentField(Base):
    __tablename__ = "document_fields"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=False)
    field_name = Column(String(100), nullable=False)
    extracted_value = Column(Text, nullable=True)
    normalized_value = Column(Text, nullable=True)
    confidence = Column(Float, default=0.85)
    confidence_level = Column(String(20), default="MEDIUM")
    page_number = Column(Integer, default=1)
    bounding_box = Column(JSON, nullable=True)
    verification_status = Column(String(30), default="UNVERIFIED")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    document = relationship("Document", back_populates="fields")
    history = relationship("DocumentFieldHistory", back_populates="field", cascade="all, delete-orphan")

class DocumentFieldHistory(Base):
    __tablename__ = "document_field_histories"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    field_id = Column(String(36), ForeignKey("document_fields.id"), nullable=False)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    action = Column(String(30), nullable=False)
    actor_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    reason = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    field = relationship("DocumentField", back_populates="history")
    actor = relationship("User")
