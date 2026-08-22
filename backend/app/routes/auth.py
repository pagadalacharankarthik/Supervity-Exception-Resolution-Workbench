from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas, auth

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login", response_model=schemas.Token)
def login(request: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == request.email).first()
    if not user or not auth.verify_password(request.password, user.hashed_password):
        # Audit failed login
        audit = models.AuditEvent(
            actor_id=None,
            event="LOGIN_FAILED",
            reason=f"Failed login attempt for email: {request.email}"
        )
        db.add(audit)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Audit successful login
    audit = models.AuditEvent(
        actor_id=user.id,
        event="LOGIN_SUCCESS",
        reason=f"User {user.email} logged in successfully."
    )
    db.add(audit)
    db.commit()
    
    # Create access token with user details
    access_token = auth.create_access_token(
        data={"email": user.email, "role": user.role, "user_id": user.id}
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "role": user.role
        }
    }

@router.get("/me", response_model=schemas.UserResponse)
def get_me(current_user: models.User = Depends(auth.get_current_user)):
    return current_user

@router.post("/logout")
def logout(current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    # Audit logout
    audit = models.AuditEvent(
        actor_id=current_user.id,
        event="LOGOUT",
        reason=f"User {current_user.email} logged out."
    )
    db.add(audit)
    db.commit()
    return {"success": True}
