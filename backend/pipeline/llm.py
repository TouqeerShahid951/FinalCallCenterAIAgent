import os
from typing import Optional
from openai import OpenAI
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

class LLMWrapper:
    """LLM inference wrapper supporting multiple backends."""
    
    def __init__(self, provider: str = "openrouter", model: str = "openai/gpt-3.5-turbo", api_key: Optional[str] = None):
        logger.info(f"🤖 Initializing LLM: {provider} / {model}")
        self.provider = provider.lower()
        self.model = model
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        
        # Initialize OpenAI client for OpenRouter if API key is available
        if self.provider == "openrouter":
            if not self.api_key:
                logger.warning("LLM: OpenRouter requested but no API key found. Set OPENROUTER_API_KEY environment variable.")
                logger.warning("LLM: You can get a free API key from https://openrouter.ai/")
                self.client = None
            else:
                logger.info("LLM: Initializing OpenRouter client...")
                self.client = OpenAI(
                    base_url="https://openrouter.ai/api/v1",
                    api_key=self.api_key,
                )
                logger.info("✅ LLM initialized successfully")
    
    def generate(self, prompt: str, max_tokens: int = 150) -> str:
        """Generate response from LLM."""
        if self.provider == "openrouter":
            if self.client:
                return self._openrouter_generate(prompt, max_tokens)
            else:
                return "❌ OpenRouter API key not configured. Please set OPENROUTER_API_KEY environment variable.\n\nYou can get a free API key from https://openrouter.ai/"
        elif self.provider == "local":
            return self._local_generate(prompt, max_tokens)
        else:
            # Fallback for demo
            return "❌ Invalid provider specified. Available providers: 'openrouter', 'local'"
    
    def _openrouter_generate(self, prompt: str, max_tokens: int) -> str:
        """Generate using OpenRouter API via OpenAI client."""
        logger.info(f"LLM: Generating response with {self.model} (max_tokens={max_tokens})")
        logger.debug(f"LLM: Prompt preview: {prompt[:100]}...")
        
        try:
            completion = self.client.chat.completions.create(
                extra_headers={
                    "HTTP-Referer": "https://github.com/your-org/voice-agent",
                    "X-Title": "Voice Agent",
                },
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.7,
            )
            response = completion.choices[0].message.content.strip()
            logger.info(f"LLM: Response generated successfully: '{response[:50]}...'")
            return response
        except Exception as e:
            logger.error(f"LLM: OpenRouter API error: {e}", exc_info=True)
            return f"❌ API Error: {str(e)}"
    
    def _local_generate(self, prompt: str, max_tokens: int) -> str:
        """Generate using local llama.cpp server (placeholder)."""
        # This would connect to a local llama.cpp server
        # For now, return a placeholder response
        return "❌ Local LLM not yet implemented. Use 'openrouter' provider instead."
    

