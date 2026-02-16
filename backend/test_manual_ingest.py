import json
import sys
import os

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.dnb_service import parse_dnb_json
from app.services.resolution_engine import resolve_entity

def test_ingestion():
    file_path = "dnb_references/Standard_DB_companyinfo_L4_companyidentifiers_Sample.json"
    
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    with open(file_path, 'r') as f:
        data = json.load(f)

    # 1. Parse
    print("Parsing D&B JSON...")
    entity_ingest = parse_dnb_json(data)
    print(f"Parsed Entity: {entity_ingest.name} (DUNS: {entity_ingest.duns})")
    print(f"Address: {entity_ingest.address}")

    # 2. Resolve
    print("\nResolving Entity...")
    candidates = [entity_ingest]
    resolved = resolve_entity(candidates)
    
    print(f"Resolved Entity ID: {resolved.id}")
    print(f"Confidence Score: {resolved.confidence_score}")
    print(f"Resolved Name: {resolved.name}")
    print(f"Resolved Address: {resolved.address}")
    
    # Check field lineage
    print("\nField Lineage:")
    for field, source in resolved.field_lineage.items():
        print(f"  {field}: {source}")

if __name__ == "__main__":
    test_ingestion()
