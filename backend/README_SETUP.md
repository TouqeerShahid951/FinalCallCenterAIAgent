# RAG System Setup Guide

## Problem: Agent Not Responding to Policy Questions

If your agent is responding with generic messages like "I'm a business assistant focused on helping with company policies..." instead of specific answers, the ChromaDB database is likely empty.

## Solution: Load Policy Documents

### Step 1: Load Policies into ChromaDB
```bash
cd backend
python load_policies.py
```

This script will:
- Read `policies/company_policies.md`
- Split it into sections (Return Policy, Shipping Policy, etc.)
- Load each section into ChromaDB with embeddings
- Test the database to ensure it's working

### Step 2: Verify Setup
Check the logs for these messages:
```
✅ Successfully loaded X policy sections into ChromaDB
✅ Database test successful - policies are retrievable
```

### Step 3: Test Your Agent
Now try these questions:
- "What's the shipping cost and how many days can I get my item?"
- "What is the policy for returns?"

Expected responses should now include specific information like:
- "Standard shipping is $5.99 and takes 5-7 business days..."
- "You can return items within 30 days of purchase..."

## Troubleshooting

### Threshold Issues
If responses are still generic, the similarity threshold might be too strict:
- Current threshold: `1.5` (lower = more lenient)
- Edit `backend/pipeline/rag.py` line 12 to adjust

### Database Location
ChromaDB stores data in `./chroma/` directory. If you move the backend, you may need to reload policies.

### Logging
Enable debug logging to see similarity scores:
```python
logging.basicConfig(level=logging.DEBUG)
```

Look for log messages like:
```
RAG: Best similarity distance = 0.845 (threshold = 1.5)
```

## Policy Content Structure

Your policies should be in `policies/company_policies.md` with sections like:
```markdown
## Return Policy
Content here...

## Shipping Policy  
Content here...

## Warranty Information
Content here...
```

Each `## Section` becomes a separate document in ChromaDB.
