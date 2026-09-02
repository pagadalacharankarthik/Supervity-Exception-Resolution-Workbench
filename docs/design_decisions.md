# Design Decisions & Engineering Tradeoffs

## 1. MockLLM First — Real LLM Second

### Decision
Ship with a deterministic `MockLLMProvider` as the default instead of requiring an OpenAI or Gemini API key.

### Why
- **Demo resilience**: The workbench works 100% offline, in CI/CD pipelines, and during evaluator review without any external dependencies.
- **Reproducibility**: Mock responses are grounded in actual database evidence (invoice amounts, PO rates, vendor history) — not random. Every test run produces the same output.
- **Evaluation fairness**: Evaluators can test the full AI reasoning pipeline without managing API quotas or incurring costs.

### Tradeoff
The mock produces structured, predictable responses while a real LLM would produce richer, more nuanced natural-language reasoning. For production use, the `OPENAI_API_KEY` or `GEMINI_API_KEY` env var switches the active provider instantly.

---

## 2. SQLite Default with PostgreSQL Upgrade Path

### Decision
Use SQLite as the default database with automatic fallback if `psycopg2` is not installed.

### Why
- **Zero-config onboarding**: Reviewers can clone and run the backend with `python -m app.seed` — no external database needed.
- **Render free tier compatibility**: Render's free plan does not include a managed database. SQLite persists on the ephemeral filesystem for the duration of the service lifecycle.
- **Same ORM, same models**: SQLAlchemy abstracts the DB difference completely — all queries, relationships, and migrations work identically on both.

### Tradeoff
SQLite is not suitable for concurrent writes in production. The `DATABASE_URL` env var switches to PostgreSQL without any code changes for production workloads.

---

## 3. Strict Evidence Grounding Validation

### Decision
All AI responses are validated against the evidence package before being persisted. If the AI claims a fact not present in the evidence, the grounding score is downgraded to `PARTIALLY_GROUNDED` or `INVALID`.

### Why
- **Hallucination prevention**: LLMs can confidently state false facts. Grounding validation anchors every AI claim to a verifiable database record.
- **Audit defensibility**: Every AI finding can be traced to a specific invoice line, PO record, or transaction. Regulators and auditors can verify AI reasoning.
- **Trust calibration**: Reviewers see the grounding status alongside AI confidence — `GROUNDED` means facts verified, `PARTIALLY_GROUNDED` means partial verification, `INVALID` means AI response discarded.

### Tradeoff
Grounding validation adds latency to the AI investigation step. This is acceptable because investigation is asynchronous and non-blocking for the reviewer UI.

---

## 4. Immutable Audit Ledger

### Decision
All status changes, AI results, policy decisions, and user actions are appended to an immutable `AuditEvent` table. Records are never updated or deleted.

### Why
- **Regulatory compliance**: Financial exception systems require a complete, tamper-proof history of every action for SOX/audit compliance.
- **Debugging**: Full event replay enables investigation of how any exception reached its current state.
- **Trust**: Reviewers and managers can see exactly who did what and when — no black boxes.

### Tradeoff
The audit table grows indefinitely. For production scale, partitioning or archiving strategies would be needed. Acceptable for the prototype scope.

---

## 5. Role-Based Access (Reviewer vs Manager)

### Decision
Two distinct roles with different capabilities:
- **Reviewer**: Can investigate, resolve, reject, and flag false positives
- **Manager**: Can do all of the above PLUS approve escalated exceptions

### Why
- **Separation of duties**: High-risk exceptions (`ESCALATED`) are locked from reviewer resolution — they require manager approval. This mirrors real enterprise procurement controls.
- **Least privilege**: Reviewers cannot see or modify policy thresholds. Managers control the policy configuration.

### Tradeoff
A single-role system would be simpler to implement but would violate the financial controls requirement where high-risk payments require a second level of approval.

---

## 6. Policy Engine Separate from AI

### Decision
The `PolicyEngine` is a pure deterministic module independent of the AI layer. It evaluates thresholds (confidence, risk, amount) and produces a routing decision regardless of AI output.

### Why
- **Predictability**: Business rules cannot be overridden by AI hallucinations. A `HIGH` risk exception above the `$50,000` threshold always escalates — even if the AI says `AUTO_RESOLVE`.
- **Auditability**: Policy decisions are explainable in plain English ("AI confidence 0.82 below threshold 0.90 — routing to human review").
- **Configurability**: Managers can tune thresholds via the Policies dashboard without touching code.

### Tradeoff
Two separate evaluation systems add complexity. However, the separation of concerns — AI for reasoning, Policy Engine for routing — produces more predictable, auditable outcomes than a single AI-driven decision system.
