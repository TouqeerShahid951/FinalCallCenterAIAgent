#!/usr/bin/env python3
"""
Quick test to verify RAG responses are working after the WebSocket fix.
"""

import asyncio
import json
import base64
import logging
from websockets import connect
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_simple_audio():
    """Create a simple audio pattern for testing."""
    # Generate 3 seconds of audio at 16kHz
    sample_rate = 16000
    duration = 3.0
    samples = int(sample_rate * duration)
    
    # Create a simple pattern that should trigger voice detection
    t = np.linspace(0, duration, samples)
    audio = np.sin(2 * np.pi * 440 * t) * 0.5  # 440Hz sine wave
    
    # Convert to 16-bit PCM
    audio_int16 = (audio * 32767).astype(np.int16)
    return audio_int16.tobytes()

async def test_rag_response():
    """Test that we get a proper audio response for a RAG query."""
    uri = "ws://localhost:8000/ws"
    
    try:
        async with connect(uri) as websocket:
            logger.info("✅ Connected to WebSocket")
            
            # Wait for connection message
            message = await websocket.recv()
            logger.info(f"📨 Connection: {json.loads(message)}")
            
            # Send test audio
            audio_data = create_simple_audio()
            logger.info(f"🎤 Sending {len(audio_data)} bytes of test audio")
            
            # Send in chunks
            chunk_size = 4096
            for i in range(0, len(audio_data), chunk_size):
                chunk = audio_data[i:i+chunk_size]
                await websocket.send(chunk)
                await asyncio.sleep(0.1)
            
            logger.info("📤 Audio sent, waiting for response...")
            
            # Wait for response with timeout
            timeout = 20.0
            start_time = asyncio.get_event_loop().time()
            
            while asyncio.get_event_loop().time() - start_time < timeout:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                    data = json.loads(message)
                    
                    logger.info(f"📨 Received: {data.get('type', 'unknown')}")
                    
                    if data.get('type') == 'audio_response':
                        logger.info("🎯 SUCCESS! Got audio_response message")
                        logger.info(f"📝 Text: {data.get('text', '')[:100]}...")
                        
                        if data.get('audio'):
                            audio_size = len(base64.b64decode(data['audio']))
                            logger.info(f"🔊 Audio: {audio_size} bytes")
                            logger.info("✅ RAG response test PASSED!")
                            return True
                        else:
                            logger.warning("⚠️ No audio in response")
                    
                    elif data.get('type') == 'transcript':
                        logger.info(f"📜 Transcript: {data.get('text', '')} (final: {data.get('final', False)})")
                    
                except asyncio.TimeoutError:
                    continue
            
            logger.error("❌ No audio response received within timeout")
            return False
            
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_rag_response())
    if success:
        print("\n🎉 RAG response test PASSED!")
    else:
        print("\n💥 RAG response test FAILED!")
