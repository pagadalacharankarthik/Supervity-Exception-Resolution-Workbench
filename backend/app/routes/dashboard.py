from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta

from app.database import get_db
from app import models, schemas, auth

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/stats", response_model=schemas.DashboardStats)
def get_stats(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    # Total exceptions
    total = db.query(models.Exception).count()
    
    # Open exceptions
    open_cases = db.query(models.Exception).filter(
        models.Exception.status.in_(["OPEN", "UNDER_REVIEW", "NEW", "INVESTIGATING"])
    ).count()
    
    # High-risk exceptions
    high_risk = db.query(models.Exception).filter(
        models.Exception.status.in_(["OPEN", "UNDER_REVIEW", "NEW", "INVESTIGATING"]),
        models.Exception.risk == "HIGH"
    ).count()
    
    # AI-resolvable (either auto-resolved already, or OPEN/UNDER_REVIEW/NEW with confidence >= 0.90 and risk == LOW)
    ai_resolvable = db.query(models.Exception).filter(
        (models.Exception.status == "AUTO_RESOLVED") | 
        (
            models.Exception.status.in_(["OPEN", "UNDER_REVIEW", "NEW", "INVESTIGATING"]) & 
            (models.Exception.confidence >= 0.90) & 
            (models.Exception.risk == "LOW")
        )
    ).count()
    
    # Resolved exceptions (closed statuses)
    resolved = db.query(models.Exception).filter(
        models.Exception.status.in_(["AUTO_RESOLVED", "RESOLVED", "REJECTED", "FALSE_POSITIVE"])
    ).count()
    
    return {
        "total_exceptions": total,
        "open_exceptions": open_cases,
        "high_risk_exceptions": high_risk,
        "ai_resolvable_exceptions": ai_resolvable,
        "resolved_exceptions": resolved
    }

@router.get("/analytics", response_model=schemas.DashboardAnalytics)
def get_analytics(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    # Exception Type distribution
    type_counts = db.query(models.Exception.type, func.count(models.Exception.id)).group_by(models.Exception.type).all()
    type_dist = {t: c for t, c in type_counts}
    
    # Severity distribution
    severity_counts = db.query(models.Exception.severity, func.count(models.Exception.id)).group_by(models.Exception.severity).all()
    severity_dist = {s: c for s, c in severity_counts}
    
    # Status distribution
    status_counts = db.query(models.Exception.status, func.count(models.Exception.id)).group_by(models.Exception.status).all()
    status_dist = {st: c for st, c in status_counts}
    
    return {
        "type_distribution": type_dist,
        "severity_distribution": severity_dist,
        "status_distribution": status_dist
    }

@router.get("/trend", response_model=schemas.DashboardTrend)
def get_trend(
    current_user: models.User = Depends(auth.get_current_manager),
    db: Session = Depends(get_db)
):
    # Return trend of exceptions for the last 7 days
    points = []
    today = datetime.utcnow().date()
    
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        day_str = day.strftime("%b %d")
        
        # Count exceptions created on this day
        count = db.query(models.Exception).filter(
            func.date(models.Exception.created_at) == day
        ).count()
        
        points.append({"date": day_str, "count": count})
        
    return {"points": points}
