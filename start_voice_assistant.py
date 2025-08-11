#!/usr/bin/env python3
"""
Quick start script for AI Voice Assistant
Handles environment setup and launches both backend and frontend
"""

import os
import sys
import subprocess
import time
import webbrowser
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    return True

def check_virtual_environment():
    """Check if virtual environment is activated."""
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ Virtual environment is active")
        return True
    else:
        print("⚠️ No virtual environment detected")
        print("Recommendation: Activate your virtual environment first")
        return False

def install_requirements():
    """Install required packages."""
    print("📦 Installing required packages...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ All packages installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install packages: {e}")
        return False

def check_api_key():
    """Check if OpenRouter API key is set."""
    api_key = os.getenv('OPENROUTER_API_KEY')
    if api_key and api_key.startswith('sk-or-'):
        print("✅ OpenRouter API key found")
        return True
    else:
        print("⚠️ OpenRouter API key not found")
        print("Set OPENROUTER_API_KEY environment variable for LLM responses")
        return False

def start_backend():
    """Start the FastAPI backend server."""
    print("🚀 Starting backend server...")
    backend_dir = Path("backend")
    if not backend_dir.exists():
        print("❌ Backend directory not found")
        return None
    
    try:
        # Set API key if not already set
        env = os.environ.copy()
        if not env.get('OPENROUTER_API_KEY'):
            env['OPENROUTER_API_KEY'] = 'sk-or-v1-demo-key'  # Demo key for testing
        
        process = subprocess.Popen([
            sys.executable, "-m", "uvicorn", "main:app",
            "--host", "127.0.0.1",
            "--port", "8000",
            "--reload"
        ], cwd=backend_dir, env=env)
        
        print("✅ Backend server starting on http://127.0.0.1:8000")
        return process
    except Exception as e:
        print(f"❌ Failed to start backend: {e}")
        return None

def start_frontend():
    """Start the frontend server."""
    print("🌐 Starting frontend server...")
    frontend_dir = Path("frontend")
    if not frontend_dir.exists():
        print("❌ Frontend directory not found")
        return None
    
    try:
        process = subprocess.Popen([
            sys.executable, "-m", "http.server", "3000"
        ], cwd=frontend_dir)
        
        print("✅ Frontend server starting on http://127.0.0.1:3000")
        return process
    except Exception as e:
        print(f"❌ Failed to start frontend: {e}")
        return None

def main():
    """Main startup function."""
    print("🎤 AI Voice Assistant Startup Script")
    print("=" * 50)
    
    # Check system requirements
    if not check_python_version():
        return
    
    check_virtual_environment()
    check_api_key()
    
    # Install requirements
    if not Path("requirements.txt").exists():
        print("❌ requirements.txt not found")
        return
    
    install_choice = input("\n📦 Install/update requirements? (y/n): ").lower()
    if install_choice in ['y', 'yes', '']:
        if not install_requirements():
            return
    
    # Start services
    print("\n🚀 Starting services...")
    
    backend_process = start_backend()
    if not backend_process:
        return
    
    # Wait for backend to start
    print("⏳ Waiting for backend to initialize...")
    time.sleep(5)
    
    frontend_process = start_frontend()
    if not frontend_process:
        backend_process.terminate()
        return
    
    # Wait for frontend to start
    time.sleep(2)
    
    # Open browser
    print("\n🌐 Opening voice assistant in browser...")
    try:
        webbrowser.open("http://127.0.0.1:3000")
    except:
        print("Could not open browser automatically")
    
    print("\n" + "=" * 50)
    print("🎉 AI Voice Assistant is ready!")
    print("\n📍 URLs:")
    print("   Frontend: http://127.0.0.1:3000")
    print("   Backend:  http://127.0.0.1:8000")
    print("   Demo:     http://127.0.0.1:3000/demo.html")
    print("\n⌨️ Commands:")
    print("   Ctrl+C: Stop all services")
    print("   Browser: Allow microphone permissions")
    print("   Click 'Start Call' to begin!")
    print("\n🎤 Ready to chat with your AI assistant!")
    
    try:
        # Keep both processes running
        while True:
            time.sleep(1)
            
            # Check if processes are still running
            if backend_process.poll() is not None:
                print("\n❌ Backend process stopped")
                break
            if frontend_process.poll() is not None:
                print("\n❌ Frontend process stopped")
                break
                
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down services...")
        
        if backend_process:
            backend_process.terminate()
        if frontend_process:
            frontend_process.terminate()
            
        print("✅ All services stopped")
        print("Thanks for using AI Voice Assistant! 👋")

if __name__ == "__main__":
    main()
