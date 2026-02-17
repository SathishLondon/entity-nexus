"""
Test Phase 0 with Ollama running
"""

import requests
import json

def test_ollama_query_parsing():
    """Test query parsing with Ollama"""
    print("\n" + "="*70)
    print("TEST: Ollama-Powered Query Parsing")
    print("="*70)
    
    test_queries = [
        "Show me the hierarchy for Apple Inc",
        "Legal structure for DUNS 123456789",
        "Ownership of Microsoft Corporation",
        "Financial data for Tesla",
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        
        response = requests.post(
            "http://localhost:8000/api/v1/agent/parse-query",
            json={"query": query},
            timeout=30  # Ollama can take a bit longer
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ Entity: {data.get('entity_identifier')}")
            print(f"  ✅ Type: {data.get('identifier_type')}")
            print(f"  ✅ View: {data.get('view_type')}")
            print(f"  ✅ Modules: {', '.join(data.get('suggested_modules', [])[:2])}")
            print(f"  ✅ Confidence: {data.get('confidence')}")
            print(f"  ✅ Reasoning: {data.get('reasoning')}")
        else:
            print(f"  ❌ Error: {response.status_code}")


def test_status():
    """Test Ollama status"""
    print("\n" + "="*70)
    print("TEST: Ollama Status")
    print("="*70)
    
    response = requests.get("http://localhost:8000/api/v1/agent/status")
    data = response.json()
    
    print(f"\nOllama Available: {data['available']}")
    if data['available']:
        print(f"Models: {data['models']}")
        print(f"Current Model: {data.get('current_model')}")
    else:
        print(f"Reason: {data['reason']}")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("PHASE 0 - OLLAMA INTEGRATION TEST")
    print("="*70)
    
    test_status()
    test_ollama_query_parsing()
    
    print("\n" + "="*70)
    print("TESTS COMPLETE")
    print("="*70)
