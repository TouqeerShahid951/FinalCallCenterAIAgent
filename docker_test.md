# Docker Testing Instructions

## Prerequisites
1. Install Docker Desktop for Windows
2. Make sure Docker is running

## Testing Steps

```bash
# 1. Set environment variable (PowerShell)
$env:OPENROUTER_API_KEY="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"

# 2. Build and run the system
docker compose up --build

# 3. In another terminal, ingest policies
docker exec -it voice-agent-backend python scripts/ingest_policies.py

# 4. Test the API
# Visit: http://localhost:8000/docs

# 5. Test the frontend
# Visit: http://localhost:5173
```

## Expected Results
- Backend API should be accessible at http://localhost:8000
- Frontend should be accessible at http://localhost:5173  
- You should be able to ask questions about company policies
