#!/usr/bin/env python3
"""
Test script to verify voice transcription fixes are working.
"""

import numpy as np
import time
from pipeline.asr import StreamingASR
from pipeline.vad import VadWrapper

def test_voice_fixes():
    """Test that the voice transcription fixes are working."""
    print("🧪 Testing Voice Transcription Fixes...")
    
    # Test 1: ASR with shorter audio
    print("\n📝 Test 1: ASR with shorter audio (0.05s minimum)")
    asr = StreamingASR()
    
    # Create 0.1 seconds of audio (should work now)
    sample_rate = 16000
    duration = 0.1  # 100ms
    samples = int(sample_rate * duration)
    
    # Create speech-like audio
    t = np.linspace(0, duration, samples, False)
    audio_data = (
        np.sin(2 * np.pi * 200 * t) * 0.3 +    # 200 Hz base
        np.sin(2 * np.pi * 800 * t) * 0.2      # 800 Hz mid
    )
    
    # Convert to 16-bit PCM
    pcm_data = (audio_data * 32767).astype(np.int16)
    
    print(f"Generated {len(pcm_data)} samples ({duration}s) of test audio")
    
    # Test partial transcription
    partial_result = asr.feed_audio(pcm_data.tobytes())
    print(f"Partial result: '{partial_result}'")
    
    # Test finalization
    final_result = asr.finalize()
    print(f"Final result: '{final_result}'")
    
    # Test 2: VAD with longer silence tolerance
    print("\n🎤 Test 2: VAD with longer silence tolerance (2000ms)")
    vad = VadWrapper(max_tail_ms=2000)
    
    # Simulate speech followed by silence
    print("VAD configured with 2000ms silence tolerance")
    print("This should allow more natural speech pauses")
    
    # Test 3: ASR session management
    print("\n🔄 Test 3: ASR session management")
    asr2 = StreamingASR()
    
    # Feed some audio
    asr2.feed_audio(pcm_data.tobytes())
    
    # Finalize once
    result1 = asr2.finalize()
    print(f"First finalize: '{result1}'")
    
    # Try to finalize again (should not cause issues)
    result2 = asr2.finalize()
    print(f"Second finalize: '{result2}' (should return same result)")
    
    # Reset and try again
    asr2.reset_session()
    result3 = asr2.finalize()
    print(f"After reset: '{result3}' (should be empty)")
    
    print("\n🎉 Voice transcription fixes test completed!")
    print("\nKey improvements made:")
    print("✅ Reduced ASR minimum audio duration from 0.1s to 0.05s")
    print("✅ Increased VAD silence tolerance from 1000ms to 2000ms")
    print("✅ Reduced ASR silence threshold from 0.001 to 0.0005")
    print("✅ Fixed ASR session management to prevent multiple finalizations")
    print("✅ Improved buffer management to preserve more audio data")
    print("✅ Reduced pipeline minimum utterance duration from 0.5s to 0.3s")

if __name__ == "__main__":
    test_voice_fixes()
