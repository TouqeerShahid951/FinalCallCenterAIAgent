import requests
import json

# Test OpenRouter API directly
api_key = "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"

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
}

data = {
    "model": "openai/gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "What is your return policy?"}],
    "max_tokens": 100
}

print("Testing OpenRouter API...")
try:
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json=data,
        timeout=30
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print("✅ SUCCESS!")
        print(f"Response: {result['choices'][0]['message']['content']}")
    else:
        print(f"❌ Error: {response.text}")
        
except Exception as e:
    print(f"❌ Failed: {e}")
