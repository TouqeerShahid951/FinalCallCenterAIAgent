import os
import subprocess
import tempfile
import logging
import asyncio
from typing import Generator
import numpy as np
import io
import wave
from pathlib import Path
import hashlib

logger = logging.getLogger(__name__)

class TTSWrapper:
    """Text-to-Speech using open-source solutions."""

    def __init__(self, voice: str = "nova", model: str = "tts-1", sample_rate: int = 16000):
        self.voice = voice
        self.model = model
        self.sample_rate = sample_rate
        self.tts_method = "placeholder"
        
        # Try to detect available TTS methods
        self._detect_tts_method()
        logger.info(f"TTS: Using {self.tts_method} method")

    def _detect_tts_method(self):
        """Detect which TTS method is available."""
        
        # Try Edge TTS (best quality, free)
        try:
            import edge_tts
            self.tts_method = "edge"
            logger.info("TTS: Microsoft Edge TTS detected")
            return
        except ImportError:
            pass
        
        # Try Piper TTS (fast, lightweight)
        try:
            result = subprocess.run(['piper', '--help'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                self.tts_method = "piper"
                logger.info("TTS: Piper TTS detected")
                return
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            pass
        
        # Try espeak (widely available)
        try:
            result = subprocess.run(['espeak', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                self.tts_method = "espeak"
                logger.info("TTS: eSpeak detected")
                return
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            pass
        
        # Try Python pyttsx3 (cross-platform TTS)
        try:
            import pyttsx3
            # Test if it works
            engine = pyttsx3.init()
            engine.stop()
            self.tts_method = "pyttsx3"
            logger.info("TTS: pyttsx3 detected")
            return
        except (ImportError, RuntimeError, OSError):
            pass
        
        # Try Windows SAPI (Windows built-in)
        if os.name == 'nt':
            try:
                result = subprocess.run(['powershell', '-Command', 
                                       'Add-Type -AssemblyName System.Speech; exit 0'], 
                                      capture_output=True, timeout=5)
                if result.returncode == 0:
                    self.tts_method = "sapi"
                    logger.info("TTS: Windows SAPI detected")
                    return
            except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
                pass
        
        # Try festival (Linux/Unix)
        try:
            result = subprocess.run(['festival', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                self.tts_method = "festival"
                logger.info("TTS: Festival detected")
                return
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            pass
        
        logger.info("TTS: No TTS engine detected, using placeholder")

    def synthesize(self, text: str) -> bytes:
        """Convert text to speech audio bytes."""
        if not text.strip():
            return b""
        
        import time
        start_time = time.time()
        logger.info(f"🔊 TTS synthesizing: '{text[:50]}...' (method: {self.tts_method})")
        
        try:
            audio_data = b""
            if self.tts_method == "edge":
                audio_data = self._edge_tts(text)
            elif self.tts_method == "piper":
                audio_data = self._piper_tts(text)
            elif self.tts_method == "espeak":
                audio_data = self._espeak_tts(text)
            elif self.tts_method == "sapi":
                audio_data = self._sapi_tts(text)
            elif self.tts_method == "pyttsx3":
                audio_data = self._pyttsx3_tts(text)
            elif self.tts_method == "festival":
                audio_data = self._festival_tts(text)
            else:
                audio_data = self._placeholder_tts(text)
            
            elapsed = time.time() - start_time
            logger.info(f"✅ TTS completed in {elapsed:.2f}s, generated {len(audio_data)} bytes")
            return audio_data
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"❌ TTS: Error in {self.tts_method} after {elapsed:.2f}s: {e}")
            return self._placeholder_tts(text)

    def _edge_tts(self, text: str) -> bytes:
        """Use Microsoft Edge TTS (best quality)."""
        import edge_tts
        import uuid
        
        # Create a unique filename
        temp_filename = f"tts_{uuid.uuid4().hex[:8]}.wav"
        temp_path = os.path.join(tempfile.gettempdir(), temp_filename)
        
        try:
            # Available voices: en-US-JennyNeural, en-US-GuyNeural, en-US-AriaNeural, etc.
            voice = "en-US-JennyNeural"  # Female voice
            
            async def generate_speech():
                communicate = edge_tts.Communicate(text, voice)
                await communicate.save(temp_path)
            
            # Run the async function safely
            try:
                # Check if we're already in an event loop
                loop = asyncio.get_running_loop()
                # If we're in a loop, we need to run in a thread
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, generate_speech())
                    future.result()
            except RuntimeError:
                # No event loop running, safe to create one
                asyncio.run(generate_speech())
            
            # Read the generated audio file
            if os.path.exists(temp_path):
                with open(temp_path, 'rb') as f:
                    audio_data = f.read()
                if len(audio_data) > 0:
                    logger.info(f"TTS: Edge TTS generated {len(audio_data)} bytes")
                    return audio_data
            
            logger.warning("TTS: Edge TTS failed or generated empty file")
            return self._placeholder_tts(text)
            
        except Exception as e:
            logger.warning(f"TTS: Edge TTS error: {e}")
            return self._placeholder_tts(text)
        finally:
            # Clean up temp file
            try:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
            except:
                pass

    def _piper_tts(self, text: str) -> bytes:
        """Use Piper TTS (recommended open-source option)."""
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            try:
                # Run piper TTS
                result = subprocess.run([
                    'piper', '--model', 'en_US-lessac-medium.onnx',
                    '--output_file', temp_file.name
                ], input=text, text=True, capture_output=True, timeout=10)
                
                if result.returncode == 0 and os.path.exists(temp_file.name):
                    with open(temp_file.name, 'rb') as f:
                        audio_data = f.read()
                    logger.info(f"TTS: Piper generated {len(audio_data)} bytes")
                    return audio_data
                else:
                    logger.warning(f"TTS: Piper failed: {result.stderr}")
                    return self._placeholder_tts(text)
            finally:
                if os.path.exists(temp_file.name):
                    os.unlink(temp_file.name)

    def _espeak_tts(self, text: str) -> bytes:
        """Use eSpeak TTS."""
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            try:
                # Run espeak
                result = subprocess.run([
                    'espeak', '-w', temp_file.name, '-s', '150', '-v', 'en+f3', text
                ], capture_output=True, timeout=10)
                
                if result.returncode == 0 and os.path.exists(temp_file.name):
                    with open(temp_file.name, 'rb') as f:
                        audio_data = f.read()
                    logger.info(f"TTS: eSpeak generated {len(audio_data)} bytes")
                    return audio_data
                else:
                    logger.warning("TTS: eSpeak failed")
                    return self._placeholder_tts(text)
            finally:
                if os.path.exists(temp_file.name):
                    os.unlink(temp_file.name)

    def _sapi_tts(self, text: str) -> bytes:
        """Use Windows SAPI TTS."""
        import uuid
        import time
        
        # Create a unique filename to avoid conflicts
        temp_filename = f"tts_{uuid.uuid4().hex[:8]}.wav"
        temp_path = os.path.join(tempfile.gettempdir(), temp_filename)
        
        try:
            # Escape text for PowerShell
            safe_text = text.replace("'", "''").replace('"', '""')
            
            # PowerShell script to use Windows SAPI
            ps_script = f"""
            Add-Type -AssemblyName System.Speech
            $synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
            $synth.Rate = 0
            $synth.Volume = 100
            $synth.SetOutputToWaveFile('{temp_path}')
            $synth.Speak('{safe_text}')
            $synth.Dispose()
            """
            
            result = subprocess.run([
                'powershell', '-ExecutionPolicy', 'Bypass', '-Command', ps_script
            ], capture_output=True, timeout=20, text=True)
            
            # Wait a moment for file to be fully written
            time.sleep(0.1)
            
            if result.returncode == 0 and os.path.exists(temp_path):
                # Wait for file to be released by Windows
                max_retries = 10
                for i in range(max_retries):
                    try:
                        with open(temp_path, 'rb') as f:
                            audio_data = f.read()
                        if len(audio_data) > 0:
                            logger.info(f"TTS: Windows SAPI generated {len(audio_data)} bytes")
                            return audio_data
                        time.sleep(0.1)
                    except (PermissionError, IOError) as e:
                        if i < max_retries - 1:
                            time.sleep(0.1)
                            continue
                        else:
                            logger.warning(f"TTS: File access error after {max_retries} retries: {e}")
                            break
            
            # If we get here, something went wrong
            if result.stderr:
                logger.warning(f"TTS: PowerShell error: {result.stderr}")
            logger.warning("TTS: Windows SAPI failed or generated empty file")
            return self._placeholder_tts(text)
            
        except subprocess.TimeoutExpired:
            logger.warning("TTS: Windows SAPI timeout")
            return self._placeholder_tts(text)
        except Exception as e:
            logger.warning(f"TTS: Windows SAPI error: {e}")
            return self._placeholder_tts(text)
        finally:
            # Clean up temp file
            try:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
            except:
                pass  # Ignore cleanup errors

    def _pyttsx3_tts(self, text: str) -> bytes:
        """Use pyttsx3 TTS (cross-platform Python TTS)."""
        import uuid
        import time
        
        # Create a unique filename
        temp_filename = f"tts_{uuid.uuid4().hex[:8]}.wav"
        temp_path = os.path.join(tempfile.gettempdir(), temp_filename)
        
        try:
            import pyttsx3
            
            engine = pyttsx3.init()
            engine.setProperty('rate', 150)    # Speed of speech
            engine.setProperty('volume', 0.9)  # Volume (0.0 to 1.0)
            
            # Save to file
            engine.save_to_file(text, temp_path)
            engine.runAndWait()
            engine.stop()
            
            # Wait for file to be written
            time.sleep(0.2)
            
            if os.path.exists(temp_path):
                with open(temp_path, 'rb') as f:
                    audio_data = f.read()
                if len(audio_data) > 0:
                    logger.info(f"TTS: pyttsx3 generated {len(audio_data)} bytes")
                    return audio_data
            
            logger.warning("TTS: pyttsx3 failed or generated empty file")
            return self._placeholder_tts(text)
            
        except Exception as e:
            logger.warning(f"TTS: pyttsx3 error: {e}")
            return self._placeholder_tts(text)
        finally:
            # Clean up temp file
            try:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
            except:
                pass

    def _festival_tts(self, text: str) -> bytes:
        """Use Festival TTS."""
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            try:
                # Run festival
                result = subprocess.run([
                    'festival', '--tts', '--otype', 'wav', '--output', temp_file.name
                ], input=text, text=True, capture_output=True, timeout=10)
                
                if result.returncode == 0 and os.path.exists(temp_file.name):
                    with open(temp_file.name, 'rb') as f:
                        audio_data = f.read()
                    logger.info(f"TTS: Festival generated {len(audio_data)} bytes")
                    return audio_data
                else:
                    logger.warning("TTS: Festival failed")
                    return self._placeholder_tts(text)
            finally:
                if os.path.exists(temp_file.name):
                    os.unlink(temp_file.name)

    def _placeholder_tts(self, text: str) -> bytes:
        """Generate placeholder audio (silence) when real TTS is not available."""
        logger.info(f"🔊 TTS placeholder would say: '{text}'")
        
        # Generate silence proportional to text length
        duration = max(1.0, len(text) * 0.08)  # At least 1 second, ~0.08s per character
        samples = int(self.sample_rate * duration)
        silence = np.zeros(samples, dtype=np.int16)
        
        # Create WAV file in memory
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(self.sample_rate)
            wav_file.writeframes(silence.tobytes())
        
        return wav_buffer.getvalue()

    def synthesize_stream(self, text: str) -> Generator[bytes, None, None]:
        """Stream TTS audio in chunks."""
        audio_bytes = self.synthesize(text)
        if audio_bytes:
            yield audio_bytes

class CachedTTSWrapper(TTSWrapper):
    """TTS wrapper with in-memory caching for common responses."""
    
    def __init__(self, voice: str = "nova", model: str = "tts-1", sample_rate: int = 16000, max_cache_size: int = 100):
        super().__init__(voice, model, sample_rate)
        self.response_cache = {}  # In-memory cache for common responses
        self.max_cache_size = max_cache_size
        self.cache_hits = 0
        self.cache_misses = 0
        
        logger.info(f"🎯 CachedTTS initialized with {max_cache_size} max cache entries")
    
    def synthesize_with_cache(self, text: str) -> bytes:
        """TTS with in-memory caching for common responses."""
        if not text or not text.strip():
            return b""
            
        # Generate hash for text (use first 100 chars for efficiency)
        text_key = text[:100].strip().lower()
        text_hash = hashlib.md5(text_key.encode()).hexdigest()
        
        if text_hash in self.response_cache:
            self.cache_hits += 1
            logger.info(f"🎯 TTS cache HIT: '{text[:30]}...' (cache hits: {self.cache_hits})")
            return self.response_cache[text_hash]
        
        # Cache miss - generate new TTS
        self.cache_misses += 1
        logger.debug(f"🎯 TTS cache MISS: '{text[:30]}...' (cache misses: {self.cache_misses})")
        
        # Generate new TTS using parent class
        audio = self.synthesize(text)
        
        # Cache if space available
        if len(self.response_cache) < self.max_cache_size:
            self.response_cache[text_hash] = audio
            logger.debug(f"🎯 TTS cached: '{text[:30]}...' (cache size: {len(self.response_cache)})")
        else:
            # Remove oldest entry if cache is full (simple FIFO)
            oldest_key = next(iter(self.response_cache))
            del self.response_cache[oldest_key]
            self.response_cache[text_hash] = audio
            logger.debug(f"🎯 TTS cache updated: '{text[:30]}...' (cache size: {len(self.response_cache)})")
        
        return audio
    
    def get_cache_stats(self) -> dict:
        """Get cache performance statistics."""
        return {
            'cache_size': len(self.response_cache),
            'max_cache_size': self.max_cache_size,
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'hit_rate': self.cache_hits / (self.cache_hits + self.cache_misses) if (self.cache_hits + self.cache_misses) > 0 else 0
        }
    
    def clear_cache(self):
        """Clear the TTS cache."""
        cache_size = len(self.response_cache)
        self.response_cache.clear()
        logger.info(f"🎯 TTS cache cleared ({cache_size} entries removed)")
    
    def get_cache_keys(self) -> list:
        """Get list of cached text keys (for debugging)."""
        return list(self.response_cache.keys())
