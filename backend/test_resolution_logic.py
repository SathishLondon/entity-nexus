import json
import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models.sql import Base, TrustMatrix, ResolvedEntity, SourcePayload, CanonicalEntity
from app.services.ingestion_service import IngestionService
from app.services.trust_resolver import TrustResolver

# Setup DB Connection
DATABASE_URL = "postgresql://user:password@localhost:5432/entity_nexus" 
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def setup_db():
    import time
    from sqlalchemy.exc import OperationalError
    from sqlalchemy import text
    
    retries = 5
    for i in range(retries):
        try:
            # Setup
            Base.metadata.create_all(bind=engine)
            session = SessionLocal()
            
            # Test connection
            session.execute(text("SELECT 1"))
            
            # Clear tables for clean test
            session.query(ResolvedEntity).delete()
            session.query(CanonicalEntity).delete()
            session.query(SourcePayload).delete()
            session.query(TrustMatrix).delete()
            session.commit()
            
            return session
        except OperationalError as e:
            if i < retries - 1:
                print(f"DB not ready yet, retrying in 2s... ({e})")
                time.sleep(2)
            else:
                print("Failed to connect to DB after retries.")
                raise e

def test_trust_matrix_resolution():
    session = setup_db()
    try:
        run_test_logic(session)
    finally:
        session.close()

def run_test_logic(db):

    print("\n--- Test: Trust Matrix Resolution ---")
    
    # 1. Configure Trust Matrix
    # D&B is trusted for Revenue (Weight 10)
    # Companies House is trusted for Legal Name (Weight 10)
    dnb_trust = TrustMatrix(source="dnb", field="revenue_usd", weight=10)
    ch_trust = TrustMatrix(source="companies_house", field="legal_name", weight=10)
    
    # Defaults (Low trust)
    dnb_default = TrustMatrix(source="dnb", field="*", weight=5)
    ch_default = TrustMatrix(source="companies_house", field="*", weight=5)
    
    db.add_all([dnb_trust, ch_trust, dnb_default, ch_default])
    db.commit()
    
    ingest_service = IngestionService(db)
    
    # 2. Ingest D&B Data
    # Revenue: 1,000,000
    # Legal Name: "Test Corp Inc."
    dnb_payload = {
        "organization": {
            "duns": "123456789",
            "primaryName": "Test Corp Inc.", # parsed as legal_name
            "financials": [{"yearlyRevenue": [{"value": 1000000}]}] # parsed as revenue_usd
        }
    }
    
    print("Ingesting D&B...")
    sp_dnb = ingest_service.ingest_payload("dnb", "123456789", dnb_payload)
    # Mock Canonicalizer output since we don't have full parser here or want to rely on it
    # We will manually create Canonical to control inputs
    canon_dnb = CanonicalEntity(
        payload_id=sp_dnb.id,
        name="Test Corp",
        legal_name="Test Corp Inc.",
        registration_number="REG123", # Shared ID
        revenue_usd=1000000,
        employee_count=100
    )
    db.add(canon_dnb)
    db.commit()
    
    resolved_1 = ingest_service.resolve(canon_dnb)
    
    print(f"Round 1 Resolved: Name={resolved_1.legal_name}, Rev={resolved_1.revenue_usd}")
    
    assert resolved_1.revenue_usd == 1000000
    assert resolved_1.legal_name == "Test Corp Inc."
    assert resolved_1.lineage_metadata['revenue_usd']['confidence'] == 10
    assert resolved_1.lineage_metadata['legal_name']['confidence'] == 5 # Default weight
    
    # 3. Ingest Companies House Data
    # Revenue: 500 (Old data? Wrong data?)
    # Legal Name: "Test Corp Limited" (Official name, should win)
    
    print("Ingesting Companies House...")
    ch_payload = {"company_number": "REG123"}
    sp_ch = ingest_service.ingest_payload("companies_house", "REG123", ch_payload)
    
    canon_ch = CanonicalEntity(
        payload_id=sp_ch.id,
        name="Test Corp",
        legal_name="Test Corp Limited",
        registration_number="REG123", # Matches!
        revenue_usd=500,
        employee_count=105
    )
    db.add(canon_ch)
    db.commit()
    
    resolved_2 = ingest_service.resolve(canon_ch)
    
    print(f"Round 2 Resolved: Name={resolved_2.legal_name}, Rev={resolved_2.revenue_usd}")
    
    # Verify Trust Logic
    # Revenue: D&B (10) vs CH (Default 5) -> D&B should remain (1,000,000)
    # Legal Name: D&B (Default 5) vs CH (10) -> CH should win ("Test Corp Limited")
    
    assert resolved_2.id == resolved_1.id # Same entity
    assert resolved_2.revenue_usd == 1000000 # Unchanged
    assert resolved_2.legal_name == "Test Corp Limited" # Updated
    
    # Verify Metadata
    meta = resolved_2.lineage_metadata
    assert meta['revenue_usd']['source'] == 'dnb'
    assert meta['legal_name']['source'] == 'companies_house'
    
    print("SUCCESS: Trust Matrix Logic Verified!")

if __name__ == "__main__":
    test_trust_matrix_resolution()
