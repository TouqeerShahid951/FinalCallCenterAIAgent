# WebSocket Audio Response Fix

## Issue Identified

From the logs, the system was working correctly until the WebSocket sending stage:

1. ✅ RAG processing completed successfully
2. ✅ LLM generated responses 
3. ✅ TTS generated audio (e.g., "✅ TTS completed in 2.78s, generated 23328 bytes")
4. ❌ **WebSocket send error: "Object of type bytes is not JSON serializable"**

## Root Cause

The pipeline manager was trying to send raw audio bytes via JSON WebSocket message:

```python
await self._send_websocket_message(websocket, {
    "type": "response",
    "audio": result['audio'],  # <- Raw bytes cannot be JSON serialized
    "text": result['text']
})
```

This caused the `json.dumps()` call to fail because bytes cannot be serialized to JSON.

## Fix Applied

**File: `backend/pipeline/pipeline_manager.py`**

Changed the pipeline manager to only send text responses via WebSocket, letting `main.py` handle the audio encoding:

```python
# OLD: Tried to send raw bytes (failed)
await self._send_websocket_message(websocket, {
    "type": "response",
    "audio": result['audio'],  # <- This failed
    "text": result['text']
})

# NEW: Only send text, let main.py handle audio
await self._send_websocket_message(websocket, {
    "type": "response", 
    "text": result['text']  # <- Text only
})
```

## How It Works Now

1. **Pipeline Manager**: Generates audio and text, sends text via WebSocket
2. **Main.py**: Receives the result with both audio and text, encodes audio as base64, sends combined response
3. **Frontend**: Receives `audio_response` message with base64 audio and plays it

## Testing

Run the test script to verify:

```bash
python test_rag_quick.py
```

Expected output:
- ✅ Connection established
- 📜 Transcript received
- 🎯 audio_response message received
- 🔊 Audio bytes decoded successfully
- ✅ Test PASSED

## Why This Fixes the Problem

- **Before**: Pipeline manager tried to send bytes → JSON serialization error → no response sent
- **After**: Pipeline manager sends text only → main.py handles audio encoding → response sent successfully

The audio generation was always working - the issue was just in the WebSocket transmission layer.
