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
    
    # Risk Data (Phase 7)
    risk_score = Column(Integer, default=50) # 0-100 (Higher is riskier)
    
    # Lineage Metadata (The "Why")
    # Structure: { "name": { "source": "dnb", "payload_id": "...", "confidence": 0.9 } }
    lineage_metadata = Column(JSONB, default=dict)
    
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class EntityDataBlock(Base):
    """
    Tracks which D&B data blocks have been loaded for each entity.
    Enables cross-module data linking and visualization of data completeness.
    """
    __tablename__ = "entity_data_blocks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_id = Column(UUID(as_uuid=True), ForeignKey('resolved_entities.id'), nullable=False, index=True)
    module_id = Column(String(255), nullable=False)
    category = Column(String(50))  # Standard, Additional, Side, Add-on
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    entity = relationship("ResolvedEntity")
    
    # Composite unique constraint: one record per entity-module pair
    __table_args__ = (
        Index('idx_entity_module', 'entity_id', 'module_id', unique=True),
    )

class KnowledgeNote(Base):
    """
    Expert knowledge notes for capturing domain expertise and nuances
    not available in automated documentation.
    """
    __tablename__ = "knowledge_notes"
    
    id = Column(Integer, primary_key=True, index=True)
    module_id = Column(String(255), index=True, nullable=True)
    field_path = Column(String(500), nullable=True)
    note_type = Column(String(50), index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    tags = Column(JSON)
    severity = Column(String(20), default="info")
    created_by = Column(String(100), default="system")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    extra_data = Column(JSON)  # Renamed from metadata to avoid SQLAlchemy reserved word

class DocumentUpload(Base):
    """Uploaded documents for knowledge extraction"""
    __tablename__ = "document_uploads"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String(500), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_path = Column(String(1000))
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    uploaded_by = Column(String(100), default="user")
    status = Column(String(50), default="pending")  # pending, processing, completed, failed
    extra_data = Column(JSON)

class KnowledgeRecommendation(Base):
    """AI-generated knowledge note recommendations"""
    __tablename__ = "knowledge_recommendations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey('document_uploads.id'), nullable=False)
    note_type = Column(String(50), nullable=False)  # comparison, nuance, gotcha, best_practice
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    severity = Column(String(20), default="info")
    tags = Column(JSON)
    module_id = Column(String(255))
    field_path = Column(String(500))
    confidence = Column(Float)
    source_excerpt = Column(Text)
    reasoning = Column(Text)
    status = Column(String(50), default="pending")  # pending, approved, rejected, edited
    reviewed_by = Column(String(100))
    reviewed_at = Column(DateTime)
    created_note_id = Column(Integer, ForeignKey('knowledge_notes.id'))
    created_at = Column(DateTime, default=datetime.utcnow)
    extra_data = Column(JSON)

