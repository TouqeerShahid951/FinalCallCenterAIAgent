# Manual Testing Steps

## Step 1: Test OpenRouter API
```bash
python quick_test.py
```
This should return a response from the API.

## Step 2: Install Required Packages (if needed)
```bash
pip install fastapi uvicorn requests sentence-transformers chromadb numpy
```

## Step 3: Test Backend Components
```bash
cd backend
python -c "from pipeline.llm import LLMWrapper; print('LLM import works')"
python -c "from pipeline.rag import PolicyRAG; print('RAG import works')"
```

## Step 4: Run Backend Server
```bash
# Set environment
set OPENROUTER_API_KEY=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

# Start server
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Step 5: Test API Endpoints
Visit http://localhost:8000/docs and test:
- GET /health
- WebSocket /ws/audio (needs browser testing)

## Step 6: Frontend Testing
```bash
cd frontend
npm install
npm run dev
```
Visit http://localhost:5173
