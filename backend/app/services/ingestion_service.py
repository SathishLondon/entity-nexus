from sqlalchemy.orm import Session
from app.models.sql import SourcePayload, CanonicalEntity, ResolvedEntity, TrustMatrix
from app.services.dnb_service import parse_dnb_json
from typing import Dict, Any, List
import uuid
import json

class IngestionService:
    def __init__(self, db: Session):
        self.db = db

    def ingest_payload(self, source: str, source_id: str, payload: Dict[str, Any]) -> SourcePayload:
        """
        Stage 1: Save Raw Payload (Immutable System of Record)
        """
        # Check if exists (deduplication logic could be here)
        existing = self.db.query(SourcePayload).filter_by(source=source, source_id=source_id).first()
        if existing:
            # For this MVP, we update the payload if ID matches, or create new version
            # Enterprise grade: Create new version, look up by ID + active
            existing.payload = payload
            self.db.commit()
            self.db.refresh(existing)
            return existing
        
        new_payload = SourcePayload(
            source=source, 
            source_id=source_id, 
            payload=payload
        )
        self.db.add(new_payload)
        self.db.commit()
        self.db.refresh(new_payload)
        return new_payload

    def canonicalize(self, payload: SourcePayload) -> CanonicalEntity:
        """
        Stage 2: Normalize to Canonical Entity
        """
        # Strategy: Use specific parsers based on source
        if payload.source == 'dnb':
            # Reuse our partial logic from dnb_service, but map to SQL model
            # Note: dnb_service currently returns Pydantic. We might refactor it or just map here.
            parsed = parse_dnb_json(payload.payload) # Pydantic object
            
            canonical = CanonicalEntity(
                payload_id=payload.id,
                name=parsed.name,
                legal_name=parsed.legal_name,
                registration_number=parsed.registration_number,
                revenue_usd=parsed.revenue_usd,
                employee_count=parsed.employee_count,
                # Add more fields mapping
            )
            
            self.db.add(canonical)
            self.db.commit()
            return canonical
        
        raise NotImplementedError(f"No canonicalizer for source {payload.source}")

    def resolve(self, canonical: CanonicalEntity) -> ResolvedEntity:
        """
        Stage 3: Resolve Golden Record
        """
        from app.services.trust_resolver import TrustResolver
        
        resolver = TrustResolver(self.db)
        
        # 1. Find matches (Simplified for MVP: Match by some unique ID if possible, or just create new)
        # In a real system, we'd have a detailed matching/blocking strategy.
        # For this pipeline test, we'll assume we are creating a fresh one or finding by a shared identifier if we had one.
        # Since CanonicalEntity is 1:1 with SourcePayload, and SourcePayload has source_id,
        # we could try to look up ResolvedEntity by ... what? 
        # For now, let's just create a new one to demonstrate the logic, 
        # OR if we want to test updates, we'd need to pass an existing resolved entity or find it.
        
        # Let's try to find an existing ResolvedEntity that might be linked to this source_id 
        # (Linkage table needed for Many-to-Many? Yes, but for now 1:1 is easiest loop).
        
        # ACTUALLY: The TrustResolver logic handles "merge if exists".
        # We need a way to ID the entity. Let's assume for this test we match on 'registration_number' if present?
        existing = None
        if canonical.registration_number:
            existing = self.db.query(ResolvedEntity).filter(ResolvedEntity.registration_number == canonical.registration_number).first()
            
        resolved = resolver.resolve(canonical, existing_resolved=existing)
        
        if not existing:
            self.db.add(resolved)
        
        # If existing, it's already attached to session, just need commit
        self.db.commit()
        self.db.refresh(resolved)
        return resolved
