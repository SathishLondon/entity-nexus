from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.entity_service import EntityService

router = APIRouter()

def get_service(db: Session = Depends(get_db)):
    return EntityService(db)

@router.get("/entities/{entity_id}/golden-record")
def get_golden_record(entity_id: str, service: EntityService = Depends(get_service)):
    """
    Returns the resolved 'Golden Record' for an entity.
    """
    entity = service.get_golden_record(entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    return entity

@router.get("/entities/{entity_id}/lineage/{field}")
def get_field_lineage(entity_id: str, field: str, service: EntityService = Depends(get_service)):
    """
    Returns the lineage metadata for a specific field.
    """
    lineage = service.get_lineage(entity_id, field)
    # Return empty dict if no lineage, or 404? 
    # Let's return the dict, even if empty, as it's valid state.
    return lineage

@router.get("/entities/{entity_id}/hierarchy")
def get_hierarchy(entity_id: str, depth: int = 1, service: EntityService = Depends(get_service)):
    """
    Returns the graph hierarchy from Neo4j.
    """
    return service.get_hierarchy(entity_id, depth)
