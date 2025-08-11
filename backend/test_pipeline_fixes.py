#!/usr/bin/env python3
"""
Test script to verify the pipeline fixes for infinite loop prevention.
Tests the new session management and duplicate detection features.
"""

import asyncio
import time
from pipeline.pipeline_manager import PipelineManager
from pipeline.asr import StreamingASR

async def test_asr_session_management():
    """Test ASR session management methods."""
    print("\n🧪 Testing ASR Session Management...")
    
    asr = StreamingASR()
    
    # Test initial state
    print(f"Initial state: finalized={asr.finalized}, buffer_size={len(asr.audio_buffer)}")
    
    # Test is_session_active when empty
    assert not asr.is_session_active(), "Should not be active with empty buffer"
    print("✅ Empty buffer correctly identified as inactive")
    
    # Add some audio data
    test_audio = b'\x00\x00' * 1000  # Some dummy audio data
    asr.audio_buffer.extend(test_audio)
    
    # Test is_session_active with audio
    assert asr.is_session_active(), "Should be active with audio in buffer"
    print("✅ Audio buffer correctly identified as active")
    
    # Test finalize
    transcript = asr.finalize()
    print(f"Finalized transcript: '{transcript}'")
    assert asr.finalized, "Should be finalized after finalize()"
    
    # Test is_session_active after finalize
    assert not asr.is_session_active(), "Should not be active after finalize"
    print("✅ Correctly inactive after finalize")
    
    # Test reset_session
    asr.reset_session()
    assert not asr.finalized, "Should not be finalized after reset"
    assert len(asr.audio_buffer) == 0, "Buffer should be empty after reset"
    print("✅ Session reset correctly")
    
    print("🎉 ASR Session Management tests passed!")

async def test_pipeline_duplicate_detection():
    """Test pipeline duplicate transcript detection."""
    print("\n🧪 Testing Pipeline Duplicate Detection...")
    
    pipeline = PipelineManager()
    
    # Test initial state
    print(f"Initial state: is_processing={pipeline.is_processing}")
    assert not pipeline.is_processing, "Should not be processing initially"
    
    # Test duplicate detection with empty history
    result = pipeline._is_duplicate_transcript("Hello world")
    assert not result, "Should not detect duplicate with empty history"
    print("✅ No false positive on first transcript")
    
    # Test exact duplicate detection
    pipeline.last_processed_transcript = "Hello world"
    pipeline.last_processed_time = time.time()
    
    result = pipeline._is_duplicate_transcript("Hello world")
    assert result, "Should detect exact duplicate"
    print("✅ Exact duplicate detected")
    
    # Test time-based filtering
    pipeline.last_processed_time = time.time() - 3.0  # 3 seconds ago
    result = pipeline._is_duplicate_transcript("Hello world")
    assert not result, "Should not detect duplicate after sufficient time"
    print("✅ Time-based filtering works")
    
    # Test similarity detection
    pipeline.last_processed_time = time.time()
    result = pipeline._is_duplicate_transcript("Hello world!")
    # Note: "Hello world" vs "Hello world!" now has 1.0 similarity (100%) after punctuation fix
    assert result, "Should detect similar transcript"
    print("✅ Similar transcript detected")
    
    print("🎉 Pipeline Duplicate Detection tests passed!")

async def test_pipeline_processing_state():
    """Test pipeline processing state management."""
    print("\n🧪 Testing Pipeline Processing State...")
    
    pipeline = PipelineManager()
    
    # Test should_trigger_processing with no active session
    result = pipeline.should_trigger_processing(6.0, 5.0)  # 6s silence, 5s threshold
    assert not result, "Should not trigger without active ASR session"
    print("✅ Processing trigger correctly blocks without active session")
    
    # Create active ASR session by adding audio
    test_audio = b'\x00\x00' * 1000
    pipeline.asr.audio_buffer.extend(test_audio)
    
    # Test should_trigger_processing with active session
    result = pipeline.should_trigger_processing(6.0, 5.0)  # 6s silence, 5s threshold
    assert result, "Should trigger processing with sufficient silence and active session"
    print("✅ Processing trigger works with sufficient silence and active session")
    
    # Test should_trigger_processing with insufficient silence
    result = pipeline.should_trigger_processing(3.0, 5.0)  # 3s silence, 5s threshold
    assert not result, "Should not trigger processing with insufficient silence"
    print("✅ Processing trigger correctly blocks insufficient silence")
    
    # Test should_trigger_processing when already processing
    pipeline.is_processing = True
    result = pipeline.should_trigger_processing(6.0, 5.0)
    assert not result, "Should not trigger when already processing"
    print("✅ Processing trigger correctly blocks when already processing")
    
    # Reset state
    pipeline.is_processing = False
    
    print("🎉 Pipeline Processing State tests passed!")

async def test_pipeline_reset_functionality():
    """Test pipeline reset functionality."""
    print("\n🧪 Testing Pipeline Reset Functionality...")
    
    pipeline = PipelineManager()
    
    # Set some state
    pipeline.is_processing = True
    pipeline.last_processed_transcript = "Test transcript"
    pipeline.last_processed_time = time.time()
    pipeline._processing_attempts = 2
    
    # Test reset
    await pipeline.reset()
    
    assert not pipeline.is_processing, "Should reset processing flag"
    assert pipeline.last_processed_transcript == "", "Should reset transcript"
    assert pipeline.last_processed_time == 0, "Should reset time"
    assert pipeline._processing_attempts == 0, "Should reset attempts"
    
    print("🎉 Pipeline Reset tests passed!")

async def main():
    """Run all tests."""
    print("🚀 Starting Pipeline Fixes Tests...")
    
    try:
        await test_asr_session_management()
        await test_pipeline_duplicate_detection()
        await test_pipeline_processing_state()
        await test_pipeline_reset_functionality()
        
        print("\n🎉 All tests passed! The pipeline fixes are working correctly.")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
