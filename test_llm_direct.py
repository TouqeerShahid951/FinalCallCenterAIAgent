#!/usr/bin/env python3
"""
Test LLM directly to diagnose response issues.
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Add backend to path
sys.path.append('./backend')

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_llm():
    """Test LLM directly."""
    print("🧪 Testing LLM directly...")
    
    # Check environment variables
    api_key = os.getenv("OPENROUTER_API_KEY")
    print(f"🔑 API Key found: {'Yes' if api_key else 'No'}")
    if api_key:
        print(f"🔑 API Key preview: {api_key[:20]}...")
    
    # Test LLM import
    try:
        from pipeline.llm import LLMWrapper
        print("✅ LLM import successful")
    except Exception as e:
        print(f"❌ LLM import failed: {e}")
        return
    
    # Test LLM initialization
    try:
        llm = LLMWrapper(provider="openrouter", model="openai/gpt-3.5-turbo")
        print("✅ LLM initialization successful")
    except Exception as e:
        print(f"❌ LLM initialization failed: {e}")
        return
    
    # Test LLM response
    try:
        test_prompt = "Hello, what is the company policy for returns?"
        print(f"🤖 Testing prompt: '{test_prompt}'")
        
        response = llm.generate(test_prompt, max_tokens=100)
        print(f"✅ LLM response: '{response}'")
        
        if response.startswith("❌"):
            print("❌ LLM returned error response")
        else:
            print("✅ LLM working correctly!")
            
    except Exception as e:
        print(f"❌ LLM generation failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_llm()
