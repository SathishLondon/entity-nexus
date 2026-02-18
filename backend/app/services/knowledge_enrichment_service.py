"""
Knowledge Enrichment Service
Manages expert knowledge notes for D&B reference data
"""

from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from app.models.sql import KnowledgeNote
from app.core.database import get_db
import logging

logger = logging.getLogger(__name__)


class KnowledgeEnrichmentService:
    """
    Service for managing expert knowledge notes.
    Captures domain expertise and nuances not in automated documentation.
    """
    
    def __init__(self, db: Session = None):
        self.db = db or next(get_db())
    
    def add_note(
        self,
        title: str,
        content: str,
        note_type: str,
        module_id: Optional[str] = None,
        field_path: Optional[str] = None,
        tags: List[str] = None,
        severity: str = "info",
        created_by: str = "system",
        metadata: Dict = None
    ) -> KnowledgeNote:
        """Create a new knowledge note"""
        note = KnowledgeNote(
            module_id=module_id,
            field_path=field_path,
            note_type=note_type,
            title=title,
            content=content,
            tags=tags or [],
            severity=severity,
            created_by=created_by,
            metadata=metadata or {}
        )
        
        self.db.add(note)
        self.db.commit()
        self.db.refresh(note)
        
        logger.info(f"Created knowledge note: {title}")
        return note
    
    def get_note(self, note_id: int) -> Optional[KnowledgeNote]:
        """Get a specific note by ID"""
        return self.db.query(KnowledgeNote).filter(KnowledgeNote.id == note_id).first()
    
    def get_all_notes(self) -> List[KnowledgeNote]:
        """Get all knowledge notes"""
        return self.db.query(KnowledgeNote).all()
    
    def get_notes_for_module(self, module_id: str) -> List[KnowledgeNote]:
        """Get all notes for a specific module"""
        return self.db.query(KnowledgeNote).filter(
            KnowledgeNote.module_id == module_id
        ).all()
    
    def search_notes(
        self,
        query: str = None,
        tags: List[str] = None,
        note_type: str = None,
        severity: str = None
    ) -> List[KnowledgeNote]:
        """
        Search knowledge notes by various criteria.
        
        Args:
            query: Search in title and content
            tags: Filter by tags (any match)
            note_type: Filter by note type
            severity: Filter by severity
        """
        q = self.db.query(KnowledgeNote)
        
        if query:
            search_term = f"%{query.lower()}%"
            q = q.filter(
                (KnowledgeNote.title.ilike(search_term)) |
                (KnowledgeNote.content.ilike(search_term))
            )
        
        if tags:
            # Match any of the provided tags
            q = q.filter(KnowledgeNote.tags.overlap(tags))
        
        if note_type:
            q = q.filter(KnowledgeNote.note_type == note_type)
        
        if severity:
            q = q.filter(KnowledgeNote.severity == severity)
        
        return q.all()
    
    def get_comparisons(self, module_ids: List[str]) -> List[KnowledgeNote]:
        """
        Get comparison notes relevant to the given modules.
        Useful when comparing multiple modules.
        """
        # Get comparison notes that mention any of the module IDs
        notes = self.db.query(KnowledgeNote).filter(
            KnowledgeNote.note_type == "comparison"
        ).all()
        
        # Filter to notes that are relevant to the modules
        relevant_notes = []
        for note in notes:
            # Check if module_id matches
            if note.module_id in module_ids:
                relevant_notes.append(note)
                continue
            
            # Check if any module_id is mentioned in tags or content
            content_lower = note.content.lower()
            for module_id in module_ids:
                if module_id.lower() in content_lower or module_id.lower() in [t.lower() for t in (note.tags or [])]:
                    relevant_notes.append(note)
                    break
        
        return relevant_notes
    
    def update_note(
        self,
        note_id: int,
        title: str = None,
        content: str = None,
        tags: List[str] = None,
        severity: str = None,
        metadata: Dict = None
    ) -> Optional[KnowledgeNote]:
        """Update an existing note"""
        note = self.get_note(note_id)
        if not note:
            return None
        
        if title is not None:
            note.title = title
        if content is not None:
            note.content = content
        if tags is not None:
            note.tags = tags
        if severity is not None:
            note.severity = severity
        if metadata is not None:
            note.extra_data = metadata
        
        self.db.commit()
        self.db.refresh(note)
        
        logger.info(f"Updated knowledge note: {note_id}")
        return note
    
    def delete_note(self, note_id: int) -> bool:
        """Delete a knowledge note"""
        note = self.get_note(note_id)
        if not note:
            return False
        
        self.db.delete(note)
        self.db.commit()
        
        logger.info(f"Deleted knowledge note: {note_id}")
        return True
    
    def seed_initial_notes(self):
        """Seed the database with initial expert knowledge notes"""
        
        # cmpbol vs cmpbos comparison
        self.add_note(
            title="cmpbol vs cmpbos: Ownership Percentage Calculation",
            content="""**Critical Difference in Ownership Percentage Calculation:**

**cmpbol (Beneficial Ownership List)**
- Shows ownership % of all entities in **UPWARD hierarchy**
- Percentages are **relative to the INQUIRY PARTY**
- Example: If querying Company A, shows % of B→A, C→B→A
- All percentages answer: "Who owns X% of the company I'm querying?"

**cmpbos (Beneficial Ownership Structure)**
- Shows ownership % **BETWEEN each entity and its sub-entity**
- Percentages are **PAIRWISE relationships** throughout the hierarchy
- Example: Shows % of B→A separately from C→B
- Each percentage answers: "What % does A own of B?"

**When this matters:**
- Use **cmpbol** when you need: "Who owns X% of the inquiry party?"
- Use **cmpbos** when you need: "What % does A own of B in the chain?"

**Additional Differences:**
- **cmpbol**: Optimized for **list format** presentation (tables, reports)
- **cmpbos**: Optimized for **visualization purposes** (graphs, network diagrams)

**Example Scenario:**
```
Company C owns 60% of Company B
Company B owns 80% of Company A (inquiry party)

cmpbol shows:
- B owns 80% of A (relative to A)
- C owns 48% of A (60% × 80%, relative to A)

cmpbos shows:
- B owns 80% of A (pairwise B→A)
- C owns 60% of B (pairwise C→B)
```
""",
            note_type="comparison",
            module_id="Side_DB_cmpbol",
            tags=["ownership", "cmpbol", "cmpbos", "calculation", "percentage", "beneficial_ownership"],
            severity="critical",
            created_by="domain_expert",
            metadata={
                "related_modules": ["Side_DB_cmpbol", "Side_DB_cmpbos"],
                "use_cases": ["ownership_analysis", "compliance", "reporting", "visualization"]
            }
        )
        
        logger.info("Seeded initial knowledge notes")
