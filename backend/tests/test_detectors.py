import sys
import os
import unittest
from decimal import Decimal
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Adjust path to find app package
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import Base
from app import models
from app.engine import (
    DuplicateInvoiceDetector,
    AmountPriceMismatchDetector,
    MissingPurchaseOrderDetector,
    TaxAnomalyDetector,
    ExceptionDetectionEngine
)

class TestExceptionEngine(unittest.TestCase):
    def setUp(self):
        # Set up an in-memory database for clean, isolated tests
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)
        self.db = self.SessionLocal()
        
        # Seed test organization and vendor
        self.org = models.Organization(name="Test Org")
        self.db.add(self.org)
        self.db.flush()
        
        self.vendor = models.Vendor(name="Test Vendor", vendor_code="VND-TEST")
        self.db.add(self.vendor)
        self.db.commit()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)

    def test_duplicate_invoice_detector(self):
        detector = DuplicateInvoiceDetector()
        
        # 1. Create original invoice
        inv1 = models.Invoice(
            invoice_number="INV-1001",
            vendor_id=self.vendor.id,
            subtotal=Decimal("1000.00"),
            tax=Decimal("80.00"),
            total=Decimal("1080.00"),
            status="paid",
            due_date=datetime.utcnow() + timedelta(days=30)
        )
        self.db.add(inv1)
        self.db.commit()
        
        # 2. Create non-duplicate invoice (different invoice number)
        inv_clean = models.Invoice(
            invoice_number="INV-1002",
            vendor_id=self.vendor.id,
            subtotal=Decimal("1000.00"),
            tax=Decimal("80.00"),
            total=Decimal("1080.00"),
            status="processing",
            due_date=datetime.utcnow() + timedelta(days=30)
        )
        self.db.add(inv_clean)
        self.db.commit()
        
        results_clean = detector.detect(self.db, inv_clean)
        self.assertEqual(len(results_clean), 0, "No duplicate exception should be detected for unique invoice number")
        
        # 3. Create duplicate invoice (same number, same vendor)
        inv_dup = models.Invoice(
            invoice_number="INV-1001",
            vendor_id=self.vendor.id,
            subtotal=Decimal("1000.00"),
            tax=Decimal("80.00"),
            total=Decimal("1080.00"),
            status="processing",
            due_date=datetime.utcnow() + timedelta(days=30)
        )
        self.db.add(inv_dup)
        self.db.commit()
        
        results_dup = detector.detect(self.db, inv_dup)
        self.assertEqual(len(results_dup), 1, "Duplicate exception must be detected for identical vendor and invoice number")
        exc, evidences = results_dup[0]
        self.assertEqual(exc.type, "DUPLICATE_INVOICE")
        self.assertEqual(exc.severity, "MEDIUM") # amount is $1080, which is >= $1000 threshold
        self.assertTrue(any(ev.field == "invoice_number" and ev.value == "INV-1001" for ev in evidences))

    def test_amount_price_mismatch_detector(self):
        detector = AmountPriceMismatchDetector()
        
        # 1. Create a PO
        po = models.PurchaseOrder(
            po_number="PO-5001",
            vendor_id=self.vendor.id,
            total_amount=Decimal("10000.00"),
            status="open"
        )
        self.db.add(po)
        self.db.flush()
        
        po_line = models.PurchaseOrderLine(
            po_id=po.id,
            description="Laptops",
            quantity=10,
            unit_price=Decimal("1000.00"),
            tax_rate=Decimal("0.00"),
            tax_amount=Decimal("0.00"),
            total_amount=Decimal("10000.00")
        )
        self.db.add(po_line)
        self.db.commit()
        
        # 2. Test exact match (no exception)
        inv_match = models.Invoice(
            invoice_number="INV-2001",
            po_id=po.id,
            vendor_id=self.vendor.id,
            subtotal=Decimal("10000.00"),
            tax=Decimal("0.00"),
            total=Decimal("10000.00"),
            status="processing",
            due_date=datetime.utcnow() + timedelta(days=30)
        )
        self.db.add(inv_match)
        self.db.flush()
        inv_match_line = models.InvoiceLine(
            invoice_id=inv_match.id,
            description="Laptops",
            quantity=10,
            unit_price=Decimal("1000.00"),
            tax_rate=Decimal("0.00"),
            tax_amount=Decimal("0.00"),
            total_amount=Decimal("10000.00")
        )
        self.db.add(inv_match_line)
        self.db.commit()
        
        results_match = detector.detect(self.db, inv_match)
        self.assertEqual(len(results_match), 0, "No mismatch should be detected for perfect match invoice/PO details")
        
        # 3. Test total amount mismatch
        inv_mismatch = models.Invoice(
            invoice_number="INV-2002",
            po_id=po.id,
            vendor_id=self.vendor.id,
            subtotal=Decimal("11000.00"),
            tax=Decimal("0.00"),
            total=Decimal("11000.00"),
            status="processing",
            due_date=datetime.utcnow() + timedelta(days=30)
        )
        self.db.add(inv_mismatch)
        self.db.flush()
        inv_mismatch_line = models.InvoiceLine(
            invoice_id=inv_mismatch.id,
            description="Laptops",
            quantity=10,
            unit_price=Decimal("1100.00"), # Price mismatch! Unit price is $1100 instead of $1000
            tax_rate=Decimal("0.00"),
            tax_amount=Decimal("0.00"),
            total_amount=Decimal("11000.00")
        )
        self.db.add(inv_mismatch_line)
        self.db.commit()
        
        results_mismatch = detector.detect(self.db, inv_mismatch)
        self.assertEqual(len(results_mismatch), 1)
        exc, evidences = results_mismatch[0]
        self.assertEqual(exc.type, "AMOUNT_PRICE_MISMATCH")
        self.assertEqual(exc.severity, "MEDIUM") # Deviation amount is $1000, >= $1000 limit
        self.assertTrue(any(ev.field == "unit_price" and ev.value == "1100.00" for ev in evidences))

    def test_missing_po_detector(self):
        detector = MissingPurchaseOrderDetector()
        
        # 1. Invoice with PO
        po = models.PurchaseOrder(po_number="PO-6001", vendor_id=self.vendor.id, total_amount=Decimal("500.00"), status="open")
        self.db.add(po)
        self.db.flush()
        
        inv_with_po = models.Invoice(
            invoice_number="INV-3001",
            po_id=po.id,
            vendor_id=self.vendor.id,
            subtotal=Decimal("500.00"),
            tax=Decimal("0.00"),
            total=Decimal("500.00"),
            status="processing",
            due_date=datetime.utcnow() + timedelta(days=30)
        )
        self.db.add(inv_with_po)
        self.db.commit()
        
        results_ok = detector.detect(self.db, inv_with_po)
        self.assertEqual(len(results_ok), 0, "No missing PO exception should be detected when PO references exist")
        
        # 2. Invoice with NULL PO reference
        inv_no_po = models.Invoice(
            invoice_number="INV-3002",
            po_id=None,
            vendor_id=self.vendor.id,
            subtotal=Decimal("500.00"),
            tax=Decimal("0.00"),
            total=Decimal("500.00"),
            status="processing",
            due_date=datetime.utcnow() + timedelta(days=30)
        )
        self.db.add(inv_no_po)
        self.db.commit()
        
        results_err = detector.detect(self.db, inv_no_po)
        self.assertEqual(len(results_err), 1)
        exc, evidences = results_err[0]
        self.assertEqual(exc.type, "MISSING_PO")
        self.assertEqual(exc.severity, "MEDIUM") # total amount is 500, < 1000 threshold
        
        # 3. Invoice with non-existent PO reference ID
        inv_bad_po = models.Invoice(
            invoice_number="INV-3003",
            po_id="non-existent-po-uuid",
            vendor_id=self.vendor.id,
            subtotal=Decimal("1200.00"),
            tax=Decimal("0.00"),
            total=Decimal("1200.00"),
            status="processing",
            due_date=datetime.utcnow() + timedelta(days=30)
        )
        self.db.add(inv_bad_po)
        self.db.commit()
        
        results_bad = detector.detect(self.db, inv_bad_po)
        self.assertEqual(len(results_bad), 1)
        exc_b, evidences_b = results_bad[0]
        self.assertEqual(exc_b.type, "MISSING_PO")
        self.assertEqual(exc_b.severity, "HIGH") # total amount is 1200, >= 1000 threshold

    def test_tax_anomaly_detector(self):
        detector = TaxAnomalyDetector()
        
        # 1. Correct standard 8% tax rate
        inv_ok = models.Invoice(
            invoice_number="INV-4001",
            vendor_id=self.vendor.id,
            subtotal=Decimal("2000.00"),
            tax=Decimal("160.00"), # 2000 * 0.08 = 160
            total=Decimal("2160.00"),
            status="processing",
            due_date=datetime.utcnow() + timedelta(days=30)
        )
        self.db.add(inv_ok)
        self.db.commit()
        
        results_ok = detector.detect(self.db, inv_ok)
        self.assertEqual(len(results_ok), 0, "No tax anomaly should be detected for exact 8% calculations")
        
        # 2. Tax rate mismatch (expected 160, billed 100)
        inv_err = models.Invoice(
            invoice_number="INV-4002",
            vendor_id=self.vendor.id,
            subtotal=Decimal("2000.00"),
            tax=Decimal("100.00"), # 100 instead of 160
            total=Decimal("2100.00"),
            status="processing",
            due_date=datetime.utcnow() + timedelta(days=30)
        )
        self.db.add(inv_err)
        self.db.commit()
        
        results_err = detector.detect(self.db, inv_err)
        self.assertEqual(len(results_err), 1)
        exc, evidences = results_err[0]
        self.assertEqual(exc.type, "TAX_ANOMALY")
        self.assertEqual(exc.severity, "LOW") # tax discrepancy is $60 (< $1000)

    def test_idempotency_run(self):
        engine = ExceptionDetectionEngine()
        
        # Create an invoice with missing PO reference
        invoice = models.Invoice(
            invoice_number="INV-5001",
            po_id=None,
            vendor_id=self.vendor.id,
            subtotal=Decimal("200.00"),
            tax=Decimal("16.00"),
            total=Decimal("216.00"),
            status="processing",
            due_date=datetime.utcnow() + timedelta(days=30)
        )
        self.db.add(invoice)
        self.db.commit()
        
        # First run: detects 1 exception
        results1 = engine.run(self.db, invoice)
        self.assertEqual(len(results1), 1)
        
        # Persist the exception manually to simulate first run store
        exc, evidences = results1[0]
        self.db.add(exc)
        self.db.flush()
        for ev in evidences:
            ev.exception_id = exc.id
            self.db.add(ev)
        self.db.commit()
        
        # Query active exception count
        count_pre = self.db.query(models.Exception).filter(models.Exception.invoice_id == invoice.id).count()
        self.assertEqual(count_pre, 1)
        
        # Simulate an idempotent POST run logic:
        # Check if an exception of same type exists in OPEN before adding
        results2 = engine.run(self.db, invoice)
        self.assertEqual(len(results2), 1)
        
        for exc_new, ev_new in results2:
            existing = self.db.query(models.Exception).filter(
                models.Exception.invoice_id == invoice.id,
                models.Exception.type == exc_new.type,
                models.Exception.status == "OPEN"
            ).first()
            self.assertIsNotNone(existing, "An open exception of the same type must be discovered in the DB")

if __name__ == "__main__":
    unittest.main()
