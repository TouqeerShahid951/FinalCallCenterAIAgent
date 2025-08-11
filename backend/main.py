from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pathlib import Path
import asyncio
import logging
import time
import json
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from pipeline.pipeline_manager import PipelineManager

# Configure logging with UTF-8 encoding to handle emojis
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('voice_agent.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Voice Agent Backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize global pipeline manager (lazy load models)
logger.info("🚀 Initializing Pipeline Manager...")
pipeline = PipelineManager()
logger.info("✅ Pipeline Manager initialized successfully")


@app.websocket("/ws/audio")
async def websocket_endpoint(ws: WebSocket):
    """Bidirectional audio stream. Client sends 16 kHz PCM bytes. Server streams back TTS audio chunks."""
    logger.info("🎤 WebSocket connection attempt")
    await ws.accept()
    logger.info("✅ WebSocket connection accepted")
    
    # Send initial connection status
    await ws.send_text(json.dumps({
        "type": "status",
        "message": "Connected and ready"
    }))
    
    chunk_count = 0
    total_bytes = 0
    try:
        async for message in ws.iter_bytes():
            chunk_count += 1
            total_bytes += len(message)
            logger.info(f"🎵 Received audio chunk #{chunk_count}, size: {len(message)} bytes, total: {total_bytes} bytes")
            
            # Log audio data details for debugging
            if len(message) > 0:
                # Convert first few bytes to see the data format
                try:
                    import numpy as np
                    audio_data = np.frombuffer(message[:100], dtype=np.int16)
                    rms = np.sqrt(np.mean(audio_data.astype(np.float32)**2))
                    peak = np.max(np.abs(audio_data))
                    logger.info(f"🔍 Audio data sample - RMS: {rms:.4f}, Peak: {peak}, Range: [{np.min(audio_data)}, {np.max(audio_data)}]")
                except Exception as e:
                    logger.debug(f"Could not analyze audio data: {e}")
            
            start_time = time.time()
            
            # Feed audio to pipeline with transcription callback
            reply_data = await pipeline.feed_audio_with_transcription(message, ws)
            processing_time = time.time() - start_time
            
            logger.info(f"⚡ Pipeline processing took {processing_time:.3f}s")
            
            if reply_data and 'audio' in reply_data:
                import base64
                logger.info(f"🔊 Sending reply audio: {len(reply_data['audio'])} bytes")
                
                # Convert audio bytes to base64 for JSON transmission
                audio_base64 = base64.b64encode(reply_data['audio']).decode('utf-8')
                
                # Send both text and audio in a single JSON message
                await ws.send_text(json.dumps({
                    "type": "audio_response",
                    "text": reply_data.get('text', ''),
                    "audio": audio_base64,
                    "audio_format": "wav"
                }))
            else:
                logger.debug("🔇 No reply audio generated")
                
    except WebSocketDisconnect:
        logger.info("🔌 WebSocket disconnected")
        await pipeline.reset()
    except Exception as e:
        logger.error(f"❌ WebSocket error: {e}", exc_info=True)
        # FIXED: Reset pipeline on any error to prevent infinite loops
        try:
            await pipeline.reset()
            logger.info("✅ Pipeline reset after error")
        except Exception as reset_error:
            logger.error(f"❌ Failed to reset pipeline: {reset_error}")
        # FIXED: Close the WebSocket connection to prevent further errors
        try:
            await ws.close(code=1011, reason="Internal error")
        except Exception:
            pass


@app.get("/health")
async def health_check():
    logger.info("💓 Health check requested")
    return {"status": "ok", "timestamp": time.time()}


# Optional: HTTP TTS endpoint (text -> audio)
@app.post("/tts")
async def tts_endpoint(text: str):
    logger.info(f"🗣️ TTS request: '{text}'")
    audio_generator = pipeline.text_to_speech(text)
    return StreamingResponse(audio_generator, media_type="audio/wav")

@app.on_event("startup")
async def startup_event():
    logger.info("🎯 Voice Agent Backend starting up...")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("🛑 Voice Agent Backend shutting down...")
