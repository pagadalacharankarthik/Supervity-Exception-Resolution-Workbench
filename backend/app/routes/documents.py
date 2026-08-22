from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import shutil
import uuid
from datetime import datetime

from app.database import get_db
from app import models, schemas, auth
from app.document_processor import document_processor

router = APIRouter(prefix="/documents", tags=["documents"])

STORAGE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "storage", "documents")
os.makedirs(STORAGE_DIR, exist_ok=True)

ALLOWED_MIME_TYPES = ["application/pdf", "image/png", "image/jpeg", "image/jpg"]
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB limit

@router.post("/upload", response_model=schemas.DocumentResponse)
def upload_document(
    file: UploadFile = File(...),
    document_type: Optional[str] = Form("INVOICE"),
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{file.content_type}'. Allowed types: PDF, PNG, JPG."
        )

    # Save file safely to storage directory
    doc_id = str(uuid.uuid4())
    safe_filename = f"{doc_id}_{file.filename}"
    file_path = os.path.join(STORAGE_DIR, safe_filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    file_size = os.path.getsize(file_path)
    if file_size > MAX_FILE_SIZE:
        os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds maximum 10MB limit."
        )

    # Create Document record
    doc = models.Document(
        id=doc_id,
        organization_id=current_user.organization_id,
        file_name=file.filename,
        content_type=file.content_type,
        file_size=file_size,
        storage_reference=file_path,
        document_type=document_type or "INVOICE",
        processing_status="UPLOADED",
        uploaded_by_id=current_user.id
    )
    db.add(doc)
    db.commit()

    # Process extraction
    processed_doc = document_processor.process_document(db, doc)
    return processed_doc

@router.get("", response_model=List[schemas.DocumentResponse])
def list_documents(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    docs = db.query(models.Document).filter(
        models.Document.organization_id == current_user.organization_id
    ).order_by(models.Document.created_at.desc()).all()
    return docs

@router.get("/{id}", response_model=schemas.DocumentResponse)
def get_document_detail(
    id: str,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    doc = db.query(models.Document).filter(models.Document.id == id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return doc

@router.get("/{id}/preview")
def preview_document(
    id: str,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    doc = db.query(models.Document).filter(models.Document.id == id).first()
    if not doc or not os.path.exists(doc.storage_reference):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document preview file not found")
    return FileResponse(path=doc.storage_reference, media_type=doc.content_type, filename=doc.file_name)

@router.post("/{id}/fields/{field_id}/verify", response_model=schemas.DocumentFieldResponse)
def verify_document_field(
    id: str,
    field_id: str,
    current_user: models.User = Depends(auth.get_current_reviewer),
    db: Session = Depends(get_db)
):
    field = db.query(models.DocumentField).filter(
        models.DocumentField.id == field_id,
        models.DocumentField.document_id == id
    ).first()
    if not field:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document field not found")

    old_status = field.verification_status
    field.verification_status = "VERIFIED"

    history = models.DocumentFieldHistory(
        field_id=field.id,
        old_value=field.extracted_value,
        new_value=field.extracted_value,
        action="VERIFY",
        actor_id=current_user.id,
        reason=f"Field verified by reviewer {current_user.name}."
    )
    db.add(history)
    db.commit()
    db.refresh(field)
    return field

@router.post("/{id}/fields/{field_id}/edit", response_model=schemas.DocumentFieldResponse)
def edit_document_field(
    id: str,
    field_id: str,
    request: schemas.DocumentFieldEditRequest,
    current_user: models.User = Depends(auth.get_current_reviewer),
    db: Session = Depends(get_db)
):
    field = db.query(models.DocumentField).filter(
        models.DocumentField.id == field_id,
        models.DocumentField.document_id == id
    ).first()
    if not field:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document field not found")

    old_val = field.extracted_value
    field.extracted_value = request.new_value
    field.normalized_value = request.new_value.replace("$", "").replace(",", "")
    field.verification_status = "EDITED"

    history = models.DocumentFieldHistory(
        field_id=field.id,
        old_value=old_val,
        new_value=request.new_value,
        action="EDIT",
        actor_id=current_user.id,
        reason=request.reason or f"Manually edited by reviewer {current_user.name}."
    )
    db.add(history)
    db.commit()
    db.refresh(field)
    return field

@router.post("/{id}/fields/{field_id}/flag", response_model=schemas.DocumentFieldResponse)
def flag_document_field(
    id: str,
    field_id: str,
    current_user: models.User = Depends(auth.get_current_reviewer),
    db: Session = Depends(get_db)
):
    field = db.query(models.DocumentField).filter(
        models.DocumentField.id == field_id,
        models.DocumentField.document_id == id
    ).first()
    if not field:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document field not found")

    field.verification_status = "FLAGGED"

    history = models.DocumentFieldHistory(
        field_id=field.id,
        old_value=field.extracted_value,
        new_value=field.extracted_value,
        action="FLAG",
        actor_id=current_user.id,
        reason=f"Flagged for review by {current_user.name}."
    )
    db.add(history)
    db.commit()
    db.refresh(field)
    return field

@router.post("/{id}/verify", response_model=schemas.DocumentResponse)
def verify_entire_document(
    id: str,
    current_user: models.User = Depends(auth.get_current_reviewer),
    db: Session = Depends(get_db)
):
    doc = db.query(models.Document).filter(models.Document.id == id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    doc.processing_status = "VERIFIED"
    for f in doc.fields:
        if f.verification_status == "UNVERIFIED":
            f.verification_status = "VERIFIED"

    # Feed verified document evidence into existing exceptions matching invoice number
    inv_num_field = next((f for f in doc.fields if f.field_name == "invoice_number"), None)
    if inv_num_field and inv_num_field.extracted_value:
        inv_num = inv_num_field.extracted_value
        invoices = db.query(models.Invoice).filter(models.Invoice.invoice_number == inv_num).all()
        for inv in invoices:
            for exc in inv.exceptions:
                for f in doc.fields:
                    db.add(models.Evidence(
                        exception_id=exc.id,
                        source=f"DOCUMENT:{doc.file_name}",
                        field=f.field_name,
                        value=str(f.extracted_value),
                        explanation=f"Verified document extraction (Confidence: {f.confidence_level})",
                        fact_type="VERIFIED_FACT"
                    ))

    db.commit()
    db.refresh(doc)
    return doc
