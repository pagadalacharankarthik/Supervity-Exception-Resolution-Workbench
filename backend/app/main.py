from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import uuid
import logging
from decimal import Decimal
from datetime import datetime, timedelta

from app.config import settings
from app.database import get_db, engine, Base
from app import models, schemas, auth, engine as exception_engine
from app.routes import auth as auth_routes, dashboard, exceptions, investigation, policies, audit, verify, documents

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Supervity Exception Resolution Workbench Backend API",
    version="1.0.0"
)

import os

# Build allowed origins from environment variable + local dev defaults
_frontend_url = os.environ.get("FRONTEND_URL", "")
_allowed_origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
if _frontend_url:
    # Support comma-separated list e.g. "https://app.vercel.app,https://custom.domain.com"
    for url in _frontend_url.split(","):
        url = url.strip()
        if url and url not in _allowed_origins:
            _allowed_origins.append(url)

# Enable CORS for frontend connection
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routes
app.include_router(auth_routes.router, prefix=settings.API_V1_STR)
app.include_router(dashboard.router, prefix=settings.API_V1_STR)
app.include_router(exceptions.router, prefix=settings.API_V1_STR)
app.include_router(investigation.router, prefix=settings.API_V1_STR)
app.include_router(policies.router, prefix=settings.API_V1_STR)
app.include_router(documents.router, prefix=settings.API_V1_STR)
app.include_router(audit.router, prefix=settings.API_V1_STR)
app.include_router(verify.router, prefix=settings.API_V1_STR)

# Ensure database tables exist
models.Base.metadata.create_all(bind=engine)

@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": "Supervity Exception Resolution API",
        "environment": "Assessment Prototype • Synthetic Data"
    }

@app.post("/api/documents/extract")
def extract_document(
    file: UploadFile = File(...),
    document_type: str = Form("invoice"), # "invoice" or "purchase_order"
    current_user: models.User = Depends(auth.get_current_reviewer),
    db: Session = Depends(get_db)
):
    """
    Mock document extraction pipeline.
    Accepts invoice PDFs/images and normalizes them into structured database entities,
    then executes the deterministic exception rules.
    To demo easily:
    - Uploading a file containing 'duplicate' creates a DUPLICATE_INVOICE case.
    - Uploading a file containing 'mismatch' creates an AMOUNT_PRICE_MISMATCH case.
    - Uploading a file containing 'anomaly' creates a MISSING_PO case.
    """
    filename = file.filename.lower()
    
    # Resolve vendor IDs
    apex = db.query(models.Vendor).filter(models.Vendor.vendor_code == "VND-APEX").first()
    vertex = db.query(models.Vendor).filter(models.Vendor.vendor_code == "VND-VERTEX").first()
    glob = db.query(models.Vendor).filter(models.Vendor.vendor_code == "VND-GLOBAL").first()
    
    if not apex or not vertex or not glob:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Vendor records not found. Please seed the database first."
        )

    # 1. Simulate Document parsing and normalization
    try:
        due_date = datetime.utcnow() + timedelta(days=30)
        if "duplicate" in filename:
            new_inv = models.Invoice(
                invoice_number="INV-2026-001", # same number as seed Case 1
                po_id=None,
                vendor_id=apex.id,
                subtotal=Decimal("4200.00"),
                tax=Decimal("336.00"),
                total=Decimal("4536.00"),
                status="processing",
                due_date=due_date
            )
            db.add(new_inv)
            db.flush()
            # Add lines
            db.add_all([
                models.InvoiceLine(invoice_id=new_inv.id, description="Heavy Duty Industrial Racks", quantity=10, unit_price=Decimal("300.00"), tax_rate=Decimal("0.08"), tax_amount=Decimal("240.00"), total_amount=Decimal("3240.00")),
                models.InvoiceLine(invoice_id=new_inv.id, description="Warehouse Storage Bins", quantity=10, unit_price=Decimal("120.00"), tax_rate=Decimal("0.08"), tax_amount=Decimal("96.00"), total_amount=Decimal("1296.00"))
            ])
        elif "mismatch" in filename:
            po = db.query(models.PurchaseOrder).filter(models.PurchaseOrder.po_number == "PO-2026-002").first()
            new_inv = models.Invoice(
                invoice_number=f"INV-{uuid.uuid4().hex[:6].upper()}",
                po_id=po.id if po else None,
                vendor_id=vertex.id,
                subtotal=Decimal("55000.00"),
                tax=Decimal("0.00"),
                total=Decimal("55000.00"),
                status="processing",
                due_date=due_date
            )
            db.add(new_inv)
            db.flush()
            db.add(models.InvoiceLine(invoice_id=new_inv.id, description="Cloud Infrastructure Compute Units", quantity=500, unit_price=Decimal("110.00"), tax_rate=Decimal("0.00"), tax_amount=Decimal("0.00"), total_amount=Decimal("55000.00")))
        elif "anomaly" in filename or "missing" in filename:
            new_inv = models.Invoice(
                invoice_number=f"INV-{uuid.uuid4().hex[:6].upper()}",
                po_id=None, # Missing PO reference
                vendor_id=glob.id,
                subtotal=Decimal("65000.00"),
                tax=Decimal("5200.00"),
                total=Decimal("70200.00"),
                status="processing",
                due_date=due_date
            )
            db.add(new_inv)
            db.flush()
            db.add(models.InvoiceLine(invoice_id=new_inv.id, description="Annual Security Auditing Services", quantity=1, unit_price=Decimal("65000.00"), tax_rate=Decimal("0.08"), tax_amount=Decimal("5200.00"), total_amount=Decimal("70200.00")))
        else:
            # Standard matching invoice
            new_inv = models.Invoice(
                invoice_number=f"INV-{uuid.uuid4().hex[:6].upper()}",
                po_id=None,
                vendor_id=apex.id,
                subtotal=Decimal("1200.00"),
                tax=Decimal("96.00"),
                total=Decimal("1296.00"),
                status="processing",
                due_date=due_date
            )
            db.add(new_inv)
            db.flush()
            db.add(models.InvoiceLine(invoice_id=new_inv.id, description="Ergonomic Chairs", quantity=10, unit_price=Decimal("120.00"), tax_rate=Decimal("0.08"), tax_amount=Decimal("96.00"), total_amount=Decimal("1296.00")))
            
        db.commit()
        db.refresh(new_inv)
        
        # 2. Execute Deterministic Exception Rules
        exceptions = exception_engine.run_exception_detection(db, new_inv)
        db.commit()
        
        # Log Audit Event for file processing
        audit = models.AuditEvent(
            exception_id=exceptions[0].id if exceptions else None,
            actor_id=current_user.id,
            event="DOCUMENT_EXTRACTED",
            previous_status=None,
            new_status="NEW" if exceptions else "MATCHED",
            reason=f"File '{file.filename}' processed. Extracted {len(exceptions)} exceptions.",
            meta_data={"filename": file.filename, "invoice_id": new_inv.id}
        )
        db.add(audit)
        db.commit()
        
        return {
            "success": True,
            "filename": file.filename,
            "extracted_invoice_id": new_inv.id,
            "invoice_number": new_inv.invoice_number,
            "amount": new_inv.total,
            "exceptions_created": len(exceptions),
            "exceptions": [{"id": e.id, "type": e.type, "severity": e.severity} for e in exceptions]
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error in mock document extractor: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document extraction pipeline failure: {str(e)}"
        )
