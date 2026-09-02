# REST API Reference

Base URL (Local): `http://127.0.0.1:8000/api`  
Base URL (Production): `https://supervity-exception-resolution-workbench-kpjg.onrender.com/api`  
Interactive Docs: `{BASE_URL}/docs` (Swagger UI)

All protected endpoints require: `Authorization: Bearer <JWT_TOKEN>`

---

## Authentication

### `POST /auth/login`
Login with email and password.

**Request Body:**
```json
{ "email": "reviewer@supervity-demo.com", "password": "supervity123" }
```

**Response:**
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "user": { "id": "...", "name": "Alex Audit", "role": "reviewer" }
}
```

---

## Dashboard

### `GET /dashboard/stats`
Returns aggregate counts for the dashboard summary cards.

**Response:**
```json
{
  "total_exceptions": 3,
  "open_exceptions": 2,
  "under_review": 1,
  "escalated": 1,
  "resolved": 0,
  "auto_resolved": 0,
  "high_risk_exceptions": 2,
  "ai_resolvable_exceptions": 1,
  "resolved_exceptions": 0
}
```

---

## Exceptions

### `GET /exceptions`
Paginated exception list with filtering and sorting.

**Query Params:** `page`, `page_size`, `status`, `severity`, `sort_by`, `sort_order`

### `GET /exceptions/{id}`
Full exception detail including evidence, investigations, policy decisions, resolutions, and audit events.

---

## Investigation

### `POST /exceptions/{id}/investigate`
Trigger AI investigation for an exception.

**Response:**
```json
{
  "id": "...",
  "finding": "Invoice INV-2026-001 is a confirmed duplicate...",
  "recommendation": "AUTO_RESOLVE",
  "confidence": 0.97,
  "risk": "HIGH",
  "grounding": "GROUNDED"
}
```

### `POST /exceptions/{id}/resolve`
Resolve an exception (Reviewer action).

**Request Body:** `{ "action": "RESOLVE", "comments": "Approved after verification" }`

### `POST /exceptions/{id}/reject`
Reject an exception.

**Request Body:** `{ "action": "REJECT", "comments": "Duplicate invoice confirmed" }`

### `POST /exceptions/{id}/escalate`
Escalate to manager queue.

**Request Body:** `{ "action": "ESCALATE", "comments": "Requires manager approval" }`

### `POST /exceptions/{id}/false-positive`
Mark as incorrectly flagged.

**Request Body:** `{ "action": "FALSE_POSITIVE", "comments": "Rate change was approved" }`

### `POST /exceptions/{id}/auto-resolve`
System-triggered auto-resolution based on policy engine decision.

---

## Policies

### `GET /policies`
List all active policies.

### `POST /policies/{id}/evaluate`
Evaluate a policy decision for a specific exception.

**Request Body:** `{ "exception_id": "...", "investigation_id": "..." }`

**Response:**
```json
{
  "decision": "HUMAN_REVIEW",
  "policy_name": "Standard Exception Policy",
  "ai_confidence": 0.82,
  "risk_level": "MEDIUM",
  "financial_impact": 55000.0,
  "reasons": ["AI confidence below auto-resolve threshold", "Financial impact exceeds medium-risk limit"]
}
```

---

## Documents

### `POST /documents/upload`
Upload an invoice document for OCR processing.

**Content-Type:** `multipart/form-data`  
**Fields:** `file` (binary), `document_type` (string: "invoice" | "purchase_order")

### `GET /documents`
List all uploaded documents with processing status.

### `GET /documents/{id}`
Get document detail with all extracted fields and confidence scores.

### `POST /documents/{id}/fields/{field_id}/verify`
Mark an extracted field as verified.

### `POST /documents/{id}/fields/{field_id}/edit`
Edit an extracted field value.

**Request Body:** `{ "new_value": "4536.00", "reason": "Corrected from OCR misread" }`

---

## Audit

### `GET /audit`
Global audit log (all events across all exceptions).

**Query Params:** `limit`, `offset`

### `GET /exceptions/{id}/audit`
Exception-specific audit trail.
