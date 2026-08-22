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
from app.engine import PolicyEngine

class TestResolutionWorkflow(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)
        self.db = self.SessionLocal()
        
        self.org = models.Organization(name="Supervity Demo Org")
        self.db.add(self.org)
        self.db.flush()
        
        self.user = models.User(
            email="reviewer@supervity-demo.com",
            hashed_password="hashed_pass_123",
            name="Alex Reviewer",
            role="REVIEWER",
            organization_id=self.org.id
        )
        self.db.add(self.user)
        self.db.flush()
        
        self.vendor = models.Vendor(name="Apex Industrial", vendor_code="VND-APEX")
        self.db.add(self.vendor)
        self.db.flush()
        
        self.po = models.PurchaseOrder(po_number="PO-1001", vendor_id=self.vendor.id, total_amount=Decimal("5000.00"), status="open")
        self.db.add(self.po)
        self.db.flush()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)

    def test_human_resolve_success(self):
        inv = models.Invoice(invoice_number="INV-8001", po_id=self.po.id, vendor_id=self.vendor.id, subtotal=Decimal("1000.00"), tax=Decimal("80.00"), total=Decimal("1080.00"), status="processing", due_date=datetime.utcnow() + timedelta(days=30))
        self.db.add(inv)
        self.db.flush()
        
        exc = models.Exception(type="AMOUNT_PRICE_MISMATCH", status="OPEN", severity="MEDIUM", confidence=0.85, risk="LOW", invoice_id=inv.id, po_id=self.po.id)
        self.db.add(exc)
        self.db.commit()
        
        # Simulate human resolve
        exc.status = "RESOLVED"
        res = models.Resolution(
            exception_id=exc.id,
            organization_id=self.org.id,
            action="RESOLVE",
            previous_status="OPEN",
            new_status="RESOLVED",
            actor_type="USER",
            actor_id=self.user.id,
            comments="Verified line item variance with supplier."
        )
        self.db.add(res)
        
        audit = models.AuditEvent(exception_id=exc.id, actor_id=self.user.id, event="EXCEPTION_RESOLVED", previous_status="OPEN", new_status="RESOLVED", reason="Verified line item variance with supplier.")
        self.db.add(audit)
        self.db.commit()
        
        self.assertEqual(exc.status, "RESOLVED")
        self.assertEqual(res.actor_type, "USER")
        self.assertEqual(audit.event, "EXCEPTION_RESOLVED")

    def test_auto_resolve_safeguard_success(self):
        inv = models.Invoice(invoice_number="INV-8002", po_id=self.po.id, vendor_id=self.vendor.id, subtotal=Decimal("2000.00"), tax=Decimal("160.00"), total=Decimal("2160.00"), status="processing", due_date=datetime.utcnow() + timedelta(days=30))
        self.db.add(inv)
        self.db.flush()
        
        exc = models.Exception(type="DUPLICATE_INVOICE", status="OPEN", severity="LOW", confidence=0.95, risk="LOW", invoice_id=inv.id, po_id=self.po.id)
        self.db.add(exc)
        self.db.flush()
        
        ev = models.Evidence(exception_id=exc.id, source="DB", field="invoice_number", value="INV-8002", explanation="Duplicate verified", fact_type="VERIFIED_FACT")
        self.db.add(ev)
        self.db.flush()
        
        inv_rep = models.Investigation(exception_id=exc.id, finding="Duplicate verified.", recommendation="AUTO_RESOLVE", confidence=0.95, risk="LOW", reason="Low risk duplicate.")
        self.db.add(inv_rep)
        self.db.flush()
        
        # Policy evaluation yields AUTO_RESOLVE
        p_engine = PolicyEngine()
        p_eval = p_engine.evaluate(self.db, exc, inv_rep)
        
        p_dec = models.PolicyDecision(
            exception_id=exc.id,
            organization_id=self.org.id,
            investigation_id=inv_rep.id,
            policy_name=p_eval["policy_name"],
            policy_version=1,
            decision=p_eval["decision"],
            ai_confidence=p_eval["ai_confidence"],
            risk=p_eval["risk"],
            financial_impact=p_eval["financial_impact"],
            evidence_complete=True,
            evaluated_conditions=p_eval["evaluated_conditions"],
            reasons=p_eval["reasons"]
        )
        self.db.add(p_dec)
        self.db.commit()
        
        self.assertEqual(p_dec.decision, "AUTO_RESOLVE")

    def test_auto_resolve_safeguard_block_on_high_risk(self):
        inv = models.Invoice(invoice_number="INV-8003", po_id=None, vendor_id=self.vendor.id, subtotal=Decimal("60000.00"), tax=Decimal("4800.00"), total=Decimal("64800.00"), status="processing", due_date=datetime.utcnow() + timedelta(days=30))
        self.db.add(inv)
        self.db.flush()
        
        exc = models.Exception(type="MISSING_PO", status="OPEN", severity="HIGH", confidence=0.90, risk="HIGH", invoice_id=inv.id, po_id=None)
        self.db.add(exc)
        self.db.commit()
        
        p_engine = PolicyEngine()
        p_eval = p_engine.evaluate(self.db, exc)
        
        self.assertNotEqual(p_eval["decision"], "AUTO_RESOLVE")
        self.assertEqual(p_eval["decision"], "ESCALATE")

if __name__ == "__main__":
    unittest.main()
