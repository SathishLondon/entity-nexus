from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Index, JSON, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()

class SourcePayload(Base):
    """
    Mutable/Immutable Store for Raw JSON from Data Providers.
    System of Record for "What did we receive and when?"
    """
    __tablename__ = "source_payloads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source = Column(String, index=True, nullable=False) # e.g., 'dnb', 'companies_house'
    source_id = Column(String, index=True, nullable=False) # Provider's native ID (DUNS, CompanyNumber)
    payload = Column(JSONB, nullable=False) # The raw JSON
    ingested_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Optional: Hash of payload to detect duplicates?
    # payload_hash = Column(String, index=True)

class CanonicalEntity(Base):
    """
    Normalized View of Source Data.
    Maps 1:1 with a relevant SourcePayload, but keys are standardized.
    """
    __tablename__ = "canonical_entities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    payload_id = Column(UUID(as_uuid=True), ForeignKey("source_payloads.id"), nullable=False)
    
    # Standardized Core Fields
    name = Column(String, index=True)
    legal_name = Column(String)
    registration_number = Column(String, index=True)
    jurisdiction_code = Column(String) # ISO Country Code
    
    # Structured Financials/Metrics (Normalized)
    revenue_usd = Column(Float)
    employee_count = Column(Integer)
    
    valid_from = Column(DateTime, default=datetime.utcnow)
    
    # Link back
    payload = relationship("SourcePayload")

class TrustMatrix(Base):
    """
    Configurable Logic for Resolution.
    """
    __tablename__ = "trust_matrix"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String, nullable=False) # 'dnb'
    field = Column(String, nullable=False) # 'revenue_usd' or '*'
    weight = Column(Integer, default=1, nullable=False)
    effective_from = Column(DateTime, default=datetime.utcnow)
    effective_to = Column(DateTime, nullable=True) # None = Current

class ResolvedEntity(Base):
    """
    The Golden Record.
    """
    __tablename__ = "resolved_entities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Core Resolved Attributes (Indexed for search)
    name = Column(String, index=True)
    legal_name = Column(String)
    registration_number = Column(String)
    jurisdiction_code = Column(String)
    
    # Resolved Metrics
    revenue_usd = Column(Float)
    employee_count = Column(Integer)
    
    # Lineage Metadata (The "Why")
    # Structure: { "name": { "source": "dnb", "payload_id": "...", "confidence": 0.9 } }
    lineage_metadata = Column(JSONB, default=dict)
    
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
