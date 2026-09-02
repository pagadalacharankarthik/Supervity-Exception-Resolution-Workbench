# User Roles & Demo Credentials

## 🔐 Login Credentials

### Live Demo (Deployed)
> URL: https://supervity-exception-resolution-work-one.vercel.app

| Role | Name | Email | Password |
|---|---|---|---|
| **Reviewer** | Alex Audit | `reviewer@supervity-demo.com` | `supervity123` |
| **Manager** | Sarah Manager | `manager@supervity-demo.com` | `supervity123` |

### Local Development
> URL: http://localhost:5173

Same credentials apply after running `python -m app.seed`.

---

## 👤 Role: Reviewer (Alex Audit)

Reviewers handle the day-to-day exception queue. They can:

| Permission | Description |
|---|---|
| ✅ View Dashboard | See all open, under-review, and escalated exceptions |
| ✅ View Exception Detail | Inspect invoice, PO, vendor data, and evidence |
| ✅ Trigger AI Investigation | Request AI analysis on any open exception |
| ✅ View Policy Decision | See what the policy engine recommended and why |
| ✅ Resolve Exception | Mark exception as resolved with mandatory comments |
| ✅ Reject Exception | Reject as invalid/fraudulent with mandatory comments |
| ✅ Mark False Positive | Flag as incorrectly flagged anomaly |
| ✅ Upload Documents | Upload invoice PDFs to the Document Workbench |
| ✅ Verify OCR Fields | Confirm or edit extracted document fields |
| ✅ View Audit Logs | Read-only access to global audit ledger |
| ❌ Approve Escalations | Cannot approve ESCALATED exceptions — manager only |
| ❌ Modify Policies | Cannot change policy thresholds — manager only |

---

## 👤 Role: Manager (Sarah Manager)

Managers have all reviewer capabilities plus elevated controls:

| Permission | Description |
|---|---|
| ✅ All Reviewer Permissions | Full reviewer access |
| ✅ Approve Escalated Exceptions | Can resolve or reject ESCALATED cases |
| ✅ Manage Policies | Configure auto-resolve thresholds, risk limits, amount caps |
| ✅ View All Audit Events | Including policy change history |

---

## 🔑 Authentication Flow

1. User submits email + password via Login page
2. Backend validates credentials and returns a signed **JWT token**
3. Token is stored in `localStorage` as `supervity_token`
4. All API requests include `Authorization: Bearer <token>` header
5. Backend validates JWT on every protected endpoint
6. Token expires after **24 hours** — user must re-login

---

## 🎬 Recommended Demo Path

### As Alex Audit (Reviewer)
1. Login → Dashboard shows 3 seeded open exceptions
2. Click **Case 2** (Price Mismatch) → click "Run AI Investigation"
3. View AI finding, confidence, and policy routing recommendation
4. Click "Resolve" → enter comment → submit
5. Navigate to Document Workbench → upload an invoice
6. View extracted fields and verify/edit confidence scores
7. Check Audit Logs for full activity history

### As Sarah Manager
1. Logout → login as `manager@supervity-demo.com`
2. Go to Dashboard → find Case 3 (ESCALATED status)
3. Open Workspace → view escalation lock warning
4. Use manager override to approve or reject the escalated case
5. Go to Policies → adjust auto-resolve confidence threshold
6. Observe new policy version created in audit log
