from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.ingestion_service import IngestionService
from app.models.sql import ResolvedEntity
# We need Pydantic schemas for response too, or return ORM objects directly if configured
# For now, let's just return a success message or the ID

router = APIRouter()

def get_ingestion_service(db: Session = Depends(get_db)):
    return IngestionService(db)

@router.post("/ingest/dnb")
async def ingest_dnb_data(payload: Dict[str, Any], service: IngestionService = Depends(get_ingestion_service)):
    """
    Ingests D&B JSON via the Enterprise 3-Stage Pipeline:
    Raw -> Canonical -> Resolved -> Graph Sync
    """
    try:
        # 1. Raw Ingest
        # Extract ID from payload or header? For D&B, getting duns from payload
        duns = payload.get("organization", {}).get("duns")
        if not duns:
             raise HTTPException(status_code=400, detail="DUNS number missing in payload")

        source_payload = service.ingest_payload(source="dnb", source_id=duns, payload=payload)
        
        # 2. Canonicalize
        canonical = service.canonicalize(source_payload)
        
        # 3. Resolve
        resolved = service.resolve(canonical)
        
        # 4. Graph Sync done inside resolve/service or here? 
        # Ideally, IngestionService calls EntityService or similar. 
        # For now, let's assume IngestionService handles it or we call a sync service here.
        from app.services.neo4j_sync_service import Neo4jSyncService
        sync_service = Neo4jSyncService()
        sync_service.sync_entity(resolved)

        return {
            "status": "success", 
            "resolved_entity_id": str(resolved.id),
            "lineage": resolved.lineage_metadata
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
