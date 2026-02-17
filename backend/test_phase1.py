"""
Phase 1 Testing Script for D&B Explorer Enhancement
Tests module categorization, Excel parsing, and knowledge management
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.reference_service import ReferenceService

def test_module_categorization():
    """Test module categorization functionality"""
    print("\n" + "="*60)
    print("TEST 1: Module Categorization")
    print("="*60)
    
    service = ReferenceService()
    
    # Test get_module_category
    print("\n1.1 Testing get_module_category()...")
    test_cases = [
        ("Standard_DB_companyinfo_L1", "Standard"),
        ("Side_DB_cmpbol", "Side"),
        ("Additional_DB_something", "Additional"),
        ("addon_DB_something", "Add-on"),
        ("Unknown_Module", "Unknown")
    ]
    
    for module_id, expected in test_cases:
        result = service.get_module_category(module_id)
        status = "✅ PASS" if result == expected else f"❌ FAIL (got {result})"
        print(f"   {module_id} -> {expected}: {status}")
    
    # Test get_modules_by_category
    print("\n1.2 Testing get_modules_by_category()...")
    categorized = service.get_modules_by_category()
    
    print(f"   Categories found: {list(categorized.keys())}")
    for category, modules in categorized.items():
        if modules:
            print(f"   - {category}: {len(modules)} modules")
            if len(modules) > 0:
                print(f"     Example: {modules[0]['id']}")
    
    if 'Standard' in categorized and len(categorized['Standard']) > 0:
        print("   ✅ PASS: Module categorization working")
    else:
        print("   ❌ FAIL: No Standard modules found")

def test_excel_parsing():
    """Test Excel dictionary parsing"""
    print("\n" + "="*60)
    print("TEST 2: Excel Dictionary Parsing")
    print("="*60)
    
    service = ReferenceService()
    
    # Get first module to test
    modules = service.get_modules()
    if not modules:
        print("   ❌ FAIL: No modules found")
        return
    
    test_module = modules[0]['id']
    print(f"\n2.1 Testing with module: {test_module}")
    
    # Test get_data_dictionary_from_excel
    print("\n2.2 Testing get_data_dictionary_from_excel()...")
    excel_data = service.get_data_dictionary_from_excel(test_module)
    
    if excel_data:
        print(f"   ✅ PASS: Found {len(excel_data)} entries")
        if len(excel_data) > 0:
            print(f"   Sample entry keys: {list(excel_data[0].keys())[:5]}")
    else:
        print("   ⚠️  WARNING: No Excel data found (file may not exist)")
    
    # Test get_available_blocks
    print("\n2.3 Testing get_available_blocks()...")
    blocks = service.get_available_blocks(test_module)
    
    if blocks:
        print(f"   ✅ PASS: Found {len(blocks)} unique blocks")
        print(f"   Blocks: {blocks[:3]}{'...' if len(blocks) > 3 else ''}")
    else:
        print("   ⚠️  WARNING: No blocks found")
    
    # Test filter_dictionary_by_block
    if blocks:
        print("\n2.4 Testing filter_dictionary_by_block()...")
        filtered = service.filter_dictionary_by_block(test_module, [blocks[0]])
        
        if filtered:
            print(f"   ✅ PASS: Filtered to {len(filtered)} entries for block '{blocks[0]}'")
        else:
            print("   ❌ FAIL: Filtering returned no results")

def test_api_endpoints():
    """Test API endpoints with requests"""
    print("\n" + "="*60)
    print("TEST 3: API Endpoints")
    print("="*60)
    
    try:
        import requests
        
        base_url = "http://localhost:8000/api/v1"
        
        # Test 1: Get modules
        print("\n3.1 Testing GET /references/modules...")
        response = requests.get(f"{base_url}/references/modules")
        if response.status_code == 200:
            modules = response.json()
            print(f"   ✅ PASS: Got {len(modules)} modules")
        else:
            print(f"   ❌ FAIL: Status {response.status_code}")
        
        # Test 2: Get modules by category
        print("\n3.2 Testing GET /references/modules/by-category...")
        response = requests.get(f"{base_url}/references/modules/by-category")
        if response.status_code == 200:
            categorized = response.json()
            print(f"   ✅ PASS: Got {len(categorized)} categories")
            for cat, mods in categorized.items():
                if mods:
                    print(f"     - {cat}: {len(mods)} modules")
        else:
            print(f"   ❌ FAIL: Status {response.status_code}")
        
        # Test 3: Get Excel dictionary
        if modules:
            module_id = modules[0]['id']
            print(f"\n3.3 Testing GET /references/{module_id}/dictionary/excel...")
            response = requests.get(f"{base_url}/references/{module_id}/dictionary/excel")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ PASS: Got {len(data)} entries")
            else:
                print(f"   ❌ FAIL: Status {response.status_code}")
            
            # Test 4: Get available blocks
            print(f"\n3.4 Testing GET /references/{module_id}/available-blocks...")
            response = requests.get(f"{base_url}/references/{module_id}/available-blocks")
            if response.status_code == 200:
                blocks = response.json()
                print(f"   ✅ PASS: Got {len(blocks)} blocks")
            else:
                print(f"   ❌ FAIL: Status {response.status_code}")
        
        # Test 5: Knowledge endpoints (will fail if DB not running, that's OK)
        print("\n3.5 Testing POST /knowledge/modules...")
        test_note = {
            "module_id": "Side_DB_cmpbol",
            "note_type": "test",
            "title": "Test Note",
            "content": "This is a test note",
            "severity": "info"
        }
        response = requests.post(f"{base_url}/knowledge/modules", json=test_note)
        if response.status_code == 201:
            print(f"   ✅ PASS: Created test note")
        else:
            print(f"   ⚠️  WARNING: Status {response.status_code} (DB may not be running)")
        
    except ImportError:
        print("   ⚠️  WARNING: requests library not installed, skipping API tests")
        print("   Install with: pip install requests")
    except Exception as e:
        print(f"   ⚠️  WARNING: API tests failed: {e}")
        print("   Make sure the backend server is running: uvicorn app.main:app --reload")

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("D&B EXPLORER ENHANCEMENT - PHASE 1 TESTS")
    print("="*60)
    
    test_module_categorization()
    test_excel_parsing()
    test_api_endpoints()
    
    print("\n" + "="*60)
    print("TESTING COMPLETE")
    print("="*60)
    print("\nNote: Some tests may show warnings if:")
    print("  - Excel files don't exist for all modules")
    print("  - Database is not running (for knowledge endpoints)")
    print("  - Backend server is not running (for API tests)")
    print("\nTo run the backend server:")
    print("  cd backend && uvicorn app.main:app --reload")

if __name__ == "__main__":
    main()
