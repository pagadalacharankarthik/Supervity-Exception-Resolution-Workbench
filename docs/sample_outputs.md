# Sample System Outputs

This document shows real representative outputs produced by the Supervity Exception Resolution Workbench across all three core exception types.

---

## Case 1 — Duplicate Invoice (AUTO_RESOLVE)

### Exception Detected
```json
{
  "id": "exc-001",
  "type": "DUPLICATE_INVOICE",
  "severity": "HIGH",
  "status": "OPEN",
  "amount": 4536.00,
  "vendor_name": "Apex Industrial Supplies",
  "invoice_number": "INV-2026-001"
}
```

### AI Investigation Output
```json
{
  "finding": "Invoice INV-2026-001 from Apex Industrial Supplies for $4,536.00 is a confirmed duplicate of an existing paid invoice. The invoice number, vendor, amount, and line items are identical. This is a high-confidence duplicate that poses a direct double-payment risk.",
  "recommendation": "AUTO_RESOLVE",
  "confidence": 0.97,
  "risk": "HIGH",
  "reason": "Exact match on invoice number INV-2026-001, vendor ID VND-APEX, total amount $4536.00. Prior invoice already closed and paid. No legitimate business reason for resubmission detected.",
  "grounding": "GROUNDED"
}
```

### Policy Engine Decision
```json
{
  "decision": "AUTO_RESOLVE",
  "policy_name": "Standard Exception Policy",
  "ai_confidence": 0.97,
  "risk_level": "HIGH",
  "financial_impact": 4536.00,
  "reasons": [
    "AI confidence (0.97) exceeds auto-resolve threshold (0.90)",
    "Exception type DUPLICATE_INVOICE qualifies for automatic rejection",
    "Grounding status GROUNDED — AI evidence verified against database facts"
  ]
}
```

### Final Status
`RESOLVED` — Automatically declined by system within seconds of detection.

---

## Case 2 — Price Mismatch (HUMAN_REVIEW)

### Exception Detected
```json
{
  "id": "exc-002",
  "type": "AMOUNT_PRICE_MISMATCH",
  "severity": "HIGH",
  "status": "UNDER_REVIEW",
  "amount": 55000.00,
  "vendor_name": "Vertex Cloud Solutions",
  "invoice_number": "INV-2026-VC-001"
}
```

### AI Investigation Output
```json
{
  "finding": "Invoice INV-2026-VC-001 from Vertex Cloud Solutions claims $55,000.00 for 500 Cloud Infrastructure Compute Units at $110.00/unit. The associated Purchase Order PO-2026-002 authorized a rate of $95.00/unit for the same compute units. This represents a 15.8% unit price deviation totalling $7,500.00 in excess charges.",
  "recommendation": "HUMAN_REVIEW",
  "confidence": 0.82,
  "risk": "MEDIUM",
  "reason": "Price deviation of 15.8% exceeds the 10% tolerance threshold in PO-2026-002. However, vendor Vertex Cloud Solutions has a clean payment history (0 prior disputes in 24 months). Possible causes: rate card update, contract amendment, or billing error. Recommend human verification before rejection.",
  "grounding": "GROUNDED"
}
```

### Policy Engine Decision
```json
{
  "decision": "HUMAN_REVIEW",
  "reasons": [
    "AI confidence (0.82) below auto-resolve threshold (0.90)",
    "Financial impact $55,000.00 exceeds medium-risk threshold $10,000.00",
    "Recommendation is HUMAN_REVIEW — manual override required"
  ]
}
```

### Reviewer Action (Sample)
```json
{
  "action": "RESOLVE",
  "comments": "Confirmed with vendor — rate card updated per Q3 contract amendment. Approved for payment.",
  "actor_name": "Alex Audit",
  "new_status": "RESOLVED"
}
```

---

## Case 3 — Missing PO (ESCALATE)

### Exception Detected
```json
{
  "id": "exc-003",
  "type": "MISSING_PO",
  "severity": "CRITICAL",
  "status": "ESCALATED",
  "amount": 70200.00,
  "vendor_name": "Global Logistics Partners"
}
```

### AI Investigation Output
```json
{
  "finding": "Invoice from Global Logistics Partners for $70,200.00 (Annual Security Auditing Services) has no associated Purchase Order reference. No PO record exists in the system for this vendor and service category. A $70,200.00 payment without PO authorization violates the organization's procurement policy and exposes the company to fraud risk.",
  "recommendation": "ESCALATE",
  "confidence": 0.91,
  "risk": "HIGH",
  "reason": "Missing PO for invoice above $50,000 threshold triggers mandatory escalation per procurement policy. No prior relationship with Global Logistics Partners for this service type found in transaction history.",
  "grounding": "GROUNDED"
}
```

### Policy Engine Decision
```json
{
  "decision": "ESCALATE",
  "reasons": [
    "Exception type MISSING_PO with financial impact $70,200.00 exceeds high-risk threshold $50,000.00",
    "HIGH risk level requires manager approval",
    "AI recommendation is ESCALATE — automatic routing to manager queue"
  ]
}
```

### Manager Action (Sample)
```json
{
  "action": "REJECT",
  "comments": "No PO authorized for this vendor. Invoice rejected. Procurement to investigate vendor relationship.",
  "actor_name": "Sarah Manager",
  "new_status": "REJECTED"
}
```

---

## Audit Trail Sample

```json
[
  {
    "event": "EXCEPTION_CREATED",
    "actor_name": "System",
    "new_status": "OPEN",
    "reason": "MISSING_PO detected for invoice INV-2026-GL-001",
    "timestamp": "2026-08-22T10:00:00Z"
  },
  {
    "event": "AI_INVESTIGATION_COMPLETED",
    "actor_name": "System (MockLLM)",
    "reason": "Confidence: 0.91 | Risk: HIGH | Recommendation: ESCALATE",
    "timestamp": "2026-08-22T10:00:02Z"
  },
  {
    "event": "POLICY_EVALUATED",
    "actor_name": "System (PolicyEngine)",
    "new_status": "ESCALATED",
    "reason": "AUTO-ESCALATED: HIGH risk + MISSING_PO + amount > $50,000",
    "timestamp": "2026-08-22T10:00:02Z"
  },
  {
    "event": "EXCEPTION_REJECTED",
    "actor_name": "Sarah Manager",
    "previous_status": "ESCALATED",
    "new_status": "REJECTED",
    "reason": "No PO authorized for this vendor. Invoice rejected.",
    "timestamp": "2026-08-22T11:45:00Z"
  }
]
```
