import os
import logging

logger = logging.getLogger(__name__)

DOCS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "storage", "documents")
os.makedirs(DOCS_DIR, exist_ok=True)

DEMO_DOCS = {
    "invoice_auto_resolution.pdf": (
        "SUPERVITY SYNTHETIC DEMO INVOICE — CASE A (AUTO-RESOLUTION)\n"
        "-----------------------------------------------------------\n"
        "Vendor Name: Acme Supplies Inc.\n"
        "Invoice Number: INV-1001\n"
        "Invoice Date: 2026-02-10\n"
        "PO Reference: PO-2026-101\n"
        "Vendor Tax ID: TAX-ACME-99182\n\n"
        "LINE ITEMS:\n"
        "1. Standard Industrial Pallets - Qty: 50 @ $80.00 = $4,000.00\n"
        "2. Heavy Duty Packaging Film - Qty: 20 @ $50.00 = $1,000.00\n\n"
        "Subtotal: $5,000.00\n"
        "Tax (0%): $0.00\n"
        "TOTAL AMOUNT DUE: $5,000.00\n"
    ),
    "invoice_amount_mismatch.pdf": (
        "SUPERVITY SYNTHETIC DEMO INVOICE — CASE B (HUMAN REVIEW)\n"
        "--------------------------------------------------------\n"
        "Vendor Name: Global Components Ltd.\n"
        "Invoice Number: INV-1002\n"
        "Invoice Date: 2026-02-14\n"
        "PO Reference: PO-2002\n"
        "Vendor Tax ID: TAX-GLOB-55201\n\n"
        "LINE ITEMS:\n"
        "1. Cloud Compute Workstation Units - Qty: 500 @ $110.00 = $55,000.00\n\n"
        "Subtotal: $55,000.00\n"
        "Tax Amount: $0.00\n"
        "TOTAL AMOUNT DUE: $55,000.00\n"
    ),
    "invoice_low_quality.pdf": (
        "SUPERVITY SYNTHETIC DEMO INVOICE — CASE C (ESCALATION / LOW QUALITY)\n"
        "-------------------------------------------------------------------\n"
        "Vendor Name: Northstar Services Corp\n"
        "Invoice Number: INV-1003\n"
        "Date: 2026-02-18\n"
        "PO Reference: NONE / UNKNOWN\n\n"
        "LINE ITEMS:\n"
        "1. Specialized Engineering Consulting - Qty: 120 hrs @ $1,000.00 = $120,000.00\n\n"
        "Subtotal: $120,000.00\n"
        "Tax Amount: $0.00\n"
        "TOTAL AMOUNT DUE: $120,000.00\n"
    )
}

def generate_demo_documents():
    print("Generating Synthetic Demo Documents...")
    for filename, content in DEMO_DOCS.items():
        filepath = os.path.join(DOCS_DIR, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  - Generated: {filepath}")

if __name__ == "__main__":
    generate_demo_documents()
