# Technical Architecture - AI Voice Assistant

## System Overview

The AI Voice Assistant is built as a microservices architecture with real-time audio processing capabilities. The system is designed for low-latency voice interactions with sub-3-second response times.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Frontend Layer                                │
├─────────────────────────────────────────────────────────────────────────────┤
│  React App (TypeScript)                                                    │
│  ├── AudioChat Component                                                   │
│  ├── WebSocket Client                                                      │
│  ├── Audio Capture (WebRTC)                                               │
│  └── Glass Morphism UI                                                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ WebSocket (ws://localhost:8000/ws/audio)
                                    │
┌─────────────────────────────────────────────────────────────────────────────┐
│                             Backend Layer                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│  FastAPI Server                                                            │
│  ├── WebSocket Handler                                                     │
│  ├── HTTP Endpoints                                                        │
│  ├── CORS Middleware                                                       │
│  └── Health Monitoring                                                     │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ Pipeline Orchestration
                                    │
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Pipeline Layer                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│  Pipeline Manager                                                          │
│  ├── State Management                                                      │
│  ├── Audio Buffering                                                       │
│  ├── Parallel Processing                                                   │
│  └── Error Handling                                                        │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌────────────────┼────────────────┐
                    │                │                │
            ┌───────▼──────┐ ┌──────▼──────┐ ┌──────▼──────┐
            │      VAD     │ │     ASR     │ │     TTS     │
            │              │ │             │ │             │
            │ • Silero VAD │ │ • Whisper   │ │ • Edge TTS  │
            │ • Threshold  │ │ • Streaming │ │ • Caching   │
            │ • Batch Mode │ │ • Ultra-Fast│ │ • Fallbacks │
            └──────────────┘ └─────────────┘ └─────────────┘
                    │                │                │
                    └────────────────┼────────────────┘
                                     │
                            ┌────────▼────────┐
                            │      RAG       │
                            │                │
                            │ • ChromaDB     │
                            │ • Embeddings   │
                            │ • LLM          │
                            │ • Policies     │
                            └────────────────┘
```

## Component Specifications

### 1. Frontend Components

#### AudioChat Component
```typescript
interface AudioChatProps {
  onCallStart: () => void;
  onCallEnd: () => void;
  onTranscriptUpdate: (text: string) => void;
}

interface AudioChatState {
  isConnected: boolean;
  isCallActive: boolean;
  transcript: string;
  audioLevel: number;
}
```

**Key Methods:**
- `startCall()`: Initialize WebSocket connection and audio capture
- `stopCall()`: Close connection and stop audio capture
- `sendAudio(audio: Blob)`: Stream audio to backend
- `handleResponse(data: WebSocketMessage)`: Process server responses

#### WebSocket Client
```typescript
class WebSocketClient {
  private ws: WebSocket;
  private reconnectAttempts: number;
  private maxReconnectAttempts: number;
  
  connect(url: string): Promise<void>;
  sendAudio(audio: Blob): void;
  onMessage(callback: (data: any) => void): void;
  disconnect(): void;
}
```

### 2. Backend Components

#### FastAPI Application
```python
app = FastAPI(
    title="Voice Agent Backend",
    version="0.1.0",
    description="Real-time voice assistant with RAG capabilities"
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
```

**Endpoints:**
- `GET /health`: Health check endpoint
- `POST /tts`: Text-to-speech conversion
- `WS /ws/audio`: WebSocket audio streaming

#### WebSocket Handler
```python
@app.websocket("/ws/audio")
async def websocket_endpoint(ws: WebSocket):
    """Bidirectional audio stream handler"""
    await ws.accept()
    
    try:
        async for message in ws.iter_bytes():
            # Process audio chunk
            reply_data = await pipeline.feed_audio_with_transcription(message, ws)
            
            if reply_data and 'audio' in reply_data:
                # Send response back to client
                await ws.send_text(json.dumps({
                    "type": "audio_response",
                    "text": reply_data.get('text', ''),
                    "audio": base64.b64encode(reply_data['audio']).decode('utf-8'),
                    "audio_format": "wav"
                }))
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
```

### 3. Pipeline Components

#### Pipeline Manager
```python
class PipelineManager:
    def __init__(self, 
                 max_buffer_duration: float = 1.5,
                 processing_timeout: float = 15.0,
                 min_processing_interval: float = 0.1,
                 enable_parallel_processing: bool = True):
        
        # Initialize components
        self.vad = VadWrapper()
        self.asr = StreamingASR()
        self.rag = PolicyRAG()
        self.tts = CachedTTSWrapper()
        
        # State management
        self._state = PipelineState.IDLE
        self._buffer = bytearray()
        self.is_processing = False
```

**State Machine:**
```python
class PipelineState(Enum):
    IDLE = "idle"           # Waiting for audio input
    LISTENING = "listening" # Receiving audio chunks
    PROCESSING = "processing" # Processing audio through pipeline
    RESPONDING = "responding" # Generating and sending response
    ERROR = "error"         # Error state
```

#### Voice Activity Detection (VAD)
```python
class VadWrapper:
    def __init__(self, 
                 threshold: float = 0.25,
                 max_tail_ms: int = 150,
                 enable_audio_monitoring: bool = False,
                 batch_processing: bool = True):
        
        self.vad_model = torch.hub.load(repo_or_dir='snakers4/silero-vad',
                                       model='silero_vad',
                                       force_reload=False)
        self.threshold = threshold
        self.max_tail_ms = max_tail_ms
        self.batch_processing = batch_processing
```

**VAD Features:**
- **Silero Model**: Pre-trained voice activity detection
- **Configurable Threshold**: Adjustable sensitivity (0.0-1.0)
- **Batch Processing**: Process multiple audio chunks simultaneously
- **Real-time Monitoring**: Continuous audio analysis

#### Speech Recognition (ASR)
```python
class StreamingASR:
    def __init__(self):
        self.model = None
        self.ultra_fast_mode = False
        self.session_id = None
        
    def enable_ultra_fast_mode(self, enabled: bool = True):
        """Enable performance optimizations"""
        self.ultra_fast_mode = enabled
        if enabled:
            self.model = faster_whisper.WhisperModel(
                model_size="base",
                device="cpu",
                compute_type="int8"
            )
```

**ASR Features:**
- **Whisper Integration**: OpenAI's speech recognition model
- **Streaming Support**: Real-time audio processing
- **Ultra-Fast Mode**: Optimized for low latency
- **Session Management**: Maintains context across utterances

#### RAG Engine
```python
class PolicyRAG:
    def __init__(self, 
                 collection_name: str = "company_policies",
                 threshold: float = 2.0):
        
        # Vector database
        self.chroma = chromadb.PersistentClient(path="./chroma")
        self.collection = self.chroma.get_or_create_collection(collection_name)
        
        # Embedding model
        self.embed_model = SentenceTransformer("all-MiniLM-L6-v2")
        
        # Language model
        self.llm = LLMWrapper()
        
        # Similarity threshold
        self.threshold = threshold
```

**RAG Features:**
- **ChromaDB**: Persistent vector database
- **SentenceTransformers**: High-quality embeddings
- **Similarity Search**: Semantic document retrieval
- **LLM Integration**: Contextual response generation

#### Text-to-Speech (TTS)
```python
class CachedTTSWrapper:
    def __init__(self, max_cache_size: int = 100):
        self.cache = {}
        self.max_cache_size = max_cache_size
        self.tts_engine = self._detect_best_tts()
        
    def _detect_best_tts(self):
        """Auto-detect best available TTS engine"""
        try:
            return EdgeTTSWrapper()  # Microsoft Edge TTS
        except:
            try:
                return Pyttsx3Wrapper()  # Cross-platform fallback
            except:
                return WindowsSAPIWrapper()  # Windows fallback
```

**TTS Features:**
- **Edge TTS**: High-quality neural voices
- **Multiple Fallbacks**: Cross-platform compatibility
- **Audio Caching**: Performance optimization
- **Voice Selection**: Multiple voice options

## Data Flow Architecture

### 1. Audio Input Flow
```
Browser Audio Capture → WebRTC → WebSocket → FastAPI → Pipeline Manager
     ↓
16kHz PCM Audio → VAD Processing → Audio Buffer → ASR Processing
```

### 2. Processing Flow
```
Audio Buffer → VAD Detection → Speech Boundary Detection → ASR Transcription
     ↓
Text Input → RAG Query → Vector Search → Policy Retrieval → LLM Generation
     ↓
Response Text → TTS Conversion → Audio Generation → WebSocket Response
```

### 3. Response Flow
```
TTS Audio → Base64 Encoding → JSON Response → WebSocket → Browser
     ↓
Audio Decoding → Audio Playback → User Experience
```

## Performance Optimizations

### 1. Ultra-Fast Mode
```python
# Pipeline optimizations
ULTRA_FAST_CONFIG = {
    "max_buffer_duration": 1.5,        # Reduced from 3.0s
    "min_processing_interval": 0.1,    # Reduced from 0.5s
    "min_time_between_responses": 0.3, # Reduced from 0.8s
    "enable_parallel_processing": True # Parallel execution
}
```

### 2. Parallel Processing
```python
# Dedicated thread pools
if self.enable_parallel_processing:
    self.asr_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="ASR")
    self.rag_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="RAG")
    self.tts_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="TTS")
```

### 3. Audio Caching
```python
# TTS response caching
def _generate_tts(self, text: str) -> Optional[bytes]:
    cache_key = hashlib.md5(text.encode()).hexdigest()
    
    if cache_key in self.tts_cache:
        logger.info("TTS: Using cached response")
        return self.tts_cache[cache_key]
    
    # Generate new audio
    audio = self.tts.generate(text)
    self.tts_cache[cache_key] = audio
    return audio
```

## Security Considerations

### 1. WebSocket Security
```python
# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
```

### 2. API Key Management
```python
# Environment variable loading
load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    raise ValueError("OPENROUTER_API_KEY environment variable is required")
```

### 3. Input Validation
```python
# Audio data validation
def validate_audio_data(audio_bytes: bytes) -> bool:
    if len(audio_bytes) == 0:
        return False
    
    # Check audio format (16kHz PCM)
    expected_size = len(audio_bytes) % 2 == 0  # 16-bit samples
    return expected_size
```

## Monitoring & Observability

### 1. Logging Strategy
```python
# Structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('voice_agent.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
```

### 2. Metrics Collection
```python
# Performance metrics
def get_stats(self) -> dict:
    return {
        "pipeline_state": self._state.value,
        "buffer_duration": self._get_buffer_duration(),
        "chunk_count": self._chunk_count,
        "processing_time": time.time() - self._last_processing_time,
        "memory_usage": self._get_memory_usage()
    }
```

### 3. Health Checks
```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "pipeline_state": pipeline.get_state().value,
        "components": {
            "vad": pipeline.vad.is_ready(),
            "asr": pipeline.asr.is_ready(),
            "rag": pipeline.rag.is_ready(),
            "tts": pipeline.tts.is_ready()
        }
    }
```

## Scalability Considerations

### 1. Horizontal Scaling
```yaml
# Docker Compose scaling
version: "3.9"
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    deploy:
      replicas: 3  # Scale to 3 instances
```

### 2. Load Balancing
```nginx
# Nginx load balancer
upstream backend_servers {
    server backend:8000;
    server backend:8001;
    server backend:8002;
}

location /ws/ {
    proxy_pass http://backend_servers;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}
```

### 3. Database Scaling
```python
# ChromaDB clustering
class PolicyRAG:
    def __init__(self):
        # Use external ChromaDB cluster
        self.chroma = chromadb.HttpClient(
            host="chroma-cluster.example.com",
            port=8000
        )
```

## Error Handling & Resilience

### 1. Circuit Breaker Pattern
```python
class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
```

### 2. Retry Logic
```python
async def _process_with_retry(self, func, *args, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await func(*args)
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
```

### 3. Graceful Degradation
```python
def _fallback_tts(self, text: str) -> bytes:
    """Fallback TTS when primary engine fails"""
    try:
        return self.edge_tts.generate(text)
    except:
        try:
            return self.pyttsx3.generate(text)
        except:
            return self.generate_simple_audio(text)  # Basic audio
```

---

*This technical architecture document provides detailed specifications for the AI Voice Assistant system. For implementation details, refer to the individual component files.*
