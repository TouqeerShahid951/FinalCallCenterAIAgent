"""Configuration settings for the voice agent backend."""

import os
from typing import Optional

class Config:
    """Application configuration."""
    
    # VAD settings
    VAD_THRESHOLD: float = float(os.getenv("VAD_THRESHOLD", "0.6"))
    VAD_MAX_TAIL_MS: int = int(os.getenv("VAD_MAX_TAIL_MS", "300"))
    
    # Wake word settings
    WAKE_WORDS: list[str] = os.getenv("WAKE_WORDS", "Hey Agent,Support please").split(",")
    
    # LLM settings
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "openrouter")  # or "local"
    LLM_MODEL: str = os.getenv("LLM_MODEL", "meta-llama/llama-3.1-8b-instruct:free")
    OPENROUTER_API_KEY: Optional[str] = os.getenv("OPENROUTER_API_KEY")
    
    # RAG settings
    POLICY_COLLECTION: str = os.getenv("POLICY_COLLECTION", "company_policies")
    RAG_THRESHOLD: float = float(os.getenv("RAG_THRESHOLD", "0.7"))
    
    # Audio settings
    SAMPLE_RATE: int = int(os.getenv("SAMPLE_RATE", "16000"))
    
    # TTS settings
    TTS_MODEL_PATH: str = os.getenv("TTS_MODEL_PATH", "models/en_US-libritts-high.onnx")
    
    # Database settings
    CHROMA_PERSIST_DIR: str = os.getenv("CHROMA_PERSIST_DIR", "./chroma")

config = Config()
