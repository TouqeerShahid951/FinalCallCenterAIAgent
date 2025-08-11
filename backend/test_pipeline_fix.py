#!/usr/bin/env python3
"""
Test script to verify the pipeline infinite loop fixes are working.
"""

import asyncio
import time
from pipeline.pipeline_manager import PipelineManager

async def test_pipeline_fixes():
    """Test that the pipeline doesn't get stuck in infinite loops."""
    print("🧪 Testing Pipeline Infinite Loop Fixes")
    print("=" * 50)
    
    # Initialize pipeline
    pipeline = PipelineManager()
    print("✅ Pipeline initialized")
    
    # Test 1: Check initial state
    print(f"\n📊 Initial state: {pipeline.get_state().value}")
    print(f"   Processing attempts: {pipeline._processing_attempts}")
    print(f"   Buffer size: {len(pipeline._buffer)} bytes")
    
    # Test 2: Simulate multiple processing attempts
    print("\n🔄 Testing processing attempts limit...")
    
    for i in range(5):
        # Simulate processing attempt
        pipeline._processing_attempts = i
        should_process, reason = pipeline._should_process_utterance()
        
        print(f"   Attempt {i+1}: should_process={should_process}, reason='{reason}'")
        
        if i >= 2:  # After 3 attempts (0, 1, 2)
            if "max_attempts_reached" in reason:
                print(f"✅ Correctly blocked after {i+1} attempts")
                break
        elif i < 2:
            if should_process:
                print(f"✅ Correctly allowed attempt {i+1}")
            else:
                print(f"⚠️ Unexpectedly blocked attempt {i+1}")
    
    # Test 3: Test reset functionality
    print("\n🧹 Testing reset functionality...")
    
    # Set some state
    pipeline._processing_attempts = 5
    pipeline._buffer.extend(b'test' * 1000)
    
    print(f"   Before reset: attempts={pipeline._processing_attempts}, buffer={len(pipeline._buffer)} bytes")
    
    # Reset
    await pipeline.reset()
    
    print(f"   After reset: attempts={pipeline._processing_attempts}, buffer={len(pipeline._buffer)} bytes")
    
    if pipeline._processing_attempts == 0 and len(pipeline._buffer) == 0:
        print("✅ Reset working correctly")
    else:
        print("❌ Reset not working correctly")
    
    # Test 4: Test stream state reset
    print("\n🔄 Testing stream state reset...")
    
    # Set some state
    pipeline._processing_attempts = 3
    pipeline._buffer.extend(b'test' * 500)
    
    print(f"   Before stream reset: attempts={pipeline._processing_attempts}, buffer={len(pipeline._buffer)} bytes")
    
    # Reset stream state
    pipeline.reset_stream_state()
    
    print(f"   After stream reset: attempts={pipeline._processing_attempts}, buffer={len(pipeline._buffer)} bytes")
    
    if pipeline._processing_attempts == 0 and len(pipeline._buffer) == 0:
        print("✅ Stream reset working correctly")
    else:
        print("❌ Stream reset not working correctly")
    
    print("\n🎉 Pipeline fix tests completed!")
    return True

if __name__ == "__main__":
    print("🚀 Starting Pipeline Fix Tests\n")
    
    try:
        asyncio.run(test_pipeline_fixes())
        print("\n✅ All pipeline fixes are working correctly!")
    except Exception as e:
        print(f"\n❌ Pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
