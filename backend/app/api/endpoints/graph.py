from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from app.core.database import get_graph_session
from app.core.neo4j_schema import LABEL_LEGAL_ENTITY

router = APIRouter()

@router.get("/graph/{entity_id}")
def get_entity_graph(entity_id: str, session=Depends(get_graph_session)):
    """
    Fetch the immediate neighborhood of an entity for visualization.
    Returns Nodes and Edges in a format suitable for React Flow/Cytoscape.
    Uses Enterprise Schema (LegalEntity).
    """
    # Cypher query to get the entity and its neighbors
    # Using format() or f-string for label injection (safe for known constants)
    query = f"""
    MATCH (e:{LABEL_LEGAL_ENTITY} {{id: $entity_id}})-[r]-(n)
    RETURN e, r, n
    LIMIT 50
    """
    result = session.run(query, entity_id=entity_id)
    
    nodes = []
    edges = []
    seen_nodes = set()
    
    for record in result:
        # Process source entity
        e_node = record["e"]
        if e_node.element_id not in seen_nodes:
            nodes.append({
                "id": e_node.element_id, # Neo4j internal ID or our ID? Ideally our ID: e_node["id"]
                "type": "entity",
                "data": dict(e_node), # Contains name, revenue, etc.
                "position": {"x": 0, "y": 0} # Frontend will handle layout
            })
            seen_nodes.add(e_node.element_id)
            
        # Process neighbor
        n_node = record["n"]
        if n_node.element_id not in seen_nodes:
            nodes.append({
                "id": n_node.element_id,
                "type": "entity",
                "data": dict(n_node),
                "position": {"x": 0, "y": 0}
            })
            seen_nodes.add(n_node.element_id)
            
        # Process relationship
        rel = record["r"]
        edges.append({
            "id": rel.element_id,
            "source": rel.start_node.element_id,
            "target": rel.end_node.element_id,
            "label": rel.type,
            "data": dict(rel) # Contains ownership_pct, effective_date
        })
        
    return {"nodes": nodes, "edges": edges}
