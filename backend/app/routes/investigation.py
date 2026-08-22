from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.database import get_db
from app import models, schemas, auth, ai

router = APIRouter(prefix="/exceptions", tags=["investigation"])

class ChatRequest(BaseModel):
    messages: List[Dict[str, Any]]
    user_message: str

class ResolutionActionRequest(BaseModel):
    reason: str
    target: Optional[str] = None

@router.post("/{id}/investigate", response_model=schemas.InvestigationResponse)
def investigate_exception(
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
        
    audit_start = models.AuditEvent(
        exception_id=exc.id,
        actor_id=current_user.id,
        event="AI_INVESTIGATION_STARTED",
        previous_status=exc.status,
        new_status="UNDER_REVIEW",
        reason=f"AI Investigation initiated by {current_user.name}."
    )
    db.add(audit_start)
    db.commit()

    ai_result = ai.run_ai_investigation(db, exc)
    
    finding = ai_result.get("finding", "Audit completed.")
    recommendation = ai_result.get("recommendation", "REVIEW")
    confidence = ai_result.get("confidence", 0.75)
    risk = ai_result.get("risk", "MEDIUM")
    reason = ai_result.get("reason", "Evidence package analyzed.")
    
    exc.confidence = confidence
    exc.risk = risk
    prev_status = exc.status
    exc.status = "UNDER_REVIEW"
    
    for ev in ai_result.get("evidence", []):
        db_ev = models.Evidence(
            exception_id=exc.id,
            source=ev.get("source_id", "AI Engine"),
            field=ev.get("field", "Investigation Fact"),
            value=str(ev.get("observed_value", "")),
            explanation=ev.get("significance", ""),
            fact_type="AI_INTERPRETATION"
        )
        db.add(db_ev)
        
    investigation = models.Investigation(
        exception_id=exc.id,
        finding=finding,
        recommendation=recommendation,
        confidence=confidence,
        risk=risk,
        reason=reason,
        raw_ai_response=ai_result
    )
    db.add(investigation)
    
    audit_comp = models.AuditEvent(
        exception_id=exc.id,
        actor_id=current_user.id,
        event="AI_INVESTIGATION_COMPLETED",
        previous_status=prev_status,
        new_status="UNDER_REVIEW",
        reason=f"AI Investigation completed by {current_user.name}. Recommendation: {recommendation}, Confidence: {confidence:.2f}, Grounding: {ai_result.get('grounding_status', 'GROUNDED')}.",
        meta_data={"finding": finding, "recommendation": recommendation}
    )
    db.add(audit_comp)
    
    db.commit()
    db.refresh(investigation)
    return investigation

@router.post("/{id}/chat")
def chat_exception(
    id: str,
    request: ChatRequest,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    exc = db.query(models.Exception).filter(models.Exception.id == id).first()
    if not exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exception not found"
        )
        
    reply = ai.run_ai_chat(db, exc, request.messages, request.user_message)
    return {"reply": reply}

@router.post("/{id}/auto-resolve")
def auto_resolve_exception(
    id: str,
    current_user: models.User = Depends(auth.get_current_reviewer),
    db: Session = Depends(get_db)
):
    exc = db.query(models.Exception).filter(models.Exception.id == id).first()
    if not exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exception not found")
        
    if exc.status in ["RESOLVED", "REJECTED", "FALSE_POSITIVE"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Exception is already closed ({exc.status}).")
        
    # Safeguard 1: Active investigation exists
    latest_inv = db.query(models.Investigation).filter(models.Investigation.exception_id == exc.id).order_by(models.Investigation.created_at.desc()).first()
    if not latest_inv:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Automatic resolution is not permitted: AI Investigation missing.")
        
    # Safeguard 2: Active PolicyDecision exists and equals AUTO_RESOLVE
    latest_decision = db.query(models.PolicyDecision).filter(models.PolicyDecision.exception_id == exc.id).order_by(models.PolicyDecision.created_at.desc()).first()
    if not latest_decision or latest_decision.decision != "AUTO_RESOLVE":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Automatic resolution is not permitted: Policy decision does not allow auto-resolution."
        )
        
    prev_status = exc.status
    exc.status = "RESOLVED"
    
    if exc.invoice:
        exc.invoice.status = "matched"
        
    res = models.Resolution(
        exception_id=exc.id,
        organization_id=current_user.organization_id,
        action="AUTO_RESOLVE",
        previous_status=prev_status,
        new_status="RESOLVED",
        actor_type="SYSTEM",
        actor_id=current_user.id,
        comments=f"Controlled Auto-Resolution executed under policy '{latest_decision.policy_name}'. Confidence: {latest_decision.ai_confidence:.2f}.",
        policy_decision_id=latest_decision.id
    )
    db.add(res)
    
    audit = models.AuditEvent(
        exception_id=exc.id,
        actor_id=None,
        event="EXCEPTION_AUTO_RESOLVED",
        previous_status=prev_status,
        new_status="RESOLVED",
        reason=f"Controlled Auto-Resolution executed by System under policy '{latest_decision.policy_name}'.",
        meta_data={"policy_decision_id": latest_decision.id}
    )
    db.add(audit)
    
    db.commit()
    return {
        "exception_id": exc.id,
        "previous_status": prev_status,
        "new_status": "RESOLVED",
        "actor_type": "SYSTEM",
        "policy_decision_id": latest_decision.id,
        "policy_version": latest_decision.policy_version
    }

@router.post("/{id}/resolve", response_model=schemas.ExceptionDetailResponse)
def resolve_exception(
    id: str,
    request: schemas.ResolutionCreate,
    current_user: models.User = Depends(auth.get_current_reviewer),
    db: Session = Depends(get_db)
):
    exc = db.query(models.Exception).filter(models.Exception.id == id).first()
    if not exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exception not found")
        
    if exc.status in ["RESOLVED", "REJECTED", "FALSE_POSITIVE"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Exception is already closed ({exc.status}).")
        
    if not request.comments or not request.comments.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A resolution reason/comment is required.")
        
    status_mapping = {
        "RESOLVE": "RESOLVED",
        "APPROVE": "RESOLVED",
        "REJECT": "REJECTED",
        "ESCALATE": "ESCALATED",
        "FALSE_POSITIVE": "FALSE_POSITIVE"
    }
    
    new_status = status_mapping.get(request.action)
    if not new_status:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid resolution action: {request.action}")
        
    prev_status = exc.status
    exc.status = new_status
    if request.action == "ESCALATE":
        exc.severity = "HIGH"
        
    if exc.invoice:
        if request.action in ["RESOLVE", "APPROVE", "FALSE_POSITIVE"]:
            exc.invoice.status = "matched"
        elif request.action == "REJECT":
            exc.invoice.status = "exception"
            
    res = models.Resolution(
        exception_id=exc.id,
        organization_id=current_user.organization_id,
        action=request.action,
        previous_status=prev_status,
        new_status=new_status,
        actor_type="USER",
        actor_id=current_user.id,
        comments=request.comments
    )
    db.add(res)
    
    audit_event_name = f"EXCEPTION_{request.action}D" if request.action in ["RESOLVE", "REJECT", "ESCALATE"] else "EXCEPTION_MARKED_FALSE_POSITIVE"
    audit = models.AuditEvent(
        exception_id=exc.id,
        actor_id=current_user.id,
        event=audit_event_name,
        previous_status=prev_status,
        new_status=new_status,
        reason=request.comments
    )
    db.add(audit)
    
    db.commit()
    db.flush()
    
    from app.routes.exceptions import get_exception_detail
    return get_exception_detail(id=id, current_user=current_user, db=db)

@router.post("/{id}/reject")
def reject_exception(
    id: str,
    request: ResolutionActionRequest,
    current_user: models.User = Depends(auth.get_current_reviewer),
    db: Session = Depends(get_db)
):
    req = schemas.ResolutionCreate(action="REJECT", comments=request.reason)
    return resolve_exception(id=id, request=req, current_user=current_user, db=db)

@router.post("/{id}/escalate")
def escalate_exception(
    id: str,
    request: ResolutionActionRequest,
    current_user: models.User = Depends(auth.get_current_reviewer),
    db: Session = Depends(get_db)
):
    req = schemas.ResolutionCreate(action="ESCALATE", comments=request.reason)
    return resolve_exception(id=id, request=req, current_user=current_user, db=db)

@router.post("/{id}/false-positive")
def false_positive_exception(
    id: str,
    request: ResolutionActionRequest,
    current_user: models.User = Depends(auth.get_current_reviewer),
    db: Session = Depends(get_db)
):
    req = schemas.ResolutionCreate(action="FALSE_POSITIVE", comments=request.reason)
    return resolve_exception(id=id, request=req, current_user=current_user, db=db)
