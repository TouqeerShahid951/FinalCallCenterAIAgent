#!/usr/bin/env python3
"""
Direct LLM test to verify the API is working correctly.
This bypasses the voice pipeline to test just the LLM component.
"""

import os
import asyncio
from pipeline.llm import LLMWrapper

async def test_llm_direct():
    """Test LLM directly without voice pipeline."""
    print("🧪 Direct LLM Test")
    print("=" * 50)
    
    # Test with OpenRouter
    try:
        llm = LLMWrapper(
            provider="openrouter",
            model="openai/gpt-3.5-turbo"
        )
        
        # Test a simple query
        prompt = "Hello, how are you? What are the company policies for rent?"
        print(f"📝 Prompt: {prompt}")
        
        response = llm.generate(prompt, max_tokens=200)
        print(f"🤖 Response: {response}")
        
        if response and "❌" not in response:
            print("✅ LLM is working correctly!")
            return True
        else:
            print("❌ LLM returned an error response")
            return False
            
    except Exception as e:
        print(f"❌ LLM test failed: {e}")
        return False

async def test_multiple_queries():
    """Test multiple queries to ensure no infinite loops."""
    print("\n🔄 Testing Multiple Queries")
    print("=" * 50)
    
    try:
        llm = LLMWrapper(provider="openrouter")
        
        queries = [
            "What is your return policy?",
            "How do I contact customer support?",
            "What are your shipping options?"
        ]
        
        for i, query in enumerate(queries, 1):
            print(f"\n📝 Query {i}: {query}")
            response = llm.generate(query, max_tokens=100)
            print(f"🤖 Response {i}: {response[:100]}...")
            
            if "❌" in response:
                print(f"❌ Query {i} failed")
                return False
        
        print("✅ All queries processed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Multiple queries test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Direct LLM Tests\n")
    
    # Run tests
    llm_works = asyncio.run(test_llm_direct())
    multiple_queries_work = asyncio.run(test_multiple_queries())
    
    print(f"\n📊 Results:")
    print(f"   Direct LLM: {'✅ Working' if llm_works else '❌ Failed'}")
    print(f"   Multiple queries: {'✅ Working' if multiple_queries_work else '❌ Failed'}")
    
    if llm_works and multiple_queries_work:
        print("\n🎉 LLM is working correctly! The issue is in the voice pipeline, not the LLM.")
    else:
        print("\n❌ LLM has issues that need fixing first.")
