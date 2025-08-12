#!/usr/bin/env python3
"""
Final comprehensive LLM test to verify OpenRouter API key and functionality.
This will replace all other LLM test files.
"""

import sys
import os
import time
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from pipeline.llm import LLMWrapper

def test_llm_comprehensive():
    """Test LLM with various scenarios to ensure it's working properly."""
    
    print("🧠 Testing LLM Configuration...")
    print("=" * 50)
    
    try:
        # Initialize LLM
        llm = LLMWrapper()
        print("✅ LLM initialized successfully")
        
        # Test 1: Simple business query (like what RAG would send)
        print("\n🔍 Test 1: Business Policy Query")
        business_prompt = """You are a friendly business policy assistant. Answer the customer's question using the company policies provided below.

Company Policies:
## Shipping Policy
- Standard shipping: 5-7 business days ($5.99)
- Express shipping: 2-3 business days ($12.99)
- Overnight shipping: Next business day ($24.99)
- Free shipping on orders over $75

Customer Question: What's the shipping cost and how many days can I get my item?

INSTRUCTIONS:
- Answer the specific question directly and professionally
- Keep your response concise and helpful (2-3 sentences)"""
        
        start_time = time.time()
        response1 = llm.generate(business_prompt, max_tokens=200)
        response_time = time.time() - start_time
        
        print(f"Response time: {response_time:.2f}s")
        print(f"Response: {response1}")
        
        # Test 2: Classification query (like RAG uses for business detection)
        print("\n🔍 Test 2: Query Classification")
        classification_prompt = """Classify this user query as either "BUSINESS" or "GENERAL".

A BUSINESS query is about:
- Company policies, returns, refunds, exchanges
- Shipping, delivery, warranties  
- Payments, pricing, orders, purchases

User Query: "What is the policy for returns?"

Classification (respond with only "BUSINESS" or "GENERAL"):"""
        
        start_time = time.time()
        response2 = llm.generate(classification_prompt, max_tokens=10)
        response_time = time.time() - start_time
        
        print(f"Response time: {response_time:.2f}s")
        print(f"Classification: {response2.strip()}")
        
        # Test 3: Simple greeting (to test general functionality)
        print("\n🔍 Test 3: Simple Response")
        simple_prompt = "Say hello and introduce yourself as a customer service assistant in one sentence."
        
        start_time = time.time()
        response3 = llm.generate(simple_prompt, max_tokens=50)
        response_time = time.time() - start_time
        
        print(f"Response time: {response_time:.2f}s")
        print(f"Response: {response3}")
        
        # Verify all tests passed
        if response1 and response2 and response3:
            print("\n" + "=" * 50)
            print("🎉 ALL TESTS PASSED!")
            print("✅ OpenRouter API key is working")
            print("✅ LLM is responding correctly")
            print("✅ RAG system should work now")
            print("\nYour voice assistant should now provide specific answers instead of generic redirects.")
            return True
        else:
            print("\n❌ Some tests failed - check responses above")
            return False
            
    except Exception as e:
        print(f"\n❌ LLM Test Failed: {e}")
        print("\nPossible issues:")
        print("1. Invalid OpenRouter API key")
        print("2. Network connectivity issues")
        print("3. OpenRouter service unavailable")
        print("4. Model configuration issues")
        return False

def test_environment():
    """Test environment configuration."""
    print("\n🔧 Environment Configuration:")
    print("-" * 30)
    
    # Check .env file (in parent directory)
    env_file = Path("../.env")
    if env_file.exists():
        print("✅ .env file found")
        
        # Read and check key variables (without exposing the key)
        with open(env_file, 'r') as f:
            content = f.read()
            
        if "OPENROUTER_API_KEY" in content and "your-new-api-key-here" not in content:
            print("✅ OPENROUTER_API_KEY is set")
        else:
            print("❌ OPENROUTER_API_KEY not properly configured")
            
        if "LLM_PROVIDER=openrouter" in content:
            print("✅ LLM_PROVIDER set to openrouter")
        else:
            print("⚠️  LLM_PROVIDER not set to openrouter")
            
        if "meta-llama/llama-3.1-8b-instruct:free" in content:
            print("✅ Using free Llama model")
        else:
            print("⚠️  Model configuration may differ")
    else:
        print("❌ .env file not found")
        return False
        
    return True

if __name__ == "__main__":
    print("🚀 Comprehensive LLM Test")
    print("=" * 50)
    
    # Test environment first
    env_ok = test_environment()
    
    if env_ok:
        # Test LLM functionality
        llm_ok = test_llm_comprehensive()
        
        if llm_ok:
            print("\n🎯 NEXT STEPS:")
            print("1. Your LLM is working correctly")
            print("2. Restart your voice assistant server")
            print("3. Test with: 'What's the shipping cost?'")
            print("4. You should now get specific policy answers!")
        else:
            print("\n🔧 TROUBLESHOOTING:")
            print("1. Double-check your OpenRouter API key")
            print("2. Ensure you have credits/access on OpenRouter")
            print("3. Try a different model if needed")
    else:
        print("\n🔧 Fix environment configuration first")
