from decimal import Decimal
from typing import List, Tuple, Optional, Dict, Any
from sqlalchemy.orm import Session
from app import models
from app.config import settings

# Severity configuration thresholds (in USD/monetary value)
SEVERITY_LOW_LIMIT = Decimal("1000.00")
SEVERITY_MEDIUM_LIMIT = Decimal("10000.00")

class BaseDetector:
    """
    Abstract interface for all exception detectors.
    """
    def detect(self, db: Session, invoice: models.Invoice) -> List[Tuple[models.Exception, List[models.Evidence]]]:
        raise NotImplementedError

class DuplicateInvoiceDetector(BaseDetector):
    """
    Detects potential duplicate invoices.
    """
    def detect(self, db: Session, invoice: models.Invoice) -> List[Tuple[models.Exception, List[models.Evidence]]]:
        exceptions = []
        
        # Check duplicate by vendor and invoice number
        duplicates = db.query(models.Invoice).filter(
            models.Invoice.id != invoice.id,
            models.Invoice.vendor_id == invoice.vendor_id,
            models.Invoice.invoice_number == invoice.invoice_number
        ).all()
        
        if duplicates:
            # Determine severity based on total amount
            severity = "LOW"
            if invoice.total >= SEVERITY_MEDIUM_LIMIT:
                severity = "HIGH"
            elif invoice.total >= SEVERITY_LOW_LIMIT:
                severity = "MEDIUM"
                
            exc = models.Exception(
                type="DUPLICATE_INVOICE",
                status="OPEN",
                severity=severity,
                confidence=0.95,
                risk=severity,
                invoice_id=invoice.id,
                po_id=invoice.po_id
            )
            
            evidences = [
                models.Evidence(
                    source="Invoice Database",
                    field="invoice_number",
                    value=invoice.invoice_number,
                    explanation=f"Invoice number '{invoice.invoice_number}' already exists in database from the same vendor.",
                    fact_type="VERIFIED_FACT"
                ),
                models.Evidence(
                    source="Invoice Database",
                    field="vendor_id",
                    value=invoice.vendor_id,
                    explanation=f"Duplicate invoice matching vendor ID '{invoice.vendor_id}' was detected.",
                    fact_type="VERIFIED_FACT"
                ),
                models.Evidence(
                    source="Invoice Database",
                    field="total",
                    value=f"{invoice.total}",
                    explanation=f"Duplicate invoice has total amount of ${invoice.total:.2f}.",
                    fact_type="VERIFIED_FACT"
                )
            ]
            exceptions.append((exc, evidences))
            invoice.status = "exception"
            
        return exceptions

class AmountPriceMismatchDetector(BaseDetector):
    """
    Compares invoice totals and line items against the referenced purchase order.
    """
    def detect(self, db: Session, invoice: models.Invoice) -> List[Tuple[models.Exception, List[models.Evidence]]]:
        exceptions = []
        if not invoice.po_id:
            return exceptions
            
        po = db.query(models.PurchaseOrder).filter(models.PurchaseOrder.id == invoice.po_id).first()
        if not po:
            return exceptions
            
        mismatch_found = False
        evidences = []
        
        # 1. Total amount mismatch (tolerance of $0.05)
        diff = invoice.total - po.total_amount
        if abs(diff) > Decimal("0.05"):
            mismatch_found = True
            po_total_float = float(po.total_amount)
            pct = (abs(diff) / po.total_amount * 100) if po_total_float > 0.0 else Decimal("0.00")
            
            evidences.append(models.Evidence(
                source="PURCHASE_ORDER",
                field="total_amount",
                value=f"{po.total_amount}",
                explanation=f"Purchase order total is ${po.total_amount:.2f}.",
                fact_type="VERIFIED_FACT"
            ))
            evidences.append(models.Evidence(
                source="INVOICE",
                field="total",
                value=f"{invoice.total}",
                explanation=f"Invoice total is ${invoice.total:.2f}, creating a difference of ${diff:.2f} ({pct:.1f}% deviation).",
                fact_type="VERIFIED_FACT"
            ))
            
        # 2. Line items price and quantity checks
        po_lines = {line.description.lower(): line for line in po.lines}
        for inv_line in invoice.lines:
            desc = inv_line.description.lower()
            if desc in po_lines:
                po_line = po_lines[desc]
                
                # Unit price mismatch
                if abs(inv_line.unit_price - po_line.unit_price) > Decimal("0.01"):
                    mismatch_found = True
                    evidences.append(models.Evidence(
                        source="INVOICE_LINE",
                        field="unit_price",
                        value=f"{inv_line.unit_price}",
                        explanation=f"Billed unit price of ${inv_line.unit_price:.2f} for item '{inv_line.description}' exceeds PO authorized price of ${po_line.unit_price:.2f}.",
                        fact_type="VERIFIED_FACT"
                    ))
                    
                # Quantity mismatch
                if inv_line.quantity > po_line.quantity:
                    mismatch_found = True
                    evidences.append(models.Evidence(
                        source="INVOICE_LINE",
                        field="quantity",
                        value=f"{inv_line.quantity}",
                        explanation=f"Billed quantity ({inv_line.quantity}) for item '{inv_line.description}' exceeds PO authorized quantity ({po_line.quantity}).",
                        fact_type="VERIFIED_FACT"
                    ))
            else:
                # Billed item not on PO
                mismatch_found = True
                evidences.append(models.Evidence(
                    source="INVOICE_LINE",
                    field="description",
                    value=inv_line.description,
                    explanation=f"Line item '{inv_line.description}' on invoice is not found in the original PO.",
                    fact_type="VERIFIED_FACT"
                ))
                
        if mismatch_found:
            # Determine severity based on total discrepancy
            severity = "LOW"
            discrepancy = abs(invoice.total - po.total_amount)
            if discrepancy >= SEVERITY_MEDIUM_LIMIT:
                severity = "HIGH"
            elif discrepancy >= SEVERITY_LOW_LIMIT:
                severity = "MEDIUM"
                
            exc = models.Exception(
                type="AMOUNT_PRICE_MISMATCH",
                status="OPEN",
                severity=severity,
                confidence=0.85,
                risk=severity,
                invoice_id=invoice.id,
                po_id=invoice.po_id
            )
            exceptions.append((exc, evidences))
            invoice.status = "exception"
            
        return exceptions

class MissingPurchaseOrderDetector(BaseDetector):
    """
    Detects invoices missing a valid purchase order.
    """
    def detect(self, db: Session, invoice: models.Invoice) -> List[Tuple[models.Exception, List[models.Evidence]]]:
        exceptions = []
        po_missing = False
        explanation = ""
        
        if not invoice.po_id:
            po_missing = True
            explanation = "Invoice has no associated purchase order."
        else:
            po = db.query(models.PurchaseOrder).filter(models.PurchaseOrder.id == invoice.po_id).first()
            if not po:
                po_missing = True
                explanation = f"Invoice references purchase order ID '{invoice.po_id}' which does not exist in database."
                
        if po_missing:
            # Invoices missing PO are high risk/severity if large, otherwise medium
            severity = "HIGH" if invoice.total >= SEVERITY_LOW_LIMIT else "MEDIUM"
            
            exc = models.Exception(
                type="MISSING_PO",
                status="OPEN",
                severity=severity,
                confidence=1.0,
                risk=severity,
                invoice_id=invoice.id,
                po_id=invoice.po_id
            )
            
            evidences = [
                models.Evidence(
                    source="INVOICE",
                    field="po_id",
                    value=f"{invoice.po_id}",
                    explanation=explanation,
                    fact_type="VERIFIED_FACT"
                )
            ]
            exceptions.append((exc, evidences))
            invoice.status = "exception"
            
        return exceptions

class TaxAnomalyDetector(BaseDetector):
    """
    Detects incorrect subtotal + tax = total math, rate discrepancies, or missing tax rate values.
    """
    def detect(self, db: Session, invoice: models.Invoice) -> List[Tuple[models.Exception, List[models.Evidence]]]:
        exceptions = []
        tax_anomaly_found = False
        evidences = []
        
        # 1. Check if total equals subtotal + tax
        calculated_total = invoice.subtotal + invoice.tax
        if abs(invoice.total - calculated_total) > Decimal("0.02"):
            tax_anomaly_found = True
            evidences.append(models.Evidence(
                source="INVOICE",
                field="total",
                value=f"{invoice.total}",
                explanation=f"Invoice total (${invoice.total:.2f}) does not match subtotal (${invoice.subtotal:.2f}) + tax (${invoice.tax:.2f}) which equals ${calculated_total:.2f}.",
                fact_type="VERIFIED_FACT"
            ))
            
        # 2. Check if tax matches standard 8% rate of subtotal
        expected_tax = invoice.subtotal * Decimal("0.08")
        if abs(invoice.tax - expected_tax) > Decimal("1.00"):
            tax_anomaly_found = True
            actual_rate = (invoice.tax / invoice.subtotal * 100) if invoice.subtotal > 0 else Decimal("0.00")
            evidences.append(models.Evidence(
                source="Tax Registry Rule",
                field="Expected Tax Rate",
                value="8.0%",
                explanation=f"Billed tax (${invoice.tax:.2f}, approx {actual_rate:.1f}%) deviates from regional tax rules (8.0% expected: ${expected_tax:.2f}).",
                fact_type="VERIFIED_FACT"
            ))
            
        if tax_anomaly_found:
            # Tax anomalies are generally low severity unless discrepancy is large
            severity = "LOW"
            tax_diff = abs(invoice.tax - expected_tax)
            if tax_diff >= SEVERITY_MEDIUM_LIMIT:
                severity = "HIGH"
            elif tax_diff >= SEVERITY_LOW_LIMIT:
                severity = "MEDIUM"
                
            exc = models.Exception(
                type="TAX_ANOMALY",
                status="OPEN",
                severity=severity,
                confidence=0.90,
                risk=severity,
                invoice_id=invoice.id,
                po_id=invoice.po_id
            )
            exceptions.append((exc, evidences))
            invoice.status = "exception"
            
        return exceptions

class ExceptionDetectionEngine:
    """
    Orchestrates the running of exception detectors against transaction records.
    """
    def __init__(self):
        self.detectors = [
            DuplicateInvoiceDetector(),
            AmountPriceMismatchDetector(),
            MissingPurchaseOrderDetector(),
            TaxAnomalyDetector()
        ]
        
    def run(self, db: Session, invoice: models.Invoice) -> List[Tuple[models.Exception, List[models.Evidence]]]:
        all_exceptions = []
        for detector in self.detectors:
            try:
                results = detector.detect(db, invoice)
                all_exceptions.extend(results)
            except Exception as e:
                # Log engine detector issues to prevent entire run failure
                print(f"Error executing detector {detector.__class__.__name__}: {e}")
        return all_exceptions


class RiskAssessment:
    """
    Evaluates risk deterministically based on financial impact, evidence completeness, and exception types.
    """
    def evaluate(self, db: Session, exception: models.Exception) -> Dict[str, Any]:
        amount = Decimal("0.00")
        if exception.invoice:
            amount = exception.invoice.total
            
        evidence_complete = len(exception.evidence) > 0
        missing_po = (exception.type == "MISSING_PO") or (not exception.po_id)
        
        risk = "LOW"
        reasons = []
        
        HIGH_RISK_AMOUNT_LIMIT = Decimal("50000.00")
        MEDIUM_RISK_AMOUNT_LIMIT = Decimal("10000.00")
        
        if amount >= HIGH_RISK_AMOUNT_LIMIT or missing_po:
            risk = "HIGH"
            if missing_po:
                reasons.append("Missing Purchase Order reference increases compliance risk.")
            if amount >= HIGH_RISK_AMOUNT_LIMIT:
                reasons.append(f"Financial impact (${amount:.2f}) exceeds high-risk threshold (${HIGH_RISK_AMOUNT_LIMIT:.2f}).")
        elif amount >= MEDIUM_RISK_AMOUNT_LIMIT:
            risk = "MEDIUM"
            reasons.append(f"Financial impact (${amount:.2f}) is in medium threshold range.")
        else:
            risk = "LOW"
            reasons.append("Financial impact is under low-risk threshold.")
            
        return {
            "risk": risk,
            "financial_impact": amount,
            "evidence_complete": evidence_complete,
            "missing_po": missing_po,
            "reasons": reasons
        }

class PolicyEngine:
    """
    Evaluates policy decisions deterministically against DB policies and initial seeded rules.
    Outputs: AUTO_RESOLVE | HUMAN_REVIEW | ESCALATE
    """
    def evaluate(self, db: Session, exception: models.Exception, investigation: Optional[models.Investigation] = None) -> Dict[str, Any]:
        risk_service = RiskAssessment()
        risk_eval = risk_service.evaluate(db, exception)
        
        financial_impact = risk_eval["financial_impact"]
        risk = risk_eval["risk"]
        evidence_complete = risk_eval["evidence_complete"]
        
        ai_confidence = investigation.confidence if investigation else exception.confidence
        
        # Priority Order Evaluation
        
        # Rule 1: Escalation (Critical safety, missing evidence, high risk, or low confidence)
        cond_evidence = {"condition": "Evidence Complete", "actual_value": evidence_complete, "passed": evidence_complete}
        cond_high_risk = {"condition": "Risk != HIGH", "actual_value": risk, "passed": risk != "HIGH"}
        cond_conf_min = {"condition": "AI Confidence >= 0.70", "actual_value": round(ai_confidence, 2), "passed": ai_confidence >= 0.70}
        
        if not evidence_complete or risk == "HIGH" or ai_confidence < 0.70:
            decision = "ESCALATE"
            policy_name = "High Risk Escalation Policy v1"
            policy_version = 1
            reasons = []
            
            if not evidence_complete:
                reasons.append("Evidence incomplete: Critical facts are missing.")
            if risk == "HIGH":
                reasons.append(f"High risk override: Calculated risk level is '{risk}'.")
            if ai_confidence < 0.70:
                reasons.append(f"AI Assessment Confidence ({ai_confidence:.2f}) is below the minimum threshold (0.70).")
                
            evaluated_conditions = [cond_evidence, cond_high_risk, cond_conf_min]
            
            return {
                "decision": decision,
                "policy_name": policy_name,
                "policy_version": policy_version,
                "ai_confidence": ai_confidence,
                "risk": risk,
                "financial_impact": financial_impact,
                "evidence_complete": evidence_complete,
                "evaluated_conditions": evaluated_conditions,
                "reasons": reasons
            }
            
        # Rule 2: Auto Resolution (Low risk, confidence >= 0.90, impact <= $10,000)
        cond_auto_conf = {"condition": "AI Confidence >= 0.90", "actual_value": round(ai_confidence, 2), "passed": ai_confidence >= 0.90}
        cond_auto_risk = {"condition": "Risk == LOW", "actual_value": risk, "passed": risk == "LOW"}
        cond_auto_amt = {"condition": "Financial Impact <= $10,000", "actual_value": float(financial_impact), "passed": financial_impact <= Decimal("10000.00")}
        
        evaluated_conditions = [cond_evidence, cond_auto_risk, cond_auto_conf, cond_auto_amt]
        
        if ai_confidence >= 0.90 and risk == "LOW" and financial_impact <= Decimal("10000.00"):
            return {
                "decision": "AUTO_RESOLVE",
                "policy_name": "Low-Risk Auto Resolution Policy v1",
                "policy_version": 1,
                "ai_confidence": ai_confidence,
                "risk": risk,
                "financial_impact": financial_impact,
                "evidence_complete": evidence_complete,
                "evaluated_conditions": evaluated_conditions,
                "reasons": ["All low-risk auto-resolution conditions passed."]
            }
            
        # Rule 3: Human Review (Default fallback for moderate risk or confidence between 0.70 and 0.90)
        reasons = []
        if ai_confidence < 0.90:
            reasons.append(f"AI Assessment Confidence ({ai_confidence:.2f}) is below the 0.90 auto-resolution threshold.")
        if risk != "LOW":
            reasons.append(f"Risk classification is '{risk}', requiring human reviewer verification.")
        if financial_impact > Decimal("10000.00"):
            reasons.append(f"Financial impact (${financial_impact:.2f}) exceeds the $10,000 auto-resolution threshold.")
            
        return {
            "decision": "HUMAN_REVIEW",
            "policy_name": "Standard Human Review Policy v1",
            "policy_version": 1,
            "ai_confidence": ai_confidence,
            "risk": risk,
            "financial_impact": financial_impact,
            "evidence_complete": evidence_complete,
            "evaluated_conditions": evaluated_conditions,
            "reasons": reasons
        }

def evaluate_policy_rules(db: Session, exception: models.Exception, confidence: float, risk: str, missing_critical_evidence: bool = False) -> str:
    engine = PolicyEngine()
    eval_res = engine.evaluate(db, exception)
    return eval_res["decision"]

