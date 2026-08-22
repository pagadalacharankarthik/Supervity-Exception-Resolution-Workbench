# 🎬 Supervity Exception Resolution Workbench — Evaluator Demo Video Script
### *Timed 5-Minute Script: Tech Stack & Architecture (2m) • Live Demo (2m) • Design Tradeoff (1m)*

This script is structured to help you deliver a 5-minute video presentation that addresses all evaluator requirements, including details on local mock capabilities and live LLM integration.

---

## 🏛️ Section 1: Tech Stack & Architecture (≈ 2 Minutes)

**[Visual: Show Codebase Structure or Architecture Diagram / Read Continuously]**

"Hello, today I am presenting the Supervity Exception Resolution Workbench, an enterprise accounts payable auditing platform designed to detect and resolve transaction anomalies safely.

For our technology stack:
*   On the **Frontend**, we chose **React with Vite and TypeScript**. React provides a component-driven, responsive UI for fast-paced reviewers, Vite ensures sub-second Hot Module Replacement for developer efficiency, and TypeScript guarantees static type safety across our API boundaries.
*   On the **Backend**, we built a high-performance **FastAPI** service in Python. FastAPI provides rapid, asynchronous endpoints, auto-documents our API contracts, and allows us to run standard numeric parsing and data calculations in Python.
*   For the **Database**, we use **PostgreSQL** with **SQLAlchemy ORM** to enforce strict foreign key constraints and transactional integrity on financial records, with a seamless SQLite fallback for local developer environments.

Our backend is structured around four primary architectural guardrails:
1.  **Deterministic Rule Engine**: Calculation scans—such as subtotal verification, tax rate validation, and duplicate invoice matching—are calculated in pure Python logic. We never use an LLM for math, eliminating hallucination risks.
2.  **Evidence-Grounded AI**: The AI Investigation Service compiles a context package containing *only* verified database facts or verified document fields. The AI acts as an advisor, never mutating database states directly.
3.  **Decoupled Compliance Policies**: Risk routing thresholds reside dynamically in database tables. The system compares the AI's confidence output against these policy rules to automatically route cases to review or escalation.
4.  **Immutable Audit timeline**: Every trigger, AI run, policy evaluation, and reviewer comment is logged in permanent ledger tables for compliance auditing."

---

## 💻 Section 2: Live Demonstration (≈ 2 Minutes)

**[Visual: Sign in as Alex Audit (`reviewer@supervity-demo.com` / `supervity123`) and show Exceptions Queue]**

"Let's look at the working application. Logging in as a Reviewer, we trigger the **Detection Engine** on our Exceptions Queue. The backend instantly scans our database and populates the dashboard queue with dynamic severity levels and calculated AI risk indicators.

We click on Case **EX-2**—a price mismatch discrepancy for Vertex Technologies. On the left, our evidence panel displays verified ground-truth values. On the right, we trigger the **AI Investigation**. 

For this demonstration, the AI service runs a high-fidelity local mock provider. This allows the workbench to be evaluated offline and run automated unit tests immediately without needing external API keys. However, the LLM layer is fully decoupled; by simply adding a Google Gemini or OpenAI API key to the environment variables, the system immediately switches to live model invocations.

The system returns a structured finding, reasoning, and recommendation alongside an 'Evidence: Grounded' badge. We can engage in contextual chat in the bottom pane to query case details. Clicking **Evaluate Policy** executes our compliance thresholds, routing this case to `HUMAN_REVIEW`. As a reviewer, we enter a comment and resolve the case.

Next, we select Case **EX-3**—a missing PO anomaly of over seventy thousand dollars. Running the investigation and evaluating the policy triggers an automatic `ESCALATE` decision. Because the amount exceeds our high-risk threshold, the actions are locked for the reviewer role. We click **Escalate** to send it to a manager.

We sign out and log back in as Sarah the **Manager** (`manager@supervity-demo.com` / `supervity123`). In Case EX-3, the action controls are now unlocked. We check the audit timeline and reject the invoice. In the **Policy Manager**, we can dynamically adjust compliance thresholds like the high-risk dollar amount, changing system behavior in real-time.

Finally, in the **Document Workbench**, we upload a raw invoice. The OCR parser extracts fields, highlights low-confidence items, and logs an edit history of reviewer modifications. Clicking **Verify Document** converts these fields into verified database facts, closing the extraction loop and feeding clean evidence back into our detection queue."

---

## ⚖️ Section 3: Design Tradeoff Made & Why (≈ 1 Minute)

**[Visual: Show Policy Engine Code (`app/engine.py`) or Workspace policy results page]**

"A key design tradeoff we made was **decoupling the AI Investigation output from the final policy decision and state mutations**.

Rather than allowing the LLM to directly approve or reject an exception, or mutate transaction states in the database, we treat the AI strictly as a **read-only advisor**. The AI evaluates evidence packages and produces a confidence score and recommendation, but it has zero direct authority to change database statuses.

Instead, a separate, deterministic Python-based **Policy Engine** evaluates the AI's confidence score and the invoice's financial risk against database-resident policy thresholds to calculate the final routing decision (`AUTO_RESOLVE`, `HUMAN_REVIEW`, or `ESCALATE`).

We made this tradeoff for three reasons:
1.  **Compliance and Auditability**: It guarantees that the rules governing financial movements are transparent, deterministic, and auditable.
2.  **State Protection**: It prevents malicious prompt injections or LLM hallucinations from directly changing invoice payment states.
3.  **Operational Safety**: It keeps final decision-making control in the hands of the business logic and human managers, ensuring a strict separation of concerns."
