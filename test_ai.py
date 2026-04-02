import os
import sys

# Add the project root to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings
from app.services import llm_service
from app.services import meeting_service

def test_config():
    print("=== Configuration Check ===")
    print(f"AI Provider: {settings.AI_PROVIDER}")
    print(f"Groq Model:  {settings.GROQ_MODEL}")
    print(f"Groq API Key: {'Set' if settings.GROQ_API_KEY else 'NOT SET'}")
    print(f"Anthropic Key: {'Set' if settings.ANTHROPIC_API_KEY else 'NOT SET'}")
    print("-" * 30)

def test_intent_classification():
    print("=== Intent Classification Test ===")
    queries = [
        "Create a new lead for John Doe",
        "How do I add a deal?",
        "Show my pipeline",
        "What's the weather like?"
    ]
    for q in queries:
        intent = llm_service.classify_query(q)
        print(f"Query:  {q}")
        print(f"Intent: {intent}")
        print()
    print("-" * 30)

def test_meeting_extraction():
    print("=== Meeting Extraction Test ===")
    transcript = """
    We had a great meeting with Acme Corp. 
    Sarah will send the contract by Friday. 
    We need to schedule a follow-up demo for next Tuesday. 
    The client is interested in the enterprise plan.
    """
    summary, tasks, points = meeting_service.process_transcript(transcript)
    print(f"Summary: {summary}")
    print("Tasks:")
    for t in tasks:
        print(f"  - {t['content']} (Owner: {t.get('owner')}, Due: {t.get('deadline')})")
    print("Points:")
    for p in points:
        print(f"  - {p['content']}")
    print("-" * 30)

if __name__ == "__main__":
    test_config()
    test_intent_classification()
    test_meeting_extraction()
