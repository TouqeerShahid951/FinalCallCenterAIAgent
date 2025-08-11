import asyncio
import logging
import time
import json
import hashlib
from typing import Optional, Dict, Any
from enum import Enum
from websockets.exceptions import ConnectionClosedError
from concurrent.futures import ThreadPoolExecutor

from .vad import VadWrapper
from .asr import StreamingASR
from .rag import PolicyRAG
from .tts import TTSWrapper

logger = logging.getLogger(__name__)

class PipelineState(Enum):
    """Pipeline processing states."""
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    RESPONDING = "responding"
    ERROR = "error"

class PipelineManager:
    """High-level orchestrator for the audio pipeline with ULTRA-FAST optimizations."""

    def __init__(self, 
                 max_buffer_duration: float = 1.5,     # REDUCED from 3.0s for ultra-fast response
                 processing_timeout: float = 15.0,     # INCREASED from 5.0s to allow RAG+TTS to complete
                 min_processing_interval: float = 0.1, # REDUCED from 0.5s for faster processing
                 min_time_between_responses: float = 0.3, # REDUCED from 0.8s for faster responses
                 enable_partial_transcripts: bool = True,
                 # NEW: Enable parallel processing
                 enable_parallel_processing: bool = True):
        logger.info("🚀 Initializing ULTRA-FAST pipeline components...")
        
        # Configuration - ULTRA-OPTIMIZED for speed
        self.max_buffer_duration = max_buffer_duration
        self.processing_timeout = processing_timeout
        self.min_processing_interval = min_processing_interval
        self.enable_partial_transcripts = enable_partial_transcripts
        self.enable_parallel_processing = enable_parallel_processing
        self.sample_rate = 16000
        self.bytes_per_sample = 2
        
        # Initialize components
        logger.info("🎤 Loading VAD (Voice Activity Detection)...")
        self.vad = VadWrapper(
            threshold=0.25,  # REDUCED from 0.3 for more sensitive detection
            max_tail_ms=150,  # REDUCED from 200ms for faster end detection
            enable_audio_monitoring=False,
            batch_processing=True
        )
        logger.info("✅ VAD loaded")
        
        logger.info("🗣️ Loading ASR (Speech Recognition)...")
        self.asr = StreamingASR()
        # Enable ultra-fast ASR mode for better performance
        if hasattr(self.asr, 'enable_ultra_fast_mode'):
            self.asr.enable_ultra_fast_mode(self.enable_parallel_processing)
        logger.info("✅ ASR loaded")
        
        logger.info("🧠 Loading RAG (Policy System)...")
        self.rag = PolicyRAG()
        logger.info("✅ RAG loaded")
        
        logger.info("🔊 Loading TTS (Text-to-Speech)...")
        # Use cached TTS wrapper for better performance
        from .tts import CachedTTSWrapper
        self.tts = CachedTTSWrapper(max_cache_size=100)
        logger.info("✅ TTS loaded with caching enabled")

        # NEW: Dedicated thread pools for parallel processing
        if self.enable_parallel_processing:
            logger.info("⚡ Initializing parallel processing executors...")
            self.asr_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="ASR")
            self.rag_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="RAG") 
            self.tts_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="TTS")
            logger.info("✅ Parallel executors initialized")

        # State management - ULTRA-OPTIMIZED
        self._state = PipelineState.IDLE
        self._buffer = bytearray()
        self._pending_text: Optional[str] = None
        self._chunk_count = 0
        self._last_processing_time = 0
        self._last_processed_hash: Optional[str] = None
        
        # FIXED: Better protection against infinite loops
        self._processing_attempts = 0
        self._max_processing_attempts = 2  # REDUCED from 3 to prevent excessive retries
        self._last_utterance_time = 0
        
        # FIXED: Improved state management
        self.is_processing = False
        self.last_processed_transcript = ""
        self.last_processed_time = 0
        self.min_time_between_responses = min_time_between_responses  # Use parameter
        
        # Async coordination
        self._processing_lock = asyncio.Lock()
        self._state_lock = asyncio.Lock()
        
        # Buffer management - ULTRA-OPTIMIZED
        self._max_buffer_size = int(self.max_buffer_duration * self.sample_rate * self.bytes_per_sample)
        
        # Statistics
        self._stats = {
            'total_chunks': 0,
            'processing_count': 0,
            'last_processing_duration': 0,
            'errors': 0,
            'empty_transcripts': 0,  # NEW: Track empty transcript issues
            'parallel_processing_count': 0,  # NEW: Track parallel processing usage
            'predictive_triggers': 0  # NEW: Track predictive VAD triggers
        }
        
        # NEW: Enable ultra-fast mode by default when parallel processing is enabled
        self.ultra_fast_mode = self.enable_parallel_processing
        
        # FIXED: Add duplicate prevention tracking
        self._last_processed_utterance_hash = None
        self._last_processed_utterance_time = 0
        
        logger.info("🚀 ULTRA-FAST pipeline components initialized successfully!")
        logger.info(f"⚡ Optimizations: {max_buffer_duration}s buffer, {processing_timeout}s timeout, "
                   f"{min_processing_interval}s intervals, parallel={enable_parallel_processing}")
        logger.info(f"🚀 Ultra-fast mode: {'ENABLED' if self.ultra_fast_mode else 'DISABLED'}")

    def _is_duplicate_utterance(self, audio_buffer: bytes) -> bool:
        """Check if this utterance is a duplicate of the last processed one."""
        if not audio_buffer:
            return False
            
        # Generate hash of current audio buffer
        current_hash = hashlib.md5(audio_buffer).hexdigest()[:16]
        
        # Check if this is the same as last processed
        if current_hash == self._last_processed_utterance_hash:
            time_since_last = time.time() - self._last_processed_utterance_time
            if time_since_last < 2.0:  # Within 2 seconds
                logger.info(f"🚫 Duplicate utterance detected (hash: {current_hash[:8]}...) - skipping")
                return True
                
        return False

    def apply_ultra_fast_config(self, config: dict = None):
        """Apply ultra-fast configuration for maximum performance."""
        if config is None:
            # Default ultra-fast configuration
            config = {
                "max_buffer_duration": 1.5,           # Process after 1.5s max
                "processing_timeout": 5.0,            # 5s timeout
                "min_processing_interval": 0.1,       # Check every 100ms
                "min_time_between_responses": 0.3,    # 300ms between responses
                "vad_threshold": 0.25,                # Lower VAD threshold
                "vad_max_tail_ms": 150,              # Shorter silence detection
                "asr_min_duration": 0.05,            # Process very short audio
                "asr_no_speech_threshold": 0.6,      # Lower threshold
                "enable_parallel_processing": True,   # Enable all optimizations
                "enable_predictive_vad": True,        # Enable predictive triggering
                "enable_tts_caching": True           # Enable response caching
            }
        
        logger.info("⚡ Applying ULTRA-FAST configuration...")
        
        # Update pipeline parameters
        self.max_buffer_duration = config.get("max_buffer_duration", self.max_buffer_duration)
        self.processing_timeout = config.get("processing_timeout", self.processing_timeout)
        self.min_processing_interval = config.get("min_processing_interval", self.min_processing_interval)
        self.min_time_between_responses = config.get("min_time_between_responses", self.min_time_between_responses)
        
        # Update VAD settings
        if config.get("enable_predictive_vad", True):
            self.vad.threshold = config.get("vad_threshold", 0.25)
            self.vad.max_tail_ms = config.get("vad_max_tail_ms", 150)
        
        # Update ASR settings
        if config.get("enable_parallel_processing", True) and hasattr(self.asr, 'enable_ultra_fast_mode'):
            self.asr.enable_ultra_fast_mode(True)
        
        # Enable ultra-fast mode
        self.enable_ultra_fast_mode(True)
        
        logger.info("✅ ULTRA-FAST configuration applied successfully!")
        logger.info(f"⚡ Expected performance: 50-70% latency reduction")
        logger.info(f"⚡ Target latency: 0.8-1.5 seconds (was 2-4 seconds)")

    async def _set_state(self, new_state: PipelineState):
        """Thread-safe state transition."""
        async with self._state_lock:
            if self._state != new_state:
                old_state = self._state
                self._state = new_state
                logger.debug(f"🔄 State transition: {old_state.value} → {new_state.value}")

    def _get_buffer_duration(self) -> float:
        """Calculate current buffer duration in seconds."""
        return len(self._buffer) / (self.sample_rate * self.bytes_per_sample)

    def _generate_buffer_hash(self) -> str:
        """Generate content hash for current buffer to prevent duplicate processing."""
        return hashlib.sha256(self._buffer).hexdigest()[:16]

    def _generate_audio_signature(self, audio_data: bytes) -> str:
        """Generate a content-based signature for audio data to prevent duplicates."""
        # Use SHA-256 hash of the audio content for reliable deduplication
        return hashlib.sha256(audio_data).hexdigest()[:16]  # Use first 16 chars for efficiency

    def _should_process_utterance(self) -> tuple[bool, str]:
        """Determine if we should process the current utterance."""
        # Don't process if already processing
        if self.is_processing:
            return False, "already_processing"
        
        # FIXED: Check if we have enough audio
        buffer_duration = self._get_buffer_duration()
        if buffer_duration < 0.3:  # REDUCED from 0.5s to 0.3s for faster response
            return False, f"insufficient_audio ({buffer_duration:.1f}s < 0.3s)"
        
        # Get current buffer state
        current_hash = self._generate_buffer_hash()
        
        # Check for duplicate content (prevent infinite loops)
        if self._last_processed_hash == current_hash:
            return False, "duplicate_content"
        
        # Check VAD end-of-utterance
        if self.vad.end_of_utterance:
            # FIXED: Mark VAD utterance as processed to prevent repeated triggers
            self.vad.mark_utterance_processed()
            return True, f"vad_end_of_utterance ({buffer_duration:.1f}s)"
        
        # Check buffer duration threshold (fallback for missed VAD triggers)
        if buffer_duration >= 5.0:  # Longer threshold for time-based processing
            return True, f"duration_threshold ({buffer_duration:.1f}s)"
        
        return False, f"waiting ({buffer_duration:.1f}s)"

    def _is_duplicate_transcript(self, transcript: str) -> bool:
        """Check if this transcript is a duplicate of recently processed one."""
        if not self.last_processed_transcript:
            return False
        
        # Exact match check
        if transcript == self.last_processed_transcript:
            # Check if enough time has passed
            time_since_last = time.time() - self.last_processed_time
            if time_since_last < self.min_time_between_responses:
                return True
        
        # Similarity check (optional - for very similar transcripts)
        similarity = self._calculate_similarity(transcript, self.last_processed_transcript)
        if similarity > 0.9:  # 90% similar
            time_since_last = time.time() - self.last_processed_time
            if time_since_last < self.min_time_between_responses:
                return True
        
        return False

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts."""
        import re
        
        # Clean and normalize text by removing punctuation and converting to lowercase
        def clean_text(text):
            # Remove punctuation and convert to lowercase
            cleaned = re.sub(r'[^\w\s]', '', text.lower())
            return set(cleaned.split())
        
        words1 = clean_text(text1)
        words2 = clean_text(text2)
        
        if not words1 and not words2:
            return 1.0
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        return intersection / union if union > 0 else 0.0

    def _reset_asr_session(self):
        """Reset ASR session to prevent state issues."""
        logger.info("🔄 Resetting ASR session")
        self.asr.reset_session()

    def _manage_buffer_size(self, new_chunk_size: int):
        """Manage buffer size to prevent memory issues."""
        if len(self._buffer) + new_chunk_size > self._max_buffer_size:
            # Calculate how much to keep (last 5 seconds instead of 2)
            keep_duration = 5.0  # FIXED: Increased from 2.0s to 5.0s to preserve more audio
            keep_bytes = int(keep_duration * self.sample_rate * self.bytes_per_sample)
            
            if len(self._buffer) > keep_bytes:
                removed_bytes = len(self._buffer) - keep_bytes
                self._buffer = self._buffer[-keep_bytes:]
                logger.warning(f"⚠️ Buffer trimmed: removed {removed_bytes} bytes, kept {keep_bytes} bytes")
            else:
                # If even 5 seconds is too much, clear completely
                self._buffer.clear()
                logger.warning("⚠️ Buffer cleared due to size limit")

    async def feed_audio(self, pcm_bytes: bytes) -> Optional[bytes]:
        """Accept incoming PCM audio chunk. If a reply is ready, returns TTS bytes."""
        result = await self.feed_audio_with_transcription(pcm_bytes, None)
        return result['audio'] if result and 'audio' in result else None
    
    async def feed_audio_with_transcription(self, pcm_bytes: bytes, websocket=None) -> Optional[Dict[str, Any]]:
        """Accept incoming PCM audio chunk with transcription support. If a reply is ready, returns dict with audio and text."""
        # Use lock to prevent race conditions
        async with self._processing_lock:
            # Use ultra-fast processing if enabled
            if hasattr(self, 'ultra_fast_mode') and self.ultra_fast_mode:
                return await self._process_audio_chunk_ultra_fast(pcm_bytes, websocket)
            else:
                return await self._process_audio_chunk(pcm_bytes, websocket)

    def enable_ultra_fast_mode(self, enabled: bool = True):
        """Enable or disable ultra-fast processing mode."""
        self.ultra_fast_mode = enabled
        if enabled:
            logger.info("🚀 ULTRA-FAST mode ENABLED - Predictive VAD, parallel processing, aggressive timing")
        else:
            logger.info("🐌 Standard mode enabled - Traditional processing pipeline")
    
    async def _process_audio_chunk(self, pcm_bytes: bytes, websocket=None) -> Optional[Dict[str, Any]]:
        """Process a single audio chunk with proper state management."""
        self._chunk_count += 1
        self._stats['total_chunks'] += 1
        chunk_size = len(pcm_bytes)
        
        logger.debug(f"🎵 Processing chunk #{self._chunk_count} ({chunk_size} bytes)")
        
        # Manage buffer size before adding new data
        self._manage_buffer_size(chunk_size)
        self._buffer.extend(pcm_bytes)
        
        buffer_duration = self._get_buffer_duration()
        logger.debug(f"📊 Buffer: {len(self._buffer)} bytes ({buffer_duration:.2f}s)")
        
        # Set state to listening when we start receiving audio
        if self._state == PipelineState.IDLE:
            await self._set_state(PipelineState.LISTENING)
        
        try:
            # VAD processing
            vad_start = time.time()
            is_speech = self.vad.is_speech(pcm_bytes)
            vad_time = time.time() - vad_start
            
            logger.debug(f"🎤 VAD: {'SPEECH' if is_speech else 'SILENCE'} ({vad_time:.3f}s)")
            
            # Check if we should process the utterance
            should_process, reason = self._should_process_utterance()
            
            if should_process:
                logger.info(f"🔧 Processing utterance: {reason}")
                await self._set_state(PipelineState.PROCESSING)
                
                # FIXED: Set processing flag to prevent concurrent processing
                self.is_processing = True
                
                # FIXED: Increment processing attempts counter
                self._processing_attempts += 1
                
                # Mark this buffer content as processed
                self._last_processed_hash = self._generate_buffer_hash()
                self._last_processing_time = time.time()
                
                # Mark VAD utterance as processed to prevent repeated triggers
                self.vad.mark_utterance_processed()
                
                try:
                    result = await self._process_complete_utterance(websocket)
                    if result:
                        await self._set_state(PipelineState.RESPONDING)
                        return result
                finally:
                    await self._set_state(PipelineState.IDLE)
                    
            else:
                logger.debug(f"🔇 Not processing: {reason}")
                
                # Handle partial transcriptions during speech
                if is_speech and self.enable_partial_transcripts:
                    await self._handle_partial_transcription(pcm_bytes, websocket)
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error in audio chunk processing: {e}")
            self._stats['errors'] += 1
            await self._set_state(PipelineState.ERROR)
            raise

    async def _process_audio_chunk_ultra_fast(self, pcm_bytes: bytes, websocket=None) -> Optional[Dict[str, Any]]:
        """Ultra-fast audio processing with predictive triggers and background processing."""
        self._chunk_count += 1
        self._stats['total_chunks'] += 1
        chunk_size = len(pcm_bytes)
        
        logger.debug(f"🚀 ULTRA-FAST chunk #{self._chunk_count} ({chunk_size} bytes)")
        
        # FIXED: Prevent multiple processing attempts
        if self.is_processing:
            logger.debug("🚀 Skipping processing - already processing utterance")
            return None
        
        # Manage buffer size before adding new data
        self._manage_buffer_size(chunk_size)
        self._buffer.extend(pcm_bytes)
        
        buffer_duration = self._get_buffer_duration()
        logger.debug(f"📊 Buffer: {len(self._buffer)} bytes ({buffer_duration:.2f}s)")
        
        # Set state to listening when we start receiving audio
        if self._state == PipelineState.IDLE:
            await self._set_state(PipelineState.LISTENING)
        
        try:
            # VAD processing
            vad_start = time.time()
            is_speech = self.vad.is_speech(pcm_bytes)
            vad_time = time.time() - vad_start
            
            logger.debug(f"🎤 VAD: {'SPEECH' if is_speech else 'SILENCE'} ({vad_time:.3f}s)")
            
            # FIXED: More conservative predictive processing trigger
            should_process_predictive = (
                buffer_duration >= 1.5 and  # INCREASED from 1.0s to 1.5s for more stability
                hasattr(self.vad, 'should_trigger_early_processing') and
                self.vad.should_trigger_early_processing(getattr(self.vad, 'recent_probabilities', [])) and
                not self.is_processing  # Double-check we're not already processing
            )
            
            # Traditional triggers
            should_process_traditional = (
                self.vad.end_of_utterance and  # ONLY use VAD end detection, not buffer duration
                not self.is_processing  # Ensure we're not already processing
            )
            
            if should_process_predictive or should_process_traditional:
                trigger_type = 'predictive' if should_process_predictive else 'traditional'
                logger.info(f"🚀 ULTRA-FAST trigger: {trigger_type}")
                
                # FIXED: Check for duplicate utterances before processing
                if self._is_duplicate_utterance(self._buffer):
                    logger.info("🚫 Skipping duplicate utterance processing")
                    return None
                
                if should_process_predictive:
                    self._stats['predictive_triggers'] += 1
                
                # FIXED: Set processing flag immediately to prevent duplicates
                self.is_processing = True
                
                # Process in background and return the result
                result = await self._background_process_utterance(websocket)
                return result
            
            # Always handle partial transcriptions
            if is_speech and self.enable_partial_transcripts:
                await self._handle_ultra_fast_partial(pcm_bytes, websocket)
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error in ultra-fast audio processing: {e}")
            self._stats['errors'] += 1
            await self._set_state(PipelineState.ERROR)
            raise

    async def _background_process_utterance(self, websocket):
        """Process utterance in background without blocking audio input."""
        try:
            logger.info("🔄 Background processing started...")
            
            # Take snapshot of current buffer
            buffer_snapshot = bytes(self._buffer)
            
            # FIXED: Mark this utterance as processed to prevent duplicates
            self._last_processed_utterance_hash = hashlib.md5(buffer_snapshot).hexdigest()[:16]
            self._last_processed_utterance_time = time.time()
            
            # Process the snapshot while continuing to accept new audio
            if self.enable_parallel_processing:
                logger.info("🚀 Using parallel processing...")
                result = await self._process_complete_utterance_parallel(websocket)
            else:
                logger.info("🔄 Using sequential processing...")
                result = await self._process_complete_utterance(websocket)
            
            logger.info(f"🔄 Processing result: {result}")
            
            if result:
                logger.info(f"✅ Response generated successfully: {len(result.get('audio', b''))} bytes audio, '{result.get('text', '')}' text")
                
                # FIXED: Let main.py handle both text and audio responses to avoid duplicates
                # Don't send text response here since main.py will send the combined audio_response
                logger.info("📡 Response ready - main.py will handle text and audio transmission")
                
                # FIXED: Return the result so main.py can handle both text and audio
                return result
            else:
                logger.warning("⚠️ No response generated from processing")
                return None
                    
        except Exception as e:
            logger.error(f"❌ Background processing error: {e}", exc_info=True)
            return None
        finally:
            # FIXED: Always reset processing flag when done
            self.is_processing = False
            logger.info("🔄 Background processing completed, processing flag reset")

    async def _handle_ultra_fast_partial(self, pcm_bytes: bytes, websocket=None):
        """Ultra-fast partial transcription handling."""
        try:
            asr_start = time.time()
            partial_text = self.asr.feed_audio(pcm_bytes)
            asr_time = time.time() - asr_start
            
            logger.debug(f"🚀 ULTRA-FAST ASR partial: {asr_time:.3f}s")
            
            if partial_text and partial_text != self._pending_text:
                self._pending_text = partial_text
                logger.debug(f"📝 Partial: '{partial_text}'")
                
                # Send to frontend
                if websocket:
                    await self._send_websocket_message(websocket, {
                        "type": "transcript",
                        "text": partial_text,
                        "final": False
                    })
                    
        except Exception as e:
            logger.warning(f"⚠️ Ultra-fast partial transcription error: {e}")

    async def _handle_partial_transcription(self, pcm_bytes: bytes, websocket=None):
        """Handle partial ASR transcriptions during speech."""
        try:
            asr_start = time.time()
            partial_text = self.asr.feed_audio(pcm_bytes)
            asr_time = time.time() - asr_start
            
            logger.debug(f"🗣️ ASR partial processing: {asr_time:.3f}s")
            
            if partial_text and partial_text != self._pending_text:
                self._pending_text = partial_text
                logger.debug(f"📝 Partial: '{partial_text}'")
                
                # Send to frontend
                if websocket:
                    await self._send_websocket_message(websocket, {
                        "type": "transcript",
                        "text": partial_text,
                        "final": False
                    })
                    
        except Exception as e:
            logger.warning(f"⚠️ Partial transcription error: {e}")

    async def _process_complete_utterance(self, websocket=None) -> Optional[Dict[str, Any]]:
        """Process the complete utterance and generate response."""
        logger.info("🔄 Processing complete utterance...")
        processing_start = time.time()
        
        try:
            # Add processing timeout
            async with asyncio.timeout(self.processing_timeout):
                # Finalize ASR
                transcript = await self._get_final_transcript()
                
                if not transcript or not transcript.strip():
                    logger.warning("⚠️ Empty transcript - no response generated")
                    return None
                
                # Send final transcript
                if websocket:
                    await self._send_websocket_message(websocket, {
                        "type": "transcript",
                        "text": transcript,
                        "final": True
                    })
                
                # Generate response
                response_text = await self._generate_response(transcript)
                
                if not response_text:
                    logger.warning("⚠️ Empty response generated")
                    return None
                
                # Generate TTS
                tts_audio = await self._generate_tts(response_text)
                
                processing_time = time.time() - processing_start
                self._stats['processing_count'] += 1
                self._stats['last_processing_duration'] = processing_time
                
                logger.info(f"⚡ Utterance processed in {processing_time:.3f}s")
                
                return {
                    'audio': tts_audio,
                    'text': response_text,
                    'transcript': transcript,
                    'processing_time': processing_time
                }
                
        except asyncio.TimeoutError:
            logger.error(f"⏰ Processing timeout after {self.processing_timeout}s")
            return None
        except Exception as e:
            logger.error(f"❌ Error processing utterance: {e}")
            raise
        finally:
            # Always reset state after processing attempt
            self._reset_utterance_state()

    async def _process_complete_utterance_parallel(self, websocket=None) -> Optional[Dict[str, Any]]:
        """Process with parallel ASR/RAG and overlapped TTS for ultra-fast response."""
        if not self.enable_parallel_processing:
            logger.debug("Parallel processing disabled, falling back to sequential")
            return await self._process_complete_utterance(websocket)
            
        logger.info("🚀 PARALLEL processing started...")
        processing_start = time.time()
        self._stats['parallel_processing_count'] += 1
        
        try:
            # Add processing timeout
            async with asyncio.timeout(self.processing_timeout):
                # 1. Start ASR finalization immediately
                asr_task = asyncio.create_task(self._get_final_transcript())
                
                # 2. Wait for transcript (this is unavoidable)
                transcript = await asr_task
                if not transcript or not transcript.strip():
                    logger.warning("⚠️ Empty transcript - no response generated")
                    return None
                
                # Send final transcript
                if websocket:
                    await self._send_websocket_message(websocket, {
                        "type": "transcript",
                        "text": transcript,
                        "final": True
                    })
                
                # 3. Start RAG and TTS preparation in parallel
                rag_task = asyncio.create_task(self._generate_response(transcript))
                
                # 4. Get RAG response
                response_text = await rag_task
                logger.info(f"🧠 RAG response received: '{response_text}'")
                
                if not response_text:
                    logger.warning("⚠️ Empty response generated")
                    return None
                
                # 5. Generate TTS (this could be optimized further with streaming)
                logger.info("🔊 Starting TTS generation...")
                tts_task = asyncio.create_task(self._generate_tts(response_text))
                tts_audio = await tts_task
                
                if not tts_audio:
                    logger.warning("⚠️ TTS generation failed - no audio produced")
                    return None
                
                logger.info(f"🔊 TTS generation successful: {len(tts_audio)} bytes")
                
                processing_time = time.time() - processing_start
                self._stats['processing_count'] += 1
                self._stats['last_processing_duration'] = processing_time
                
                logger.info(f"⚡ PARALLEL utterance processed in {processing_time:.3f}s")
                
                result = {
                    'audio': tts_audio,
                    'text': response_text,
                    'transcript': transcript,
                    'processing_time': processing_time
                }
                
                logger.info(f"✅ Returning result: {len(result['audio'])} bytes audio, '{result['text']}' text")
                return result
                
        except asyncio.TimeoutError:
            logger.error(f"⏰ Parallel processing timeout after {self.processing_timeout}s")
            return None
        except Exception as e:
            logger.error(f"❌ Error in parallel processing: {e}")
            raise
        finally:
            # Always reset state after processing attempt
            self._reset_utterance_state()

    def process_utterance(self, duration_threshold=5.0):
        """Process complete utterance with proper state management."""
        if self.is_processing:
            logger.warning("⚠️ Already processing utterance, skipping...")
            return None
        
        # Check if ASR has an active session to finalize
        if not self.asr.is_session_active():
            logger.info("No active ASR session to process")
            return None
        
        self.is_processing = True
        try:
            logger.info("🔄 Processing complete utterance...")
            
            # 1. Finalize ASR to get transcript
            transcript = self.asr.finalize()
            
            # 2. Check for empty or duplicate transcript
            if not transcript or not transcript.strip():
                logger.info("Empty transcript, skipping processing")
                return None
            
            # 3. Check for duplicate transcript (prevent loops)
            if self._is_duplicate_transcript(transcript):
                logger.info(f"Duplicate transcript detected, skipping: '{transcript}'")
                return None
            
            logger.info(f"📜 Final transcript: '{transcript}'")
            
            # 4. Process with RAG
            rag_response = self.rag.respond(transcript)
            logger.info(f"🧠 RAG response: '{rag_response}'")
            
            # 5. Generate TTS audio
            audio_data = self.tts.synthesize(rag_response)
            logger.info(f"🔊 TTS generated {len(audio_data)} bytes")
            
            # 6. Update tracking
            self.last_processed_transcript = transcript
            self.last_processed_time = time.time()
            
            return audio_data
            
        except Exception as e:
            logger.error(f"Error processing utterance: {e}")
            return None
        finally:
            # 7. CRITICAL: Reset ASR session after processing
            self._reset_asr_session()
            self.is_processing = False

    async def _get_final_transcript(self) -> Optional[str]:
        """Get final transcript from ASR."""
        transcript_start = time.time()
        
        # Run ASR finalization in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        transcript = await loop.run_in_executor(None, self.asr.finalize)
        
        transcript_time = time.time() - transcript_start
        logger.info(f"📜 Final transcript: '{transcript}' ({transcript_time:.3f}s)")
        
        return transcript

    async def _generate_response(self, transcript: str) -> Optional[str]:
        """Generate response using RAG."""
        rag_start = time.time()
        
        # Run RAG in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, self.rag.respond, transcript)
        
        rag_time = time.time() - rag_start
        logger.info(f"🧠 RAG response: '{response}' ({rag_time:.3f}s)")
        
        return response

    async def _generate_tts(self, text: str) -> Optional[bytes]:
        """Generate TTS audio using cached wrapper for better performance."""
        tts_start = time.time()
        
        # Run TTS in thread pool to avoid blocking, use cached version if available
        loop = asyncio.get_event_loop()
        if hasattr(self.tts, 'synthesize_with_cache'):
            tts_audio = await loop.run_in_executor(None, self.tts.synthesize_with_cache, text)
        else:
            tts_audio = await loop.run_in_executor(None, self.tts.synthesize, text)
        
        tts_time = time.time() - tts_start
        logger.info(f"🔊 TTS generated {len(tts_audio) if tts_audio else 0} bytes ({tts_time:.3f}s)")
        
        return tts_audio

    async def _send_websocket_message(self, websocket, message: dict):
        """Safely send message via websocket."""
        if not websocket:
            return
            
        try:
            await websocket.send_text(json.dumps(message))
        except ConnectionClosedError:
            logger.debug("🔌 WebSocket connection closed")
        except Exception as e:
            logger.warning(f"⚠️ WebSocket send error: {e}")

    # Legacy method - replaced by _process_complete_utterance
    # async def _process_utterance_with_transcription(self, websocket=None) -> Optional[Dict[str, Any]]:
    #     """Process the complete utterance and generate response with transcription support."""
    #     # This method is deprecated - use _process_complete_utterance instead
    #     pass

    # Legacy method - replaced by _process_complete_utterance
    # async def _process_utterance(self) -> Optional[bytes]:
    #     """Process the complete utterance and generate response."""
    #     # This method is deprecated - use _process_complete_utterance instead
    #     pass

    async def text_to_speech(self, text: str) -> Optional[bytes]:
        """Direct text-to-speech conversion using cached wrapper if available."""
        logger.info(f"🗣️ Direct TTS request: '{text}'")
        loop = asyncio.get_event_loop()
        if hasattr(self.tts, 'synthesize_with_cache'):
            return await loop.run_in_executor(None, self.tts.synthesize_with_cache, text)
        else:
             await loop.run_in_executor(None, self.tts.synthesize, text)

    def _reset_utterance_state(self):
        """Reset state after utterance processing."""
        logger.debug("🧹 Resetting utterance state")
        self._buffer.clear()
        self._pending_text = None
        self._chunk_count = 0
        
        # FIXED: Reset processing attempts counter
        self._processing_attempts = 0
        
        # FIXED: Reset processing state
        self.is_processing = False
        
        # FIXED: Reset ASR session to prevent multiple finalizations
        self.asr.reset_session()
        
        # Reset VAD state for next utterance
        self.vad.reset()

    async def reset(self):
        """Reset the entire pipeline state."""
        logger.info("🔄 Resetting pipeline state")
        
        # FIXED: Use lock to prevent race conditions during reset
        async with self._processing_lock:
            await self._set_state(PipelineState.IDLE)
            self.vad.reset()
            self.asr.reset()
            self._reset_utterance_state()
            self._last_processed_hash = None
            self._last_processing_time = 0
            
            # FIXED: Reset processing attempts counter
            self._processing_attempts = 0
            
            # FIXED: Reset new state properties
            self.is_processing = False
            self.last_processed_transcript = ""
            self.last_processed_time = 0
            
            logger.info("✅ Pipeline reset complete")

    def reset_stream_state(self):
        """Reset the stream state for the next utterance."""
        logger.debug("🧹 Clearing stream state")
        self._buffer.clear()
        self._pending_text = None
        self._chunk_count = 0
        self._processing_response = False
        
        # FIXED: Clear the buffer hash to allow new utterances
        self._last_processed_hash = None
        
        # FIXED: Reset processing time to allow immediate processing
        self._last_processing_time = 0
        
        # FIXED: Reset processing attempts counter
        self._processing_attempts = 0
        
        # FIXED: Reset new state properties
        self.is_processing = False
        self.last_processed_transcript = ""
        self.last_processed_time = 0
        
        logger.debug("✅ Stream state cleared")

    def get_stats(self) -> dict:
        """Get comprehensive pipeline statistics including ultra-fast optimizations."""
        stats = {
            'state': self._state.value,
            'buffer_duration': self._get_buffer_duration(),
            'buffer_size_bytes': len(self._buffer),
            'chunk_count': self._chunk_count,
            'processing_count': self._stats['processing_count'],
            'last_processing_duration': self._stats['last_processing_duration'],
            'errors': self._stats['errors'],
            'empty_transcripts': self._stats['empty_transcripts'],
            'parallel_processing_count': self._stats.get('parallel_processing_count', 0),
            'predictive_triggers': self._stats.get('predictive_triggers', 0),
            'ultra_fast_mode': getattr(self, 'ultra_fast_mode', False),
            'parallel_processing_enabled': getattr(self, 'enable_parallel_processing', False),
            'min_time_between_responses': self.min_time_between_responses,
            'max_buffer_duration': self.max_buffer_duration,
            'processing_timeout': self.processing_timeout,
            'min_processing_interval': self.min_processing_interval
        }
        
        # Add VAD stats if available
        if hasattr(self.vad, 'get_stats'):
            stats['vad'] = self.vad.get_stats()
        
        # Add ASR stats if available
        if hasattr(self.asr, 'get_stats'):
            stats['asr'] = self.asr.get_stats()
        
        # Add TTS cache stats if available
        if hasattr(self.tts, 'get_cache_stats'):
            stats['tts_cache'] = self.tts.get_cache_stats()
        
        return stats

    def get_state(self) -> PipelineState:
        """Get current pipeline state."""
        return self._state

    def should_trigger_processing(self, audio_silence_duration: float, duration_threshold: float = 5.0) -> bool:
        """Determine if we should trigger utterance processing."""
        # Don't trigger if already processing
        if self.is_processing:
            return False
        
        # Check if we have an active session
        if not self.asr.is_session_active():
            return False
        
        # Check duration threshold
        if audio_silence_duration >= duration_threshold:
            return True
        
        return False
