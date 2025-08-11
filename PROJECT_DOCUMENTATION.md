# AI Voice Assistant - Complete Project Documentation

## Table of Contents
1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Installation & Setup](#installation--setup)
4. [API Documentation](#api-documentation)
5. [Pipeline Components](#pipeline-components)
6. [Frontend Components](#frontend-components)
7. [Testing](#testing)
8. [Deployment](#deployment)
9. [Configuration](#configuration)
10. [Troubleshooting](#troubleshooting)
11. [Development Guide](#development-guide)

## Project Overview

The AI Voice Assistant is a production-ready, real-time conversational AI system that combines speech recognition, natural language processing, and text-to-speech capabilities. It features a modern glass morphism UI and is designed for customer support scenarios with company policy knowledge.

### Key Features
- **Real-time Speech Recognition**: OpenAI Whisper with voice activity detection
- **Intelligent Responses**: RAG (Retrieval-Augmented Generation) for policy-based answers
- **High-Quality TTS**: Microsoft Edge TTS with neural voices
- **Modern Web Interface**: React-based frontend with WebSocket communication
- **Ultra-Fast Processing**: Optimized pipeline for sub-3-second response times
- **Policy Management**: ChromaDB-based vector search for company policies

### Technology Stack
- **Backend**: FastAPI, Python 3.8+
- **Frontend**: React 18, TypeScript, Vite
- **AI Models**: Whisper, SentenceTransformers, ChromaDB
- **Audio Processing**: Silero VAD, Edge TTS
- **Communication**: WebSocket, WebRTC
- **Deployment**: Docker, Docker Compose

## Architecture

### System Architecture
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend        │    │   External      │
│   (React)       │◄──►│   (FastAPI)      │◄──►│   Services      │
│                 │    │                  │    │                 │
│ • WebSocket     │    │ • Pipeline       │    │ • OpenAI API    │
│ • Audio Capture │    │ • RAG Engine     │    │ • Edge TTS      │
│ • UI Components │    │ • ASR/TTS        │    │ • ChromaDB      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Pipeline Architecture
```
Audio Input → VAD → ASR → RAG → LLM → TTS → Audio Output
    ↓         ↓     ↓     ↓     ↓     ↓        ↓
  WebSocket  Buffer Whisper Policy OpenAI  Edge TTS  WebSocket
```

### Data Flow
1. **Audio Capture**: Browser captures 16kHz PCM audio via WebRTC
2. **WebSocket Transmission**: Audio chunks sent to FastAPI backend
3. **Voice Activity Detection**: Silero VAD detects speech boundaries
4. **Speech Recognition**: Whisper transcribes audio to text
5. **RAG Processing**: Vector search finds relevant policy documents
6. **Response Generation**: LLM generates contextual responses
7. **Text-to-Speech**: Edge TTS converts response to audio
8. **Audio Streaming**: Response audio streamed back via WebSocket

## Installation & Setup

### Prerequisites
- Python 3.8+
- Node.js 16+
- Docker & Docker Compose (optional)
- Microphone access
- OpenAI API key (for LLM responses)

### Local Development Setup

#### 1. Clone and Setup
```bash
git clone <repository-url>
cd Newproject

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows
```

#### 2. Backend Setup
```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp ../env.example .env
# Edit .env with your API keys

# Load company policies
python load_policies.py

# Start backend server
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

#### 3. Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### Docker Setup
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Environment Variables
```bash
# Required
OPENROUTER_API_KEY=your_openrouter_key_here

# Optional
OPENAI_API_KEY=your_openai_key_here
CHROMA_HOST=localhost
CHROMA_PORT=8001
```

## API Documentation

### WebSocket Endpoint
**URL**: `ws://localhost:8000/ws/audio`

**Purpose**: Bidirectional audio streaming for real-time voice communication

**Message Types**:
- `status`: Connection status updates
- `audio_response`: Audio and text responses from assistant

### HTTP Endpoints

#### Health Check
```http
GET /health
```
Returns server health status.

#### Text-to-Speech
```http
POST /tts
Content-Type: application/x-www-form-urlencoded

text=Hello world
```
Converts text to speech and returns audio file.

### WebSocket Message Format

#### Client → Server
```json
{
  "type": "audio",
  "data": "base64_encoded_pcm_audio"
}
```

#### Server → Client
```json
{
  "type": "audio_response",
  "text": "Assistant response text",
  "audio": "base64_encoded_wav_audio",
  "audio_format": "wav"
}
```

## Pipeline Components

### 1. Pipeline Manager (`pipeline_manager.py`)
**Purpose**: Orchestrates the entire audio processing pipeline

**Key Features**:
- State management (IDLE, LISTENING, PROCESSING, RESPONDING)
- Audio buffering and processing coordination
- Parallel processing optimization
- Duplicate utterance prevention

**Configuration**:
```python
PipelineManager(
    max_buffer_duration=1.5,        # Audio buffer size
    processing_timeout=15.0,        # Processing timeout
    min_processing_interval=0.1,    # Min time between processing
    enable_parallel_processing=True # Parallel execution
)
```

### 2. Voice Activity Detection (`vad.py`)
**Purpose**: Detects speech boundaries in audio streams

**Features**:
- Silero VAD integration
- Configurable sensitivity thresholds
- Batch processing for performance
- Real-time audio monitoring

**Usage**:
```python
vad = VadWrapper(
    threshold=0.25,        # Speech detection sensitivity
    max_tail_ms=150,       # Silence duration for end detection
    batch_processing=True  # Enable batch mode
)
```

### 3. Speech Recognition (`asr.py`)
**Purpose**: Converts audio to text using Whisper

**Features**:
- Streaming Whisper integration
- Ultra-fast mode optimization
- Partial transcript support
- Session management

**Configuration**:
```python
asr = StreamingASR()
asr.enable_ultra_fast_mode(True)  # Enable performance mode
```

### 4. RAG Engine (`rag.py`)
**Purpose**: Retrieves relevant policy documents and generates responses

**Features**:
- ChromaDB vector database
- SentenceTransformer embeddings
- LLM-powered response generation
- Business query classification

**Architecture**:
```python
class PolicyRAG:
    def __init__(self):
        self.chroma = chromadb.PersistentClient(path="./chroma")
        self.embed_model = SentenceTransformer("all-MiniLM-L6-v2")
        self.llm = LLMWrapper()
        self.threshold = 2.0  # Similarity threshold
```

### 5. Text-to-Speech (`tts.py`)
**Purpose**: Converts text responses to audio

**Features**:
- Microsoft Edge TTS integration
- Multiple TTS engine fallbacks
- Audio caching for performance
- Multiple voice options

**Supported Engines**:
1. Microsoft Edge TTS (recommended)
2. pyttsx3 (cross-platform)
3. Windows SAPI (Windows)
4. eSpeak (Linux/Unix)

## Frontend Components

### Core Structure
```
frontend/
├── src/
│   ├── App.tsx              # Main application component
│   ├── components/
│   │   └── AudioChat.tsx    # Voice chat interface
│   └── main.tsx             # Application entry point
├── index.html               # HTML template
├── styles.css               # Global styles
└── script.js                # Legacy JavaScript (deprecated)
```

### AudioChat Component
**Purpose**: Main voice interaction interface

**Features**:
- WebSocket audio streaming
- Real-time transcription display
- Voice visualizer animations
- Call controls and status

**Key Methods**:
```typescript
class AudioChat {
    startCall(): void           // Initialize voice session
    stopCall(): void            // End voice session
    sendAudio(audio: Blob): void // Send audio to backend
    handleResponse(data: any): void // Process server responses
}
```

### UI Features
- **Glass Morphism Design**: Translucent cards with backdrop blur
- **Voice Visualizer**: Real-time audio wave animations
- **Responsive Layout**: Mobile-first design approach
- **Dark Theme**: Modern gradient backgrounds
- **Smooth Animations**: CSS transitions and keyframes

## Testing

### Test Structure
```
backend/
├── test_asr_transcription.py      # ASR functionality tests
├── test_llm_direct.py            # LLM integration tests
├── test_pipeline_fixes.py        # Pipeline optimization tests
├── test_rag_policies.py          # RAG system tests
├── test_tts.py                   # TTS engine tests
└── test_voice_fix.py             # Voice processing tests
```

### Running Tests
```bash
cd backend

# Run all tests
python -m pytest

# Run specific test
python test_rag_policies.py

# Run with verbose output
python -m pytest -v
```

### Test Categories

#### 1. Unit Tests
- Individual component functionality
- Mock dependencies for isolation
- Fast execution (< 1 second)

#### 2. Integration Tests
- Pipeline component interaction
- WebSocket communication
- End-to-end audio processing

#### 3. Performance Tests
- Response time measurement
- Memory usage monitoring
- Concurrent user simulation

### Test Data
- **Audio Samples**: `test_audio_*.wav` files
- **Policy Documents**: Company policy markdown files
- **Expected Responses**: Predefined response patterns

## Deployment

### Production Deployment

#### 1. Docker Deployment
```bash
# Build and start
docker-compose -f docker-compose.prod.yml up -d

# Scale backend
docker-compose up -d --scale backend=3
```

#### 2. Environment Configuration
```bash
# Production environment
export ENVIRONMENT=production
export LOG_LEVEL=WARNING
export MAX_WORKERS=4
export CHROMA_HOST=chroma-db
```

#### 3. Reverse Proxy (Nginx)
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://frontend:3000;
        proxy_set_header Host $host;
    }
    
    location /ws/ {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### Monitoring & Logging

#### 1. Application Logs
```python
# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('voice_agent.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
```

#### 2. Health Checks
```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "pipeline_state": pipeline.get_state().value
    }
```

#### 3. Metrics Collection
- Response time tracking
- Error rate monitoring
- Resource usage statistics
- User session analytics

## Configuration

### Pipeline Configuration
```python
# Ultra-fast mode settings
ULTRA_FAST_CONFIG = {
    "max_buffer_duration": 1.5,
    "processing_timeout": 15.0,
    "min_processing_interval": 0.1,
    "min_time_between_responses": 0.3,
    "enable_parallel_processing": True
}
```

### Audio Configuration
```python
AUDIO_CONFIG = {
    "sample_rate": 16000,
    "channels": 1,
    "bytes_per_sample": 2,
    "chunk_size": 1024
}
```

### RAG Configuration
```python
RAG_CONFIG = {
    "collection_name": "company_policies",
    "similarity_threshold": 2.0,
    "max_results": 3,
    "embedding_model": "all-MiniLM-L6-v2"
}
```

### TTS Configuration
```python
TTS_CONFIG = {
    "voice": "en-US-AriaNeural",
    "rate": "+0%",
    "volume": "+0%",
    "cache_size": 100
}
```

## Troubleshooting

### Common Issues

#### 1. Audio Not Working
**Symptoms**: No audio input/output
**Solutions**:
- Check microphone permissions
- Verify WebSocket connection
- Check browser console for errors
- Ensure backend is running

#### 2. Poor Recognition Quality
**Symptoms**: Incorrect transcriptions
**Solutions**:
- Reduce background noise
- Speak clearly and slowly
- Adjust VAD sensitivity
- Check audio sample rate

#### 3. Slow Response Times
**Symptoms**: Delays > 5 seconds
**Solutions**:
- Enable ultra-fast mode
- Check network latency
- Optimize model loading
- Use parallel processing

#### 4. TTS Failures
**Symptoms**: No audio responses
**Solutions**:
- Verify Edge TTS access
- Check fallback engines
- Clear TTS cache
- Restart TTS service

### Debug Mode
```python
# Enable debug logging
logging.getLogger().setLevel(logging.DEBUG)

# Enable pipeline debugging
pipeline.enable_debug_mode(True)

# Monitor WebSocket messages
logger.debug(f"WebSocket message: {message}")
```

### Performance Optimization
```python
# Enable caching
tts.enable_caching(True)

# Use parallel processing
pipeline.enable_parallel_processing(True)

# Optimize buffer sizes
pipeline.set_buffer_optimization(True)
```

## Development Guide

### Code Structure
```
backend/
├── pipeline/           # Core processing components
├── tests/              # Test files
├── config.py           # Configuration management
├── main.py             # FastAPI application
└── requirements.txt    # Dependencies

frontend/
├── src/                # React source code
├── public/             # Static assets
├── package.json        # Node.js dependencies
└── vite.config.js      # Build configuration
```

### Development Workflow
1. **Feature Development**
   - Create feature branch
   - Implement changes
   - Add tests
   - Update documentation

2. **Testing**
   - Run unit tests
   - Test integration
   - Performance testing
   - User acceptance testing

3. **Deployment**
   - Build Docker images
   - Deploy to staging
   - Run smoke tests
   - Deploy to production

### Contributing
1. Fork the repository
2. Create feature branch
3. Make changes with tests
4. Submit pull request
5. Code review process
6. Merge to main branch

### Code Standards
- **Python**: PEP 8, type hints, docstrings
- **TypeScript**: ESLint, Prettier, strict mode
- **Testing**: 90%+ coverage, meaningful test names
- **Documentation**: Inline comments, README updates

---

## Quick Reference

### Start Development
```bash
# Backend
cd backend && uvicorn main:app --reload

# Frontend
cd frontend && npm run dev

# Docker
docker-compose up -d
```

### Key Commands
```bash
# Load policies
python load_policies.py

# Run tests
python -m pytest

# Build frontend
npm run build

# Check health
curl http://localhost:8000/health
```

### Configuration Files
- `.env`: Environment variables
- `docker-compose.yml`: Service orchestration
- `requirements.txt`: Python dependencies
- `package.json`: Node.js dependencies

---

*This documentation covers the complete AI Voice Assistant project. For specific implementation details, refer to the individual component files and inline documentation.*
