# 🛡️ Supervity Exception Resolution Workbench
### *Evidence-Driven AI Exception Resolution & Document Verification for AP Transactions*

The **Supervity Exception Resolution Workbench** is a professional enterprise application for auditing accounts payable anomalies. It integrates deterministic transaction rules, optical text extraction/OCR parsing, and evidence-grounded AI analysis to streamline human reviewer decisions while enforcing strict compliance bounds.

---

## 🏛️ System Architecture & Guardrails

The workbench is built on a hybrid architecture designed for enterprise safety. It enforces four primary architectural guardrails:

```mermaid
flowchart TD
    subgraph Ingestion["1. Document Ingestion"]
        doc[Raw Invoice PDF/Image] --> ocr[OCR Text Extraction]
        ocr --> fields[Extracted Fields & Confidence]
        fields --> verify[Reviewer Verification & Edits]
    end

    subgraph Detection["2. Deterministic Detection"]
        verify --> db[(Verified Database Facts)]
        po[(Contract POs / Ledgers)] --> eng[Python Rule Engine]
        db --> eng
        eng --> exc[Exception Triggered]
    end

    subgraph Advisory["3. Grounded AI Investigation"]
        exc --> pkg[Verified Evidence Fact Package]
        pkg --> llm[AI Analyst - Read-Only LLM]
        llm --> report[Advisory Report: Confidence, Risk & Recommendation]
    end

    subgraph Compliance["4. Decoupled Policy Routing"]
        report --> policy[Database Policy Threshold Rules]
        policy --> route{Policy Decision}
        route -->|Low Risk / High Conf| auto[AUTO_RESOLVE]
        route -->|Medium Risk| review[HUMAN_REVIEW]
        route -->|High Risk / Missing PO| esc[ESCALATE]
    end

    subgraph Resolution["5. Human-in-the-Loop & Audit"]
        auto --> resolve[Resolution Executed]
        review -->|Reviewer Comments| resolve
        esc -->|Manager Approval/Decline| resolve
        resolve --> ledger[(Immutable Audit Ledger)]
    end
```

1. **Deterministic Rule Engine**: All financial calculations, invoice matching, tax checks, and duplicate scans are executed in pure, strict Python backend logic. The AI is *never* used for mathematical operations or threshold checks, eliminating calculation hallucination risks.
2. **Evidence-Grounded AI Analysis**: AI investigations must only proceed on verified facts from database records or verified document fields. The AI provides advisory recommendations and structured reasoning, but is *never* permitted to directly perform mutations or close exceptions on its own.
3. **Decoupled Compliance Policy Layer**: Business policies live in the database as configurable rules (e.g., risk thresholds, confidence limits). The system evaluates AI suggestions against these rules to classify cases into `AUTO_RESOLVE`, `HUMAN_REVIEW`, or `ESCALATE` transitions.
4. **Human-in-the-Loop & Audit Ledger**: Reviewers retain override capabilities. Manager-level sign-offs are enforced for high-value or missing PO escalations. A permanent, immutable ledger records all automated engine decisions and manual reviewer actions.

---

## 🛠️ Technology Stack & Rationale

Our technical choices were driven by the requirements of high-performance financial systems:

*   **Frontend**: Built with **React, Vite, and TypeScript**. React provides a component-driven, responsive UI for fast-paced reviewers, Vite ensures sub-second Hot Module Replacement (HMR) for developer efficiency, and TypeScript guarantees static type safety across our API boundaries.
*   **Backend**: Built with **FastAPI** in Python. FastAPI provides rapid, asynchronous endpoints, auto-documents our API contracts, and allows us to run standard numeric parsing and data calculations in Python.
*   **Database**: Uses **PostgreSQL** with **SQLAlchemy ORM** to enforce strict foreign key constraints and transactional integrity on financial records, with a seamless SQLite fallback (`app.db`) for local developer environments.

```mermaid
graph TD
    subgraph UI["Client Presentation (Frontend)"]
        react[React 18 Component Tree]
        vite[Vite Dev Server]
        ts[TypeScript Typings]
        tailwind[Tailwind CSS Theme]
        react --- ts
        react --- tailwind
        vite --- react
    end

    subgraph Service["Application Core (Backend)"]
        fastapi[FastAPI Routers & Schemas]
        uvicorn[Uvicorn ASGI Server]
        rules[Python Rule Engine]
        ai[AI Advisor Interface]
        fastapi --- rules
        fastapi --- ai
        uvicorn --- fastapi
    end

    subgraph Data["Persistence & Storage (Database)"]
        orm[SQLAlchemy ORM]
        pg[(PostgreSQL Production DB)]
        sqlite[(SQLite Local Fallback app.db)]
        orm --> pg
        orm --> sqlite
    end

    UI -->|JSON HTTPS / JWT Auth| Service
    Service -->|SQL Sessions| Data
```

---

## 📂 Project Structure

- **`/backend`**: FastAPI application with SQLAlchemy ORM (defaulting to SQLite `app.db` fallback).
  - `app/engine.py`: Strict AP anomaly engine and policy decision calculator.
  - `app/ai.py`: Evidence package assembler, prompt template builder, and LLM chat.
  - `app/document_processor.py`: Text parser and OCR field normalizer.
  - `app/routes/`: Specialized API routers (auth, dashboard, exceptions, investigation, policies, documents, audit).
  - `app/seed.py`: Seeder script generating initial vendors, POs, invoices, and standard test cases.
- **`/frontend`**: React client built with Vite, TypeScript, Tailwind CSS, and Lucide icons.
  - `src/pages/Dashboard.tsx`: Exceptions Queue with sorting, filtering, and engine controls.
  - `src/pages/Workspace.tsx`: Double-pane case detail panel with evidence list, AI chat, policy results, and resolution actions.
  - `src/pages/Documents.tsx`: Document Workbench for uploading invoices, inspecting field confidence, editing, and verifying fields.
  - `src/pages/Policies.tsx`: Manager threshold settings dashboard.
  - `src/pages/Audit.tsx`: Permanent audit ledger view.

---

## 🚀 Quick Start Guide

### 1. Environment & Setup

Ensure Python 3.10+ and Node.js 18+ are installed.

**Clone & Install Backend Dependencies**:
```bash
cd backend
pip install -r requirements.txt
```

**Seed Database & Generate Synthetic Docs**:
```bash
# Seed schemas, vendors, users, policies, and standard exceptions
python -m app.seed

# Generate synthetic invoice text files for Document Workbench testing
python -m app.generate_demo_docs
```

**Launch backend server**:
```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```
*API documentation is available at `http://127.0.0.1:8000/docs`.*

---

### 2. Frontend React Client

**Install dependencies & launch dev server**:
```bash
cd frontend
npm install
npm run dev
```
*Web client is available at `http://localhost:5173/`.*

---

## 👥 Seeded Quick-Demo Identities

Authentication is governed by JWT cookie sessions. Use the credentials below to test user roles:

| Role | Name | Email | Password |
| :--- | :--- | :--- | :--- |
| **Reviewer** | Alex Audit | `reviewer@supervity-demo.com` | `supervity123` |
| **Manager** | Sarah Manager | `manager@supervity-demo.com` | `supervity123` |

---

## 🎬 Testing & Verification Walkthrough

See [`DEMO_SCRIPT.md`](file:///c:/Users/chara/OneDrive/Desktop/Supervity/DEMO_SCRIPT.md) for a comprehensive 5-minute step-by-step walkthrough demonstrating:
1. **Case 1 (Duplicate Invoice)**: Auto-decline and closed status on identical matching amounts.
2. **Case 2 (Price Mismatch)**: Cloud rate deviation triggering review, AI investigation, policy evaluation, and reviewer override.
3. **Case 3 (Missing PO Anomaly)**: Escalation lock forcing manager approval due to high financial risk.
4. **Document Ingestion**: Uploading invoices, verifying OCR fields, and logging field history.
5. **System Audit Logs**: Inspecting timelines of actions and policy updates.
