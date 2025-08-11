#!/usr/bin/env python3
"""
Test if the agent responds properly after fixing the RAG method call.
"""

import asyncio
import sys
import logging

# Add backend to path
sys.path.append('./backend')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_agent_response():
    """Test if the agent responds to a simple query."""
    try:
        from pipeline.pipeline_manager import PipelineManager
        
        print("🧪 Testing agent response...")
        
        # Initialize pipeline
        pipeline = PipelineManager(
            enable_parallel_processing=True,
            enable_partial_transcripts=False
        )
        
        print("✅ Pipeline initialized")
        
        # Test direct RAG response
        test_query = "Hello, what is the company policy for returns?"
        print(f"🤖 Testing query: '{test_query}'")
        
        response = pipeline.rag.respond(test_query)
        print(f"✅ RAG response: '{response}'")
        
        if response and not response.startswith("❌"):
            print("🎉 SUCCESS: Agent is responding!")
        else:
            print("❌ FAILED: Agent not responding properly")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_agent_response())
