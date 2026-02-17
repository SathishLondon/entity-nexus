"""
Comprehensive Test Suite for Phase 0A: D&B Reference Data Assistant
Tests knowledge base building, RAG retrieval, and question answering
"""

import sys
import os
import requests
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.reference_service import ReferenceService
from app.services.knowledge_base_builder import KnowledgeBaseBuilder
from app.services.reference_data_assistant import ReferenceDataAssistant


class TestResults:
    def __init__(self):
        self.passed = []
        self.failed = []
    
    def add_pass(self, test_name, details=""):
        self.passed.append((test_name, details))
        print(f"  ✅ {test_name}: {details}")
    
    def add_fail(self, test_name, error):
        self.failed.append((test_name, error))
        print(f"  ❌ {test_name}: {error}")
    
    def summary(self):
        total = len(self.passed) + len(self.failed)
        pass_rate = (len(self.passed) / total * 100) if total > 0 else 0
        print(f"\n{'='*70}")
        print(f"PHASE 0A TEST SUMMARY")
        print(f"{'='*70}")
        print(f"Total Tests: {total}")
        print(f"Passed: {len(self.passed)} ({pass_rate:.1f}%)")
        print(f"Failed: {len(self.failed)}")
        
        if self.failed:
            print(f"\n{'='*70}")
            print("FAILED TESTS:")
            for name, error in self.failed:
                print(f"  ❌ {name}: {error}")
        
        return len(self.failed) == 0


def test_knowledge_base_building():
    """Test knowledge base construction"""
    print("\n" + "="*70)
    print("TEST 1: Knowledge Base Building")
    print("="*70)
    
    results = TestResults()
    
    try:
        reference_service = ReferenceService()
        kb_builder = KnowledgeBaseBuilder(reference_service)
        
        # Build knowledge base
        kb = kb_builder.build()
        
        # Check structure
        if 'fields' in kb and 'modules' in kb:
            results.add_pass("Knowledge base structure", f"{len(kb['fields'])} fields, {len(kb['modules'])} modules")
        else:
            results.add_fail("Knowledge base structure", "Missing required keys")
        
        # Check field indexing
        if kb['field_index']:
            results.add_pass("Field indexing", f"{len(kb['field_index'])} unique field names")
        else:
            results.add_fail("Field indexing", "No fields indexed")
        
        # Check module indexing
        if kb['module_index']:
            results.add_pass("Module indexing", f"{len(kb['module_index'])} modules indexed")
        else:
            results.add_fail("Module indexing", "No modules indexed")
        
        # Check topic mappings
        if kb['topics']:
            results.add_pass("Topic mappings", f"{len(kb['topics'])} topics mapped")
        else:
            results.add_fail("Topic mappings", "No topics mapped")
        
        # Test field search
        search_results = kb_builder.search_fields("ownership")
        if search_results:
            results.add_pass("Field search", f"Found {len(search_results)} ownership-related fields")
        else:
            results.add_fail("Field search", "No results for 'ownership'")
        
        # Test module search by topic
        ownership_modules = kb_builder.find_modules_by_topic("ownership")
        if ownership_modules:
            results.add_pass("Module topic search", f"Found {len(ownership_modules)} ownership modules")
        else:
            results.add_fail("Module topic search", "No ownership modules found")
        
    except Exception as e:
        results.add_fail("Knowledge base building", str(e))
    
    return results


def test_assistant_service():
    """Test reference data assistant"""
    print("\n" + "="*70)
    print("TEST 2: Reference Data Assistant Service")
    print("="*70)
    
    results = TestResults()
    
    try:
        reference_service = ReferenceService()
        assistant = ReferenceDataAssistant(reference_service)
        
        # Test questions
        test_questions = [
            "Where can I find ownership information?",
            "What's the difference between DUNS and registration number?",
            "How do I get financial data?",
            "Show me all hierarchy-related endpoints",
        ]
        
        for question in test_questions:
            print(f"\nQuestion: {question}")
            try:
                response = assistant.ask(question)
                
                # Check response structure
                if 'answer' in response:
                    results.add_pass(f"Answer for: {question[:40]}...", f"{len(response['answer'])} chars")
                else:
                    results.add_fail(f"Answer for: {question[:40]}...", "No answer field")
                
                # Check relevant modules
                if response.get('relevant_modules'):
                    print(f"  📦 Modules: {[m['id'] for m in response['relevant_modules'][:2]]}")
                
                # Check actions
                if response.get('try_it_actions'):
                    print(f"  🎯 Actions: {len(response['try_it_actions'])}")
                
            except Exception as e:
                results.add_fail(f"Question: {question[:40]}...", str(e))
        
        # Test suggested questions
        suggestions = assistant.get_suggested_questions()
        if suggestions and len(suggestions) > 0:
            results.add_pass("Suggested questions", f"{len(suggestions)} suggestions")
        else:
            results.add_fail("Suggested questions", "No suggestions")
        
    except Exception as e:
        results.add_fail("Assistant service", str(e))
    
    return results


def test_api_endpoints():
    """Test API endpoints"""
    print("\n" + "="*70)
    print("TEST 3: API Endpoints")
    print("="*70)
    
    results = TestResults()
    BASE_URL = "http://localhost:8000"
    
    # Test /ask endpoint
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/assistant/ask",
            json={"question": "Where can I find ownership information?"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            results.add_pass("POST /assistant/ask", f"Got answer: {len(data.get('answer', ''))} chars")
            
            # Check response structure
            if data.get('relevant_modules'):
                print(f"  📦 Modules: {[m['id'] for m in data['relevant_modules'][:2]]}")
            if data.get('try_it_actions'):
                print(f"  🎯 Actions: {len(data['try_it_actions'])}")
        else:
            results.add_fail("POST /assistant/ask", f"Status {response.status_code}")
    except Exception as e:
        results.add_fail("POST /assistant/ask", str(e))
    
    # Test /suggest-questions endpoint
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/assistant/suggest-questions",
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            questions = data.get('questions', [])
            results.add_pass("GET /assistant/suggest-questions", f"{len(questions)} questions")
            print(f"  Sample: {questions[0] if questions else 'None'}")
        else:
            results.add_fail("GET /assistant/suggest-questions", f"Status {response.status_code}")
    except Exception as e:
        results.add_fail("GET /assistant/suggest-questions", str(e))
    
    # Test /render-example endpoint
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/assistant/render-example",
            json={"module_id": "Standard_DB_companyinfo_L1"},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            results.add_pass("POST /assistant/render-example", "Sample data retrieved")
        else:
            results.add_fail("POST /assistant/render-example", f"Status {response.status_code}")
    except Exception as e:
        results.add_fail("POST /assistant/render-example", str(e))
    
    return results


def test_regression():
    """Regression test - ensure previous phases still work"""
    print("\n" + "="*70)
    print("TEST 4: Regression Testing (Phases 0-4)")
    print("="*70)
    
    results = TestResults()
    BASE_URL = "http://localhost:8000"
    
    # Phase 0: Agent parse-query
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/agent/parse-query",
            json={"query": "Show hierarchy for Apple Inc"},
            timeout=5
        )
        if response.status_code == 200:
            results.add_pass("Phase 0: Agent parse-query", "Working")
        else:
            results.add_fail("Phase 0: Agent parse-query", f"Status {response.status_code}")
    except Exception as e:
        results.add_fail("Phase 0: Agent parse-query", str(e))
    
    # Phase 1: Get modules
    try:
        response = requests.get(f"{BASE_URL}/api/v1/references/modules", timeout=5)
        if response.status_code == 200:
            results.add_pass("Phase 1: Get modules", "Working")
        else:
            results.add_fail("Phase 1: Get modules", f"Status {response.status_code}")
    except Exception as e:
        results.add_fail("Phase 1: Get modules", str(e))
    
    # Phase 2: Module analysis
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/references/Standard_DB_companyinfo_L1/analyze",
            timeout=5
        )
        if response.status_code == 200:
            results.add_pass("Phase 2: Module analysis", "Working")
        else:
            results.add_fail("Phase 2: Module analysis", f"Status {response.status_code}")
    except Exception as e:
        results.add_fail("Phase 2: Module analysis", str(e))
    
    # Phase 3: Field mappings
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/references/Standard_DB_companyinfo_L1/mappings",
            timeout=5
        )
        if response.status_code == 200:
            results.add_pass("Phase 3: Field mappings", "Working")
        else:
            results.add_fail("Phase 3: Field mappings", f"Status {response.status_code}")
    except Exception as e:
        results.add_fail("Phase 3: Field mappings", str(e))
    
    # Phase 4: Hierarchy
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/references/hierarchy/summary",
            timeout=5
        )
        if response.status_code == 200:
            results.add_pass("Phase 4: Hierarchy summary", "Working")
        else:
            results.add_fail("Phase 4: Hierarchy summary", f"Status {response.status_code}")
    except Exception as e:
        results.add_fail("Phase 4: Hierarchy summary", str(e))
    
    return results


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("PHASE 0A COMPREHENSIVE TEST SUITE")
    print("D&B Reference Data Assistant")
    print("="*70)
    
    all_results = []
    
    # Run tests
    all_results.append(test_knowledge_base_building())
    all_results.append(test_assistant_service())
    all_results.append(test_api_endpoints())
    all_results.append(test_regression())
    
    # Combined summary
    print("\n" + "="*70)
    print("OVERALL TEST SUMMARY")
    print("="*70)
    
    total_passed = sum(len(r.passed) for r in all_results)
    total_failed = sum(len(r.failed) for r in all_results)
    total_tests = total_passed + total_failed
    pass_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
    
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {total_passed} ({pass_rate:.1f}%)")
    print(f"Failed: {total_failed}")
    
    if total_failed == 0:
        print("\n✅ ALL TESTS PASSED!")
    else:
        print(f"\n⚠️  {total_failed} TESTS FAILED")
    
    print("="*70)
    
    return total_failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
