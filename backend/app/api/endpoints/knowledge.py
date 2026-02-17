from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel

from app.core.database import get_db
from app.services.knowledge_service import KnowledgeService

router = APIRouter()

# ========== Request/Response Models ==========

class ModuleNoteCreate(BaseModel):
    module_id: str
    note_type: str
    title: str
    content: str
    category: Optional[str] = None
    severity: str = 'info'
    tags: Optional[List[str]] = None
    created_by: Optional[str] = None

class ModuleNoteUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    severity: Optional[str] = None
    tags: Optional[List[str]] = None

class FieldNoteCreate(BaseModel):
    module_id: str
    field_path: str
    note_type: str
    title: str
    content: str
    severity: str = 'info'
    affected_entity_types: Optional[List[str]] = None
    field_name: Optional[str] = None

class FieldNoteUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    severity: Optional[str] = None
    affected_entity_types: Optional[List[str]] = None

# ========== Module Notes Endpoints ==========

@router.post("/modules", status_code=201)
def create_module_note(note: ModuleNoteCreate, db: Session = Depends(get_db)):
    """Create a new module-level note"""
    service = KnowledgeService(db)
    created_note = service.create_module_note(**note.dict())
    return {
        "id": str(created_note.id),
        "module_id": created_note.module_id,
        "note_type": created_note.note_type,
        "title": created_note.title,
        "content": created_note.content,
        "severity": created_note.severity,
        "tags": created_note.tags,
        "created_at": created_note.created_at.isoformat(),
        "updated_at": created_note.updated_at.isoformat()
    }

@router.get("/modules/{module_id}/notes")
def get_module_notes(module_id: str, note_type: Optional[str] = None, db: Session = Depends(get_db)):
    """Get all notes for a module"""
    service = KnowledgeService(db)
    notes = service.get_module_notes(module_id, note_type)
    return [
        {
            "id": str(note.id),
            "module_id": note.module_id,
            "category": note.category,
            "note_type": note.note_type,
            "title": note.title,
            "content": note.content,
            "severity": note.severity,
            "tags": note.tags,
            "created_at": note.created_at.isoformat(),
            "updated_at": note.updated_at.isoformat()
        }
        for note in notes
    ]

@router.put("/modules/{note_id}")
def update_module_note(note_id: str, note: ModuleNoteUpdate, db: Session = Depends(get_db)):
    """Update an existing module note"""
    service = KnowledgeService(db)
    try:
        updated_note = service.update_module_note(UUID(note_id), **note.dict(exclude_unset=True))
        return {
            "id": str(updated_note.id),
            "module_id": updated_note.module_id,
            "note_type": updated_note.note_type,
            "title": updated_note.title,
            "content": updated_note.content,
            "severity": updated_note.severity,
            "tags": updated_note.tags,
            "updated_at": updated_note.updated_at.isoformat()
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/modules/{note_id}")
def delete_module_note(note_id: str, db: Session = Depends(get_db)):
    """Delete a module note"""
    service = KnowledgeService(db)
    success = service.delete_module_note(UUID(note_id))
    if not success:
        raise HTTPException(status_code=404, detail="Note not found")
    return {"success": True}

# ========== Field Notes Endpoints ==========

@router.post("/fields", status_code=201)
def create_field_note(note: FieldNoteCreate, db: Session = Depends(get_db)):
    """Create a new field-level note"""
    service = KnowledgeService(db)
    created_note = service.create_field_note(**note.dict())
    return {
        "id": str(created_note.id),
        "module_id": created_note.module_id,
        "field_path": created_note.field_path,
        "field_name": created_note.field_name,
        "note_type": created_note.note_type,
        "title": created_note.title,
        "content": created_note.content,
        "severity": created_note.severity,
        "affected_entity_types": created_note.affected_entity_types,
        "created_at": created_note.created_at.isoformat(),
        "updated_at": created_note.updated_at.isoformat()
    }

@router.get("/fields/{module_id}/notes")
def get_field_notes(module_id: str, field_path: Optional[str] = None, db: Session = Depends(get_db)):
    """Get field notes for a module"""
    service = KnowledgeService(db)
    notes = service.get_field_notes(module_id, field_path)
    return [
        {
            "id": str(note.id),
            "module_id": note.module_id,
            "field_path": note.field_path,
            "field_name": note.field_name,
            "note_type": note.note_type,
            "title": note.title,
            "content": note.content,
            "severity": note.severity,
            "affected_entity_types": note.affected_entity_types,
            "created_at": note.created_at.isoformat(),
            "updated_at": note.updated_at.isoformat()
        }
        for note in notes
    ]

@router.put("/fields/{note_id}")
def update_field_note(note_id: str, note: FieldNoteUpdate, db: Session = Depends(get_db)):
    """Update an existing field note"""
    service = KnowledgeService(db)
    try:
        updated_note = service.update_field_note(UUID(note_id), **note.dict(exclude_unset=True))
        return {
            "id": str(updated_note.id),
            "module_id": updated_note.module_id,
            "field_path": updated_note.field_path,
            "title": updated_note.title,
            "content": updated_note.content,
            "severity": updated_note.severity,
            "updated_at": updated_note.updated_at.isoformat()
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/fields/{note_id}")
def delete_field_note(note_id: str, db: Session = Depends(get_db)):
    """Delete a field note"""
    service = KnowledgeService(db)
    success = service.delete_field_note(UUID(note_id))
    if not success:
        raise HTTPException(status_code=404, detail="Note not found")
    return {"success": True}

# ========== Search & Aggregation ==========

@router.get("/search")
def search_notes(q: str, note_type: Optional[str] = None, db: Session = Depends(get_db)):
    """Search notes by content/title"""
    service = KnowledgeService(db)
    results = service.search_notes(q, note_type)
    
    return {
        "query": q,
        "module_notes": [
            {
                "id": str(note.id),
                "module_id": note.module_id,
                "title": note.title,
                "note_type": note.note_type,
                "severity": note.severity
            }
            for note in results['module_notes']
        ],
        "field_notes": [
            {
                "id": str(note.id),
                "module_id": note.module_id,
                "field_path": note.field_path,
                "title": note.title,
                "note_type": note.note_type,
                "severity": note.severity
            }
            for note in results['field_notes']
        ]
    }

@router.get("/dq-issues/summary")
def get_dq_issues_summary(db: Session = Depends(get_db)):
    """Get summary of all DQ issues"""
    service = KnowledgeService(db)
    return service.get_dq_issues_summary()
