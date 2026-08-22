import sys
import os
import uuid
from decimal import Decimal
from datetime import datetime, timedelta

# Adjust path to find app package
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine, SessionLocal, Base
from app import models
from app.auth import get_password_hash

def seed_db():
    db = SessionLocal()
    try:
        print("Starting Database Seed Process...")
        
        # Create all tables first
        Base.metadata.create_all(bind=engine)
        
        # 1. Clean existing records in reverse dependency order to prevent FK constraints issues
        print("Cleaning old records...")
        db.query(models.AuditEvent).delete()
        db.query(models.Resolution).delete()
        db.query(models.Investigation).delete()
        db.query(models.Evidence).delete()
        db.query(models.Exception).delete()
        db.query(models.Transaction).delete()
        db.query(models.InvoiceLine).delete()
        db.query(models.Invoice).delete()
        db.query(models.PurchaseOrderLine).delete()
        db.query(models.PurchaseOrder).delete()
        db.query(models.Vendor).delete()
        db.query(models.User).delete()
        db.query(models.Policy).delete()
        db.query(models.Organization).delete()
        db.commit()

        # 2. Seed Organization
        print("Seeding Organization...")
        org = models.Organization(
            name="Supervity Demo Operations"
        )
        db.add(org)
        db.flush()

        # 3. Seed Users
        print("Seeding Users...")
        reviewer = models.User(
            email="reviewer@supervity-demo.com",
            hashed_password=get_password_hash("supervity123"),
            name="Alex Audit",
            role="reviewer",
            organization_id=org.id
        )
        manager = models.User(
            email="manager@supervity-demo.com",
            hashed_password=get_password_hash("supervity123"),
            name="Sarah Manager",
            role="manager",
            organization_id=org.id
        )
        db.add_all([reviewer, manager])
        db.flush()

        # 4. Seed 6 Vendors
        print("Seeding Vendors...")
        vendors_data = [
            {"name": "Apex Industrial Supplies", "code": "VND-APEX"},
            {"name": "Global Office Systems", "code": "VND-GLOBAL"},
            {"name": "Nova Components", "code": "VND-NOVA"},
            {"name": "Prime Logistics", "code": "VND-PRIME"},
            {"name": "Vertex Technologies", "code": "VND-VERTEX"},
            {"name": "Eastern Manufacturing Supplies", "code": "VND-EASTERN"},
        ]
        vendors = {}
        for v in vendors_data:
            vendor = models.Vendor(name=v["name"], vendor_code=v["code"])
            db.add(vendor)
            vendors[v["code"]] = vendor
        db.flush()

        # 5. Seed Policies
        print("Seeding Policies...")
        policy = models.Policy(
            name="Enterprise Accounts Payable Audit Policy",
            is_active=True,
            description="Controls the automatic and manual routing of transaction anomalies based on invoice risk values and AI decision confidence scores.",
            rules={
                "auto_resolve_confidence_min": 0.90,
                "human_review_confidence_min": 0.70,
                "high_risk_amount_threshold": 50000.00
            }
        )
        db.add(policy)
        db.flush()

        # 6. Seed Purchase Orders & Lines (at least 15 POs)
        print("Seeding 15 Purchase Orders and lines...")
        pos = {}
        po_details = [
            # PO 1: Case 1 base PO (Apex)
            {"num": "PO-2026-001", "vendor": "VND-APEX", "amount": Decimal("4200.00"), "status": "fully_invoiced", "days_ago": 25,
             "lines": [{"desc": "Heavy Duty Industrial Racks", "qty": 10, "price": Decimal("300.00"), "tax_rate": Decimal("0.08")},
                       {"desc": "Warehouse Storage Bins", "qty": 10, "price": Decimal("120.00"), "tax_rate": Decimal("0.08")}]},
            
            # PO 2: Case 2 base PO (Vertex)
            {"num": "PO-2026-002", "vendor": "VND-VERTEX", "amount": Decimal("50000.00"), "status": "open", "days_ago": 15,
             "lines": [{"desc": "Cloud Infrastructure Compute Units", "qty": 500, "price": Decimal("100.00"), "tax_rate": Decimal("0.00")}]}, # no tax contract
            
            # PO 3: Nova Components PO (Clean)
            {"num": "PO-2026-003", "vendor": "VND-NOVA", "amount": Decimal("8500.00"), "status": "fully_invoiced", "days_ago": 30,
             "lines": [{"desc": "Electronic Micro-controllers", "qty": 1000, "price": Decimal("8.50"), "tax_rate": Decimal("0.00")}]},
             
            # PO 4: Prime Logistics PO (Clean)
            {"num": "PO-2026-004", "vendor": "VND-PRIME", "amount": Decimal("15000.00"), "status": "fully_invoiced", "days_ago": 22,
             "lines": [{"desc": "Freight Transport Services - Q1", "qty": 1, "price": Decimal("15000.00"), "tax_rate": Decimal("0.00")}]},

            # PO 5: Eastern Manufacturing PO (Clean)
            {"num": "PO-2026-005", "vendor": "VND-EASTERN", "amount": Decimal("3200.00"), "status": "fully_invoiced", "days_ago": 12,
             "lines": [{"desc": "Steel Hex Bolts & Nuts (Bulk)", "qty": 50, "price": Decimal("64.00"), "tax_rate": Decimal("0.08")}]},

            # PO 6: Global Office Systems PO (Clean)
            {"num": "PO-2026-006", "vendor": "VND-GLOBAL", "amount": Decimal("1800.00"), "status": "fully_invoiced", "days_ago": 18,
             "lines": [{"desc": "Executive Mesh Chairs", "qty": 6, "price": Decimal("300.00"), "tax_rate": Decimal("0.08")}]},

            # PO 7: Vertex Tech PO (Clean)
            {"num": "PO-2026-007", "vendor": "VND-VERTEX", "amount": Decimal("12500.00"), "status": "fully_invoiced", "days_ago": 10,
             "lines": [{"desc": "Developer Workstations", "qty": 5, "price": Decimal("2500.00"), "tax_rate": Decimal("0.00")}]},

            # PO 8: Apex Supplies PO (Clean)
            {"num": "PO-2026-008", "vendor": "VND-APEX", "amount": Decimal("6200.00"), "status": "open", "days_ago": 8,
             "lines": [{"desc": "Safety Goggles & Gloves", "qty": 200, "price": Decimal("31.00"), "tax_rate": Decimal("0.08")}]},

            # PO 9: Nova Components PO (Clean)
            {"num": "PO-2026-009", "vendor": "VND-NOVA", "amount": Decimal("9450.00"), "status": "open", "days_ago": 7,
             "lines": [{"desc": "Custom LED Backlit Panels", "qty": 300, "price": Decimal("31.50"), "tax_rate": Decimal("0.00")}]},

            # PO 10: Prime Logistics PO (Clean)
            {"num": "PO-2026-010", "vendor": "VND-PRIME", "amount": Decimal("4800.00"), "status": "fully_invoiced", "days_ago": 14,
             "lines": [{"desc": "Pallet Storage Fees - Monthly", "qty": 4, "price": Decimal("1200.00"), "tax_rate": Decimal("0.00")}]},

            # PO 11: Eastern Manufacturing PO (Clean)
            {"num": "PO-2026-011", "vendor": "VND-EASTERN", "amount": Decimal("2150.00"), "status": "open", "days_ago": 5,
             "lines": [{"desc": "Copper Tube Fittings", "qty": 100, "price": Decimal("21.50"), "tax_rate": Decimal("0.08")}]},

            # PO 12: Global Office Systems PO (Clean)
            {"num": "PO-2026-012", "vendor": "VND-GLOBAL", "amount": Decimal("5500.00"), "status": "open", "days_ago": 6,
             "lines": [{"desc": "Smart Conference Display 65\"", "qty": 2, "price": Decimal("2750.00"), "tax_rate": Decimal("0.08")}]},

            # PO 13: Vertex Tech PO (Clean)
            {"num": "PO-2026-013", "vendor": "VND-VERTEX", "amount": Decimal("35000.00"), "status": "open", "days_ago": 4,
             "lines": [{"desc": "Enterprise Software Licensing", "qty": 1, "price": Decimal("35000.00"), "tax_rate": Decimal("0.00")}]},

            # PO 14: Apex Supplies PO (Clean)
            {"num": "PO-2026-014", "vendor": "VND-APEX", "amount": Decimal("1100.00"), "status": "open", "days_ago": 3,
             "lines": [{"desc": "Heavy Duty Extension Cords", "qty": 20, "price": Decimal("55.00"), "tax_rate": Decimal("0.08")}]},

            # PO 15: Nova Components PO (Clean)
            {"num": "PO-2026-015", "vendor": "VND-NOVA", "amount": Decimal("17500.00"), "status": "open", "days_ago": 2,
             "lines": [{"desc": "Microchip Processors", "qty": 500, "price": Decimal("35.00"), "tax_rate": Decimal("0.00")}]},
        ]

        for p in po_details:
            vendor = vendors[p["vendor"]]
            po = models.PurchaseOrder(
                po_number=p["num"],
                vendor_id=vendor.id,
                total_amount=p["amount"],
                currency="USD",
                status=p["status"],
                order_date=datetime.utcnow() - timedelta(days=p["days_ago"]),
                created_at=datetime.utcnow() - timedelta(days=p["days_ago"])
            )
            db.add(po)
            db.flush()
            pos[p["num"]] = po

            for line in p["lines"]:
                po_line = models.PurchaseOrderLine(
                    po_id=po.id,
                    description=line["desc"],
                    quantity=line["qty"],
                    unit_price=line["price"],
                    tax_rate=line["tax_rate"],
                    tax_amount=Decimal(str(line["qty"])) * line["price"] * line["tax_rate"],
                    total_amount=Decimal(str(line["qty"])) * line["price"] * (Decimal("1.00") + line["tax_rate"])
                )
                db.add(po_line)
        db.flush()

        # 7. Seed Invoices & Lines (at least 20 Invoices)
        print("Seeding 20 Invoices and lines...")
        invoices = {}
        invoice_details = [
            # INV 1: Case 1 Original Paid Invoice (Apex)
            {"num": "INV-2026-001", "vendor": "VND-APEX", "po": "PO-2026-001", "status": "paid", "days_ago": 15, "due_days": 15,
             "subtotal": Decimal("4200.00"), "tax": Decimal("336.00"), "total": Decimal("4536.00"),
             "lines": [{"desc": "Heavy Duty Industrial Racks", "qty": 10, "price": Decimal("300.00"), "tax_rate": Decimal("0.08")},
                       {"desc": "Warehouse Storage Bins", "qty": 10, "price": Decimal("120.00"), "tax_rate": Decimal("0.08")}]},
            
            # INV 2: Case 1 Duplicate Invoice (Apex - Exception)
            {"num": "INV-2026-001", "vendor": "VND-APEX", "po": "PO-2026-001", "status": "exception", "days_ago": 1, "due_days": 29,
             "subtotal": Decimal("4200.00"), "tax": Decimal("336.00"), "total": Decimal("4536.00"),
             "lines": [{"desc": "Heavy Duty Industrial Racks", "qty": 10, "price": Decimal("300.00"), "tax_rate": Decimal("0.08")},
                       {"desc": "Warehouse Storage Bins", "qty": 10, "price": Decimal("120.00"), "tax_rate": Decimal("0.08")}]},

            # INV 3: Case 2 Price/Amount Mismatch Invoice (Vertex - Exception)
            # PO amount = 50000. Invoice amount = 55000 (unit price 110 instead of 100)
            {"num": "INV-2026-002", "vendor": "VND-VERTEX", "po": "PO-2026-002", "status": "exception", "days_ago": 2, "due_days": 28,
             "subtotal": Decimal("55000.00"), "tax": Decimal("0.00"), "total": Decimal("55000.00"),
             "lines": [{"desc": "Cloud Infrastructure Compute Units", "qty": 500, "price": Decimal("110.00"), "tax_rate": Decimal("0.00")}]},

            # INV 4: Case 3 Tax Anomaly Invoice (Apex - Exception)
            # Subtotal 4200. Billed tax 150.00 (expected tax 336.00)
            {"num": "INV-2026-004", "vendor": "VND-APEX", "po": "PO-2026-001", "status": "exception", "days_ago": 3, "due_days": 27,
             "subtotal": Decimal("4200.00"), "tax": Decimal("150.00"), "total": Decimal("4350.00"),
             "lines": [{"desc": "Heavy Duty Industrial Racks", "qty": 10, "price": Decimal("300.00"), "tax_rate": Decimal("0.08")},
                       {"desc": "Warehouse Storage Bins", "qty": 10, "price": Decimal("120.00"), "tax_rate": Decimal("0.08")}]},

            # INV 5: Case 3 / Missing PO Anomaly (Global Services - Exception)
            # No PO referenced. Large amount: 65000.00
            {"num": "INV-2026-003", "vendor": "VND-GLOBAL", "po": None, "status": "exception", "days_ago": 2, "due_days": 28,
             "subtotal": Decimal("65000.00"), "tax": Decimal("5200.00"), "total": Decimal("70200.00"),
             "lines": [{"desc": "Annual Security Auditing Services", "qty": 1, "price": Decimal("65000.00"), "tax_rate": Decimal("0.08")}]},

            # INV 6: Nova Components clean invoice (paid)
            {"num": "INV-2026-005", "vendor": "VND-NOVA", "po": "PO-2026-003", "status": "paid", "days_ago": 28, "due_days": 2,
             "subtotal": Decimal("8500.00"), "tax": Decimal("0.00"), "total": Decimal("8500.00"),
             "lines": [{"desc": "Electronic Micro-controllers", "qty": 1000, "price": Decimal("8.50"), "tax_rate": Decimal("0.00")}]},

            # INV 7: Prime Logistics clean invoice (paid)
            {"num": "INV-2026-006", "vendor": "VND-PRIME", "po": "PO-2026-004", "status": "paid", "days_ago": 20, "due_days": 10,
             "subtotal": Decimal("15000.00"), "tax": Decimal("0.00"), "total": Decimal("15000.00"),
             "lines": [{"desc": "Freight Transport Services - Q1", "qty": 1, "price": Decimal("15000.00"), "tax_rate": Decimal("0.00")}]},

            # INV 8: Eastern Manufacturing clean invoice (paid)
            {"num": "INV-2026-007", "vendor": "VND-EASTERN", "po": "PO-2026-005", "status": "paid", "days_ago": 10, "due_days": 20,
             "subtotal": Decimal("3200.00"), "tax": Decimal("256.00"), "total": Decimal("3456.00"),
             "lines": [{"desc": "Steel Hex Bolts & Nuts (Bulk)", "qty": 50, "price": Decimal("64.00"), "tax_rate": Decimal("0.08")}]},

            # INV 9: Global Office Systems clean invoice (paid)
            {"num": "INV-2026-008", "vendor": "VND-GLOBAL", "po": "PO-2026-006", "status": "paid", "days_ago": 15, "due_days": 15,
             "subtotal": Decimal("1800.00"), "tax": Decimal("144.00"), "total": Decimal("1944.00"),
             "lines": [{"desc": "Executive Mesh Chairs", "qty": 6, "price": Decimal("300.00"), "tax_rate": Decimal("0.08")}]},

            # INV 10: Vertex Tech clean invoice (paid)
            {"num": "INV-2026-009", "vendor": "VND-VERTEX", "po": "PO-2026-007", "status": "paid", "days_ago": 8, "due_days": 22,
             "subtotal": Decimal("12500.00"), "tax": Decimal("0.00"), "total": Decimal("12500.00"),
             "lines": [{"desc": "Developer Workstations", "qty": 5, "price": Decimal("2500.00"), "tax_rate": Decimal("0.00")}]},

            # INV 11: Prime Logistics clean invoice (paid)
            {"num": "INV-2026-010", "vendor": "VND-PRIME", "po": "PO-2026-010", "status": "paid", "days_ago": 12, "due_days": 18,
             "subtotal": Decimal("4800.00"), "tax": Decimal("0.00"), "total": Decimal("4800.00"),
             "lines": [{"desc": "Pallet Storage Fees - Monthly", "qty": 4, "price": Decimal("1200.00"), "tax_rate": Decimal("0.00")}]},

            # INV 12: Apex Supplies clean invoice (received)
            {"num": "INV-2026-011", "vendor": "VND-APEX", "po": "PO-2026-008", "status": "received", "days_ago": 4, "due_days": 26,
             "subtotal": Decimal("6200.00"), "tax": Decimal("496.00"), "total": Decimal("6696.00"),
             "lines": [{"desc": "Safety Goggles & Gloves", "qty": 200, "price": Decimal("31.00"), "tax_rate": Decimal("0.08")}]},

            # INV 13: Nova Components clean invoice (received)
            {"num": "INV-2026-012", "vendor": "VND-NOVA", "po": "PO-2026-009", "status": "received", "days_ago": 3, "due_days": 27,
             "subtotal": Decimal("9450.00"), "tax": Decimal("0.00"), "total": Decimal("9450.00"),
             "lines": [{"desc": "Custom LED Backlit Panels", "qty": 300, "price": Decimal("31.50"), "tax_rate": Decimal("0.00")}]},

            # INV 14: Eastern Manufacturing clean invoice (received)
            {"num": "INV-2026-013", "vendor": "VND-EASTERN", "po": "PO-2026-011", "status": "received", "days_ago": 2, "due_days": 28,
             "subtotal": Decimal("2150.00"), "tax": Decimal("172.00"), "total": Decimal("2322.00"),
             "lines": [{"desc": "Copper Tube Fittings", "qty": 100, "price": Decimal("21.50"), "tax_rate": Decimal("0.08")}]},

            # INV 15: Global Office Systems clean invoice (received)
            {"num": "INV-2026-014", "vendor": "VND-GLOBAL", "po": "PO-2026-012", "status": "received", "days_ago": 2, "due_days": 28,
             "subtotal": Decimal("5500.00"), "tax": Decimal("440.00"), "total": Decimal("5940.00"),
             "lines": [{"desc": "Smart Conference Display 65\"", "qty": 2, "price": Decimal("2750.00"), "tax_rate": Decimal("0.08")}]},

            # INV 16: Vertex Tech clean invoice (received)
            {"num": "INV-2026-015", "vendor": "VND-VERTEX", "po": "PO-2026-013", "status": "received", "days_ago": 1, "due_days": 29,
             "subtotal": Decimal("35000.00"), "tax": Decimal("0.00"), "total": Decimal("35000.00"),
             "lines": [{"desc": "Enterprise Software Licensing", "qty": 1, "price": Decimal("35000.00"), "tax_rate": Decimal("0.00")}]},

            # INV 17: Apex Supplies clean invoice (received)
            {"num": "INV-2026-016", "vendor": "VND-APEX", "po": "PO-2026-014", "status": "received", "days_ago": 1, "due_days": 29,
             "subtotal": Decimal("1100.00"), "tax": Decimal("88.00"), "total": Decimal("1188.00"),
             "lines": [{"desc": "Heavy Duty Extension Cords", "qty": 20, "price": Decimal("55.00"), "tax_rate": Decimal("0.08")}]},

            # INV 18: Nova Components clean invoice (received)
            {"num": "INV-2026-017", "vendor": "VND-NOVA", "po": "PO-2026-015", "status": "received", "days_ago": 1, "due_days": 29,
             "subtotal": Decimal("17500.00"), "tax": Decimal("0.00"), "total": Decimal("17500.00"),
             "lines": [{"desc": "Microchip Processors", "qty": 500, "price": Decimal("35.00"), "tax_rate": Decimal("0.00")}]},

            # INV 19: Missing PO Exception Case 4 (Vertex - Exception)
            # Low amount missing PO: 850.00
            {"num": "INV-2026-018", "vendor": "VND-VERTEX", "po": None, "status": "exception", "days_ago": 5, "due_days": 25,
             "subtotal": Decimal("850.00"), "tax": Decimal("0.00"), "total": Decimal("850.00"),
             "lines": [{"desc": "Developer Headsets", "qty": 10, "price": Decimal("85.00"), "tax_rate": Decimal("0.00")}]},

            # INV 20: Missing PO Exception Case 5 (Prime Logistics - Exception)
            # Medium amount missing PO: 3500.00
            {"num": "INV-2026-019", "vendor": "VND-PRIME", "po": None, "status": "exception", "days_ago": 6, "due_days": 24,
             "subtotal": Decimal("3500.00"), "tax": Decimal("0.00"), "total": Decimal("3500.00"),
             "lines": [{"desc": "Expedited Courier Services", "qty": 1, "price": Decimal("3500.00"), "tax_rate": Decimal("0.00")}]}
        ]

        for i in invoice_details:
            vendor = vendors[i["vendor"]]
            po = pos[i["po"]] if i["po"] else None
            
            inv = models.Invoice(
                invoice_number=i["num"],
                po_id=po.id if po else None,
                vendor_id=vendor.id,
                subtotal=i["subtotal"],
                tax=i["tax"],
                total=i["total"],
                status=i["status"],
                invoice_date=datetime.utcnow() - timedelta(days=i["days_ago"]),
                due_date=datetime.utcnow() - timedelta(days=i["days_ago"]) + timedelta(days=i["due_days"]),
                received_at=datetime.utcnow() - timedelta(days=i["days_ago"])
            )
            db.add(inv)
            db.flush()
            invoices[f"{i['num']}_{i['vendor']}"] = inv

            for line in i["lines"]:
                inv_line = models.InvoiceLine(
                    invoice_id=inv.id,
                    description=line["desc"],
                    quantity=line["qty"],
                    unit_price=line["price"],
                    tax_rate=line["tax_rate"],
                    tax_amount=Decimal(str(line["qty"])) * line["price"] * line["tax_rate"],
                    total_amount=Decimal(str(line["qty"])) * line["price"] * (Decimal("1.00") + line["tax_rate"])
                )
                db.add(inv_line)
        db.flush()

        # 8. Seed 26 Payment Ledger Transactions linking relevant entities
        print("Seeding 26 ledger transactions...")
        tx_data = [
            # Settled paid invoice transactions (1-9)
            {"inv": "INV-2026-001", "vendor": "VND-APEX", "po": "PO-2026-001", "amt": Decimal("4536.00"), "status": "settled", "days_ago": 14},
            {"inv": "INV-2026-005", "vendor": "VND-NOVA", "po": "PO-2026-003", "amt": Decimal("8500.00"), "status": "settled", "days_ago": 27},
            {"inv": "INV-2026-006", "vendor": "VND-PRIME", "po": "PO-2026-004", "amt": Decimal("15000.00"), "status": "settled", "days_ago": 19},
            {"inv": "INV-2026-007", "vendor": "VND-EASTERN", "po": "PO-2026-005", "amt": Decimal("3456.00"), "status": "settled", "days_ago": 9},
            {"inv": "INV-2026-008", "vendor": "VND-GLOBAL", "po": "PO-2026-006", "amt": Decimal("1944.00"), "status": "settled", "days_ago": 14},
            {"inv": "INV-2026-009", "vendor": "VND-VERTEX", "po": "PO-2026-007", "amt": Decimal("12500.00"), "status": "settled", "days_ago": 7},
            {"inv": "INV-2026-010", "vendor": "VND-PRIME", "po": "PO-2026-010", "amt": Decimal("4800.00"), "status": "settled", "days_ago": 11},
            
            # Pending normal invoice transactions (10-16)
            {"inv": "INV-2026-011", "vendor": "VND-APEX", "po": "PO-2026-008", "amt": Decimal("6696.00"), "status": "pending", "days_ago": 4},
            {"inv": "INV-2026-012", "vendor": "VND-NOVA", "po": "PO-2026-009", "amt": Decimal("9450.00"), "status": "pending", "days_ago": 3},
            {"inv": "INV-2026-013", "vendor": "VND-EASTERN", "po": "PO-2026-011", "amt": Decimal("2322.00"), "status": "pending", "days_ago": 2},
            {"inv": "INV-2026-014", "vendor": "VND-GLOBAL", "po": "PO-2026-012", "amt": Decimal("5940.00"), "status": "pending", "days_ago": 2},
            {"inv": "INV-2026-015", "vendor": "VND-VERTEX", "po": "PO-2026-013", "amt": Decimal("35000.00"), "status": "pending", "days_ago": 1},
            {"inv": "INV-2026-016", "vendor": "VND-APEX", "po": "PO-2026-014", "amt": Decimal("1188.00"), "status": "pending", "days_ago": 1},
            {"inv": "INV-2026-017", "vendor": "VND-NOVA", "po": "PO-2026-015", "amt": Decimal("17500.00"), "status": "pending", "days_ago": 1},
            
            # Clean transactions directly on POs/advances (17-26)
            {"inv": None, "vendor": "VND-APEX", "po": "PO-2026-001", "amt": Decimal("1000.00"), "status": "settled", "days_ago": 24},
            {"inv": None, "vendor": "VND-VERTEX", "po": "PO-2026-002", "amt": Decimal("20000.00"), "status": "settled", "days_ago": 14},
            {"inv": None, "vendor": "VND-NOVA", "po": "PO-2026-003", "amt": Decimal("3000.00"), "status": "settled", "days_ago": 29},
            {"inv": None, "vendor": "VND-PRIME", "po": "PO-2026-004", "amt": Decimal("5000.00"), "status": "settled", "days_ago": 21},
            {"inv": None, "vendor": "VND-EASTERN", "po": "PO-2026-005", "amt": Decimal("1000.00"), "status": "settled", "days_ago": 11},
            {"inv": None, "vendor": "VND-GLOBAL", "po": "PO-2026-006", "amt": Decimal("500.00"), "status": "settled", "days_ago": 17},
            {"inv": None, "vendor": "VND-VERTEX", "po": "PO-2026-007", "amt": Decimal("4000.00"), "status": "settled", "days_ago": 9},
            {"inv": None, "vendor": "VND-APEX", "po": "PO-2026-008", "amt": Decimal("2000.00"), "status": "settled", "days_ago": 7},
            {"inv": None, "vendor": "VND-NOVA", "po": "PO-2026-009", "amt": Decimal("3000.00"), "status": "settled", "days_ago": 6},
            {"inv": None, "vendor": "VND-PRIME", "po": "PO-2026-010", "amt": Decimal("1500.00"), "status": "settled", "days_ago": 13},
            {"inv": None, "vendor": "VND-EASTERN", "po": "PO-2026-011", "amt": Decimal("800.00"), "status": "settled", "days_ago": 4},
            {"inv": None, "vendor": "VND-GLOBAL", "po": "PO-2026-012", "amt": Decimal("2000.00"), "status": "settled", "days_ago": 5}
        ]

        for tx_idx, t in enumerate(tx_data):
            inv = invoices.get(f"{t['inv']}_{t['vendor']}") if t["inv"] else None
            po = pos[t["po"]] if t["po"] else None
            
            transaction = models.Transaction(
                invoice_id=inv.id if inv else None,
                po_id=po.id if po else None,
                amount=t["amt"],
                currency="USD",
                status=t["status"],
                transaction_date=datetime.utcnow() - timedelta(days=t["days_ago"])
            )
            db.add(transaction)
        db.flush()

        # 9. Seed Intended Exceptions with Evidence & Audit Logs
        print("Seeding Case 1 Exception (Duplicate)...")
        # Duplicate exception for inv1_dup
        inv_dup = invoices["INV-2026-001_VND-APEX"] # This is the second INV-2026-001 with 'exception' status
        exc1 = models.Exception(
            type="DUPLICATE_INVOICE",
            status="AUTO_RESOLVED", # Seed as auto resolved for Case 1
            severity="LOW",
            confidence=0.96,
            risk="LOW",
            invoice_id=inv_dup.id,
            po_id=pos["PO-2026-001"].id,
            created_at=datetime.utcnow() - timedelta(hours=6)
        )
        db.add(exc1)
        db.flush()

        ev1_1 = models.Evidence(
            exception_id=exc1.id,
            source="Invoice Database",
            field="Invoice Number",
            value="INV-2026-001",
            explanation="Invoice number 'INV-2026-001' already exists from vendor 'Apex Industrial Supplies' and has been paid.",
            fact_type="VERIFIED_FACT"
        )
        ev1_2 = models.Evidence(
            exception_id=exc1.id,
            source="Invoice Database",
            field="Amount Comparison",
            value="$4,536.00",
            explanation="The billed total amount is identical to already paid invoice INV-2026-001.",
            fact_type="VERIFIED_FACT"
        )
        db.add_all([ev1_1, ev1_2])

        # Write AI Investigation for Case 1
        inv_report1 = models.Investigation(
            exception_id=exc1.id,
            finding="Duplicate billing attempt for warehouse equipment purchase PO-2026-001.",
            recommendation="AUTO_RESOLVE",
            confidence=0.96,
            risk="LOW",
            reason="Verified duplicate invoice number and total amount against settled transaction TX1. Automated rules decline duplicate submissions to prevent double disbursement.",
            created_at=datetime.utcnow() - timedelta(hours=5, minutes=58)
        )
        db.add(inv_report1)

        # Audit Logs for Case 1
        audit1_1 = models.AuditEvent(
            exception_id=exc1.id,
            actor_id=None,
            event="EXCEPTION_DETECTED",
            previous_status=None,
            new_status="NEW",
            reason="Deterministic AP scanner discovered matching invoice number, vendor, and amount.",
            timestamp=datetime.utcnow() - timedelta(hours=6)
        )
        audit1_2 = models.AuditEvent(
            exception_id=exc1.id,
            actor_id=None,
            event="AUTO_RESOLUTION_RUN",
            previous_status="NEW",
            new_status="AUTO_RESOLVED",
            reason="System evaluated AI confidence (0.96) >= 0.90, risk is LOW, and verified duplication. Decline invoice processed.",
            timestamp=datetime.utcnow() - timedelta(hours=5, minutes=57)
        )
        db.add_all([audit1_1, audit1_2])

        print("Seeding Case 2 Exception (Amount / Price Mismatch)...")
        # Price mismatch for inv2 (PO 50000, Invoice 55000)
        inv_mismatch = invoices["INV-2026-002_VND-VERTEX"]
        exc2 = models.Exception(
            type="AMOUNT_PRICE_MISMATCH",
            status="NEW",
            severity="MEDIUM",
            confidence=0.85,
            risk="MEDIUM",
            invoice_id=inv_mismatch.id,
            po_id=pos["PO-2026-002"].id,
            created_at=datetime.utcnow() - timedelta(hours=12)
        )
        db.add(exc2)
        db.flush()

        ev2_1 = models.Evidence(
            exception_id=exc2.id,
            source="Comparison Service",
            field="Total Amount",
            value="Invoice: $55,000.00 vs PO: $50,000.00",
            explanation="The total billed amount exceeds PO authorized limit by $5,000.00 (10% variance).",
            fact_type="VERIFIED_FACT"
        )
        ev2_2 = models.Evidence(
            exception_id=exc2.id,
            source="Line Item Comparer",
            field="Unit Price (Cloud Infrastructure Compute Units)",
            value="Invoice: $110.00 vs PO: $100.00",
            explanation="The unit rate charged ($110.00) is $10.00 higher than PO authorized rate ($100.00).",
            fact_type="VERIFIED_FACT"
        )
        db.add_all([ev2_1, ev2_2])

        audit2_1 = models.AuditEvent(
            exception_id=exc2.id,
            actor_id=None,
            event="EXCEPTION_DETECTED",
            previous_status=None,
            new_status="NEW",
            reason="Amount price mismatch flagged. Invoice rate exceeds PO rate.",
            timestamp=datetime.utcnow() - timedelta(hours=12)
        )
        db.add(audit2_1)

        print("Seeding Case 3 Exception (Escalation / Missing PO)...")
        # Missing PO for inv3 (Global Services, 65000.00)
        inv_anomaly = invoices["INV-2026-003_VND-GLOBAL"]
        exc3 = models.Exception(
            type="MISSING_PO",
            status="NEW",
            severity="HIGH",
            confidence=0.65,
            risk="HIGH",
            invoice_id=inv_anomaly.id,
            po_id=None,
            created_at=datetime.utcnow() - timedelta(hours=2)
        )
        db.add(exc3)
        db.flush()

        ev3_1 = models.Evidence(
            exception_id=exc3.id,
            source="Invoice File",
            field="PO Number Reference",
            value="Missing / Null",
            explanation="No purchase order reference matches this invoice sheet or was provided in metadata.",
            fact_type="VERIFIED_FACT"
        )
        ev3_2 = models.Evidence(
            exception_id=exc3.id,
            source="Financial Policy Checker",
            field="High Value Threshold",
            value="$70,200.00",
            explanation="Invoice total exceeds high risk policy limit ($50,000.00) by $20,200.00.",
            fact_type="VERIFIED_FACT"
        )
        db.add_all([ev3_1, ev3_2])

        audit3_1 = models.AuditEvent(
            exception_id=exc3.id,
            actor_id=None,
            event="EXCEPTION_DETECTED",
            previous_status=None,
            new_status="NEW",
            reason="Missing purchase order reference detected on a high-value invoice.",
            timestamp=datetime.utcnow() - timedelta(hours=2)
        )
        db.add(audit3_1)

        # Seeding Case 4 Exception (Tax Anomaly)
        inv_tax = invoices["INV-2026-004_VND-APEX"]
        exc4 = models.Exception(
            type="TAX_ANOMALY",
            status="NEW",
            severity="LOW",
            confidence=0.90,
            risk="LOW",
            invoice_id=inv_tax.id,
            po_id=pos["PO-2026-001"].id,
            created_at=datetime.utcnow() - timedelta(hours=24)
        )
        db.add(exc4)
        db.flush()

        ev4_1 = models.Evidence(
            exception_id=exc4.id,
            source="Tax Registry Rule",
            field="Expected Tax Rate",
            value="8.0%",
            explanation="Calculated tax should be $336.00 based on standard regional rate of 8%.",
            fact_type="VERIFIED_FACT"
        )
        ev4_2 = models.Evidence(
            exception_id=exc4.id,
            source="Invoice File",
            field="Billed Tax Amount",
            value="$150.00",
            explanation="The billed tax amount of $150.00 deviates from regional rules by $186.00.",
            fact_type="VERIFIED_FACT"
        )
        db.add_all([ev4_1, ev4_2])

        audit4_1 = models.AuditEvent(
            exception_id=exc4.id,
            actor_id=None,
            event="EXCEPTION_DETECTED",
            previous_status=None,
            new_status="NEW",
            reason="Billed tax amount deviates from calculated expectation.",
            timestamp=datetime.utcnow() - timedelta(hours=24)
        )
        db.add(audit4_1)

        # Seeding Case 5 Exception (Missing PO - Low Value)
        inv_mpo_low = invoices["INV-2026-018_VND-VERTEX"]
        exc5 = models.Exception(
            type="MISSING_PO",
            status="NEW",
            severity="MEDIUM",
            confidence=0.80,
            risk="LOW",
            invoice_id=inv_mpo_low.id,
            po_id=None,
            created_at=datetime.utcnow() - timedelta(hours=18)
        )
        db.add(exc5)
        db.flush()

        ev5_1 = models.Evidence(
            exception_id=exc5.id,
            source="Invoice File",
            field="PO Number Reference",
            value="Missing / Null",
            explanation="No purchase order reference matches this invoice sheet or was provided in metadata.",
            fact_type="VERIFIED_FACT"
        )
        db.add_all([ev5_1])

        audit5_1 = models.AuditEvent(
            exception_id=exc5.id,
            actor_id=None,
            event="EXCEPTION_DETECTED",
            previous_status=None,
            new_status="NEW",
            reason="Missing purchase order reference detected.",
            timestamp=datetime.utcnow() - timedelta(hours=18)
        )
        db.add(audit5_1)

        db.commit()
        print("Database synthetic enterprise records seeded successfully!")
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    seed_db()
