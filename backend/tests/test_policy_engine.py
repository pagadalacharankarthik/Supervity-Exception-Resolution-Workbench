import sys
import os
import unittest
from decimal import Decimal
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import Base
from app import models
from app.engine import PolicyEngine, RiskAssessment

class TestPolicyEngine(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)
        self.db = self.SessionLocal()
        
        self.vendor = models.Vendor(name="Apex Industrial", vendor_code="VND-APEX")
        self.db.add(self.vendor)
        self.db.flush()
        
        self.po = models.PurchaseOrder(po_number="PO-1001", vendor_id=self.vendor.id, total_amount=Decimal("5000.00"), status="open")
        self.db.add(self.po)
        self.db.flush()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)

    def test_auto_resolve_decision(self):
        inv = models.Invoice(
            invoice_number="INV-7001",
            po_id=self.po.id,
            vendor_id=self.vendor.id,
            subtotal=Decimal("5000.00"),
            tax=Decimal("400.00"),
            total=Decimal("5400.00"),
            status="processing",
            due_date=datetime.utcnow() + timedelta(days=30)
        )
        self.db.add(inv)
        self.db.flush()
        
        exc = models.Exception(type="DUPLICATE_INVOICE", status="OPEN", severity="LOW", confidence=0.95, risk="LOW", invoice_id=inv.id, po_id=self.po.id)
        self.db.add(exc)
        self.db.flush()
        
        ev = models.Evidence(exception_id=exc.id, source="DB", field="invoice_number", value="INV-7001", explanation="Verified", fact_type="VERIFIED_FACT")
        self.db.add(ev)
        self.db.commit()
        
        policy_engine = PolicyEngine()
        res = policy_engine.evaluate(self.db, exc)
        
        self.assertEqual(res["decision"], "AUTO_RESOLVE")
        self.assertEqual(res["policy_name"], "Low-Risk Auto Resolution Policy v1")
        self.assertTrue(len(res["evaluated_conditions"]) >= 3)

    def test_human_review_decision(self):
        inv = models.Invoice(
            invoice_number="INV-7002",
            po_id=self.po.id,
            vendor_id=self.vendor.id,
            subtotal=Decimal("5000.00"),
            tax=Decimal("400.00"),
            total=Decimal("5400.00"),
            status="processing",
            due_date=datetime.utcnow() + timedelta(days=30)
        )
        self.db.add(inv)
        self.db.flush()
        
        # Confidence is 0.82 (< 0.90 threshold) -> HUMAN_REVIEW
        exc = models.Exception(type="AMOUNT_PRICE_MISMATCH", status="OPEN", severity="MEDIUM", confidence=0.82, risk="LOW", invoice_id=inv.id, po_id=self.po.id)
        self.db.add(exc)
        self.db.flush()
        
        ev = models.Evidence(exception_id=exc.id, source="DB", field="total", value="5400.00", explanation="Mismatch", fact_type="VERIFIED_FACT")
        self.db.add(ev)
        self.db.commit()
        
        policy_engine = PolicyEngine()
        res = policy_engine.evaluate(self.db, exc)
        
        self.assertEqual(res["decision"], "HUMAN_REVIEW")
        self.assertTrue(any("0.90" in r for r in res["reasons"]))

    def test_high_risk_escalation_override(self):
        inv = models.Invoice(
            invoice_number="INV-7003",
            po_id=None,
            vendor_id=self.vendor.id,
            subtotal=Decimal("15000.00"),
            tax=Decimal("1200.00"),
            total=Decimal("16200.00"),
            status="processing",
            due_date=datetime.utcnow() + timedelta(days=30)
        )
        self.db.add(inv)
        self.db.flush()
        
        # High confidence 0.99 but High Risk and Missing PO -> ESCALATE
        exc = models.Exception(type="MISSING_PO", status="OPEN", severity="HIGH", confidence=0.99, risk="HIGH", invoice_id=inv.id, po_id=None)
        self.db.add(exc)
        self.db.flush()
        
        ev = models.Evidence(exception_id=exc.id, source="DB", field="po_id", value="NULL", explanation="Missing PO", fact_type="VERIFIED_FACT")
        self.db.add(ev)
        self.db.commit()
        
        policy_engine = PolicyEngine()
        res = policy_engine.evaluate(self.db, exc)
        
        self.assertEqual(res["decision"], "ESCALATE")
        self.assertEqual(res["policy_name"], "High Risk Escalation Policy v1")

    def test_missing_evidence_escalation(self):
        inv = models.Invoice(
            invoice_number="INV-7004",
            po_id=self.po.id,
            vendor_id=self.vendor.id,
            subtotal=Decimal("1000.00"),
            tax=Decimal("80.00"),
            total=Decimal("1080.00"),
            status="processing",
            due_date=datetime.utcnow() + timedelta(days=30)
        )
        self.db.add(inv)
        self.db.flush()
        
        # No evidence items created -> missing evidence -> ESCALATE
        exc = models.Exception(type="TAX_ANOMALY", status="OPEN", severity="LOW", confidence=0.95, risk="LOW", invoice_id=inv.id, po_id=self.po.id)
        self.db.add(exc)
        self.db.commit()
        
        policy_engine = PolicyEngine()
        res = policy_engine.evaluate(self.db, exc)
        
        self.assertEqual(res["decision"], "ESCALATE")
        self.assertFalse(res["evidence_complete"])

if __name__ == "__main__":
    unittest.main()
