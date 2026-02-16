import json
import sys
import os
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.ingestion_service import IngestionService
from app.services.entity_service import EntityService
from app.models.sql import Base
from app.core.config import settings

# Setup DB Connection (User's Localhost)
# Ensure this matches docker-compose settings
DATABASE_URL = "postgresql://user:password@localhost:5432/entity_nexus" 
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    print("Initializing DB Tables...")
    Base.metadata.create_all(bind=engine)

def test_enterprise_pipeline():
    init_db()
    db = SessionLocal()
    
    ingest_service = IngestionService(db)
    entity_service = EntityService(db)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, "dnb_references", "Standard_DB_companyinfo_L4_companyidentifiers_Sample.json")
    
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    try:
        with open(file_path, 'r') as f:
            payload = json.load(f)

        # 1. Ingest (Source Layer)
        print("\n--- Stage 1: Ingestion (Source Layer) ---")
        duns = payload.get("organization", {}).get("duns")
        source_payload = ingest_service.ingest_payload(source="dnb", source_id=duns, payload=payload)
        print(f"Stored SourcePayload: {source_payload.id} (Source: {source_payload.source})")

        # 2. Canonicalize (Normalization Layer)
        print("\n--- Stage 2: Canonicalization (Normalization Layer) ---")
        canonical = ingest_service.canonicalize(source_payload)
        print(f"Created CanonicalEntity: {canonical.name} (Rev: ${canonical.revenue_usd:,.2f})")

        # 3. Resolve (Golden Record Layer)
        print("\n--- Stage 3: Resolution (Golden Record Layer) ---")
        resolved = ingest_service.resolve(canonical)
        print(f"Resolved Golden Record: {resolved.id}")
        print(f"Name: {resolved.name}")
        print(f"Revenue: ${resolved.revenue_usd:,.2f}")
        
        # 4. Verify Lineage
        print("\n--- Stage 4: Lineage Verification ---")
        rev_lineage = entity_service.get_lineage(str(resolved.id), "revenue_usd")
        print(f"Revenue Lineage: {json.dumps(rev_lineage, indent=2)}")
        
        if rev_lineage.get("source") == "dnb":
            print("SUCCESS: Lineage correctly tracked to D&B.")
        else:
            print("FAILURE: Lineage mismatch.")

    except Exception as e:
        print(f"TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_enterprise_pipeline()
