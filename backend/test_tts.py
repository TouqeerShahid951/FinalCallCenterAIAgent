# Test TTS before starting the pipeline
from pipeline.tts import TTSWrapper, CachedTTSWrapper

print("Testing TTS...")
tts = CachedTTSWrapper()
test_response = "Hello! I'm working properly now."
audio_bytes = tts.synthesize_with_cache(test_response)
print(f"TTS generated {len(audio_bytes)} bytes")

# Save to file for testing
with open('test_tts.wav', 'wb') as f:
    f.write(audio_bytes)
print("Saved test_tts.wav - try playing it!")