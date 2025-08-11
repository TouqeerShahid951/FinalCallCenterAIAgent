#!/usr/bin/env python3
"""
Simple LLM test to check what's working.
"""

import os
import sys
from pathlib import Path

# Add the pipeline directory to the path
sys.path.insert(0, str(Path(__file__).parent / "pipeline"))

from pipeline.llm import LLMWrapper

def test_simple_query():
    """Test LLM with a simple query."""
    print("🧪 Testing LLM with Simple Query...")
    
    # Test with invalid provider to see error handling
    try:
        llm = LLMWrapper(provider="invalid_provider")
        
        prompt = "What is the weather like today?"
        print(f"📝 Prompt: {prompt}")
        
        response = llm.generate(prompt, max_tokens=100)
        print(f"🤖 Response: {response}")
        
        if "❌ Invalid provider" in response:
            print("✅ LLM error handling is working correctly!")
            return True
        else:
            print("❌ LLM didn't handle invalid provider correctly")
            return False
            
    except Exception as e:
        print(f"❌ LLM test failed: {e}")
        return False

def test_openrouter_if_available():
    """Test OpenRouter if API key is available."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("⚠️ No OpenRouter API key found - skipping OpenRouter test")
        print("💡 To test OpenRouter, set OPENROUTER_API_KEY environment variable")
        print("💡 You can get a free API key from https://openrouter.ai/")
        return False
    
    print("\n🔑 Testing OpenRouter with API key...")
    try:
        llm = LLMWrapper(
            provider="openrouter",
            model="openai/gpt-3.5-turbo",
            api_key=api_key
        )
        
        prompt = "Tell me a short joke"
        print(f"📝 Prompt: {prompt}")
        
        response = llm.generate(prompt, max_tokens=50)
        print(f"🤖 Response: {response}")
        
        if "❌" not in response and len(response) > 10:
            print("✅ OpenRouter is working!")
            return True
        else:
            print("❌ OpenRouter failed")
            return False
            
    except Exception as e:
        print(f"❌ OpenRouter test failed: {e}")
        return False

def test_openrouter_without_key():
    """Test OpenRouter behavior when no API key is provided."""
    print("\n🔑 Testing OpenRouter without API key...")
    
    # Temporarily unset the API key to test the no-key scenario
    original_key = os.environ.get("OPENROUTER_API_KEY")
    if original_key:
        del os.environ["OPENROUTER_API_KEY"]
    
    try:
        llm = LLMWrapper(provider="openrouter")
        
        prompt = "Tell me a short joke"
        print(f"📝 Prompt: {prompt}")
        
        response = llm.generate(prompt, max_tokens=50)
        print(f"🤖 Response: {response}")
        
        if "❌ OpenRouter API key not configured" in response:
            print("✅ OpenRouter properly handles missing API key!")
            return True
        else:
            print("❌ OpenRouter didn't handle missing API key correctly")
            return False
            
    except Exception as e:
        print(f"❌ OpenRouter test failed: {e}")
        return False
    finally:
        # Restore the original API key
        if original_key:
            os.environ["OPENROUTER_API_KEY"] = original_key

if __name__ == "__main__":
    print("🚀 Simple LLM Test\n")
    
    # Test error handling
    error_handling_works = test_simple_query()
    
    # Test OpenRouter without API key
    openrouter_no_key_works = test_openrouter_without_key()
    
    # Test OpenRouter if available
    openrouter_works = test_openrouter_if_available()
    
    print(f"\n📊 Results:")
    print(f"   Error handling: {'✅ Working' if error_handling_works else '❌ Failed'}")
    print(f"   OpenRouter (no key): {'✅ Working' if openrouter_no_key_works else '❌ Failed'}")
    print(f"   OpenRouter (with key): {'✅ Working' if openrouter_works else '❌ Failed'}")
    
    if openrouter_works:
        print("\n🎉 Your LLM is working with OpenRouter API!")
    elif openrouter_no_key_works:
        print("\n⚠️ LLM error handling works, but you need an OpenRouter API key for real LLM responses")
        print("💡 Get a free API key from https://openrouter.ai/")
        print("💡 Then set OPENROUTER_API_KEY environment variable")
    else:
        print("\n❌ Your LLM has issues that need fixing")
