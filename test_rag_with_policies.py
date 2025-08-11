#!/usr/bin/env python3
"""
Test the RAG system with real policy data.
"""

import os
import sys

# Set environment
os.environ["OPENROUTER_API_KEY"] = "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"

# Add backend to path
sys.path.append('./backend')

from pipeline.rag import PolicyRAG

def test_policy_queries():
    """Test various queries against the policy database."""
    print("🧪 Testing RAG with real policy data...\n")
    
    rag = PolicyRAG()
    
    test_queries = [
        "What is your return policy?",
        "How long do I have to return an item?", 
        "What about shipping costs for returns?",
        "Do you offer warranties?",
        "How much does shipping cost?",
        "What's the weather like today?",  # Should be rejected
        "Tell me a joke",  # Should be rejected
        "Can you help me with my account password?",
        "What payment methods do you accept?",
    ]
    
    for query in test_queries:
        print(f"❓ Query: {query}")
        response = rag.respond(query)
        print(f"🤖 Response: {response}")
        print("-" * 80)

if __name__ == "__main__":
    test_policy_queries()
