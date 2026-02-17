"""
Comprehensive Test Suite for D&B Explorer Enhancement - Phases 1-4
Tests all phases with regression testing and detailed reporting
"""

import sys
import os
import requests
from typing import Dict, List
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.reference_service import ReferenceService

# Test configuration
BASE_URL = "http://localhost:8000/api/v1"
TEST_MODULE_L1 = "Standard_DB_companyinfo_L1"
TEST_MODULE_L2 = "Standard_DB_companyinfo_L2"
TEST_MODULE_HIERARCHY = "Standard_DB_Hierarchy_Connections"

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
        print(f"\n{'='*70}")
        print(f"TEST SUMMARY - PHASES 1-4")
        print(f"{'='*70}")
        print(f"Total Tests: {total}")
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        print(f"⚠️  Warnings: {self.warnings}")
        print(f"Success Rate: {(self.passed/total*100):.1f}%")
        return self.failed == 0

results = TestResults()

# ============================================================
# PHASE 1 REGRESSION TESTS
# ============================================================

def test_phase1():
    """Test Phase 1 - Backend Foundation"""
    print("\n" + "="*70)
    print("PHASE 1 REGRESSION TESTS - Backend Foundation")
    print("="*70)
    
    service = ReferenceService()
    
    # Service layer tests
    print("\n[Service Layer]")
    try:
        category = service.get_module_category(TEST_MODULE_L1)
        results.add_pass("Module categorization", f"{TEST_MODULE_L1} → {category}")
    except Exception as e:
        results.add_fail("Module categorization", str(e))
    
    try:
        categorized = service.get_modules_by_category()
        results.add_pass("Modules by category", f"{len(categorized)} categories")
    except Exception as e:
        results.add_fail("Modules by category", str(e))
    
    try:
        excel_data = service.get_data_dictionary_from_excel(TEST_MODULE_L1)
        results.add_pass("Excel dictionary parsing", f"{len(excel_data)} entries")
    except Exception as e:
        results.add_fail("Excel dictionary parsing", str(e))
    
    try:
        blocks = service.get_available_blocks(TEST_MODULE_L1)
        results.add_pass("Available blocks", f"{len(blocks)} blocks")
    except Exception as e:
        results.add_fail("Available blocks", str(e))
    
    # API endpoint tests
    print("\n[API Endpoints]")
    try:
        response = requests.get(f"{BASE_URL}/references/modules", timeout=5)
        if response.status_code == 200:
            results.add_pass("GET /modules", f"{len(response.json())} modules")
        else:
            results.add_fail("GET /modules", f"Status {response.status_code}")
    except Exception as e:
        results.add_fail("GET /modules", str(e))
    
    try:
        response = requests.get(f"{BASE_URL}/references/modules/by-category", timeout=5)
        if response.status_code == 200:
            results.add_pass("GET /modules/by-category", "Success")
        else:
            results.add_fail("GET /modules/by-category", f"Status {response.status_code}")
    except Exception as e:
        results.add_fail("GET /modules/by-category", str(e))

# ============================================================
# PHASE 2 REGRESSION TESTS
# ============================================================

def test_phase2():
    """Test Phase 2 - Analysis & Compare Features"""
    print("\n" + "="*70)
    print("PHASE 2 REGRESSION TESTS - Analysis & Compare")
    print("="*70)
    
    service = ReferenceService()
    
    # Service layer tests
    print("\n[Service Layer]")
    try:
        paths = service.extract_json_paths(TEST_MODULE_L1)
        results.add_pass("JSON path extraction", f"{len(paths)} paths")
    except Exception as e:
        results.add_fail("JSON path extraction", str(e))
    
    try:
        analysis = service.analyze_module(TEST_MODULE_L1)
        complexity = analysis.get('complexity_score', 0)
        label = analysis.get('complexity_label', 'Unknown')
        results.add_pass("Module analysis", f"Complexity: {complexity}/10 ({label})")
    except Exception as e:
        results.add_fail("Module analysis", str(e))
    
    try:
        comparison = service.compare_modules(TEST_MODULE_L1, TEST_MODULE_L2)
        common = comparison.get('comparison', {}).get('common_fields_count', 0)
        results.add_pass("Module comparison", f"{common} common fields")
    except Exception as e:
        results.add_fail("Module comparison", str(e))
    
    # API endpoint tests
    print("\n[API Endpoints]")
    try:
        response = requests.get(f"{BASE_URL}/references/{TEST_MODULE_L1}/analyze", timeout=5)
        if response.status_code == 200:
            data = response.json()
            results.add_pass("GET /analyze", f"Complexity: {data.get('complexity_score')}/10")
        else:
            results.add_fail("GET /analyze", f"Status {response.status_code}")
    except Exception as e:
        results.add_fail("GET /analyze", str(e))
    
    try:
        response = requests.get(f"{BASE_URL}/references/{TEST_MODULE_L1}/json-paths", timeout=5)
        if response.status_code == 200:
            results.add_pass("GET /json-paths", f"{len(response.json())} paths")
        else:
            results.add_fail("GET /json-paths", f"Status {response.status_code}")
    except Exception as e:
        results.add_fail("GET /json-paths", str(e))

# ============================================================
# PHASE 3 REGRESSION TESTS
# ============================================================

def test_phase3():
    """Test Phase 3 - Field Mapping Feature"""
    print("\n" + "="*70)
    print("PHASE 3 REGRESSION TESTS - Field Mapping")
    print("="*70)
    
    service = ReferenceService()
    
    # Service layer tests
    print("\n[Service Layer]")
    try:
        schema = service.get_canonical_schema_endpoint()
        total_fields = sum(len(fields) for fields in schema.values())
        results.add_pass("Canonical schema", f"{total_fields} fields in {len(schema)} categories")
    except Exception as e:
        results.add_fail("Canonical schema", str(e))
    
    try:
        mappings = service.suggest_field_mappings(TEST_MODULE_L1)
        total = mappings.get('summary', {}).get('total_suggestions', 0)
        exact = mappings.get('summary', {}).get('exact_matches', 0)
        results.add_pass("Field mapping suggestions", f"{total} suggestions, {exact} exact")
    except Exception as e:
        results.add_fail("Field mapping suggestions", str(e))
    
    # API endpoint tests
    print("\n[API Endpoints]")
    try:
        response = requests.get(f"{BASE_URL}/references/canonical-schema", timeout=5)
        if response.status_code == 200:
            schema = response.json()
            results.add_pass("GET /canonical-schema", f"{len(schema)} categories")
        else:
            results.add_fail("GET /canonical-schema", f"Status {response.status_code}")
    except Exception as e:
        results.add_fail("GET /canonical-schema", str(e))
    
    try:
        response = requests.get(f"{BASE_URL}/references/{TEST_MODULE_L1}/mappings", timeout=5)
        if response.status_code == 200:
            data = response.json()
            total = data.get('summary', {}).get('total_suggestions', 0)
            results.add_pass("GET /mappings", f"{total} suggestions")
        else:
            results.add_fail("GET /mappings", f"Status {response.status_code}")
    except Exception as e:
        results.add_fail("GET /mappings", str(e))

# ============================================================
# PHASE 4 TESTS
# ============================================================

def test_phase4():
    """Test Phase 4 - Hierarchy Visualization"""
    print("\n" + "="*70)
    print("PHASE 4 TESTS - Hierarchy Visualization")
    print("="*70)
    
    service = ReferenceService()
    
    # Service layer tests
    print("\n[Service Layer]")
    try:
        structure = service.extract_hierarchy_structure(TEST_MODULE_HIERARCHY)
        nodes = len(structure.get('nodes', []))
        depth = structure.get('summary', {}).get('max_depth', 0)
        results.add_pass("Hierarchy extraction", f"{nodes} nodes, depth {depth}")
    except Exception as e:
        results.add_fail("Hierarchy extraction", str(e))
    
    try:
        summary = service.get_hierarchy_summary()
        h_modules = summary.get('hierarchy_modules', 0)
        results.add_pass("Hierarchy summary", f"{h_modules} hierarchy-capable modules")
    except Exception as e:
        results.add_fail("Hierarchy summary", str(e))
    
    # API endpoint tests
    print("\n[API Endpoints]")
    try:
        response = requests.get(f"{BASE_URL}/references/{TEST_MODULE_HIERARCHY}/hierarchy", timeout=5)
        if response.status_code == 200:
            data = response.json()
            nodes = data.get('summary', {}).get('total_nodes', 0)
            results.add_pass("GET /hierarchy", f"{nodes} nodes extracted")
        else:
            results.add_fail("GET /hierarchy", f"Status {response.status_code}")
    except Exception as e:
        results.add_fail("GET /hierarchy", str(e))
    
    try:
        response = requests.get(f"{BASE_URL}/references/hierarchy/summary", timeout=5)
        if response.status_code == 200:
            data = response.json()
            h_modules = data.get('hierarchy_modules', 0)
            results.add_pass("GET /hierarchy/summary", f"{h_modules} modules")
        else:
            results.add_fail("GET /hierarchy/summary", f"Status {response.status_code}")
    except Exception as e:
        results.add_fail("GET /hierarchy/summary", str(e))
    
    # Save hierarchy data for visualization
    try:
        response = requests.get(f"{BASE_URL}/references/{TEST_MODULE_HIERARCHY}/hierarchy", timeout=5)
        if response.status_code == 200:
            with open('hierarchy_data.json', 'w') as f:
                json.dump(response.json(), f, indent=2)
            print(f"\n  📊 Hierarchy data saved to hierarchy_data.json")
    except Exception as e:
        print(f"\n  ⚠️  Could not save hierarchy data: {e}")

# ============================================================
# MAIN TEST RUNNER
# ============================================================

def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("D&B EXPLORER - COMPREHENSIVE TEST SUITE")
    print("Phases 1-4 - Full Regression Testing")
    print("="*70)
    
    # Run all test suites
    test_phase1()
    test_phase2()
    test_phase3()
    test_phase4()
    
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
