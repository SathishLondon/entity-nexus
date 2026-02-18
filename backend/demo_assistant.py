"""
Live Demo of D&B Reference Data Assistant
Shows the assistant answering various questions about D&B data
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def demo_question(question: str):
    """Ask a question and display the response"""
    print("\n" + "="*70)
    print(f"❓ QUESTION: {question}")
    print("="*70)
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/assistant/ask",
            json={"question": question},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Display answer
            print("\n📝 ANSWER:")
            print(data['answer'])
            
            # Display relevant modules
            if data.get('relevant_modules'):
                print("\n📦 RELEVANT MODULES:")
                for module in data['relevant_modules'][:3]:
                    print(f"  - {module['id']}")
                    print(f"    Category: {module['category']}")
                    print(f"    Has Sample: {module['has_sample']}")
            
            # Display try-it actions
            if data.get('try_it_actions'):
                print("\n🎯 TRY IT ACTIONS:")
                for action in data['try_it_actions']:
                    print(f"  - {action['label']}")
            
            # Display related questions
            if data.get('related_questions'):
                print("\n💡 RELATED QUESTIONS:")
                for q in data['related_questions'][:2]:
                    print(f"  - {q}")
            
            return True
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def demo_suggested_questions():
    """Show suggested questions"""
    print("\n" + "="*70)
    print("💡 SUGGESTED QUESTIONS")
    print("="*70)
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/assistant/suggest-questions",
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            questions = data.get('questions', [])
            
            for i, q in enumerate(questions, 1):
                print(f"{i}. {q}")
            
            return True
        else:
            print(f"❌ Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    """Run the demo"""
    print("\n" + "="*70)
    print("🤖 D&B REFERENCE DATA ASSISTANT - LIVE DEMO")
    print("="*70)
    
    # Show suggested questions first
    demo_suggested_questions()
    
    # Demo various questions
    questions = [
        "Where can I find ownership information?",
        "What's the difference between DUNS and registration number?",
        "Show me all hierarchy-related endpoints",
        "How do I get financial data?",
    ]
    
    for question in questions:
        demo_question(question)
        input("\nPress Enter to continue...")
    
    print("\n" + "="*70)
    print("✅ DEMO COMPLETE")
    print("="*70)


if __name__ == "__main__":
    main()
