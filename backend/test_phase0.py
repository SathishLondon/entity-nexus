"""
Test suite for Phase 0: Basic AI Agent
Tests query parsing with and without Ollama
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.basic_agent_service import BasicAgentService, QueryIntent


def test_fallback_parsing():
    """Test fallback parsing without Ollama"""
    print("\n" + "="*70)
    print("TEST: Fallback Parsing (No Ollama)")
    print("="*70)
    
    agent = BasicAgentService()
    
    test_queries = [
        "Show me the hierarchy for Apple Inc",
        "Legal structure for DUNS 123456789",
        "Ownership of Microsoft Corporation",
        "Financial data for Tesla",
        "Family tree for DUNS 987654321",
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        intent = agent._fallback_parse(query)
        print(f"  Entity: {intent.entity_identifier}")
        print(f"  Type: {intent.identifier_type}")
        print(f"  View: {intent.view_type}")
        print(f"  Modules: {', '.join(intent.suggested_modules[:2])}")
        print(f"  Confidence: {intent.confidence}")


def test_module_suggestions():
    """Test module suggestion logic"""
    print("\n" + "="*70)
    print("TEST: Module Suggestions")
    print("="*70)
    
    agent = BasicAgentService()
    
    test_intents = [
        QueryIntent(view_type="hierarchy"),
        QueryIntent(view_type="ownership"),
        QueryIntent(view_type="legal"),
        QueryIntent(view_type="financial"),
    ]
    
    for intent in test_intents:
        modules = agent._suggest_modules(intent)
        print(f"\nView Type: {intent.view_type}")
        print(f"  Suggested Modules: {modules}")


def test_ollama_status():
    """Test Ollama availability check"""
    print("\n" + "="*70)
    print("TEST: Ollama Status Check")
    print("="*70)
    
    agent = BasicAgentService()
    status = agent.check_ollama_status()
    
    print(f"\nOllama Available: {status['available']}")
    if status['available']:
        print(f"Models: {status['models']}")
        print(f"Current Model: {status.get('current_model')}")
    else:
        print(f"Reason: {status['reason']}")


def test_api_endpoint():
    """Test API endpoint"""
    print("\n" + "="*70)
    print("TEST: API Endpoint")
    print("="*70)
    
    import requests
    
    try:
        # Test parse-query endpoint
        response = requests.post(
            "http://localhost:8000/api/v1/agent/parse-query",
            json={"query": "Show hierarchy for Apple Inc"},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            print("\n✅ Parse Query Endpoint Working")
            print(f"  Entity: {data.get('entity_identifier')}")
            print(f"  View Type: {data.get('view_type')}")
            print(f"  Modules: {data.get('suggested_modules')}")
        else:
            print(f"\n❌ Endpoint returned status {response.status_code}")
            
        # Test status endpoint
        response = requests.get(
            "http://localhost:8000/api/v1/agent/status",
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            print("\n✅ Status Endpoint Working")
            print(f"  Available: {data.get('available')}")
        else:
            print(f"\n❌ Status endpoint returned {response.status_code}")
            
    except Exception as e:
        print(f"\n❌ Error testing API: {e}")


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("PHASE 0 TEST SUITE - Basic AI Agent")
    print("="*70)
    
    test_fallback_parsing()
    test_module_suggestions()
    test_ollama_status()
    test_api_endpoint()
    
    print("\n" + "="*70)
    print("PHASE 0 TESTS COMPLETE")
    print("="*70)


if __name__ == "__main__":
    main()
