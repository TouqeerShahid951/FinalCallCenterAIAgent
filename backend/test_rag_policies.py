#!/usr/bin/env python3
"""
Test script to verify that the RAG system can now answer questions about company policies.
"""

import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pipeline.rag import PolicyRAG

def test_rag_policies():
    """Test that the RAG system can answer policy questions."""
    print("🧪 Testing RAG System with Company Policies...")
    
    # Initialize RAG system
    rag = PolicyRAG()
    
    # Test questions
    test_questions = [
        "What is the return policy?",
        "How long is the warranty?",
        "What are the shipping costs?",
        "How can I create an account?",
        "What is your privacy policy?",
        "Do you price match?",
        "What are your technical support hours?"
    ]
    
    print(f"\n📝 Testing {len(test_questions)} policy questions...")
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n--- Question {i}: {question} ---")
        
        try:
            response = rag.respond(question)
            print(f"Response: {response}")
            
            # Check if response contains relevant information
            if len(response) > 50 and not response.startswith("I'd be happy to help! However"):
                print("✅ Good response - contains policy information")
            else:
                print("⚠️ Response seems generic or redirecting")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n🎉 RAG policy testing completed!")
    print("\nThe agent should now be able to answer questions about company policies instead of giving generic responses.")

if __name__ == "__main__":
    test_rag_policies()
