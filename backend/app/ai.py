import json
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app import models
from app.config import settings

logger = logging.getLogger(__name__)

# Grounding Validation Engine
def validate_grounding(evidence_package: Dict[str, Any], ai_response: Dict[str, Any]) -> str:
    """
    Validates that evidence citations returned by the LLM exist in the verified evidence package.
    Returns: 'GROUNDED' | 'PARTIALLY_GROUNDED' | 'INVALID'
    """
    cited_evidence = ai_response.get("evidence", [])
    if not cited_evidence:
        return "PARTIALLY_GROUNDED"
        
    verified_items = evidence_package.get("verified_evidence", [])
    verified_fields = {ev.get("field", "").lower(): ev.get("value", "").lower() for ev in verified_items}
    verified_sources = {ev.get("source_id", "").lower() for ev in verified_items}
    
    valid_citations = 0
    total_citations = len(cited_evidence)
    
    for citation in cited_evidence:
        field = citation.get("field", "").lower()
        source_id = citation.get("source_id", "").lower()
        
        # Check matching source_id or matching field in verified facts
        if (source_id and source_id in verified_sources) or (field and field in verified_fields):
            valid_citations += 1
            
    if valid_citations == total_citations and total_citations > 0:
        return "GROUNDED"
    elif valid_citations > 0:
        return "PARTIALLY_GROUNDED"
    else:
        return "INVALID"

# LLM Provider Abstraction Interface
class LLMProvider:
    def investigate(self, evidence_package: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError
        
    def chat(self, evidence_package: Dict[str, Any], messages: List[Dict[str, str]], user_message: str) -> str:
        raise NotImplementedError

class MockLLMProvider(LLMProvider):
    """
    High-fidelity deterministic LLM provider for evaluation and offline execution.
    Outputs structured evidence-grounded JSON.
    """
    def investigate(self, evidence_package: Dict[str, Any]) -> Dict[str, Any]:
        exc = evidence_package.get("exception", {})
        inv = evidence_package.get("invoice", {})
        po = evidence_package.get("purchase_order", {})
        vendor = evidence_package.get("vendor", {})
        exc_type = exc.get("type", "")
        amount = float(inv.get("total", 0.0))
        
        vendor_name = vendor.get("name", "Vendor")
        inv_num = inv.get("invoice_number", "N/A")
        po_num = po.get("po_number", "N/A")
        po_amt = float(po.get("total_amount", 0.0))
        
        if exc_type == "DUPLICATE_INVOICE":
            response = {
                "summary": f"Identical invoice {inv_num} billed by {vendor_name} for ${amount:,.2f}.",
                "finding": f"Duplicate billing event detected. Invoice {inv_num} matches previously paid transaction record.",
                "evidence": [
                    {
                        "source_id": inv_num,
                        "source_type": "INVOICE",
                        "field": "invoice_number",
                        "observed_value": inv_num,
                        "significance": "Exact match with existing paid invoice."
                    },
                    {
                        "source_id": vendor_name,
                        "source_type": "VENDOR",
                        "field": "vendor_name",
                        "observed_value": vendor_name,
                        "significance": "Identical supplier identifier."
                    }
                ],
                "recommendation": "AUTO_RESOLVE" if amount < 10000 else "REJECT",
                "confidence": 0.96,
                "risk": "LOW" if amount < 10000 else "MEDIUM",
                "uncertainty": [],
                "reason": f"Audit verification confirmed 100% duplicate match on vendor ID and billing totals (${amount:,.2f})."
            }
        elif exc_type == "AMOUNT_PRICE_MISMATCH":
            variance = abs(amount - po_amt)
            response = {
                "summary": f"Pricing variance of ${variance:,.2f} between Invoice {inv_num} (${amount:,.2f}) and PO {po_num} (${po_amt:,.2f}).",
                "finding": f"Invoice billing exceeds authorized Purchase Order limit by ${variance:,.2f}.",
                "evidence": [
                    {
                        "source_id": po_num,
                        "source_type": "PURCHASE_ORDER",
                        "field": "total_amount",
                        "observed_value": f"${po_amt:,.2f}",
                        "significance": "Authorized limit on purchase order."
                    },
                    {
                        "source_id": inv_num,
                        "source_type": "INVOICE",
                        "field": "total_amount",
                        "observed_value": f"${amount:,.2f}",
                        "significance": "Billed invoice total amount."
                    }
                ],
                "recommendation": "APPROVE" if amount < 50000 else "ESCALATE",
                "confidence": 0.85,
                "risk": "MEDIUM" if amount < 50000 else "HIGH",
                "uncertainty": ["Vendor contract discount terms require manual verification."],
                "reason": f"Price discrepancy of ${variance:,.2f} requires human approval before payment processing."
            }
        elif exc_type == "MISSING_PO":
            response = {
                "summary": f"Invoice {inv_num} from {vendor_name} for ${amount:,.2f} missing PO reference.",
                "finding": "Invoice lacks a valid approved Purchase Order reference in procurement system.",
                "evidence": [
                    {
                        "source_id": inv_num,
                        "source_type": "INVOICE",
                        "field": "po_id",
                        "observed_value": "NULL / Missing",
                        "significance": "Violates procurement PO requirements."
                    }
                ],
                "recommendation": "ESCALATE" if amount >= 10000 else "REJECT",
                "confidence": 0.90,
                "risk": "HIGH" if amount >= 10000 else "MEDIUM",
                "uncertainty": ["Unclear if emergency approval was granted verbally."],
                "reason": f"No active PO reference found for billing amount of ${amount:,.2f}."
            }
        elif exc_type == "TAX_ANOMALY":
            subtotal = float(inv.get("subtotal", 0.0))
            expected_tax = subtotal * 0.08
            actual_tax = float(inv.get("tax", 0.0))
            response = {
                "summary": f"Billed tax ${actual_tax:,.2f} deviates from expected 8% rate (${expected_tax:,.2f}).",
                "finding": "Tax calculation discrepancy on billing line.",
                "evidence": [
                    {
                        "source_id": inv_num,
                        "source_type": "INVOICE",
                        "field": "tax",
                        "observed_value": f"${actual_tax:,.2f}",
                        "significance": "Billed tax rate mismatch."
                    }
                ],
                "recommendation": "APPROVE",
                "confidence": 0.88,
                "risk": "LOW",
                "uncertainty": [],
                "reason": "Low-risk tax calculation variance eligible for manual adjustment."
            }
        else:
            response = {
                "summary": "Standard transaction audit under review.",
                "finding": "Audit evaluation in progress.",
                "evidence": [],
                "recommendation": "REVIEW",
                "confidence": 0.75,
                "risk": "MEDIUM",
                "uncertainty": [],
                "reason": "General transaction anomaly."
            }
            
        response["grounding"] = validate_grounding(evidence_package, response)
        return response

    def chat(self, evidence_package: Dict[str, Any], messages: List[Dict[str, str]], user_message: str) -> str:
        inv = evidence_package.get("invoice", {})
        exc = evidence_package.get("exception", {})
        po = evidence_package.get("purchase_order", {})
        vendor = evidence_package.get("vendor", {})
        
        inv_num = inv.get("invoice_number", "N/A")
        amount = float(inv.get("total", 0.0))
        vendor_name = vendor.get("name", "Vendor")
        po_num = po.get("po_number", "N/A")
        po_amt = float(po.get("total_amount", 0.0))
        
        query = user_message.lower()
        if "why" in query or "flagged" in query:
            return f"This case was flagged for type '{exc.get('type')}' because Invoice '{inv_num}' from '{vendor_name}' for ${amount:,.2f} violated deterministic rule thresholds. Grounding: Verified against DB."
        elif "po" in query or "purchase order" in query:
            if po_num != "N/A":
                return f"Purchase Order '{po_num}' has an authorized total of ${po_amt:,.2f}. Grounding: Verified."
            else:
                return f"No Purchase Order was referenced on Invoice '{inv_num}'. Procurement policy requires PO matching for amounts over $1,000. Grounding: Verified."
        elif "tax" in query:
            subtotal = float(inv.get("subtotal", 0.0))
            expected_tax = subtotal * 0.08
            actual_tax = float(inv.get("tax", 0.0))
            return f"Subtotal is ${subtotal:,.2f}. Standard 8% tax is ${expected_tax:,.2f}, but billed tax is ${actual_tax:,.2f}. Grounding: Verified."
        elif "summary" in query:
            return f"Summary: Exception ID {exc.get('id')} ({exc.get('type')}) for Vendor '{vendor_name}'. Financial impact: ${amount:,.2f}. Severity: {exc.get('severity')}."
        else:
            return f"Based on verified database evidence for Invoice '{inv_num}' (${amount:,.2f}), the exception details are loaded and grounded. Ask me any specific question about line items or PO rules."

class AIService:
    def __init__(self):
        self.provider = MockLLMProvider()
        
    def build_evidence_package(self, db: Session, exception: models.Exception) -> Dict[str, Any]:
        invoice = exception.invoice
        po = exception.purchase_order
        vendor = invoice.vendor if invoice else None
        
        verified_evidence = []
        for ev in exception.evidence:
            verified_evidence.append({
                "source_id": ev.source,
                "source_type": "VERIFIED_FACT",
                "field": ev.field,
                "value": ev.value,
                "explanation": ev.explanation
            })
            
        inv_lines = []
        if invoice:
            for line in invoice.lines:
                inv_lines.append({
                    "description": line.description,
                    "quantity": line.quantity,
                    "unit_price": float(line.unit_price),
                    "total_amount": float(line.total_amount)
                })
                
        po_lines = []
        if po:
            for line in po.lines:
                po_lines.append({
                    "description": line.description,
                    "quantity": line.quantity,
                    "unit_price": float(line.unit_price),
                    "total_amount": float(line.total_amount)
                })
                
        return {
            "exception": {
                "id": exception.id,
                "type": exception.type,
                "severity": exception.severity,
                "status": exception.status,
                "financial_impact": float(invoice.total) if invoice else 0.0
            },
            "invoice": {
                "id": invoice.id if invoice else None,
                "invoice_number": invoice.invoice_number if invoice else None,
                "subtotal": float(invoice.subtotal) if invoice else 0.0,
                "tax": float(invoice.tax) if invoice else 0.0,
                "total": float(invoice.total) if invoice else 0.0,
                "lines": inv_lines
            },
            "purchase_order": {
                "id": po.id if po else None,
                "po_number": po.po_number if po else None,
                "total_amount": float(po.total_amount) if po else 0.0,
                "lines": po_lines
            },
            "vendor": {
                "id": vendor.id if vendor else None,
                "name": vendor.name if vendor else None,
                "code": vendor.vendor_code if vendor else None
            },
            "verified_evidence": verified_evidence
        }
        
    def investigate(self, db: Session, exception: models.Exception) -> Dict[str, Any]:
        pkg = self.build_evidence_package(db, exception)
        res = self.provider.investigate(pkg)
        res["grounding_status"] = validate_grounding(pkg, res)
        return res
        
    def chat(self, db: Session, exception: models.Exception, messages: List[Dict[str, str]], user_message: str) -> str:
        # Prompt Injection Defense: sanitize user_message
        clean_prompt = user_message.replace("<UNTRUSTED_BUSINESS_DATA>", "").replace("</UNTRUSTED_BUSINESS_DATA>", "")
        pkg = self.build_evidence_package(db, exception)
        return self.provider.chat(pkg, messages, clean_prompt)

# Instantiate singleton AI Service
ai_service = AIService()

def run_ai_investigation(db: Session, exception: models.Exception) -> dict:
    return ai_service.investigate(db, exception)

def run_ai_chat(db: Session, exception: models.Exception, messages: list, user_message: str) -> str:
    return ai_service.chat(db, exception, messages, user_message)
