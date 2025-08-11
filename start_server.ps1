# PowerShell script to start the voice agent server with API key
$env:OPENROUTER_API_KEY="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"

Write-Host "🔑 API Key set: $($env:OPENROUTER_API_KEY.Substring(0,20))..."
Write-Host "🚀 Starting Voice Agent Server..."

uvicorn main:app --host 127.0.0.1 --port 8000
