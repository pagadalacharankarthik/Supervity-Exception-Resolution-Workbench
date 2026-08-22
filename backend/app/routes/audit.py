from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload
from typing import List

from app.database import get_db
from app import models, schemas, auth

router = APIRouter(prefix="/audit", tags=["audit"])

@router.get("/logs", response_model=List[schemas.AuditEventResponse])
def get_global_audit_logs(
    current_user: models.User = Depends(auth.get_current_manager), # Manager role only
    db: Session = Depends(get_db)
):
    audit_events = db.query(models.AuditEvent).options(
        joinedload(models.AuditEvent.actor)
    ).order_by(models.AuditEvent.timestamp.desc()).all()
    
    result = []
    for audit in audit_events:
        result.append({
            "id": audit.id,
            "actor_id": audit.actor_id,
            "actor_name": audit.actor.name if audit.actor else "System",
            "event": audit.event,
            "previous_status": audit.previous_status,
            "new_status": audit.new_status,
            "reason": audit.reason,
            "meta_data": audit.meta_data,
            "timestamp": audit.timestamp
        })
        
    return result
