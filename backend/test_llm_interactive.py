#!/usr/bin/env python3
"""
Interactive LLM test script.
Allows manual testing with custom prompts.
"""

import os
import sys
from pathlib import Path

# Add the pipeline directory to the path
sys.path.insert(0, str(Path(__file__).parent / "pipeline"))

from llm import LLMWrapper

def main():
    """Interactive LLM testing."""
    print("🤖 Interactive LLM Testing")
    print("=" * 40)
    
    # Check for API key
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("❌ OPENROUTER_API_KEY environment variable not set!")
        print("Please set your OpenRouter API key and try again.")
        return
    
    print(f"✅ API key found: {api_key[:8]}...")
    
    try:
        # Initialize LLM
        print("\n🔧 Initializing LLM...")
        llm = LLMWrapper(
            provider="openrouter",
            model="openai/gpt-3.5-turbo",
            api_key=api_key
        )
        print("✅ LLM initialized successfully!")
        
        print("\n💡 Type your prompts below. Type 'quit' to exit.")
        print("-" * 40)
        
        while True:
            try:
                # Get user input
                prompt = input("\n📝 Your prompt: ").strip()
                
                if prompt.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                
                if not prompt:
                    print("⚠️ Please enter a prompt.")
                    continue
                
                # Get max tokens
                try:
                    max_tokens = input("🔢 Max tokens (default 100): ").strip()
                    max_tokens = int(max_tokens) if max_tokens else 100
                except ValueError:
                    max_tokens = 100
                    print("⚠️ Invalid input, using default: 100 tokens")
                
                # Generate response
                print(f"\n🔄 Generating response (max {max_tokens} tokens)...")
                response = llm.generate(prompt, max_tokens=max_tokens)
                
                print(f"\n🤖 Response:")
                print("-" * 30)
                print(response)
                print("-" * 30)
                
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
                print("Please try again.")
    
    except Exception as e:
        print(f"❌ Failed to initialize LLM: {e}")

if __name__ == "__main__":
    main()
