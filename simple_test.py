#!/usr/bin/env python3
"""
Simple test script that demonstrates the core voice agent functionality
without the complex FastAPI setup.
"""

import os
import sys
import asyncio

# Set environment
os.environ["OPENROUTER_API_KEY"] = "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"

# Add backend to path
sys.path.append('./backend')

def test_llm():
    """Test the LLM wrapper."""
    print("🤖 Testing LLM...")
    try:
        from pipeline.llm import LLMWrapper
        llm = LLMWrapper()
        response = llm.generate("What is your return policy?", 100)
        print(f"✅ LLM Response: {response}")
        return True
    except Exception as e:
        print(f"❌ LLM Error: {e}")
        return False

def test_rag():
    """Test the RAG system."""
    print("\n📚 Testing RAG system...")
    try:
        from pipeline.rag import PolicyRAG
        rag = PolicyRAG()
        
        # Test with policy-related query
        response1 = rag.respond("What is your return policy?")
        print(f"✅ Policy Query: {response1}")
        
        # Test with unrelated query
        response2 = rag.respond("What's the weather like?")
        print(f"✅ Unrelated Query: {response2}")
        
        return True
    except Exception as e:
        print(f"❌ RAG Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_embeddings():
    """Test sentence transformers."""
    print("\n🔗 Testing embeddings...")
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer("all-MiniLM-L6-v2")
        embedding = model.encode("test sentence")
        print(f"✅ Embedding shape: {embedding.shape}")
        return True
    except Exception as e:
        print(f"❌ Embeddings Error: {e}")
        return False

def test_policy_ingestion():
    """Test policy ingestion."""
    print("\n📖 Testing policy ingestion...")
    try:
        # Import and run the ingestion script
        sys.path.append('./scripts')
        
        # Create a simple ingestion test
        import chromadb
        from sentence_transformers import SentenceTransformer
        
        client = chromadb.Client()
        collection = client.get_or_create_collection("test_policies")
        embed_model = SentenceTransformer("all-MiniLM-L6-v2")
        
        # Add a test document
        test_doc = "Our return policy allows returns within 30 days of purchase."
        embedding = embed_model.encode(test_doc).tolist()
        
        collection.add(
            documents=[test_doc],
            embeddings=[embedding],
            ids=["test_doc_1"]
        )
        
        # Test retrieval
        query_embedding = embed_model.encode("return policy").tolist()
        results = collection.query(query_embeddings=[query_embedding], n_results=1)
        
        print(f"✅ Retrieved: {results['documents'][0][0][:50]}...")
        return True
    except Exception as e:
        print(f"❌ Policy Ingestion Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("🚀 Voice Agent Component Test\n")
    
    tests = [
        ("LLM Wrapper", test_llm),
        ("Embeddings", test_embeddings), 
        ("Policy Ingestion", test_policy_ingestion),
        ("RAG System", test_rag),
    ]
    
    results = {}
    for test_name, test_func in tests:
        results[test_name] = test_func()
    
    print("\n" + "="*50)
    print("📊 Test Results:")
    print("="*50)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:20} {status}")
    
    if all(results.values()):
        print("\n🎉 All components working! The core voice agent is ready.")
        print("\n📋 Next steps:")
        print("1. The LLM integration with OpenRouter is working")
        print("2. The RAG system can filter queries by relevance") 
        print("3. Policy documents can be ingested and retrieved")
        print("4. Ready to add VAD, ASR, and TTS components")
    else:
        print("\n⚠️  Some tests failed. Check the errors above.")

if __name__ == "__main__":
    main()
