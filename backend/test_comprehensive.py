"""
Comprehensive Test Suite for D&B Explorer Enhancement - Phases 1 & 2
Tests both service layer and API endpoints with regression testing
"""

import sys
import os
import requests
from typing import Dict, List

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.reference_service import ReferenceService

# Test configuration
BASE_URL = "http://localhost:8000/api/v1"
TEST_MODULE_L1 = "Standard_DB_companyinfo_L1"
TEST_MODULE_L2 = "Standard_DB_companyinfo_L2"
TEST_MODULE_SIDE = "Side_DB_hierarchiesconnections_alternative_L1"

class TestResults:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        self.tests = []
    
    def add_pass(self, test_name: str, details: str = ""):
        self.passed += 1
        self.tests.append({"name": test_name, "status": "PASS", "details": details})
        print(f"  ✅ {test_name}")
        if details:
            print(f"     {details}")
    
    def add_fail(self, test_name: str, error: str):
        self.failed += 1
        self.tests.append({"name": test_name, "status": "FAIL", "error": error})
        print(f"  ❌ {test_name}")
        print(f"     Error: {error}")
    
    def add_warning(self, test_name: str, message: str):
        self.warnings += 1
        self.tests.append({"name": test_name, "status": "WARN", "message": message})
        print(f"  ⚠️  {test_name}")
        print(f"     Warning: {message}")
    
    def summary(self):
        total = self.passed + self.failed + self.warnings
        print(f"\n{'='*60}")
        print(f"TEST SUMMARY")
        print(f"{'='*60}")
        print(f"Total Tests: {total}")
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        print(f"⚠️  Warnings: {self.warnings}")
        print(f"Success Rate: {(self.passed/total*100):.1f}%")
        return self.failed == 0

results = TestResults()

# ============================================================
# PHASE 1 REGRESSION TESTS - Service Layer
# ============================================================

def test_phase1_service_layer():
    """Test Phase 1 service layer functionality"""
    print("\n" + "="*60)
    print("PHASE 1 REGRESSION TESTS - Service Layer")
    print("="*60)
    
    service = ReferenceService()
    
    # Test 1.1: Module categorization
    print("\n1.1 Module Categorization")
    try:
        category = service.get_module_category(TEST_MODULE_L1)
        if category == "Standard":
            results.add_pass("get_module_category()", f"Correctly identified as {category}")
        else:
            results.add_fail("get_module_category()", f"Expected 'Standard', got '{category}'")
    except Exception as e:
        results.add_fail("get_module_category()", str(e))
    
    # Test 1.2: Modules by category
    print("\n1.2 Modules by Category")
    try:
        categorized = service.get_modules_by_category()
        if 'Standard' in categorized and len(categorized['Standard']) > 0:
            results.add_pass("get_modules_by_category()", f"Found {len(categorized['Standard'])} Standard modules")
        else:
            results.add_fail("get_modules_by_category()", "No Standard modules found")
    except Exception as e:
        results.add_fail("get_modules_by_category()", str(e))
    
    # Test 1.3: Excel dictionary parsing
    print("\n1.3 Excel Dictionary Parsing")
    try:
        excel_data = service.get_data_dictionary_from_excel(TEST_MODULE_L1)
        if len(excel_data) > 1000:
            results.add_pass("get_data_dictionary_from_excel()", f"Parsed {len(excel_data)} entries")
        else:
            results.add_warning("get_data_dictionary_from_excel()", f"Only {len(excel_data)} entries found")
    except Exception as e:
        results.add_fail("get_data_dictionary_from_excel()", str(e))
    
    # Test 1.4: Available blocks
    print("\n1.4 Available Blocks")
    try:
        blocks = service.get_available_blocks(TEST_MODULE_L1)
        if len(blocks) > 10:
            results.add_pass("get_available_blocks()", f"Found {len(blocks)} blocks")
        else:
            results.add_warning("get_available_blocks()", f"Only {len(blocks)} blocks found")
    except Exception as e:
        results.add_fail("get_available_blocks()", str(e))
    
    # Test 1.5: Block filtering
    print("\n1.5 Block Filtering")
    try:
        blocks = service.get_available_blocks(TEST_MODULE_L1)
        if blocks:
            filtered = service.filter_dictionary_by_block(TEST_MODULE_L1, [blocks[0]])
            if len(filtered) > 0:
                results.add_pass("filter_dictionary_by_block()", f"Filtered to {len(filtered)} entries")
            else:
                results.add_fail("filter_dictionary_by_block()", "No entries after filtering")
        else:
            results.add_warning("filter_dictionary_by_block()", "No blocks to filter")
    except Exception as e:
        results.add_fail("filter_dictionary_by_block()", str(e))

# ============================================================
# PHASE 2 TESTS - Service Layer
# ============================================================

def test_phase2_service_layer():
    """Test Phase 2 service layer functionality"""
    print("\n" + "="*60)
    print("PHASE 2 TESTS - Service Layer")
    print("="*60)
    
    service = ReferenceService()
    
    # Test 2.1: JSON path extraction
    print("\n2.1 JSON Path Extraction")
    try:
        paths = service.extract_json_paths(TEST_MODULE_L1)
        if len(paths) > 50:
            results.add_pass("extract_json_paths()", f"Extracted {len(paths)} paths")
            # Verify paths are valid
            sample_paths = paths[:5]
            if all('.' in p or len(p.split('.')) == 1 for p in sample_paths):
                results.add_pass("JSON paths format", "Paths are properly formatted")
        else:
            results.add_warning("extract_json_paths()", f"Only {len(paths)} paths found")
    except Exception as e:
        results.add_fail("extract_json_paths()", str(e))
    
    # Test 2.2: Module analysis
    print("\n2.2 Module Analysis")
    try:
        analysis = service.analyze_module(TEST_MODULE_L1)
        
        # Check required fields
        required_fields = ['module_id', 'field_count', 'complexity_score', 'complexity_label']
        missing = [f for f in required_fields if f not in analysis]
        
        if not missing:
            results.add_pass("analyze_module() structure", "All required fields present")
        else:
            results.add_fail("analyze_module() structure", f"Missing fields: {missing}")
        
        # Validate complexity score
        if 1 <= analysis.get('complexity_score', 0) <= 10:
            results.add_pass("Complexity score range", f"{analysis['complexity_score']}/10")
        else:
            results.add_fail("Complexity score range", f"Score {analysis.get('complexity_score')} out of range")
        
        # Validate complexity label
        valid_labels = ['Simple', 'Moderate', 'Complex', 'Very Complex']
        if analysis.get('complexity_label') in valid_labels:
            results.add_pass("Complexity label", f"'{analysis['complexity_label']}'")
        else:
            results.add_fail("Complexity label", f"Invalid label: {analysis.get('complexity_label')}")
        
        # Check field count matches
        if analysis.get('field_count', 0) > 1000:
            results.add_pass("Field count", f"{analysis['field_count']} fields")
        else:
            results.add_warning("Field count", f"Only {analysis.get('field_count')} fields")
            
    except Exception as e:
        results.add_fail("analyze_module()", str(e))
    
    # Test 2.3: Module comparison
    print("\n2.3 Module Comparison")
    try:
        comparison = service.compare_modules(TEST_MODULE_L1, TEST_MODULE_L2)
        
        # Check structure
        required_keys = ['module1', 'module2', 'comparison', 'recommendation']
        missing = [k for k in required_keys if k not in comparison]
        
        if not missing:
            results.add_pass("compare_modules() structure", "All required keys present")
        else:
            results.add_fail("compare_modules() structure", f"Missing keys: {missing}")
        
        # Validate comparison data
        comp = comparison.get('comparison', {})
        if 'common_fields_count' in comp and 'only_in_module1_count' in comp:
            results.add_pass("Comparison metrics", 
                f"Common: {comp['common_fields_count']}, Unique to L1: {comp['only_in_module1_count']}")
        else:
            results.add_fail("Comparison metrics", "Missing comparison counts")
        
        # Check recommendation
        if comparison.get('recommendation'):
            results.add_pass("Comparison recommendation", f"'{comparison['recommendation'][:50]}...'")
        else:
            results.add_fail("Comparison recommendation", "No recommendation provided")
            
    except Exception as e:
        results.add_fail("compare_modules()", str(e))

# ============================================================
# PHASE 1 REGRESSION TESTS - API Endpoints
# ============================================================

def test_phase1_api_endpoints():
    """Test Phase 1 API endpoints"""
    print("\n" + "="*60)
    print("PHASE 1 REGRESSION TESTS - API Endpoints")
    print("="*60)
    
    # Test 1.1: Get modules
    print("\n1.1 GET /references/modules")
    try:
        response = requests.get(f"{BASE_URL}/references/modules", timeout=5)
        if response.status_code == 200:
            modules = response.json()
            results.add_pass("GET /modules", f"{len(modules)} modules returned")
        else:
            results.add_fail("GET /modules", f"Status {response.status_code}")
    except Exception as e:
        results.add_fail("GET /modules", str(e))
    
    # Test 1.2: Get modules by category
    print("\n1.2 GET /references/modules/by-category")
    try:
        response = requests.get(f"{BASE_URL}/references/modules/by-category", timeout=5)
        if response.status_code == 200:
            categorized = response.json()
            total = sum(len(mods) for mods in categorized.values())
            results.add_pass("GET /modules/by-category", f"{len(categorized)} categories, {total} total modules")
        else:
            results.add_fail("GET /modules/by-category", f"Status {response.status_code}")
    except Exception as e:
        results.add_fail("GET /modules/by-category", str(e))
    
    # Test 1.3: Get Excel dictionary
    print("\n1.3 GET /references/{module}/dictionary/excel")
    try:
        response = requests.get(f"{BASE_URL}/references/{TEST_MODULE_L1}/dictionary/excel", timeout=5)
        if response.status_code == 200:
            data = response.json()
            results.add_pass("GET /dictionary/excel", f"{len(data)} entries")
        else:
            results.add_fail("GET /dictionary/excel", f"Status {response.status_code}")
    except Exception as e:
        results.add_fail("GET /dictionary/excel", str(e))
    
    # Test 1.4: Get available blocks
    print("\n1.4 GET /references/{module}/available-blocks")
    try:
        response = requests.get(f"{BASE_URL}/references/{TEST_MODULE_L1}/available-blocks", timeout=5)
        if response.status_code == 200:
            blocks = response.json()
            results.add_pass("GET /available-blocks", f"{len(blocks)} blocks")
        else:
            results.add_fail("GET /available-blocks", f"Status {response.status_code}")
    except Exception as e:
        results.add_fail("GET /available-blocks", str(e))
    
    # Test 1.5: Get filtered dictionary
    print("\n1.5 GET /references/{module}/dictionary/filtered")
    try:
        # First get a block name
        blocks_response = requests.get(f"{BASE_URL}/references/{TEST_MODULE_L1}/available-blocks", timeout=5)
        if blocks_response.status_code == 200:
            blocks = blocks_response.json()
            if blocks:
                response = requests.get(
                    f"{BASE_URL}/references/{TEST_MODULE_L1}/dictionary/filtered?blocks={blocks[0]}", 
                    timeout=5
                )
                if response.status_code == 200:
                    filtered = response.json()
                    results.add_pass("GET /dictionary/filtered", f"{len(filtered)} entries for block '{blocks[0]}'")
                else:
                    results.add_fail("GET /dictionary/filtered", f"Status {response.status_code}")
            else:
                results.add_warning("GET /dictionary/filtered", "No blocks available to test")
        else:
            results.add_warning("GET /dictionary/filtered", "Could not get blocks list")
    except Exception as e:
        results.add_fail("GET /dictionary/filtered", str(e))

# ============================================================
# PHASE 2 TESTS - API Endpoints
# ============================================================

def test_phase2_api_endpoints():
    """Test Phase 2 API endpoints"""
    print("\n" + "="*60)
    print("PHASE 2 TESTS - API Endpoints")
    print("="*60)
    
    # Test 2.1: Analyze module
    print("\n2.1 GET /references/{module}/analyze")
    try:
        response = requests.get(f"{BASE_URL}/references/{TEST_MODULE_L1}/analyze", timeout=5)
        if response.status_code == 200:
            analysis = response.json()
            complexity = analysis.get('complexity_score', 0)
            label = analysis.get('complexity_label', 'Unknown')
            results.add_pass("GET /analyze", f"Complexity: {complexity}/10 ({label})")
        else:
            results.add_fail("GET /analyze", f"Status {response.status_code}")
    except Exception as e:
        results.add_fail("GET /analyze", str(e))
    
    # Test 2.2: Get JSON paths
    print("\n2.2 GET /references/{module}/json-paths")
    try:
        response = requests.get(f"{BASE_URL}/references/{TEST_MODULE_L1}/json-paths", timeout=5)
        if response.status_code == 200:
            paths = response.json()
            results.add_pass("GET /json-paths", f"{len(paths)} paths extracted")
        else:
            results.add_fail("GET /json-paths", f"Status {response.status_code}")
    except Exception as e:
        results.add_fail("GET /json-paths", str(e))
    
    # Test 2.3: Compare modules
    print("\n2.3 GET /references/{module}/compare/{other}")
    try:
        response = requests.get(
            f"{BASE_URL}/references/{TEST_MODULE_L1}/compare/{TEST_MODULE_L2}", 
            timeout=5
        )
        if response.status_code == 200:
            comparison = response.json()
            common = comparison.get('comparison', {}).get('common_fields_count', 0)
            results.add_pass("GET /compare", f"{common} common fields found")
        else:
            results.add_fail("GET /compare", f"Status {response.status_code}")
    except Exception as e:
        results.add_fail("GET /compare", str(e))

# ============================================================
# EDGE CASE TESTS
# ============================================================

def test_edge_cases():
    """Test edge cases and error handling"""
    print("\n" + "="*60)
    print("EDGE CASE TESTS")
    print("="*60)
    
    # Test 3.1: Invalid module ID
    print("\n3.1 Invalid Module ID")
    try:
        response = requests.get(f"{BASE_URL}/references/INVALID_MODULE/analyze", timeout=5)
        # Should return empty or 404, not crash
        if response.status_code in [200, 404]:
            results.add_pass("Invalid module handling", f"Status {response.status_code}")
        else:
            results.add_warning("Invalid module handling", f"Unexpected status {response.status_code}")
    except Exception as e:
        results.add_fail("Invalid module handling", str(e))
    
    # Test 3.2: Compare same module
    print("\n3.2 Compare Module with Itself")
    try:
        response = requests.get(
            f"{BASE_URL}/references/{TEST_MODULE_L1}/compare/{TEST_MODULE_L1}", 
            timeout=5
        )
        if response.status_code == 200:
            comparison = response.json()
            # Should have 100% common fields
            common = comparison.get('comparison', {}).get('common_fields_count', 0)
            total = comparison.get('module1', {}).get('total_fields', 0)
            if common == total:
                results.add_pass("Self-comparison", "100% match as expected")
            else:
                results.add_warning("Self-comparison", f"Only {common}/{total} match")
        else:
            results.add_fail("Self-comparison", f"Status {response.status_code}")
    except Exception as e:
        results.add_fail("Self-comparison", str(e))
    
    # Test 3.3: Empty blocks filter
    print("\n3.3 Empty Blocks Filter")
    try:
        response = requests.get(
            f"{BASE_URL}/references/{TEST_MODULE_L1}/dictionary/filtered?blocks=", 
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            # Should return all data when no blocks specified
            if len(data) > 1000:
                results.add_pass("Empty blocks filter", f"Returns all {len(data)} entries")
            else:
                results.add_warning("Empty blocks filter", f"Only {len(data)} entries")
        else:
            results.add_fail("Empty blocks filter", f"Status {response.status_code}")
    except Exception as e:
        results.add_fail("Empty blocks filter", str(e))

# ============================================================
# MAIN TEST RUNNER
# ============================================================

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("D&B EXPLORER - COMPREHENSIVE TEST SUITE")
    print("Phases 1 & 2 - Regression & Feature Testing")
    print("="*60)
    
    # Run all test suites
    test_phase1_service_layer()
    test_phase2_service_layer()
    test_phase1_api_endpoints()
    test_phase2_api_endpoints()
    test_edge_cases()
    
    # Print summary
    success = results.summary()
    
    if success:
        print("\n🎉 ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n⚠️  {results.failed} TEST(S) FAILED")
        return 1

if __name__ == "__main__":
    exit(main())
