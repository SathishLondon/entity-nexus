from sqlalchemy.orm import Session
from app.models.sql import ResolvedEntity
from app.core.database import neo4j_driver
from typing import Dict, Any, Optional

class EntityService:
    def __init__(self, db: Session):
        self.db = db

    def get_golden_record(self, entity_id: str) -> Optional[ResolvedEntity]:
        """
        Retrieves the definitive resolved entity from Postgres.
        """
        return self.db.query(ResolvedEntity).filter(ResolvedEntity.id == entity_id).first()

    def get_lineage(self, entity_id: str, field: str) -> Dict[str, Any]:
        """
        Retrieves the granular lineage for a specific field.
        Returns: { "value": ..., "source": ..., "payload_id": ..., "confidence": ... }
        """
        entity = self.get_golden_record(entity_id)
        if not entity or not entity.lineage_metadata:
            return {}
        
        return entity.lineage_metadata.get(field, {})

    def get_hierarchy(self, entity_id: str, depth: int = 1) -> Dict[str, Any]:
        """
        Queries Neo4j for the organizational hierarchy.
        """
        query = f"""
        MATCH (root {{id: $id}})-[r:OWNS|PARENT_OF*1..{depth}]-(child)
        RETURN root, r, child
        """
        # Note: In a real implementation, we'd parse this into a clean JSON structure
        # similar to the graph endpoint we wrote earlier.
        # reusing logic or calling GraphService would be better.
        return {"message": "Hierarchy query placeholder"}
