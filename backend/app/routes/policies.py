from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app import models, schemas, auth
from app.engine import PolicyEngine

router = APIRouter(prefix="", tags=["policies"])

@router.get("/policies", response_model=List[schemas.PolicyResponse])
def list_policies(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    policies = db.query(models.Policy).all()
    # If no policies in DB yet, return synthetic demo policies
    if not policies:
        return [
            {
                "id": "pol-001",
                "name": "Low-Risk Auto Resolution Policy v1",
                "version": 1,
                "priority": 10,
                "is_active": True,
                "decision": "AUTO_RESOLVE",
                "rules": {
                    "confidence_min": 0.90,
                    "risk_allowed": "LOW",
                    "max_financial_amount": 10000.00
                },
                "description": "Auto-resolves high-confidence low-risk transaction discrepancies under $10,000.",
                "created_at": "2026-08-22T00:00:00",
                "updated_at": "2026-08-22T00:00:00"
            },
            {
                "id": "pol-002",
                "name": "Standard Human Review Policy v1",
                "version": 1,
                "priority": 20,
                "is_active": True,
                "decision": "HUMAN_REVIEW",
                "rules": {
                    "confidence_min": 0.70,
                    "confidence_max": 0.89,
                    "risk_allowed": "MEDIUM",
                    "max_financial_amount": 50000.00
                },
                "description": "Routes moderate risk or confidence cases between 0.70 and 0.89 to human reviewers.",
                "created_at": "2026-08-22T00:00:00",
                "updated_at": "2026-08-22T00:00:00"
            },
            {
                "id": "pol-003",
                "name": "High Risk Escalation Policy v1",
                "version": 1,
                "priority": 30,
                "is_active": True,
                "decision": "ESCALATE",
                "rules": {
                    "confidence_max": 0.69,
                    "risk_allowed": "HIGH",
                    "require_missing_po_escalation": True
                },
                "description": "Escalates high-risk anomalies, low-confidence findings, or missing PO references.",
                "created_at": "2026-08-22T00:00:00",
                "updated_at": "2026-08-22T00:00:00"
            }
        ]
    return policies

@router.get("/policies/{id}", response_model=schemas.PolicyResponse)
def get_policy_detail(
    id: str,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    policy = db.query(models.Policy).filter(models.Policy.id == id).first()
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Policy not found"
        )
    return policy

@router.post("/exceptions/{id}/evaluate-policy", response_model=schemas.PolicyDecisionResponse)
def evaluate_exception_policy(
    id: str,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    exc = db.query(models.Exception).filter(models.Exception.id == id).first()
    if not exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exception not found"
        )
        
    # Audit Event: POLICY_EVALUATION_STARTED
    audit_start = models.AuditEvent(
        exception_id=exc.id,
        actor_id=current_user.id,
        event="POLICY_EVALUATION_STARTED",
        previous_status=exc.status,
        new_status=exc.status,
        reason=f"Policy decision engine evaluation triggered by {current_user.name}."
    )
    db.add(audit_start)
    db.commit()

    # Get latest investigation if any
    latest_inv = db.query(models.Investigation).filter(models.Investigation.exception_id == exc.id).order_by(models.Investigation.created_at.desc()).first()
    
    # Run deterministic PolicyEngine
    engine = PolicyEngine()
    result = engine.evaluate(db, exc, latest_inv)
    
    # Persist PolicyDecision (Without mutating exception status)
    policy_decision = models.PolicyDecision(
        exception_id=exc.id,
        organization_id=current_user.organization_id,
        investigation_id=latest_inv.id if latest_inv else None,
        policy_name=result["policy_name"],
        policy_version=result["policy_version"],
        decision=result["decision"],
        ai_confidence=result["ai_confidence"],
        risk=result["risk"],
        financial_impact=result["financial_impact"],
        evidence_complete=result["evidence_complete"],
        evaluated_conditions=result["evaluated_conditions"],
        reasons=result["reasons"]
    )
    db.add(policy_decision)
    
    # Audit Event: POLICY_EVALUATION_COMPLETED
    audit_comp = models.AuditEvent(
        exception_id=exc.id,
        actor_id=current_user.id,
        event="POLICY_EVALUATION_COMPLETED",
        previous_status=exc.status,
        new_status=exc.status,
        reason=f"Policy decision calculated: {result['decision']} under policy '{result['policy_name']}'. Reasons: {', '.join(result['reasons'])}",
        meta_data={"decision": result["decision"], "policy_name": result["policy_name"]}
    )
    db.add(audit_comp)
    
    db.commit()
    db.refresh(policy_decision)
    return policy_decision

@router.get("/exceptions/{id}/decision", response_model=schemas.PolicyDecisionResponse)
def get_latest_policy_decision(
    id: str,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    decision = db.query(models.PolicyDecision).filter(models.PolicyDecision.exception_id == id).order_by(models.PolicyDecision.created_at.desc()).first()
    if not decision:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No policy decision evaluated yet for this exception case."
        )
    return decision
