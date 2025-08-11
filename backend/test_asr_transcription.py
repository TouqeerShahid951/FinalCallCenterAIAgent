#!/usr/bin/env python3
"""
Test script to verify ASR transcription is working with the new fixes.
"""

import numpy as np
import time
from pipeline.asr import StreamingASR

def test_asr_transcription():
    """Test that ASR can transcribe audio properly."""
    print("🧪 Testing ASR Transcription...")
    
    # Initialize ASR
    asr = StreamingASR()
    
    # Create some dummy audio data (simulating speech)
    # Generate 2 seconds of audio at 16kHz
    sample_rate = 16000
    duration = 2.0  # 2 seconds
    samples = int(sample_rate * duration)
    
    # Create more complex audio to simulate speech (multiple frequencies)
    t = np.linspace(0, duration, samples, False)
    
    # Mix multiple frequencies to make it more speech-like
    audio_data = (
        np.sin(2 * np.pi * 200 * t) * 0.4 +    # 200 Hz base
        np.sin(2 * np.pi * 800 * t) * 0.3 +    # 800 Hz mid
        np.sin(2 * np.pi * 1200 * t) * 0.2 +   # 1200 Hz high
        np.sin(2 * np.pi * 1600 * t) * 0.1     # 1600 Hz very high
    )
    
    # Add some variation to make it more natural
    audio_data += np.random.normal(0, 0.05, len(audio_data))
    
    # Convert to 16-bit PCM
    pcm_data = (audio_data * 32767).astype(np.int16)
    
    print(f"Generated {len(pcm_data)} samples ({duration}s) of test audio")
    print(f"Audio RMS: {np.sqrt(np.mean((pcm_data.astype(np.float32) / 32767) ** 2)):.4f}")
    
    # Test partial transcription
    print("\n📝 Testing partial transcription...")
    partial_result = asr.feed_audio(pcm_data.tobytes())
    print(f"Partial result: '{partial_result}'")
    
    # Test finalization
    print("\n🔚 Testing finalization...")
    final_result = asr.finalize()
    print(f"Final result: '{final_result}'")
    
    # Test session management
    print(f"\n📊 Session state:")
    print(f"  - finalized: {asr.finalized}")
    print(f"  - buffer size: {len(asr.audio_buffer)} bytes")
    print(f"  - session active: {asr.is_session_active()}")
    
    # Test reset
    print("\n🔄 Testing session reset...")
    asr.reset_session()
    print(f"  - finalized: {asr.finalized}")
    print(f"  - buffer size: {len(asr.audio_buffer)} bytes")
    print(f"  - session active: {asr.is_session_active()}")
    
    print("\n🎉 ASR Transcription test completed!")

if __name__ == "__main__":
    test_asr_transcription()
