#!/usr/bin/env python3
"""
Debug test script for the voice agent pipeline.
This will help identify where issues are occurring.
"""

import logging
import sys
import os
import asyncio
import numpy as np
import time

# Set up detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('debug_test.log'),
        logging.StreamHandler()
    ]
)

# Set API key
os.environ["OPENROUTER_API_KEY"] = "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"

# Add backend to path
sys.path.append('./backend')

async def test_pipeline_step_by_step():
    """Test each component of the pipeline individually."""
    print("🧪 Testing Voice Agent Pipeline Components Step-by-Step")
    print("=" * 60)
    
    try:
        # Test 1: Import and initialize components
        print("\n1️⃣ Testing Component Imports...")
        
        from pipeline.vad import VadWrapper
        from pipeline.asr import StreamingASR
        from pipeline.rag import PolicyRAG
        from pipeline.tts import TTSWrapper
        from pipeline.pipeline_manager import PipelineManager
        
        print("✅ All imports successful")
        
        # Test 2: Initialize individual components
        print("\n2️⃣ Testing Individual Component Initialization...")
        
        print("📡 Initializing VAD...")
        vad = VadWrapper()
        print("✅ VAD initialized")
        
        print("🗣️ Initializing ASR...")
        asr = StreamingASR(model_name="tiny")
        print("✅ ASR initialized")
        
        print("🧠 Initializing RAG...")
        rag = PolicyRAG()
        print("✅ RAG initialized")
        
        print("🔊 Initializing TTS...")
        tts = TTSWrapper()
        print("✅ TTS initialized")
        
        # Test 3: Test with synthetic audio
        print("\n3️⃣ Testing with Synthetic Audio...")
        
        # Create test audio (sine wave)
        sample_rate = 16000
        duration = 2.0  # 2 seconds
        frequency = 440  # A4 note
        
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio_signal = np.sin(2 * np.pi * frequency * t) * 0.3
        audio_int16 = (audio_signal * 32767).astype(np.int16)
        
        print(f"Generated {len(audio_int16)} samples of test audio")
        
        # Test VAD with chunks
        chunk_size = 512  # VAD expects 512 samples for 16kHz
        speech_detected = False
        
        print("🎤 Testing VAD with audio chunks...")
        for i in range(0, min(len(audio_int16), chunk_size * 10), chunk_size):
            chunk = audio_int16[i:i+chunk_size]
            if len(chunk) < chunk_size:
                # Pad the chunk
                padded_chunk = np.zeros(chunk_size, dtype=np.int16)
                padded_chunk[:len(chunk)] = chunk
                chunk = padded_chunk
            
            chunk_bytes = chunk.tobytes()
            is_speech = vad.is_speech(chunk_bytes)
            
            if is_speech:
                speech_detected = True
                print(f"🎵 Speech detected in chunk {i//chunk_size + 1}")
                
                # Feed to ASR
                asr.feed_audio(chunk_bytes)
                
        print(f"VAD Results: Speech detected = {speech_detected}")
        
        # Test ASR finalization
        print("🗣️ Testing ASR finalization...")
        transcript = asr.finalize()
        print(f"ASR Transcript: '{transcript}'")
        
        # Test RAG with a real query
        print("\n4️⃣ Testing RAG System...")
        test_queries = [
            "What is your return policy?",
            "How much does shipping cost?",
            "Tell me a joke"  # Should be rejected
        ]
        
        for query in test_queries:
            print(f"Query: '{query}'")
            response = rag.respond(query)
            print(f"Response: '{response[:100]}...'")
            print("-" * 40)
        
        # Test TTS
        print("\n5️⃣ Testing TTS...")
        test_text = "Hello, this is a test of the text to speech system."
        audio_bytes = tts.synthesize(test_text)
        print(f"TTS generated {len(audio_bytes)} bytes of audio")
        
        # Test 6: Full pipeline
        print("\n6️⃣ Testing Complete Pipeline...")
        pipeline = PipelineManager()
        
        # Simulate audio chunks
        print("Feeding audio chunks to pipeline...")
        for i in range(0, min(len(audio_int16), chunk_size * 20), chunk_size):
            chunk = audio_int16[i:i+chunk_size]
            if len(chunk) < chunk_size:
                padded_chunk = np.zeros(chunk_size, dtype=np.int16)
                padded_chunk[:len(chunk)] = chunk
                chunk = padded_chunk
            
            chunk_bytes = chunk.tobytes()
            result = await pipeline.feed_audio(chunk_bytes)
            
            if result:
                print(f"🎉 Pipeline generated response! {len(result)} bytes")
                break
        else:
            print("⚠️ No response generated from pipeline")
        
        print("\n✅ All tests completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

async def test_websocket_simulation():
    """Simulate what happens in the WebSocket connection."""
    print("\n🌐 WebSocket Simulation Test")
    print("-" * 30)
    
    try:
        from pipeline.pipeline_manager import PipelineManager
        
        pipeline = PipelineManager()
        
        # Simulate receiving audio chunks like WebSocket would
        sample_rate = 16000
        chunk_duration = 0.1  # 100ms chunks
        samples_per_chunk = int(sample_rate * chunk_duration)
        
        # Generate speech-like audio
        frequency = 300  # Lower frequency for voice-like sound
        duration = 3.0  # 3 seconds total
        
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio_signal = np.sin(2 * np.pi * frequency * t) * 0.4
        audio_int16 = (audio_signal * 32767).astype(np.int16)
        
        print(f"Simulating WebSocket with {len(audio_int16)} total samples")
        print(f"Chunk size: {samples_per_chunk} samples ({chunk_duration*1000}ms)")
        
        chunk_count = 0
        for i in range(0, len(audio_int16), samples_per_chunk):
            chunk = audio_int16[i:i+samples_per_chunk]
            
            # Pad if necessary
            if len(chunk) < samples_per_chunk:
                padded_chunk = np.zeros(samples_per_chunk, dtype=np.int16)
                padded_chunk[:len(chunk)] = chunk
                chunk = padded_chunk
            
            chunk_bytes = chunk.tobytes()
            chunk_count += 1
            
            print(f"📡 Sending chunk #{chunk_count} ({len(chunk_bytes)} bytes)")
            
            start_time = time.time()
            result = await pipeline.feed_audio(chunk_bytes)
            processing_time = time.time() - start_time
            
            print(f"⚡ Processing took {processing_time:.3f}s")
            
            if result:
                print(f"🎉 Got response! {len(result)} bytes")
                break
            
            # Small delay to simulate real-time
            await asyncio.sleep(0.01)
        
        print("🔚 WebSocket simulation completed")
        
    except Exception as e:
        print(f"❌ WebSocket simulation failed: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Run all debug tests."""
    print("🎯 Voice Agent Debug Test Suite")
    print("=" * 60)
    
    await test_pipeline_step_by_step()
    await test_websocket_simulation()
    
    print("\n📊 Debug test completed!")
    print("📝 Check 'debug_test.log' for detailed logs")
    print("📝 Check 'voice_agent.log' for server logs when running")

if __name__ == "__main__":
    asyncio.run(main())
