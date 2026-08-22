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
from app.document_processor import document_processor

class TestDocumentExtraction(unittest.TestCase):
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
        self.db.commit()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)

    def test_document_processing_pipeline(self):
        doc = models.Document(
            organization_id=self.org.id,
            file_name="sample_invoice.pdf",
            content_type="application/pdf",
            file_size=1024,
            storage_reference="non_existent_file.pdf",
            document_type="INVOICE",
            processing_status="UPLOADED",
            uploaded_by_id=self.user.id
        )
        self.db.add(doc)
        self.db.commit()
        
        processed_doc = document_processor.process_document(self.db, doc)
        self.assertIn(processed_doc.processing_status, ["EXTRACTED", "NEEDS_REVIEW"])
        self.assertTrue(len(processed_doc.fields) >= 4)
        
        field_names = [f.field_name for f in processed_doc.fields]
        self.assertIn("invoice_number", field_names)
        self.assertIn("total_amount", field_names)

    def test_field_verification_and_editing(self):
        doc = models.Document(
            organization_id=self.org.id,
            file_name="invoice_scan.png",
            content_type="image/png",
            file_size=2048,
            storage_reference="scan.png",
            document_type="INVOICE",
            processing_status="UPLOADED"
        )
        self.db.add(doc)
        self.db.commit()
        
        field = models.DocumentField(
            document_id=doc.id,
            field_name="total_amount",
            extracted_value="$55,000.00",
            normalized_value="55000.00",
            confidence=0.85,
            confidence_level="MEDIUM",
            verification_status="UNVERIFIED"
        )
        self.db.add(field)
        self.db.commit()
        
        # Test editing field
        field.extracted_value = "$50,000.00"
        field.verification_status = "EDITED"
        history = models.DocumentFieldHistory(
            field_id=field.id,
            old_value="$55,000.00",
            new_value="$50,000.00",
            action="EDIT",
            actor_id=self.user.id,
            reason="Corrected value against scan"
        )
        self.db.add(history)
        self.db.commit()
        
        self.assertEqual(field.extracted_value, "$50,000.00")
        self.assertEqual(field.verification_status, "EDITED")
        self.assertEqual(len(field.history), 1)
        self.assertEqual(field.history[0].old_value, "$55,000.00")

    def test_confidence_evaluator(self):
        evaluator = document_processor.confidence_evaluator
        self.assertEqual(evaluator.evaluate(0.95), "HIGH")
        self.assertEqual(evaluator.evaluate(0.75), "MEDIUM")
        self.assertEqual(evaluator.evaluate(0.50), "LOW")

if __name__ == "__main__":
    unittest.main()
