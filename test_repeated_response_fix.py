#!/usr/bin/env python3
"""
Test script to verify the repeated response fix is working.
This simulates the audio processing pipeline to ensure no duplicate responses.
"""

import asyncio
import time
from backend.pipeline.pipeline_manager import PipelineManager

async def test_repeated_response_fix():
    """Test that the pipeline doesn't generate repeated responses."""
    print("🧪 Testing Repeated Response Fix")
    print("=" * 50)
    
    # Initialize pipeline
    pipeline = PipelineManager()
    print("✅ Pipeline initialized")
    
    # Simulate audio data (same audio chunk multiple times)
    test_audio = b'\x00\x00' * 1000  # 1 second of silence at 16kHz
    
    print("\n📡 Testing with repeated audio chunks...")
    
    responses = []
    for i in range(5):
        print(f"\n🎵 Chunk {i+1}: Processing {len(test_audio)} bytes...")
        
        # Feed the same audio multiple times
        result = await pipeline.feed_audio_with_transcription(test_audio)
        
        if result:
            print(f"🔊 Response generated: {len(result.get('audio', b''))} bytes")
            print(f"📝 Text: {result.get('text', 'No text')}")
            responses.append(result)
        else:
            print("🔇 No response generated (expected for duplicate audio)")
        
        # Small delay between chunks
        await asyncio.sleep(0.1)
    
    print(f"\n📊 Results:")
    print(f"   Total responses: {len(responses)}")
    print(f"   Expected: 1 (only first chunk should generate response)")
    
    if len(responses) == 1:
        print("✅ SUCCESS: No repeated responses generated!")
    else:
        print(f"❌ FAILED: {len(responses)} responses generated (expected 1)")
    
    return len(responses) == 1

async def test_vad_reset():
    """Test that VAD properly resets between utterances."""
    print("\n\n🎤 Testing VAD Reset")
    print("=" * 30)
    
    pipeline = PipelineManager()
    
    # First utterance
    test_audio_1 = b'\x00\x00' * 2000  # 2 seconds
    print("🎵 First utterance...")
    result1 = await pipeline.feed_audio_with_transcription(test_audio_1)
    
    if result1:
        print("✅ First utterance processed")
    else:
        print("❌ First utterance failed")
    
    # Reset pipeline
    print("🔄 Resetting pipeline...")
    await pipeline.reset()
    
    # Second utterance (should work after reset)
    test_audio_2 = b'\x00\x00' * 2000  # 2 seconds
    print("🎵 Second utterance after reset...")
    result2 = await pipeline.feed_audio_with_transcription(test_audio_2)
    
    if result2:
        print("✅ Second utterance processed after reset")
        return True
    else:
        print("❌ Second utterance failed after reset")
        return False

if __name__ == "__main__":
    print("🚀 Testing Voice Assistant Repeated Response Fix")
    print("=" * 60)
    
    async def main():
        # Test 1: No repeated responses
        success1 = await test_repeated_response_fix()
        
        # Test 2: VAD reset functionality
        success2 = await test_vad_reset()
        
        print("\n" + "=" * 60)
        if success1 and success2:
            print("🎉 ALL TESTS PASSED! Repeated response issue is fixed!")
        else:
            print("⚠️  Some tests failed. Check the output above.")
    
    asyncio.run(main())
