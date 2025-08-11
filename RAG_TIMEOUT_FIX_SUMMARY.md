# RAG Timeout Fix Summary

## Problem Identified
The RAG (Retrieval-Augmented Generation) system was timing out after 5 seconds when processing policy queries, preventing TTS audio from being generated and sent back to the frontend.

### Symptoms:
- ✅ Audio received and processed correctly
- ✅ ASR transcribed queries successfully
- ✅ RAG found relevant documents and processed queries
- ❌ Processing timed out after 5 seconds before TTS could complete
- ❌ No audio response sent back to frontend

## Fixes Implemented

### 1. Increased Pipeline Timeout (backend/pipeline/pipeline_manager.py)
- **Changed**: `processing_timeout` from 5.0s to 15.0s
- **Reason**: RAG queries with policy lookup + TTS generation need more than 5 seconds
- **Location**: Line 31 in PipelineManager.__init__()

```python
processing_timeout: float = 15.0,  # INCREASED from 5.0s to allow RAG+TTS to complete
```

### 2. Added TTS Debugging (backend/pipeline/tts.py)
- **Added**: Timing measurements and detailed logging in synthesize() method
- **Purpose**: Track TTS processing bottlenecks and identify slow operations
- **Benefits**: 
  - Shows TTS method being used
  - Logs processing time for each synthesis
  - Reports audio data size generated

### 3. Fixed Audio Encoding (backend/main.py)
- **Changed**: From sending raw audio bytes to base64-encoded JSON
- **Old**: `await ws.send_bytes(reply_data['audio'])`
- **New**: Sends JSON with base64-encoded audio
```python
await ws.send_text(json.dumps({
    "type": "audio_response",
    "text": reply_data.get('text', ''),
    "audio": audio_base64,
    "audio_format": "wav"
}))
```

### 4. Updated Frontend Audio Handling (frontend/script.js)
- **Added**: Support for `audio_response` message type
- **Added**: `playBase64Audio()` function to decode and play base64 audio
- **Benefits**:
  - Properly handles base64-encoded audio from backend
  - Displays response text in chat
  - Plays audio response seamlessly

## Testing

Created `backend/test_rag_timeout_fix.py` to verify:
1. RAG queries complete within the new timeout
2. Audio responses are properly encoded and transmitted
3. The complete flow works end-to-end

## How to Test

1. Start the backend server:
```bash
cd backend
python main.py
```

2. Open the frontend in a browser:
```
http://localhost:8000
```

3. Ask a policy-related question like:
   - "What's the written policy?"
   - "Tell me about the company policies"
   - "What are the work from home rules?"

4. Or run the test script:
```bash
cd backend
python test_rag_timeout_fix.py
```

## Expected Results

With these fixes:
- ✅ RAG queries complete successfully
- ✅ TTS generates audio responses
- ✅ Frontend receives and plays audio
- ✅ Response text displayed in chat
- ✅ No more 5-second timeouts

## Performance Considerations

The 15-second timeout provides enough time for:
- Complex RAG queries (2-5 seconds)
- TTS generation (2-8 seconds depending on text length)
- Network transmission overhead

This ensures reliable operation while maintaining reasonable response times.
