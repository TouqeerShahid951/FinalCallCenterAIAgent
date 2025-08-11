# API Reference - AI Voice Assistant

## Base URL
```
Development: http://localhost:8000
Production: https://your-domain.com
```

## Authentication
Currently, the API does not require authentication for development purposes. For production deployment, consider implementing:
- API key authentication
- JWT tokens
- OAuth 2.0

## WebSocket API

### WebSocket Endpoint
**URL**: `ws://localhost:8000/ws/audio`

**Purpose**: Bidirectional audio streaming for real-time voice communication

**Connection**: 
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/audio');
```

### WebSocket Message Types

#### 1. Client → Server Messages

##### Audio Data
```json
{
  "type": "audio",
  "data": "base64_encoded_pcm_audio",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

**Fields:**
- `type` (string, required): Message type identifier
- `data` (string, required): Base64-encoded PCM audio data
- `timestamp` (string, optional): ISO 8601 timestamp

**Audio Format Requirements:**
- **Sample Rate**: 16,000 Hz
- **Channels**: 1 (mono)
- **Bit Depth**: 16-bit
- **Encoding**: PCM (uncompressed)
- **Chunk Size**: Variable (typically 1024-4096 bytes)

##### Connection Status
```json
{
  "type": "connection_status",
  "status": "connected",
  "client_id": "unique_client_identifier"
}
```

#### 2. Server → Client Messages

##### Connection Status
```json
{
  "type": "status",
  "message": "Connected and ready",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

**Fields:**
- `type` (string): Message type
- `message` (string): Status message
- `timestamp` (string): ISO 8601 timestamp

##### Audio Response
```json
{
  "type": "audio_response",
  "text": "Hello! How can I help you today?",
  "audio": "base64_encoded_wav_audio",
  "audio_format": "wav",
  "timestamp": "2024-01-01T12:00:00Z",
  "processing_time": 2.45
}
```

**Fields:**
- `type` (string): Message type
- `text` (string): Transcribed and processed text
- `audio` (string): Base64-encoded WAV audio response
- `audio_format` (string): Audio format (always "wav")
- `timestamp` (string): ISO 8601 timestamp
- `processing_time` (number): Processing time in seconds

##### Error Messages
```json
{
  "type": "error",
  "error_code": "AUDIO_PROCESSING_ERROR",
  "message": "Failed to process audio data",
  "details": "Invalid audio format detected",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

**Fields:**
- `type` (string): Message type
- `error_code` (string): Error identifier
- `message` (string): Human-readable error message
- `details` (string): Additional error details
- `timestamp` (string): ISO 8601 timestamp

##### Processing Status
```json
{
  "type": "processing_status",
  "status": "processing",
  "stage": "asr",
  "progress": 0.75,
  "timestamp": "2024-01-01T12:00:00Z"
}
```

**Fields:**
- `type` (string): Message type
- `status` (string): Processing status
- `stage` (string): Current processing stage
- `progress` (number): Progress percentage (0.0-1.0)
- `timestamp` (string): ISO 8601 timestamp

### WebSocket Connection States

#### Connection Lifecycle
1. **Connecting**: WebSocket connection attempt
2. **Connected**: Successfully connected and ready
3. **Processing**: Audio processing in progress
4. **Disconnected**: Connection closed or failed

#### Error Handling
```javascript
ws.onerror = (error) => {
  console.error('WebSocket error:', error);
  // Implement reconnection logic
};

ws.onclose = (event) => {
  console.log('WebSocket closed:', event.code, event.reason);
  // Handle connection closure
};
```

## HTTP API

### Health Check

#### GET /health
Returns the health status of the backend service.

**Request:**
```http
GET /health HTTP/1.1
Host: localhost:8000
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "version": "0.1.0",
  "pipeline_state": "idle",
  "components": {
    "vad": true,
    "asr": true,
    "rag": true,
    "tts": true
  },
  "uptime": 3600.5,
  "memory_usage": {
    "total": 1073741824,
    "available": 536870912,
    "used": 536870912
  }
}
```

**Response Fields:**
- `status` (string): Service health status
- `timestamp` (string): ISO 8601 timestamp
- `version` (string): API version
- `pipeline_state` (string): Current pipeline state
- `components` (object): Component health status
- `uptime` (number): Service uptime in seconds
- `memory_usage` (object): Memory usage statistics

### Text-to-Speech

#### POST /tts
Converts text to speech and returns audio data.

**Request:**
```http
POST /tts HTTP/1.1
Host: localhost:8000
Content-Type: application/x-www-form-urlencoded

text=Hello world&voice=en-US-AriaNeural&rate=+0%&volume=+0%
```

**Request Parameters:**
- `text` (string, required): Text to convert to speech
- `voice` (string, optional): TTS voice identifier
- `rate` (string, optional): Speech rate adjustment
- `volume` (string, optional): Volume adjustment

**Response:**
```http
HTTP/1.1 200 OK
Content-Type: audio/wav
Content-Length: 12345

[Binary audio data]
```

**Error Response:**
```json
{
  "error": "TTS_GENERATION_FAILED",
  "message": "Failed to generate speech from text",
  "details": "Invalid text input provided",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### Pipeline Status

#### GET /pipeline/status
Returns the current status of the audio processing pipeline.

**Request:**
```http
GET /pipeline/status HTTP/1.1
Host: localhost:8000
```

**Response:**
```json
{
  "state": "idle",
  "buffer_duration": 0.0,
  "chunk_count": 0,
  "last_processing_time": 0.0,
  "processing_attempts": 0,
  "ultra_fast_mode": true,
  "parallel_processing": true,
  "components": {
    "vad": {
      "status": "ready",
      "threshold": 0.25,
      "batch_processing": true
    },
    "asr": {
      "status": "ready",
      "model": "whisper-base",
      "ultra_fast_mode": true
    },
    "rag": {
      "status": "ready",
      "collection": "company_policies",
      "threshold": 2.0
    },
    "tts": {
      "status": "ready",
      "engine": "edge-tts",
      "cache_size": 100
    }
  }
}
```

### Pipeline Configuration

#### PUT /pipeline/config
Updates the pipeline configuration.

**Request:**
```http
PUT /pipeline/config HTTP/1.1
Host: localhost:8000
Content-Type: application/json

{
  "max_buffer_duration": 1.5,
  "processing_timeout": 15.0,
  "min_processing_interval": 0.1,
  "enable_parallel_processing": true,
  "vad_threshold": 0.25,
  "rag_threshold": 2.0
}
```

**Request Body:**
- `max_buffer_duration` (number): Maximum audio buffer duration in seconds
- `processing_timeout` (number): Processing timeout in seconds
- `min_processing_interval` (number): Minimum time between processing
- `enable_parallel_processing` (boolean): Enable parallel processing
- `vad_threshold` (number): VAD sensitivity threshold
- `rag_threshold` (number): RAG similarity threshold

**Response:**
```json
{
  "status": "success",
  "message": "Pipeline configuration updated",
  "config": {
    "max_buffer_duration": 1.5,
    "processing_timeout": 15.0,
    "min_processing_interval": 0.1,
    "enable_parallel_processing": true,
    "vad_threshold": 0.25,
    "rag_threshold": 2.0
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### RAG Operations

#### GET /rag/collections
Returns available RAG collections.

**Request:**
```http
GET /rag/collections HTTP/1.1
Host: localhost:8000
```

**Response:**
```json
{
  "collections": [
    {
      "name": "company_policies",
      "count": 15,
      "metadata": {
        "description": "Company policy documents",
        "created": "2024-01-01T12:00:00Z",
        "last_updated": "2024-01-01T12:00:00Z"
      }
    }
  ]
}
```

#### POST /rag/query
Performs a RAG query without audio processing.

**Request:**
```http
POST /rag/query HTTP/1.1
Host: localhost:8000
Content-Type: application/json

{
  "query": "What is your return policy?",
  "collection": "company_policies",
  "max_results": 3
}
```

**Request Body:**
- `query` (string, required): Text query
- `collection` (string, optional): Collection name
- `max_results` (number, optional): Maximum results to return

**Response:**
```json
{
  "query": "What is your return policy?",
  "response": "Our return policy allows returns within 30 days of purchase...",
  "sources": [
    {
      "document": "return_policy.md",
      "similarity": 0.85,
      "excerpt": "Returns are accepted within 30 days..."
    }
  ],
  "processing_time": 0.45,
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### System Information

#### GET /system/info
Returns system information and statistics.

**Request:**
```http
GET /system/info HTTP/1.1
Host: localhost:8000
```

**Response:**
```json
{
  "system": {
    "platform": "Windows-10-10.0.26100",
    "python_version": "3.9.7",
    "cpu_count": 8,
    "memory_total": 17179869184,
    "memory_available": 8589934592
  },
  "performance": {
    "avg_response_time": 2.3,
    "total_requests": 1250,
    "success_rate": 0.98,
    "error_rate": 0.02
  },
  "models": {
    "vad": "silero-vad",
    "asr": "whisper-base",
    "embeddings": "all-MiniLM-L6-v2",
    "tts": "edge-tts"
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## Error Codes

### WebSocket Error Codes
- `CONNECTION_FAILED`: Failed to establish WebSocket connection
- `AUDIO_PROCESSING_ERROR`: Error during audio processing
- `ASR_FAILED`: Speech recognition failed
- `RAG_FAILED`: RAG processing failed
- `TTS_FAILED`: Text-to-speech generation failed
- `TIMEOUT_ERROR`: Processing timeout exceeded
- `INVALID_AUDIO_FORMAT`: Unsupported audio format
- `SERVICE_UNAVAILABLE`: Service temporarily unavailable

### HTTP Error Codes
- `400 Bad Request`: Invalid request parameters
- `404 Not Found`: Endpoint not found
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Server-side error
- `503 Service Unavailable`: Service temporarily unavailable

## Rate Limiting

Currently, the API does not implement rate limiting. For production deployment, consider implementing:
- Request rate limiting per client
- Audio chunk size limits
- Concurrent connection limits
- Bandwidth throttling

## WebSocket Best Practices

### 1. Connection Management
```javascript
class WebSocketManager {
  constructor(url) {
    this.url = url;
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
  }

  connect() {
    this.ws = new WebSocket(this.url);
    this.ws.onopen = () => this.onOpen();
    this.ws.onmessage = (event) => this.onMessage(event);
    this.ws.onerror = (error) => this.onError(error);
    this.ws.onclose = (event) => this.onClose(event);
  }

  reconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      setTimeout(() => {
        this.reconnectAttempts++;
        this.connect();
      }, Math.pow(2, this.reconnectAttempts) * 1000);
    }
  }
}
```

### 2. Audio Streaming
```javascript
class AudioStreamer {
  constructor(websocket) {
    this.ws = websocket;
    this.mediaRecorder = null;
    this.audioChunks = [];
  }

  startStreaming() {
    navigator.mediaDevices.getUserMedia({ audio: true })
      .then(stream => {
        this.mediaRecorder = new MediaRecorder(stream);
        this.mediaRecorder.ondataavailable = (event) => {
          this.audioChunks.push(event.data);
          this.sendAudioChunk(event.data);
        };
        this.mediaRecorder.start(100); // 100ms chunks
      });
  }

  sendAudioChunk(audioBlob) {
    const reader = new FileReader();
    reader.onload = () => {
      const base64Audio = reader.result.split(',')[1];
      this.ws.send(JSON.stringify({
        type: 'audio',
        data: base64Audio,
        timestamp: new Date().toISOString()
      }));
    };
    reader.readAsDataURL(audioBlob);
  }
}
```

### 3. Error Handling
```javascript
function handleWebSocketError(error) {
  switch (error.error_code) {
    case 'AUDIO_PROCESSING_ERROR':
      console.error('Audio processing failed:', error.message);
      // Retry audio processing
      break;
    case 'TIMEOUT_ERROR':
      console.error('Processing timeout:', error.message);
      // Increase timeout or retry
      break;
    case 'SERVICE_UNAVAILABLE':
      console.error('Service unavailable:', error.message);
      // Implement fallback or retry
      break;
    default:
      console.error('Unknown error:', error);
  }
}
```

## Testing the API

### 1. WebSocket Testing with wscat
```bash
# Install wscat
npm install -g wscat

# Connect to WebSocket
wscat -c ws://localhost:8000/ws/audio

# Send test message
{"type": "test", "message": "Hello"}
```

### 2. HTTP API Testing with curl
```bash
# Health check
curl http://localhost:8000/health

# TTS endpoint
curl -X POST http://localhost:8000/tts \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "text=Hello world" \
  --output response.wav

# Pipeline status
curl http://localhost:8000/pipeline/status
```

### 3. Python Testing
```python
import websockets
import asyncio
import json

async def test_websocket():
    uri = "ws://localhost:8000/ws/audio"
    async with websockets.connect(uri) as websocket:
        # Send test message
        await websocket.send(json.dumps({
            "type": "test",
            "message": "Hello"
        }))
        
        # Receive response
        response = await websocket.recv()
        print(f"Received: {response}")

# Run test
asyncio.run(test_websocket())
```

## Performance Considerations

### 1. Audio Chunk Optimization
- **Optimal Chunk Size**: 1024-4096 bytes
- **Sample Rate**: 16kHz for optimal quality/size balance
- **Encoding**: PCM for minimal processing overhead

### 2. Connection Management
- **Keep-Alive**: Maintain persistent connections
- **Reconnection**: Implement exponential backoff
- **Heartbeat**: Send periodic ping messages

### 3. Error Recovery
- **Retry Logic**: Implement retry with backoff
- **Fallback**: Graceful degradation on failures
- **Monitoring**: Track error rates and response times

---

*This API reference covers all endpoints and message formats for the AI Voice Assistant. For implementation details, refer to the source code and technical architecture documentation.*
