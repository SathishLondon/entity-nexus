from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.sql import TrustMatrix, ResolvedEntity, CanonicalEntity
from datetime import datetime
from typing import Optional, Dict, Any, List

class TrustResolver:
    def __init__(self, db: Session):
        self.db = db

    def get_trust_score(self, source: str, field: str) -> int:
        """
        Fetch the trust weight for a given source and field.
        Defaults to 1 if no rule exists.
        """
        # Look for specific field match first, then wildcard '*'
        # We need to handle effective_date in the future, for now assume current rules
        
        # Specific field rule
        rule = self.db.query(TrustMatrix).filter(
            TrustMatrix.source == source,
            TrustMatrix.field == field
        ).first()

        if rule:
            return rule.weight

        # Wildcard rule
        wildcard = self.db.query(TrustMatrix).filter(
            TrustMatrix.source == source,
            TrustMatrix.field == '*'
        ).first()

        if wildcard:
            return wildcard.weight
        
        return 1 # Default confidence

    def resolve(self, canonical: CanonicalEntity, existing_resolved: Optional[ResolvedEntity] = None) -> ResolvedEntity:
        """
        Merges a Canonical Entity into a Resolved Entity (Golden Record) based on Trust Matrix.
        """
        source = canonical.payload.source if canonical.payload else "unknown" # Assuming link exists
        # In case canonical.payload is not loaded/available, we might need to pass source explicitly or ensure eager loading.
        # For now, let's assume we can access it or pass it.
        # Actually CanonicalEntity has a relationship `payload`, so we can access `canonical.payload.source`.

        if not existing_resolved:
            return self._create_initial_resolved(canonical, source)
        
        return self._merge_resolved(existing_resolved, canonical, source)

    def _create_initial_resolved(self, canonical: CanonicalEntity, source: str) -> ResolvedEntity:
        lineage = {}
        
        # Fields to map
        fields = ['name', 'legal_name', 'registration_number', 'jurisdiction_code', 'revenue_usd', 'employee_count']
        
        resolved_data = {}
        
        for field in fields:
            val = getattr(canonical, field)
            if val is not None:
                resolved_data[field] = val
                trust_score = self.get_trust_score(source, field)
                lineage[field] = {
                    "source": source,
                    "value": val, # Optional: store value in lineage for audit
                    "confidence": trust_score,
                    "payload_id": str(canonical.payload_id),
                    "last_updated": datetime.utcnow().isoformat()
                }

        resolved = ResolvedEntity(**resolved_data)
        resolved.lineage_metadata = lineage
        return resolved

    def _merge_resolved(self, resolved: ResolvedEntity, canonical: CanonicalEntity, source: str) -> ResolvedEntity:
        fields = ['name', 'legal_name', 'registration_number', 'jurisdiction_code', 'revenue_usd', 'employee_count']
        
        current_lineage = dict(resolved.lineage_metadata or {})
        
        changed = False
        
        for field in fields:
            new_val = getattr(canonical, field)
            if new_val is None:
                continue

            # Check existing
            existing_meta = current_lineage.get(field)
            
            should_update = False
            new_score = self.get_trust_score(source, field)

            if not existing_meta:
                should_update = True
            else:
                current_score = existing_meta.get("confidence", 0)
                if new_score > current_score:
                    should_update = True
                elif new_score == current_score:
                    # Tie-breaker: Latest update wins (or keep existing? Let's say Last Write Wins for now)
                    should_update = True 

            if should_update:
                setattr(resolved, field, new_val)
                current_lineage[field] = {
                    "source": source,
                    "value": new_val,
                    "confidence": new_score,
                    "payload_id": str(canonical.payload_id),
                    "last_updated": datetime.utcnow().isoformat()
                }
                changed = True
        
        if changed:
            resolved.lineage_metadata = current_lineage
            # resolved.updated_at will be handled by SQLAlchemy onupdate
            
        return resolved
