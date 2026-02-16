from langchain.tools import tool
from app.services.entity_service import EntityService
from app.core.database import SessionLocal
import json

# Helper to get service instance
def get_service():
    db = SessionLocal()
    return EntityService(db)

@tool
def get_entity_info(entity_id: str):
    """
    Retrieves the 'Golden Record' for an entity by its ID (UUID).
    Useful for answering 'What is the revenue of X?' or 'Who is the legal parent of Y?'.
    """
    service = get_service()
    entity = service.get_golden_record(entity_id)
    if not entity:
        return "Entity not found."
    
    return {
        "name": entity.name,
        "revenue": entity.revenue_usd,
        "employees": entity.employee_count,
        "jurisdiction": entity.jurisdiction_code,
        "lineage": entity.lineage_metadata
    }

@tool
def explain_field_source(entity_id: str, field: str):
    """
    Explains WHERE a specific piece of data came from.
    Use this when the user asks 'Where did you get that revenue number?' or 'Why do you say they have 500 employees?'.
    """
    service = get_service()
    lineage = service.get_lineage(entity_id, field)
    if not lineage:
        return f"No lineage found for field '{field}' on entity {entity_id}."
    
    return lineage
