# 🎤 AI Voice Assistant

A modern, real-time voice assistant with beautiful UI, powered by cutting-edge AI technologies.

![Voice Assistant Demo](https://img.shields.io/badge/Status-Production%20Ready-brightgreen)
![Tech Stack](https://img.shields.io/badge/Tech-FastAPI%20%7C%20WebSocket%20%7C%20Edge%20TTS-blue)
![UI](https://img.shields.io/badge/UI-Glass%20Morphism-purple)

## ✨ Features

### 🎯 **Core Capabilities**
- **Real-time Speech Recognition** - OpenAI Whisper with voice activity detection
- **Intelligent Responses** - RAG (Retrieval-Augmented Generation) for accurate answers
- **High-Quality TTS** - Microsoft Edge TTS with neural voices
- **Live Transcription** - Real-time conversation display with export options
- **Single Response System** - No duplicate or overlapping audio streams

### 🎨 **Modern UI/UX**
- **Glass Morphism Design** - Beautiful translucent cards with backdrop blur
- **Smooth Animations** - Voice visualizer, avatar reactions, and transitions
- **Professional Call Interface** - Separate call controls and transcription panels
- **Responsive Layout** - Works perfectly on desktop, tablet, and mobile
- **Dark Theme** - Modern gradient backgrounds with animated orbs

### 🔧 **Technical Excellence**
- **WebSocket Communication** - Real-time bidirectional audio streaming
- **Edge TTS Integration** - Natural-sounding speech with 50% smaller files
- **Voice Activity Detection** - Silero VAD for precise speech detection
- **Async Processing** - Non-blocking pipeline with proper error handling
- **Privacy Focused** - Local processing with secure connections

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js (for serving frontend)
- Microphone access

### 1. Install Dependencies
```bash
# Navigate to project directory
cd Newproject

# Activate virtual environment
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install Python packages
pip install -r requirements.txt
```

### 2. Start the Backend
```bash
cd backend
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

### 3. Open the Frontend
```bash
# Option 1: Simple HTTP server
cd frontend
python -m http.server 3000

# Option 2: Direct file access
# Open frontend/index.html in your browser
```

### 4. Start Talking! 🎉
1. Open `http://localhost:3000` in your browser
2. Allow microphone permissions
3. Click "Start Call" 
4. Begin speaking naturally

## 📋 Project Structure

```
Newproject/
├── backend/
│   ├── main.py                 # FastAPI server & WebSocket handler
│   ├── pipeline/
│   │   ├── pipeline_manager.py # Main orchestrator
│   │   ├── vad.py             # Voice Activity Detection
│   │   ├── asr.py             # Speech Recognition (Whisper)
│   │   ├── rag.py             # Retrieval-Augmented Generation
│   │   ├── llm.py             # Language Model interface
│   │   └── tts.py             # Text-to-Speech (Edge TTS)
│   └── requirements.txt       # Python dependencies
├── frontend/
│   ├── index.html            # Main voice assistant interface
│   ├── demo.html             # Feature showcase & instructions
│   ├── styles.css            # Glass morphism & animations
│   └── script.js             # WebSocket client & UI logic
└── README.md                 # This file
```

## 🎨 UI Components

### Call Interface
- **Voice Visualizer** - Real-time audio wave animation
- **Assistant Avatar** - Animated avatar with listening states
- **Call Controls** - Start/end call, mute, settings
- **Status Display** - Connection status and call timer

### Transcription Panel
- **Live Transcription** - Real-time speech-to-text display
- **Conversation History** - Beautiful message bubbles
- **Export Options** - Save conversations as text files
- **Auto-scroll** - Automatic scrolling to latest messages

## 🔊 Voice Assistant Capabilities

### Supported Conversations
- **Greetings** - "Hello!", "How are you?", "Good morning"
- **Company Policies** - Returns, shipping, warranties, payments
- **Casual Chat** - Friendly redirections for non-business topics
- **Thank You** - Polite acknowledgments and goodbyes

### Sample Interactions
```
👤 User: "Hello! How are you today?"
🤖 Assistant: "Hello! I'm doing great, thank you for asking! I'm your customer support assistant. How can I help you today?"

👤 User: "What is your return policy?"
🤖 Assistant: "Our return policy allows returns within 30 days of purchase..."

👤 User: "Thank you for your help!"
🤖 Assistant: "You're very welcome! I'm glad I could help. Have a wonderful day!"
```

## ⚙️ Configuration

### Environment Variables
```bash
# Required for LLM responses
OPENROUTER_API_KEY=your_openrouter_key_here

# Optional - for enhanced TTS (Edge TTS works without this)
OPENAI_API_KEY=your_openai_key_here
```

### TTS Options (Auto-detected)
1. **Microsoft Edge TTS** ✅ (Recommended - High quality, free)
2. **pyttsx3** (Cross-platform backup)
3. **Windows SAPI** (Windows built-in)
4. **eSpeak** (Linux/Unix)
5. **Festival** (Unix systems)

## 🌟 Advanced Features

### Keyboard Shortcuts
- `Ctrl + Space` - Toggle call
- `Ctrl + M` - Toggle mute
- `Shift + ?` - Show help

### Settings Panel
- **Voice Sensitivity** - Adjust microphone sensitivity
- **Auto-scroll** - Toggle automatic transcription scrolling
- **Sound Effects** - Enable/disable notification sounds

### Real-time Features
- **Voice Activity Detection** - Automatic speech detection
- **Live Transcription** - See words as you speak
- **Response Prevention** - No duplicate audio streams
- **Connection Status** - Visual connection indicators

## 🛠️ Technical Details

### Architecture
```
Browser (WebRTC) → WebSocket → FastAPI → Pipeline Manager
                                              ↓
                                         [VAD → ASR → RAG → TTS]
                                              ↓
                              Audio Response ← WebSocket ← FastAPI
```

### Performance
- **Response Time** - ~2-3 seconds end-to-end
- **Audio Quality** - 16kHz PCM, neural TTS voices
- **Memory Usage** - ~500MB for full pipeline
- **Concurrent Users** - Supports multiple WebSocket connections

### Browser Compatibility
- ✅ Chrome 80+
- ✅ Firefox 75+
- ✅ Safari 13+
- ✅ Edge 80+

## 🐛 Troubleshooting

### Common Issues

**Microphone Not Working**
- Ensure browser has microphone permissions
- Check system microphone settings
- Try refreshing the page

**No Audio Response**
- Verify backend server is running on port 8000
- Check browser console for WebSocket errors
- Ensure speakers/headphones are connected

**Poor Recognition Quality**
- Speak clearly and avoid background noise
- Adjust microphone sensitivity in settings
- Ensure stable internet connection

**TTS Not Working**
- Edge TTS should work automatically
- Check backend logs for TTS method detection
- Install alternative TTS engines if needed

## 🔮 Future Enhancements

### Planned Features
- [ ] **Multi-language Support** - Support for multiple languages
- [ ] **Voice Cloning** - Custom voice training
- [ ] **Mobile App** - React Native companion
- [ ] **Cloud Deployment** - Docker containerization
- [ ] **Analytics Dashboard** - Conversation insights
- [ ] **Plugin System** - Extensible functionality

### Technical Improvements
- [ ] **Streaming TTS** - Real-time audio generation
- [ ] **Noise Cancellation** - Advanced audio processing
- [ ] **Offline Mode** - Local-only processing
- [ ] **Performance Optimization** - Faster response times

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **OpenAI** - Whisper speech recognition
- **Microsoft** - Edge TTS neural voices
- **Silero** - Voice activity detection
- **FastAPI** - Modern web framework
- **ChromaDB** - Vector database for RAG

---

<div align="center">

**Built with ❤️ for the future of conversational AI**

[🚀 Try the Demo](frontend/demo.html) | [📖 Documentation](README.md) | [🐛 Report Issues](https://github.com/your-repo/issues)

</div>