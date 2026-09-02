# System Architecture

## Overview

The Supervity Exception Resolution Workbench is a full-stack AI-assisted financial exception management system. It ingests invoices, detects anomalies using deterministic rules, enriches findings with AI investigation, applies configurable policy engines, and routes cases to human reviewers or auto-resolves them.

---

## End-to-End Data Flow

```
┌──────────────────────────────────────────────────────────────────────────┐
│                          FRONTEND (Vercel)                                │
│   React 19 + Vite + TypeScript + TailwindCSS + Lucide Icons              │
│                                                                            │
│  ┌──────────┐  ┌──────────────┐  ┌───────────────┐  ┌────────────────┐  │
│  │ Dashboard│  │  Workspace   │  │   Documents   │  │  Audit / Policy│  │
│  │ (Queue)  │  │ (Case View)  │  │  (Workbench)  │  │    Views       │  │
│  └──────────┘  └──────────────┘  └───────────────┘  └────────────────┘  │
│                        │  JWT Bearer Auth                                  │
└────────────────────────┼─────────────────────────────────────────────────┘
                         │ HTTPS / REST JSON
┌────────────────────────▼─────────────────────────────────────────────────┐
│                         BACKEND (Render)                                  │
│                FastAPI + Uvicorn + SQLAlchemy + Python 3.10               │
│                                                                            │
│   ┌──────────────────────────────────────────────────────────────┐        │
│   │                      API Routes Layer                        │        │
│   │  /auth  /dashboard  /exceptions  /investigation  /policies   │        │
│   │  /documents  /audit  /verify                                 │        │
│   └─────────────────────────┬────────────────────────────────────┘        │
│                             │                                              │
│   ┌──────────────┐  ┌───────▼────────┐  ┌──────────────────────┐         │
│   │ PolicyEngine │  │  AIService     │  │  DocumentProcessor   │         │
│   │ (engine.py)  │  │  (ai.py)       │  │  (document_processor)│         │
│   │              │  │                │  │                      │         │
│   │ • Anomaly    │  │ • Evidence     │  │ • Text extraction    │         │
│   │   detection  │  │   packaging    │  │ • Field parsing      │         │
│   │ • Risk assess│  │ • LLM routing  │  │ • Confidence scoring │         │
│   │ • Auto/Manual│  │ • Grounding    │  │ • OCR normalization  │         │
│   │   routing    │  │   validation   │  │                      │         │
│   └──────────────┘  └───────┬────────┘  └──────────────────────┘         │
│                             │                                              │
│   ┌─────────────────────────▼────────────────────────────────────┐        │
│   │              LLM Provider Interface                           │        │
│   │  ┌──────────────────┐    ┌────────────────┐                  │        │
│   │  │  MockLLMProvider │    │ OpenAI/Gemini  │                  │        │
│   │  │  (default/offline│    │ (via env vars) │                  │        │
│   │  │   deterministic) │    │                │                  │        │
│   │  └──────────────────┘    └────────────────┘                  │        │
│   └──────────────────────────────────────────────────────────────┘        │
│                                                                            │
│   ┌──────────────────────────────────────────────────────────────┐        │
│   │                 Data Layer (SQLAlchemy ORM)                   │        │
│   │    SQLite (local/Render free)  or  PostgreSQL (production)   │        │
│   └──────────────────────────────────────────────────────────────┘        │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Exception Lifecycle

```
Invoice Uploaded / Seeded
         │
         ▼
┌─────────────────────┐
│  Exception Detector │  ← Deterministic rules engine
│  (engine.py)        │    Checks: duplicate invoice numbers,
│                     │    amount vs PO mismatch, missing PO ref,
│                     │    tax anomalies                          
└──────────┬──────────┘
           │  Exception created → status: OPEN
           ▼
┌─────────────────────┐
│   AI Investigation  │  ← AIService.investigate()
│   (ai.py)           │    Builds evidence package from DB
│                     │    Sends to MockLLM / OpenAI / Gemini
│                     │    Returns: finding, recommendation,
│                     │    confidence, risk, grounding score
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   Policy Engine     │  ← PolicyEngine.evaluate()
│   (engine.py)       │    Applies configurable thresholds:
│                     │    confidence_min, amount_threshold,
│                     │    risk_level rules
│                     │    Returns: AUTO_RESOLVE / HUMAN_REVIEW
│                     │            / ESCALATE
└──────────┬──────────┘
           │
    ┌──────┴──────────┐
    ▼                 ▼
AUTO_RESOLVE      HUMAN_REVIEW / ESCALATE
    │                 │
    │                 ▼
    │         ┌───────────────┐
    │         │ Reviewer Queue│  Reviewer: Resolve / Reject /
    │         │ (Dashboard)   │            False-Positive
    │         └───────┬───────┘  Manager:  Approve Escalation
    │                 │
    └────────┬────────┘
             ▼
    ┌─────────────────┐
    │  Audit Ledger   │  ← Permanent immutable log of all
    │  (AuditEvent)   │    actions, status changes, policy
    └─────────────────┘    decisions, AI responses
```

---

## Database Schema (Simplified)

```
Organization
    └── User (reviewer | manager)
    └── Policy (rules + thresholds)

Vendor
    └── PurchaseOrder
            └── PurchaseOrderLine
    └── Invoice
            └── InvoiceLine
            └── Exception
                    ├── Evidence[]
                    ├── Investigation[]
                    ├── PolicyDecision[]
                    ├── Resolution[]
                    └── AuditEvent[]

Document
    └── DocumentField[]
            └── DocumentFieldHistory[]
```

---

## Key System Guardrails

| Guardrail | Description |
|---|---|
| **Grounding Validation** | AI responses verified against evidence package before accepted |
| **Duplicate Resolution Block** | Closed exceptions cannot be re-resolved (race condition prevention) |
| **Escalation Lock** | HIGH risk exceptions cannot be auto-resolved — require manager approval |
| **Immutable Audit Trail** | Every action appended to audit ledger, never deleted or modified |
