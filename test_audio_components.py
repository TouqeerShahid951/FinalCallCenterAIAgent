#!/usr/bin/env python3
"""
Test the new audio components (VAD, ASR, TTS) individually.
"""

import os
import sys
import numpy as np

# Set environment
os.environ["OPENROUTER_API_KEY"] = "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"

# Add backend to path
sys.path.append('./backend')

def test_vad():
    """Test Voice Activity Detection."""
    print("🎤 Testing VAD (Voice Activity Detection)...")
    try:
        from pipeline.vad import VadWrapper
        
        print("Loading Silero VAD model...")
        vad = VadWrapper()
        
        # Create test audio (sine wave to simulate speech)
        sample_rate = 16000
        duration = 1.0  # 1 second
        frequency = 440  # A4 note
        
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio_signal = np.sin(2 * np.pi * frequency * t) * 0.5
        audio_int16 = (audio_signal * 32767).astype(np.int16)
        audio_bytes = audio_int16.tobytes()
        
        # Test speech detection
        is_speech = vad.is_speech(audio_bytes)
        print(f"✅ VAD loaded and tested. Speech detected: {is_speech}")
        return True
        
    except Exception as e:
        print(f"❌ VAD Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_asr():
    """Test Automatic Speech Recognition."""
    print("\n🗣️ Testing ASR (Whisper)...")
    try:
        from pipeline.asr import StreamingASR
        
        print("Loading Whisper model (this may take a moment)...")
        asr = StreamingASR(model_name="tiny")  # Use tiny model for faster loading
        
        # Create test audio (silence, but valid format)
        sample_rate = 16000
        duration = 1.0
        audio_signal = np.zeros(int(sample_rate * duration))
        audio_int16 = (audio_signal * 32767).astype(np.int16)
        audio_bytes = audio_int16.tobytes()
        
        # Test ASR processing
        asr.feed_audio(audio_bytes)
        transcript = asr.finalize()
        
        print(f"✅ ASR loaded and tested. Transcript: '{transcript}' (empty expected for silence)")
        return True
        
    except Exception as e:
        print(f"❌ ASR Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_tts():
    """Test Text-to-Speech."""
    print("\n🔊 Testing TTS (OpenAI)...")
    try:
        from pipeline.tts import TTSWrapper
        
        tts = TTSWrapper()
        
        # Test TTS synthesis
        test_text = "Hello, this is a test of the text to speech system."
        audio_bytes = tts.synthesize(test_text)
        
        if audio_bytes:
            print(f"✅ TTS working! Generated {len(audio_bytes)} bytes of audio")
            return True
        else:
            print("❌ TTS returned empty audio")
            return False
            
    except Exception as e:
        print(f"❌ TTS Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all audio component tests."""
    print("🎵 Audio Component Tests\n")
    
    tests = [
        ("Voice Activity Detection", test_vad),
        ("Speech Recognition", test_asr), 
        ("Text-to-Speech", test_tts),
    ]
    
    results = {}
    for test_name, test_func in tests:
        results[test_name] = test_func()
    
    print("\n" + "="*60)
    print("📊 Audio Component Test Results:")
    print("="*60)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:25} {status}")
    
    if all(results.values()):
        print("\n🎉 All audio components are working!")
        print("Ready to test the complete voice pipeline!")
    else:
        print("\n⚠️  Some audio tests failed. Check the errors above.")

if __name__ == "__main__":
    main()
