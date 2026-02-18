from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.knowledge_enrichment_service import KnowledgeEnrichmentService

router = APIRouter()

class KnowledgeNoteCreate(BaseModel):
    module_id: Optional[str] = None
    field_path: Optional[str] = None
    note_type: str  # comparison, nuance, gotcha, best_practice
    title: str
    content: str
    tags: List[str] = []
    severity: str = "info"  # info, warning, critical
    created_by: str = "user"
    metadata: Dict[str, Any] = {}

class KnowledgeNoteUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[List[str]] = None
    severity: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class KnowledgeNoteResponse(BaseModel):
    id: int
    module_id: Optional[str]
    field_path: Optional[str]
    note_type: str
    title: str
    content: str
    tags: List[str]
    severity: str
    created_by: str
    created_at: Any
    updated_at: Any
    metadata: Dict[str, Any]
    
    class Config:
        from_attributes = True

@router.post("/notes", response_model=KnowledgeNoteResponse)
def create_note(note: KnowledgeNoteCreate, db: Session = Depends(get_db)):
    """Create a new knowledge note"""
    service = KnowledgeEnrichmentService(db)
    
    created_note = service.add_note(
        title=note.title,
        content=note.content,
        note_type=note.note_type,
        module_id=note.module_id,
        field_path=note.field_path,
        tags=note.tags,
        severity=note.severity,
        created_by=note.created_by,
        extra_data=note.metadata
    )
    
    return created_note

@router.get("/notes", response_model=List[KnowledgeNoteResponse])
def list_notes(db: Session = Depends(get_db)):
    """List all knowledge notes"""
    service = KnowledgeEnrichmentService(db)
    return service.get_all_notes()

@router.get("/notes/{note_id}", response_model=KnowledgeNoteResponse)
def get_note(note_id: int, db: Session = Depends(get_db)):
    """Get a specific knowledge note"""
    service = KnowledgeEnrichmentService(db)
    note = service.get_note(note_id)
    
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    return note

@router.put("/notes/{note_id}", response_model=KnowledgeNoteResponse)
def update_note(note_id: int, update: KnowledgeNoteUpdate, db: Session = Depends(get_db)):
    """Update a knowledge note"""
    service = KnowledgeEnrichmentService(db)
    
    updated_note = service.update_note(
        note_id=note_id,
        title=update.title,
        content=update.content,
        tags=update.tags,
        severity=update.severity,
        extra_data=update.metadata
    )
    
    if not updated_note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    return updated_note

@router.delete("/notes/{note_id}")
def delete_note(note_id: int, db: Session = Depends(get_db)):
    """Delete a knowledge note"""
    service = KnowledgeEnrichmentService(db)
    
    if not service.delete_note(note_id):
        raise HTTPException(status_code=404, detail="Note not found")
    
    return {"message": "Note deleted successfully"}

@router.get("/notes/module/{module_id}", response_model=List[KnowledgeNoteResponse])
def get_notes_for_module(module_id: str, db: Session = Depends(get_db)):
    """Get all notes for a specific module"""
    service = KnowledgeEnrichmentService(db)
    return service.get_notes_for_module(module_id)

@router.get("/notes/search", response_model=List[KnowledgeNoteResponse])
def search_notes(
    query: Optional[str] = None,
    tags: Optional[str] = None,  # Comma-separated
    note_type: Optional[str] = None,
    severity: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Search knowledge notes"""
    service = KnowledgeEnrichmentService(db)
    
    tag_list = tags.split(",") if tags else None
    
    return service.search_notes(
        query=query,
        tags=tag_list,
        note_type=note_type,
        severity=severity
    )

@router.post("/notes/seed")
def seed_notes(db: Session = Depends(get_db)):
    """Seed initial knowledge notes (admin only)"""
    service = KnowledgeEnrichmentService(db)
    service.seed_initial_notes()
    return {"message": "Initial notes seeded successfully"}
