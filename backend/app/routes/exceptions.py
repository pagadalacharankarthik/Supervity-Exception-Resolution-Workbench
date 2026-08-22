from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, desc, asc
from typing import List, Optional
from math import ceil
from decimal import Decimal

from app.database import get_db
from app import models, schemas, auth

router = APIRouter(prefix="/exceptions", tags=["exceptions"])

@router.get("", response_model=schemas.PaginatedExceptionResponse)
def list_exceptions(
    page: int = 1,
    page_size: int = 20,
    search: Optional[str] = None,
    status_filter: Optional[str] = None,
    risk_filter: Optional[str] = None,
    type_filter: Optional[str] = None,
    severity_filter: Optional[str] = None,
    vendor_filter: Optional[str] = None,
    sort_by: Optional[str] = "severity",
    sort_order: Optional[str] = "desc",
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(models.Exception).outerjoin(models.Invoice).outerjoin(models.Vendor).outerjoin(models.PurchaseOrder)
    
    # 1. Filters
    if status_filter:
        query = query.filter(models.Exception.status == status_filter)
    if risk_filter:
        query = query.filter(models.Exception.risk == risk_filter)
    if type_filter:
        query = query.filter(models.Exception.type == type_filter)
    if severity_filter:
        query = query.filter(models.Exception.severity == severity_filter)
    if vendor_filter:
        query = query.filter(models.Vendor.name.ilike(f"%{vendor_filter}%") | models.Vendor.vendor_code.ilike(f"%{vendor_filter}%"))
        
    # 2. Search
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                models.Exception.id.ilike(search_pattern),
                models.Exception.type.ilike(search_pattern),
                models.Invoice.invoice_number.ilike(search_pattern),
                models.PurchaseOrder.po_number.ilike(search_pattern),
                models.Vendor.name.ilike(search_pattern)
            )
        )
        
    # 3. Sorting
    if sort_by == "created_at":
        order_col = models.Exception.created_at
        query = query.order_by(desc(order_col) if sort_order == "desc" else asc(order_col))
    elif sort_by == "amount":
        order_col = models.Invoice.total
        query = query.order_by(desc(order_col) if sort_order == "desc" else asc(order_col))
    elif sort_by == "status":
        order_col = models.Exception.status
        query = query.order_by(desc(order_col) if sort_order == "desc" else asc(order_col))
    else:
        # Default: Highest severity / most recent open exceptions first
        query = query.order_by(
            desc(models.Exception.severity),
            desc(models.Exception.created_at)
        )
        
    total = query.count()
    total_pages = ceil(total / page_size) if page_size > 0 else 1
    
    # Apply pagination offset & limit
    offset = (page - 1) * page_size
    exceptions = query.offset(offset).limit(page_size).all()
    
    items = []
    for exc in exceptions:
        invoice = exc.invoice
        vendor_name = invoice.vendor.name if (invoice and invoice.vendor) else "Unknown Vendor"
        amount = invoice.total if invoice else Decimal("0.00")
        
        items.append({
            "id": exc.id,
            "type": exc.type,
            "status": exc.status,
            "severity": exc.severity,
            "confidence": exc.confidence,
            "risk": exc.risk,
            "amount": amount,
            "vendor_name": vendor_name,
            "created_at": exc.created_at,
            "updated_at": exc.updated_at
        })
        
    return {
        "items": items,
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": total_pages
    }

@router.post("/detect")
def detect_exceptions(
    current_user: models.User = Depends(auth.get_current_reviewer),
    db: Session = Depends(get_db)
):
    from app.engine import ExceptionDetectionEngine
    engine = ExceptionDetectionEngine()
    
    invoices = db.query(models.Invoice).all()
    
    detected_count = 0
    new_count = 0
    existing_count = 0
    
    for invoice in invoices:
        results = engine.run(db, invoice)
        for exc, evidences in results:
            detected_count += 1
            
            existing = db.query(models.Exception).filter(
                models.Exception.invoice_id == invoice.id,
                models.Exception.type == exc.type,
                models.Exception.status.in_(["OPEN", "UNDER_REVIEW", "ESCALATED"])
            ).first()
            
            if existing:
                existing_count += 1
            else:
                new_count += 1
                db.add(exc)
                db.flush()
                
                for ev in evidences:
                    ev.exception_id = exc.id
                    db.add(ev)
                
                audit = models.AuditEvent(
                    exception_id=exc.id,
                    actor_id=None,
                    event="EXCEPTION_DETECTED",
                    previous_status=None,
                    new_status="OPEN",
                    reason=f"Deterministic audit rule flagged {exc.type} discrepancy."
                )
                db.add(audit)
                
    db.commit()
    return {
        "detected": detected_count,
        "new_exceptions": new_count,
        "existing_exceptions": existing_count
    }

@router.get("/{id}", response_model=schemas.ExceptionDetailResponse)
def get_exception_detail(
    id: str,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    exc = db.query(models.Exception).options(
        joinedload(models.Exception.invoice).joinedload(models.Invoice.vendor),
        joinedload(models.Exception.purchase_order),
        joinedload(models.Exception.evidence),
        joinedload(models.Exception.investigations),
        joinedload(models.Exception.resolutions).joinedload(models.Resolution.actor),
        joinedload(models.Exception.audit_events).joinedload(models.AuditEvent.actor)
    ).filter(models.Exception.id == id).first()
    
    if not exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exception case not found"
        )
        
    invoice = exc.invoice
    vendor_name = invoice.vendor.name if (invoice and invoice.vendor) else "Unknown Vendor"
    vendor_id = invoice.vendor_id if invoice else None
    amount = invoice.total if invoice else Decimal("0.00")
    items = invoice.lines if invoice else []
    tax_amount = invoice.tax if invoice else Decimal("0.00")
    po_num = exc.purchase_order.po_number if exc.purchase_order else None
    
    resolutions_list = []
    for res in exc.resolutions:
        resolutions_list.append({
            "id": res.id,
            "action": res.action,
            "actor_id": res.actor_id,
            "actor_name": res.actor.name,
            "comments": res.comments,
            "created_at": res.created_at
        })
        
    audit_list = []
    for audit in exc.audit_events:
        audit_list.append({
            "id": audit.id,
            "actor_id": audit.actor_id,
            "actor_name": audit.actor.name if audit.actor else "System",
            "event": audit.event,
            "previous_status": audit.previous_status,
            "new_status": audit.new_status,
            "reason": audit.reason,
            "meta_data": audit.meta_data,
            "timestamp": audit.timestamp
        })

    audit_list = sorted(audit_list, key=lambda x: x["timestamp"])

    return {
        "id": exc.id,
        "type": exc.type,
        "status": exc.status,
        "severity": exc.severity,
        "confidence": exc.confidence,
        "risk": exc.risk,
        "invoice_id": exc.invoice_id,
        "invoice_number": invoice.invoice_number if invoice else None,
        "po_id": exc.po_id,
        "po_number": po_num,
        "vendor_id": vendor_id,
        "vendor_name": vendor_name,
        "amount": amount,
        "items": items,
        "tax_amount": tax_amount,
        "created_at": exc.created_at,
        "updated_at": exc.updated_at,
        "evidence": exc.evidence,
        "investigations": exc.investigations,
        "resolutions": resolutions_list,
        "audit_events": audit_list
    }
