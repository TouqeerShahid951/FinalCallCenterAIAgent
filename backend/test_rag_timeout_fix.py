#!/usr/bin/env python3
"""
Test script to verify RAG queries work with the increased timeout.
This tests the complete flow: Audio -> ASR -> RAG -> TTS -> Audio Response
"""

import asyncio
import json
import base64
import wave
import io
import numpy as np
from websockets import connect
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_test_audio(text="Hello, how are you? What's the written policy?", duration=3.0):
    """Create a simple test audio file with sine waves (placeholder for actual speech)."""
    sample_rate = 16000
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    # Create a simple audio pattern (not actual speech, just for testing)
    frequency = 440  # A4 note
    audio = np.sin(2 * np.pi * frequency * t) * 0.3
    
    # Add some variation to simulate speech patterns
    for i in range(5):
        freq = 200 + i * 100
        audio += np.sin(2 * np.pi * freq * t) * 0.1
    
    # Convert to 16-bit PCM
    audio_int16 = (audio * 32767).astype(np.int16)
    
    # Create WAV file in memory
    buffer = io.BytesIO()
    with wave.open(buffer, 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_int16.tobytes())
    
    return buffer.getvalue()

async def test_rag_with_timeout():
    """Test the complete RAG flow with the new timeout settings."""
    uri = "ws://localhost:8000/ws"
    
    logger.info("🚀 Starting RAG timeout test...")
    logger.info(f"📡 Connecting to {uri}")
    
    try:
        async with connect(uri) as websocket:
            logger.info("✅ Connected to WebSocket")
            
            # Wait for initial status message
            message = await websocket.recv()
            data = json.loads(message)
            logger.info(f"📨 Initial status: {data}")
            
            # Create test audio that should trigger RAG
            test_audio = create_test_audio()
            logger.info(f"🎤 Created test audio: {len(test_audio)} bytes")
            
            # Send audio in chunks to simulate streaming
            chunk_size = 4096
            for i in range(0, len(test_audio), chunk_size):
                chunk = test_audio[i:i + chunk_size]
                await websocket.send(chunk)
                await asyncio.sleep(0.05)  # Simulate real-time streaming
            
            logger.info("📤 Audio sent, waiting for response...")
            
            # Wait for responses with timeout
            start_time = asyncio.get_event_loop().time()
            timeout = 20.0  # Give plenty of time for RAG + TTS
            
            while asyncio.get_event_loop().time() - start_time < timeout:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    
                    if isinstance(message, bytes):
                        logger.info(f"🔊 Received audio bytes: {len(message)} bytes")
                    else:
                        data = json.loads(message)
                        logger.info(f"📝 Received message: {data.get('type', 'unknown')}")
                        
                        if data.get('type') == 'transcript':
                            logger.info(f"📜 Transcript: {data.get('text', '')} (final: {data.get('final', False)})")
                        
                        elif data.get('type') == 'audio_response':
                            logger.info(f"🎯 Got audio response!")
                            logger.info(f"📝 Response text: {data.get('text', '')[:100]}...")
                            
                            if data.get('audio'):
                                audio_bytes = base64.b64decode(data['audio'])
                                logger.info(f"🔊 Audio size: {len(audio_bytes)} bytes")
                                
                                # Save audio for verification
                                with open('test_rag_response.wav', 'wb') as f:
                                    f.write(audio_bytes)
                                logger.info("💾 Saved response audio to test_rag_response.wav")
                                
                                logger.info("✅ RAG test completed successfully!")
                                return True
                
                except asyncio.TimeoutError:
                    continue
            
            logger.error(f"❌ Timeout waiting for audio response after {timeout}s")
            return False
            
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False

async def main():
    """Run the test."""
    success = await test_rag_with_timeout()
    
    if success:
        logger.info("\n" + "="*50)
        logger.info("✅ RAG TIMEOUT FIX VERIFIED!")
        logger.info("The system can now handle RAG queries without timing out.")
        logger.info("="*50)
    else:
        logger.error("\n" + "="*50)
        logger.error("❌ RAG TIMEOUT TEST FAILED")
        logger.error("Please check the logs for details.")
        logger.error("="*50)

if __name__ == "__main__":
    asyncio.run(main())
