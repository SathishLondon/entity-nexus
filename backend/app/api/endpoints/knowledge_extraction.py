"""
Knowledge Extraction API Endpoints
"""

import os
import shutil
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from app.core.database import get_db
from app.services.knowledge_extraction_service import KnowledgeExtractionService
from app.services.reference_service import ReferenceService

router = APIRouter()

# Pydantic models
class DocumentUploadResponse(BaseModel):
    id: str
    filename: str
    file_type: str
    status: str
    uploaded_at: str
    entities_count: Optional[int] = None
    nuances_count: Optional[int] = None
    recommendations_count: Optional[int] = None

class RecommendationResponse(BaseModel):
    id: str
    document_id: str
    note_type: str
    title: str
    content: str
    severity: str
    tags: List[str]
    module_id: Optional[str]
    field_path: Optional[str]
    confidence: float
    source_excerpt: str
    reasoning: str
    status: str
    reviewed_by: Optional[str]
    reviewed_at: Optional[str]

class RecommendationUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[List[str]] = None
    severity: Optional[str] = None
    module_id: Optional[str] = None
    field_path: Optional[str] = None

class ApprovalResponse(BaseModel):
    status: str
    note_id: int
    recommendation_id: str

class RejectionRequest(BaseModel):
    reason: str


@router.post("/extract/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload a document for knowledge extraction.
    Supports: TXT, MD, DOCX, PDF, EML
    """
    # Validate file type
    allowed_extensions = {'.txt', '.md', '.docx', '.pdf', '.eml', '.msg'}
    file_ext = os.path.splitext(file.filename)[1].lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file_ext}. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # Save uploaded file
    upload_dir = "uploads/knowledge_extraction"
    os.makedirs(upload_dir, exist_ok=True)
    
    file_path = os.path.join(upload_dir, file.filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Process document
    extraction_service = KnowledgeExtractionService(db)

    
    result = extraction_service.process_document(
        file_path=file_path,
        filename=file.filename
    )
    
    # Get document details
    doc = extraction_service.get_document(result["document_id"])
    
    return DocumentUploadResponse(
        id=str(doc.id),
        filename=doc.filename,
        file_type=doc.file_type,
        status=doc.status,
        uploaded_at=doc.uploaded_at.isoformat(),
        entities_count=result.get("entities_count"),
        nuances_count=result.get("nuances_count"),
        recommendations_count=result.get("recommendations_count")
    )


@router.get("/extract/documents", response_model=List[DocumentUploadResponse])
def list_documents(db: Session = Depends(get_db)):
    """List all uploaded documents"""
    extraction_service = KnowledgeExtractionService(db)
    
    documents = extraction_service.get_all_documents()
    
    return [
        DocumentUploadResponse(
            id=str(doc.id),
            filename=doc.filename,
            file_type=doc.file_type,
            status=doc.status,
            uploaded_at=doc.uploaded_at.isoformat(),
            entities_count=doc.extra_data.get("entities_count") if doc.extra_data else None,
            nuances_count=doc.extra_data.get("nuances_count") if doc.extra_data else None,
            recommendations_count=doc.extra_data.get("recommendations_count") if doc.extra_data else None
        )
        for doc in documents
    ]


@router.get("/extract/documents/{document_id}", response_model=DocumentUploadResponse)
def get_document(document_id: str, db: Session = Depends(get_db)):
    """Get document details"""
    extraction_service = KnowledgeExtractionService(db)
    
    doc = extraction_service.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return DocumentUploadResponse(
        id=str(doc.id),
        filename=doc.filename,
        file_type=doc.file_type,
        status=doc.status,
        uploaded_at=doc.uploaded_at.isoformat(),
        entities_count=doc.extra_data.get("entities_count") if doc.extra_data else None,
        nuances_count=doc.extra_data.get("nuances_count") if doc.extra_data else None,
        recommendations_count=doc.extra_data.get("recommendations_count") if doc.extra_data else None
    )


@router.get("/extract/documents/{document_id}/recommendations", response_model=List[RecommendationResponse])
def get_recommendations(document_id: str, db: Session = Depends(get_db)):
    """Get all recommendations for a document"""
    extraction_service = KnowledgeExtractionService(db)
    
    recommendations = extraction_service.get_recommendations(document_id)
    
    return [
        RecommendationResponse(
            id=str(rec.id),
            document_id=str(rec.document_id),
            note_type=rec.note_type,
            title=rec.title,
            content=rec.content,
            severity=rec.severity,
            tags=rec.tags or [],
            module_id=rec.module_id,
            field_path=rec.field_path,
            confidence=rec.confidence,
            source_excerpt=rec.source_excerpt,
            reasoning=rec.reasoning,
            status=rec.status,
            reviewed_by=rec.reviewed_by,
            reviewed_at=rec.reviewed_at.isoformat() if rec.reviewed_at else None
        )
        for rec in recommendations
    ]


@router.post("/extract/recommendations/{rec_id}/approve", response_model=ApprovalResponse)
def approve_recommendation(rec_id: str, db: Session = Depends(get_db)):
    """Approve a recommendation and create knowledge note"""
    extraction_service = KnowledgeExtractionService(db)
    
    try:
        result = extraction_service.approve_recommendation(rec_id)
        return ApprovalResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/extract/recommendations/{rec_id}/reject")
def reject_recommendation(
    rec_id: str,
    rejection: RejectionRequest,
    db: Session = Depends(get_db)
):
    """Reject a recommendation with feedback"""
    extraction_service = KnowledgeExtractionService(db)
    
    try:
        result = extraction_service.reject_recommendation(rec_id, rejection.reason)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/extract/recommendations/{rec_id}/edit", response_model=RecommendationResponse)
def edit_recommendation(
    rec_id: str,
    updates: RecommendationUpdate,
    db: Session = Depends(get_db)
):
    """Edit a recommendation before approval"""
    extraction_service = KnowledgeExtractionService(db)
    
    try:
        rec = extraction_service.edit_recommendation(rec_id, updates.dict(exclude_unset=True))
        
        return RecommendationResponse(
            id=str(rec.id),
            document_id=str(rec.document_id),
            note_type=rec.note_type,
            title=rec.title,
            content=rec.content,
            severity=rec.severity,
            tags=rec.tags or [],
            module_id=rec.module_id,
            field_path=rec.field_path,
            confidence=rec.confidence,
            source_excerpt=rec.source_excerpt,
            reasoning=rec.reasoning,
            status=rec.status,
            reviewed_by=rec.reviewed_by,
            reviewed_at=rec.reviewed_at.isoformat() if rec.reviewed_at else None
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
