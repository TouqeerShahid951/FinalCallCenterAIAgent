#!/usr/bin/env python3
"""
Test script for LLM functionality.
Tests basic generation, error handling, and different prompt types.
"""

import os
import sys
import logging
from pathlib import Path

# Add the pipeline directory to the path
sys.path.insert(0, str(Path(__file__).parent / "pipeline"))

from llm import LLMWrapper

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_llm_basic():
    """Test basic LLM functionality."""
    print("🧪 Testing Basic LLM Functionality...")
    
    try:
        # Test with OpenRouter
        llm = LLMWrapper(
            provider="openrouter",
            model="openai/gpt-3.5-turbo",
            api_key=os.getenv("OPENROUTER_API_KEY")
        )
        
        # Test simple prompt
        prompt = "Hello! Can you tell me a short joke?"
        print(f"📝 Prompt: {prompt}")
        
        response = llm.generate(prompt, max_tokens=100)
        print(f"🤖 Response: {response}")
        print("✅ Basic LLM test passed!")
        
        return True
        
    except Exception as e:
        print(f"❌ Basic LLM test failed: {e}")
        return False

def test_llm_company_policy():
    """Test LLM with company policy related questions."""
    print("\n🏢 Testing Company Policy Questions...")
    
    try:
        llm = LLMWrapper(
            provider="openrouter",
            model="openai/gpt-3.5-turbo",
            api_key=os.getenv("OPENROUTER_API_KEY")
        )
        
        # Test company policy question
        prompt = "What are the company's policies regarding remote work?"
        print(f"📝 Prompt: {prompt}")
        
        response = llm.generate(prompt, max_tokens=150)
        print(f"🤖 Response: {response}")
        print("✅ Company policy test passed!")
        
        return True
        
    except Exception as e:
        print(f"❌ Company policy test failed: {e}")
        return False

def test_llm_fallback():
    """Test LLM fallback behavior."""
    print("\n🔄 Testing Fallback Behavior...")
    
    try:
        # Test with invalid provider
        llm = LLMWrapper(provider="invalid_provider")
        
        prompt = "This should use fallback"
        print(f"📝 Prompt: {prompt}")
        
        response = llm.generate(prompt, max_tokens=50)
        print(f"🤖 Response: {response}")
        
        if "company-related questions" in response.lower():
            print("✅ Fallback test passed!")
            return True
        else:
            print("❌ Fallback test failed - unexpected response")
            return False
        
    except Exception as e:
        print(f"❌ Fallback test failed: {e}")
        return False

def test_llm_error_handling():
    """Test LLM error handling."""
    print("\n⚠️ Testing Error Handling...")
    
    try:
        # Test with invalid API key
        llm = LLMWrapper(
            provider="openrouter",
            model="openai/gpt-3.5-turbo",
            api_key="invalid_key"
        )
        
        prompt = "This should fail gracefully"
        print(f"📝 Prompt: {prompt}")
        
        response = llm.generate(prompt, max_tokens=50)
        print(f"🤖 Response: {response}")
        
        if "trouble processing" in response.lower():
            print("✅ Error handling test passed!")
            return True
        else:
            print("❌ Error handling test failed - unexpected response")
            return False
        
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False

def main():
    """Run all LLM tests."""
    print("🚀 Starting LLM Tests...\n")
    
    tests = [
        test_llm_basic,
        test_llm_company_policy,
        test_llm_fallback,
        test_llm_error_handling
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your LLM is working correctly.")
    else:
        print("⚠️ Some tests failed. Check the output above for details.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
