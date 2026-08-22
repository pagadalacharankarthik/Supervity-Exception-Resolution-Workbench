# 🎬 Supervity Exception Resolution Workbench — 5-Minute Demo Script
### *Grounded AI Investigation, Deterministic Policy Routing & Human-in-the-Loop AP Resolution*

This script guides you through a complete end-to-end demonstration of the **Supervity Exception Resolution Workbench** in under 5 minutes. It showcases document ingestion, field verification, exception detection, evidence-grounded AI analysis, compliance policy routing, and final resolution.

---

## 🛠️ Step 0: Reset the Environment (15 Seconds)

Ensure the database and synthetic documents are in a clean, deterministic state before starting.

1. **Seed the database** (removes old transactions, recreates users, compliance policies, POs, and 20 invoices):
   ```bash
   cd backend
   python -m app.seed
   ```
2. **Generate synthetic demo invoice text files**:
   ```bash
   python -m app.generate_demo_docs
   ```
   *These text files (simulating PDFs) are stored in `backend/app/storage/documents/` and are ready for upload.*

---

## 👤 Scenario 1: Reviewer Verification & Anomaly Detection (2 Minutes)

### 1. Secure Authentication & Dashboard Audit
1. Open the workbench client at `http://localhost:5173/`.
2. Sign in with the **Reviewer** credentials:
   - **Email**: `reviewer@supervity-demo.com`
   - **Password**: `supervity123`
3. Notice the premium dark sidebar layout, the **Assessment Prototype** tenant tag, and the real-time API status badge.
4. Click **Run Detection Engine** on the Exceptions Queue dashboard. The engine runs strict, deterministic Python checks on the database invoices:
   - Evaluates subtotal discrepancies, duplicate invoice numbers, missing purchase orders, and tax anomalies.
   - You will see the counts update on the KPI cards instantly.

---

### 2. Case 2: Price Mismatch & Evidence-Grounded AI Investigation
1. Select Case **EX-2** (`AMOUNT_PRICE_MISMATCH` for Vertex Technologies) from the queue.
2. In the split-pane workspace:
   - Inspect the **Verified Source Evidence** showing the contract PO quantity/rate vs. the received invoice lines.
   - Click **Run AI Investigation**. The workbench compiles database facts into a secure prompt and requests an advisory evaluation from the LLM.
   - Review the result: Notice the **"Evidence: Grounded"** validation badge and the **AI Recommendation** of `APPROVE` with confidence scoring.
   - Expand **"Ask AI about this case"** and type: `Why did this triggers a mismatch?` to test the real-time contextual chat.
3. Click **Evaluate Policy**:
   - The deterministic policy engine compares the AI's confidence and risk level against the compliance thresholds stored in the database.
   - It outputs a strict decision of `HUMAN_REVIEW`.
4. Resolve the exception:
   - Click **✓ Resolve**, type: `Price deviation is within pre-approved contract bounds for Q1.` and click **Confirm Resolution**.
   - The status updates to **Resolved** and the transaction is closed.

---

### 3. Case 3: Missing PO & Automated Escalation Safeguard
1. Go back to the queue and select Case **EX-3** (`MISSING_PO` for Global Office Systems, Amount: `$70,200.00`).
2. Click **Run AI Investigation** followed by **Evaluate Policy**.
3. Notice that the policy decision evaluates to **ESCALATE**:
   - **Reason**: The amount exceeds the `$50,000` high-risk threshold and has no matching PO.
   - As a **Reviewer**, the action controls are locked. The screen displays: *"Escalated to Manager. This case requires manager-level authorization to proceed."*
4. Click **↑ Escalate**, type: `Requires managerial sign-off due to missing PO and high financial impact.` and click **Confirm Escalation**.

---

## 👤 Scenario 2: Manager Sign-off & Audit Trails (1 Minute)

### 1. Sign In as Sarah Manager
1. Click **Sign Out** in the footer of the sidebar.
2. Sign in with the **Manager** credentials:
   - **Email**: `manager@supervity-demo.com`
   - **Password**: `supervity123`
3. Click on the escalated case **EX-3**. As a Manager, the action buttons are now unlocked.
4. Click **✕ Reject**, type: `Invoice rejected. Vendor must provide a valid purchase order reference before payment.` and confirm. The case resolves to **Rejected**.

---

### 2. System Audit Trails & Policy Settings
1. Click **Audit Timeline** on the sidebar navigation:
   - Review the permanent ledger tracking all events, actors, previous/new states, timestamps, and comments.
   - Observe the entry for the manager reject action, reviewer escalations, and engine detections.
2. Click **Resolution Policies**:
   - This page is manager-only. Try changing the **High-Risk Amount Threshold** to `$100,000` and save.
   - The rules are updated instantly in the database, dictating all future policy routing logic.

---

## 📁 Scenario 3: Ingestion & Document Workbench (1 Minute)

1. Click **Document Workbench** on the sidebar.
2. Click the upload box and select `invoice_amount_mismatch.pdf` from `backend/app/storage/documents/`.
3. The parser processes the file, extracts structured key-value fields, and displays confidence levels (`HIGH`/`MEDIUM`/`LOW`).
4. Inspect the low-confidence field or incorrect value:
   - Click **Edit** on `vendor_name`, change it to `Vertex Technologies Corp`, specify the reason, and save.
   - Expand the **History** to view the audit timeline of field modifications.
5. Click **Verify Document**:
   - The status updates to **Verified**.
   - The verified field facts are successfully converted into `VERIFIED_FACT` evidence nodes, feeding back into matching exceptions.
