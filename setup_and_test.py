#!/usr/bin/env python3
"""
Setup script to install dependencies and test the voice agent system.
Run this instead of using virtual environment for now.
"""

import subprocess
import sys
import os

def install_package(package):
    """Install a Python package using pip."""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package, "--user"])
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to install {package}: {e}")
        return False

def setup_environment():
    """Install required packages."""
    print("🔧 Setting up environment...")
    
    packages = [
        "fastapi==0.110.0",
        "uvicorn[standard]==0.29.0", 
        "requests==2.31.0",
        "sentence-transformers==2.5.1",
        "chromadb==0.4.24",
        "numpy==1.26.4"
    ]
    
    success_count = 0
    for package in packages:
        print(f"Installing {package}...")
        if install_package(package):
            success_count += 1
    
    print(f"✅ Installed {success_count}/{len(packages)} packages")
    return success_count == len(packages)

def test_openrouter():
    """Test OpenRouter API connection."""
    print("🔗 Testing OpenRouter API...")
    
    import requests
    
    api_key = "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"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    data = {
        "model": "openai/gpt-3.5-turbo",
        "messages": [{"role": "user", "content": "Hello! Say 'API working'"}],
        "max_tokens": 20
    }
    
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ OpenRouter API working!")
            print(f"Response: {result['choices'][0]['message']['content']}")
            return True
        else:
            print(f"❌ API Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def test_backend_import():
    """Test if backend modules can be imported."""
    print("🧩 Testing backend imports...")
    
    try:
        sys.path.insert(0, './backend')
        
        # Test imports
        from pipeline.llm import LLMWrapper
        print("✅ LLM module imported")
        
        from pipeline.rag import PolicyRAG  
        print("✅ RAG module imported")
        
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def run_backend_server():
    """Instructions to run the backend server."""
    print("\n🚀 To test the full system:")
    print("1. Set environment variable:")
    print('   $env:OPENROUTER_API_KEY="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"')
    print()
    print("2. Start the backend server:")
    print("   cd backend")
    print("   uvicorn main:app --reload --host 0.0.0.0 --port 8000")
    print()
    print("3. In another terminal, ingest policies:")
    print("   cd backend")  
    print("   python scripts/ingest_policies.py")
    print()
    print("4. Test the API at: http://localhost:8000/docs")
    print()
    print("5. For frontend testing:")
    print("   cd frontend")
    print("   npm install")
    print("   npm run dev")
    print("   Open http://localhost:5173")

def main():
    """Main setup and test function."""
    print("🎯 Voice Agent Setup & Test\n")
    
    # Setup
    if not setup_environment():
        print("⚠️  Some packages failed to install, but continuing...")
    
    # Test API
    api_works = test_openrouter()
    
    # Test imports
    imports_work = test_backend_import()
    
    # Results
    print("\n📊 Test Results:")
    print("=" * 30)
    print(f"OpenRouter API: {'✅ PASS' if api_works else '❌ FAIL'}")
    print(f"Backend Imports: {'✅ PASS' if imports_work else '❌ FAIL'}")
    
    if api_works and imports_work:
        print("\n🎉 System ready for testing!")
        run_backend_server()
    else:
        print("\n⚠️  Some tests failed. Check the errors above.")

if __name__ == "__main__":
    main()
