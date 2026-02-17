from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session
from app.models.knowledge import ModuleNote, FieldNote
from uuid import UUID
from sqlalchemy import or_

class KnowledgeService:
    """
    Service for managing knowledge notes about D&B API reference modules.
    Supports module-level and field-level notes for institutional knowledge capture.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    # ========== Module Notes ==========
    
    def create_module_note(
        self, 
        module_id: str, 
        note_type: str, 
        title: str, 
        content: str, 
        category: str = None, 
        severity: str = 'info', 
        tags: List[str] = None,
        created_by: str = None
    ) -> ModuleNote:
        """Create a new module-level note"""
        note = ModuleNote(
            module_id=module_id,
            category=category,
            note_type=note_type,
            title=title,
            content=content,
            severity=severity,
            tags=tags or [],
            created_by=created_by
        )
        self.db.add(note)
        self.db.commit()
        self.db.refresh(note)
        return note
    
    def get_module_notes(self, module_id: str, note_type: str = None) -> List[ModuleNote]:
        """Get all notes for a module, optionally filtered by type"""
        query = self.db.query(ModuleNote).filter(ModuleNote.module_id == module_id)
        
        if note_type:
            query = query.filter(ModuleNote.note_type == note_type)
        
        return query.order_by(ModuleNote.created_at.desc()).all()
    
    def update_module_note(self, note_id: UUID, **kwargs) -> ModuleNote:
        """Update an existing module note"""
        note = self.db.query(ModuleNote).filter(ModuleNote.id == note_id).first()
        if not note:
            raise ValueError(f"Note {note_id} not found")
        
        for key, value in kwargs.items():
            if hasattr(note, key):
                setattr(note, key, value)
        
        self.db.commit()
        self.db.refresh(note)
        return note
    
    def delete_module_note(self, note_id: UUID) -> bool:
        """Delete a module note"""
        note = self.db.query(ModuleNote).filter(ModuleNote.id == note_id).first()
        if not note:
            return False
        
        self.db.delete(note)
        self.db.commit()
        return True
    
    # ========== Field Notes ==========
    
    def create_field_note(
        self,
        module_id: str,
        field_path: str,
        note_type: str,
        title: str,
        content: str,
        severity: str = 'info',
        affected_entity_types: List[str] = None,
        field_name: str = None
    ) -> FieldNote:
        """Create a new field-level note"""
        note = FieldNote(
            module_id=module_id,
            field_path=field_path,
            field_name=field_name or field_path.split('.')[-1],
            note_type=note_type,
            title=title,
            content=content,
            severity=severity,
            affected_entity_types=affected_entity_types or []
        )
        self.db.add(note)
        self.db.commit()
        self.db.refresh(note)
        return note
    
    def get_field_notes(self, module_id: str, field_path: str = None) -> List[FieldNote]:
        """Get field notes, optionally filtered by field path"""
        query = self.db.query(FieldNote).filter(FieldNote.module_id == module_id)
        
        if field_path:
            query = query.filter(FieldNote.field_path == field_path)
        
        return query.order_by(FieldNote.created_at.desc()).all()
    
    def update_field_note(self, note_id: UUID, **kwargs) -> FieldNote:
        """Update an existing field note"""
        note = self.db.query(FieldNote).filter(FieldNote.id == note_id).first()
        if not note:
            raise ValueError(f"Note {note_id} not found")
        
        for key, value in kwargs.items():
            if hasattr(note, key):
                setattr(note, key, value)
        
        self.db.commit()
        self.db.refresh(note)
        return note
    
    def delete_field_note(self, note_id: UUID) -> bool:
        """Delete a field note"""
        note = self.db.query(FieldNote).filter(FieldNote.id == note_id).first()
        if not note:
            return False
        
        self.db.delete(note)
        self.db.commit()
        return True
    
    # ========== Search & Aggregation ==========
    
    def search_notes(self, query: str, note_type: str = None) -> Dict[str, List]:
        """Search notes by content/title"""
        search_pattern = f"%{query}%"
        
        # Search module notes
        module_query = self.db.query(ModuleNote).filter(
            or_(
                ModuleNote.title.ilike(search_pattern),
                ModuleNote.content.ilike(search_pattern)
            )
        )
        
        if note_type:
            module_query = module_query.filter(ModuleNote.note_type == note_type)
        
        # Search field notes
        field_query = self.db.query(FieldNote).filter(
            or_(
                FieldNote.title.ilike(search_pattern),
                FieldNote.content.ilike(search_pattern)
            )
        )
        
        if note_type:
            field_query = field_query.filter(FieldNote.note_type == note_type)
        
        return {
            'module_notes': module_query.all(),
            'field_notes': field_query.all()
        }
    
    def get_dq_issues_summary(self) -> Dict[str, Any]:
        """Get summary of all DQ issues across modules"""
        module_dq = self.db.query(ModuleNote).filter(
            ModuleNote.note_type == 'dq_issue'
        ).all()
        
        field_dq = self.db.query(FieldNote).filter(
            FieldNote.note_type == 'dq_issue'
        ).all()
        
        # Group by severity
        severity_counts = {'info': 0, 'warning': 0, 'critical': 0}
        
        for note in module_dq + field_dq:
            severity_counts[note.severity] = severity_counts.get(note.severity, 0) + 1
        
        return {
            'total_issues': len(module_dq) + len(field_dq),
            'module_issues': len(module_dq),
            'field_issues': len(field_dq),
            'by_severity': severity_counts,
            'recent_issues': (module_dq + field_dq)[:10]  # Last 10
        }
