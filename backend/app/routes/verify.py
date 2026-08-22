from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload
from typing import List

from app.database import get_db
from app import models, schemas, auth

router = APIRouter(tags=["verification"])

@router.get("/vendors", response_model=List[schemas.VendorResponse])
def get_vendors(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns list of seeded vendors.
    """
    vendors = db.query(models.Vendor).order_by(models.Vendor.name).all()
    return vendors

@router.get("/purchase-orders", response_model=List[schemas.PurchaseOrderResponse])
def get_purchase_orders(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns list of seeded purchase orders and their line items.
    """
    pos = db.query(models.PurchaseOrder).options(
        joinedload(models.PurchaseOrder.lines)
    ).order_by(models.PurchaseOrder.po_number).all()
    return pos

@router.get("/invoices", response_model=List[schemas.InvoiceResponse])
def get_invoices(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns list of seeded invoices and their line items.
    """
    invoices = db.query(models.Invoice).options(
        joinedload(models.Invoice.lines)
    ).order_by(models.Invoice.invoice_date.desc()).all()
    return invoices

@router.get("/transactions", response_model=List[schemas.TransactionResponse])
def get_transactions(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns list of seeded payment ledger transactions.
    """
    transactions = db.query(models.Transaction).order_by(models.Transaction.transaction_date.desc()).all()
    return transactions
