from sqlalchemy.orm import Session
from app.models.sql import ResolvedEntity
from app.core.database import neo4j_driver
from app.core.neo4j_schema import LABEL_LEGAL_ENTITY, PROP_SOURCE
import json

class Neo4jSyncService:
    def __init__(self):
        self.driver = neo4j_driver

    def sync_entity(self, entity: ResolvedEntity):
        """
        Projects a ResolvedEntity into Neo4j as a Node.
        """
        query = f"""
        MERGE (e:{LABEL_LEGAL_ENTITY} {{id: $id}})
        SET e.name = $name,
            e.jurisdiction_code = $jurisdiction_code,
            e.revenue_usd = $revenue_usd,
            e.employee_count = $employee_count,
            e.risk_score = $risk_score,
            e.last_updated = datetime()
        """
        
        with self.driver.session() as session:
            session.run(query, 
                id=str(entity.id),
                name=entity.name,
                jurisdiction_code=entity.jurisdiction_code,
                revenue_usd=entity.revenue_usd,
                employee_count=entity.employee_count,
                risk_score=entity.risk_score or 50
            )

    def sync_relationships(self, parent_id: str, child_id: str, relationship_type: str, properties: dict):
        """
        Creates a relationship between two entities.
        """
        # properties_cypher = ", ".join([f"r.{k} = ${k}" for k in properties.keys()])
        # Simplified for now
        
        query = f"""
        MATCH (p:{LABEL_LEGAL_ENTITY} {{id: $parent_id}})
        MATCH (c:{LABEL_LEGAL_ENTITY} {{id: $child_id}})
        MERGE (p)-[r:{relationship_type}]->(c)
        SET r += $props
        """
        
        with self.driver.session() as session:
            session.run(query, parent_id=parent_id, child_id=child_id, props=properties)
