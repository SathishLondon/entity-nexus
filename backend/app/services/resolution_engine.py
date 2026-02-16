from sqlalchemy.orm import Session
from app.models.sql import CanonicalEntity, ResolvedEntity, TrustMatrix, SourcePayload
from typing import List, Optional
from datetime import datetime
import json

class ResolutionEngine:
    def __init__(self, db: Session):
        self.db = db
        # Pre-load effective trust matrix for performance?
        # Or query per field? Let's query per field for MVP clarity.

    def get_effective_weight(self, source: str, field: str) -> int:
        """
        Finds the weight for a source+field at the current time.
        """
        now = datetime.utcnow()
        rule = self.db.query(TrustMatrix).filter(
            TrustMatrix.source == source,
            TrustMatrix.field.in_([field, '*']), # Specific field or wildcard
            TrustMatrix.effective_from <= now,
            (TrustMatrix.effective_to == None) | (TrustMatrix.effective_to >= now)
        ).order_by(TrustMatrix.weight.desc()).first()
        
        return rule.weight if rule else 1 # Default trust

    def resolve_canonical_to_golden(self, canonical: CanonicalEntity) -> ResolvedEntity:
        """
        Core Logic:
        1. Find all 'candidate' canonical entities that match this one (by ID, tax_id, etc.)
        2. For each field (name, revenue, etc.), pick value from highest weighted source.
        3. Construct refined ResolvedEntity with Lineage.
        """
        
        # 1. Matching (Simplistic for now: Just use this one candidate)
        candidates = [canonical] 
        
        # 2. Field-level Resolution
        resolved_data = {}
        lineage_metadata = {}
        
        fields_to_resolve = ["name", "legal_name", "revenue_usd", "employee_count"]
        
        for field in fields_to_resolve:
            best_val = None
            best_score = -1
            best_source = None
            best_payload_id = None
            
            for cand in candidates:
                val = getattr(cand, field, None)
                if val is not None:
                    # Get source from the payload relation
                    # Optimized: Eager load payload in query
                    source_name = cand.payload.source
                    weight = self.get_effective_weight(source_name, field)
                    
                    if weight > best_score:
                        best_score = weight
                        best_val = val
                        best_source = source_name
                        best_payload_id = cand.payload_id
            
            if best_val is not None:
                resolved_data[field] = best_val
                lineage_metadata[field] = {
                    "value": best_val,
                    "source": best_source,
                    "payload_id": str(best_payload_id),
                    "confidence": 1.0 # Could be calculated based on weight difference
                }

        # 3. Create/Update Resolved Entity
        # Check if we already have a resolved entity for this cluster?
        # For MVP, assuming 1:1 or new creation
        
        resolved = ResolvedEntity(
            **resolved_data,
            lineage_metadata=lineage_metadata
        )
        self.db.add(resolved)
        self.db.commit()
        return resolved
