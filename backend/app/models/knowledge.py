from sqlalchemy import Column, String, Text, DateTime, UUID as SQLUUID, ARRAY
from sqlalchemy.sql import func
from app.core.database import Base
import uuid

class ModuleNote(Base):
    """
    Module-level notes for D&B API reference modules.
    Supports comparisons, clarifications, usage notes, and DQ issues.
    """
    __tablename__ = "dnb_module_notes"
    
    id = Column(SQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    module_id = Column(String(255), nullable=False, index=True)
    category = Column(String(50))  # Standard, Additional, Side, Add-on
    note_type = Column(String(50), index=True)  # clarification, usage_note, dq_issue, comparison
    title = Column(String(500))
    content = Column(Text)
    severity = Column(String(20))  # info, warning, critical
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_by = Column(String(100))  # For future multi-user support
    tags = Column(ARRAY(Text))

class FieldNote(Base):
    """
    Field-level notes for specific fields within D&B modules.
    Primarily for DQ issues, mapping notes, and validation rules.
    """
    __tablename__ = "dnb_field_notes"
    
    id = Column(SQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    module_id = Column(String(255), nullable=False, index=True)
    field_path = Column(String(500), nullable=False)  # e.g., "organization.primaryAddress.postalCode"
    field_name = Column(String(255))
    note_type = Column(String(50))  # dq_issue, mapping_note, validation_rule
    title = Column(String(500))
    content = Column(Text)
    severity = Column(String(20))  # info, warning, critical
    affected_entity_types = Column(ARRAY(Text))  # e.g., ["UK entities", "US entities"]
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
