from typing import Optional, List
from faster_whisper import WhisperModel
import numpy as np
import logging
import time
import hashlib

logger = logging.getLogger(__name__)

class StreamingASR:
    """Improved Faster-Whisper-based ASR wrapper for streaming audio with duplicate prevention."""
    
    def __init__(self, 
                 model_name: str = "tiny",  # CHANGED from "small" to "tiny" for much faster processing
                 sample_rate: int = 16000,
                 enable_partial_results: bool = True,
                 partial_update_interval: float = 0.2):  # REDUCED from 0.3s to 0.2s for faster partial results
        logger.info(f"🗣️ Loading OPTIMIZED Faster-Whisper model: {model_name}")
        
        self.model = WhisperModel(
            model_name,
            device="cpu",
            compute_type="int8",  # FIXED: Changed from "int8_float16" to "int8" for better compatibility
            num_workers=2,  # INCREASED from 1 to 2 for better parallel processing
            download_root=None,  # Use default cache location
            local_files_only=False  # Allow model downloads if needed
        )
        
        self.sample_rate = sample_rate
        self.bytes_per_sample = 2
        self.enable_partial_results = enable_partial_results
        self.partial_update_interval = partial_update_interval
        
        # Processing parameters - OPTIMIZED for speed
        self.min_audio_duration = 0.1  # INCREASED from 0.05s to 0.1s to reduce unnecessary processing
        self.max_buffer_duration = 8.0  # REDUCED from 15.0s to 8.0s for faster response
        self.silence_threshold = 0.001  # INCREASED from 0.0005 to 0.001 to reduce false positives
        
        # State tracking
        self.last_partial_transcript = ""
        self.last_partial_hash = ""
        self.last_partial_time = 0
        self.last_final_transcript = ""
        self.transcription_count = 0
        self.finalized = False  # Track if current session has been finalized
        
        # NEW: Ultra-fast ASR mode
        self.ultra_fast_mode = False
        
        logger.info(f"ASR OPTIMIZED: {model_name}, sample_rate={sample_rate}, partial_results={enable_partial_results}")
        logger.info(f"ASR SPEED OPTIMIZATIONS: tiny model, int8, 2 workers, 8s buffer")
        self.reset()
    
    def enable_ultra_fast_mode(self, enabled: bool = True):
        """Enable or disable ultra-fast ASR mode for maximum speed."""
        self.ultra_fast_mode = enabled
        if enabled:
            logger.info("🚀 ULTRA-FAST ASR mode ENABLED - Early cutoff, aggressive parameters")
        else:
            logger.info("🐌 Standard ASR mode enabled - Balanced speed/accuracy")
    
    def reset(self):
        """Reset ASR state for new audio session."""
        logger.debug("ASR: Resetting state")
        self.audio_buffer = bytearray()
        self.last_partial_transcript = ""
        self.last_partial_hash = ""
        self.last_partial_time = 0
        self.last_final_transcript = ""
        self.transcription_count = 0
        self.finalized = False
        logger.debug("ASR: State reset complete")
    
    def _get_audio_hash(self, audio_data: np.ndarray) -> str:
        """Generate hash of audio data for duplicate detection."""
        if len(audio_data) == 0:
            return ""
        # Use a sample of the audio for efficiency
        sample_size = min(1000, len(audio_data))
        sample = audio_data[:sample_size]
        return hashlib.md5(sample.tobytes()).hexdigest()[:8]
    
    def _validate_audio_chunk(self, audio_data: np.ndarray) -> tuple[bool, str]:
        """Validate audio chunk quality and return validation result."""
        if len(audio_data) == 0:
            return False, "empty_audio"
        
        # Check duration
        duration = len(audio_data) / self.sample_rate
        if duration < self.min_audio_duration:
            return False, f"too_short ({duration:.2f}s)"
        
        # Check for silence
        rms = np.sqrt(np.mean(audio_data ** 2))
        if rms < self.silence_threshold:
            return False, f"silence (RMS={rms:.4f})"
        
        # Check for clipping
        max_amplitude = np.max(np.abs(audio_data))
        if max_amplitude > 0.95:
            logger.warning(f"ASR: Audio may be clipped (max={max_amplitude:.3f})")
        
        return True, f"valid (duration={duration:.2f}s, RMS={rms:.4f})"
    
    def _normalize_audio(self, audio_data: np.ndarray) -> np.ndarray:
        """Normalize audio to prevent clipping and improve recognition."""
        max_val = np.max(np.abs(audio_data))
        if max_val > 0:
            # Normalize to 80% of maximum to avoid clipping
            normalized = audio_data / max_val * 0.8
            return normalized
        return audio_data
    
    def _should_generate_partial(self) -> tuple[bool, str]:
        """Determine if we should generate a partial result."""
        if not self.enable_partial_results:
            return False, "partial_results_disabled"
        
        current_time = time.time()
        
        # Check time interval
        if current_time - self.last_partial_time < self.partial_update_interval:
            return False, f"too_frequent ({current_time - self.last_partial_time:.1f}s)"
        
        # Check if we have enough new audio
        buffer_duration = len(self.audio_buffer) / (self.sample_rate * self.bytes_per_sample)
        if buffer_duration < self.min_audio_duration:
            return False, f"insufficient_audio ({buffer_duration:.2f}s)"
        
        return True, f"ready ({buffer_duration:.2f}s)"
    
    def _transcribe_audio(self, audio_data: np.ndarray, is_partial: bool = False) -> tuple[str, float]:
        """Transcribe audio with error handling and timing - OPTIMIZED for speed."""
        start_time = time.time()
        
        try:
            # Configure transcription parameters for SPEED - OPTIMIZED
            beam_size = 1  # ALWAYS use 1 for speed (was 3 for final)
            best_of = 1    # ALWAYS use 1 for speed (was 3 for final)
            
            logger.debug(f"ASR: Transcribing {len(audio_data)} samples "
                        f"({len(audio_data)/self.sample_rate:.2f}s, {'partial' if is_partial else 'final'})")
            
            segments, info = self.model.transcribe(
                audio_data,
                language='en',
                beam_size=beam_size,
                best_of=best_of,
                temperature=0.0,
                compression_ratio_threshold=2.4,
                log_prob_threshold=-1.0,
                no_speech_threshold=0.8,  # INCREASED from 0.6 for faster processing
                condition_on_previous_text=False,
                initial_prompt=None,
                word_timestamps=False,  # Disable for speed
                prepend_punctuations="\"'([{-",
                append_punctuations="\"'.!?):]}",
                vad_filter=False,  # DISABLED VAD filtering for speed (was True)
                vad_parameters=dict(min_silence_duration_ms=500)
            )
            
            # Extract text from segments - OPTIMIZED
            transcript_parts = []
            for segment in segments:
                text = segment.text.strip()
                if text:
                    transcript_parts.append(text)
                    # BREAK after first segment for partial results to save time
                    if is_partial:
                        break
            
            transcript = " ".join(transcript_parts).strip()
            processing_time = time.time() - start_time
            
            if transcript:
                confidence = getattr(info, 'language_probability', 0.0)
                logger.debug(f"ASR: {'Partial' if is_partial else 'Final'} transcription: "
                           f"'{transcript}' (confidence={confidence:.2f}, time={processing_time:.3f}s)")
            else:
                logger.debug(f"ASR: No speech detected in audio chunk (time={processing_time:.3f}s)")
            
            return transcript, processing_time
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"ASR: Transcription error after {processing_time:.3f}s: {e}")
            return "", processing_time

    def _transcribe_audio_ultra_fast(self, audio_data: np.ndarray, is_partial: bool = False) -> tuple[str, float]:
        """Ultra-fast transcription with early cutoff and aggressive parameters for maximum speed."""
        start_time = time.time()
        
        try:
            # ULTRA-AGGRESSIVE parameters for maximum speed
            logger.debug(f"🚀 ULTRA-FAST ASR: Transcribing {len(audio_data)} samples "
                        f"({len(audio_data)/self.sample_rate:.2f}s, {'partial' if is_partial else 'final'})")
            
            segments, info = self.model.transcribe(
                audio_data,
                language='en',
                beam_size=1,           # Minimum for speed
                best_of=1,             # Minimum for speed
                temperature=0.0,       # Deterministic
                compression_ratio_threshold=2.4,
                log_prob_threshold=-1.0,
                no_speech_threshold=0.6,  # LOWERED from 0.8 for faster processing
                condition_on_previous_text=False,
                initial_prompt=None,
                word_timestamps=False,  # Disable for speed
                prepend_punctuations="\"'([{-",
                append_punctuations="\"'.!?):]}",
                vad_filter=False,      # Disabled for maximum speed
                vad_parameters=dict(min_silence_duration_ms=300),  # REDUCED from 500ms
                # NEW: Early stopping parameters
                patience=1.0,          # Stop early if confident
                length_penalty=1.0
            )
            
            # Process only first segment for partial results (speed optimization)
            transcript_parts = []
            for i, segment in enumerate(segments):
                transcript_parts.append(segment.text.strip())
                # EARLY CUTOFF: Stop after first good segment for partials
                if is_partial and i == 0 and segment.text.strip():
                    break
                    
            transcript = " ".join(transcript_parts).strip()
            processing_time = time.time() - start_time
            
            if transcript:
                confidence = getattr(info, 'language_probability', 0.0)
                logger.debug(f"🚀 ULTRA-FAST ASR: {'Partial' if is_partial else 'Final'} transcription: "
                           f"'{transcript}' (confidence={confidence:.2f}, time={processing_time:.3f}s)")
            else:
                logger.debug(f"🚀 ULTRA-FAST ASR: No speech detected (time={processing_time:.3f}s)")
            
            return transcript, processing_time
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"🚀 ULTRA-FAST ASR: Transcription error after {processing_time:.3f}s: {e}")
            return "", processing_time
    
    def feed_audio(self, pcm_bytes: bytes) -> Optional[str]:
        """
        Add audio chunk to buffer and return partial transcript if appropriate.
        
        Returns:
            Optional[str]: Partial transcript if available and different from last result
        """
        if not pcm_bytes or self.finalized:
            return None
        
        # Add to buffer
        self.audio_buffer.extend(pcm_bytes)
        
        # Check if we should generate partial result
        should_partial, reason = self._should_generate_partial()
        
        if not should_partial:
            logger.debug(f"ASR: Skipping partial transcription: {reason}")
            return None
        
        # Convert buffer to audio data
        try:
            audio_data = np.frombuffer(self.audio_buffer, dtype=np.int16).astype(np.float32) / 32768.0
            
            # Validate audio
            is_valid, validation_reason = self._validate_audio_chunk(audio_data)
            if not is_valid:
                logger.debug(f"ASR: Audio validation failed: {validation_reason}")
                return None
            
            # Check for duplicate audio content
            audio_hash = self._get_audio_hash(audio_data)
            if audio_hash == self.last_partial_hash:
                logger.debug("ASR: Duplicate audio content, skipping partial transcription")
                return None
            
            # Normalize audio
            audio_data = self._normalize_audio(audio_data)
            
            # FIXED: Add better logging for debugging
            logger.debug(f"ASR: Attempting partial transcription of {len(audio_data)} samples "
                        f"({len(audio_data)/self.sample_rate:.3f}s)")
            
            # Transcribe
            if self.ultra_fast_mode:
                transcript, processing_time = self._transcribe_audio_ultra_fast(audio_data, is_partial=True)
            else:
                transcript, processing_time = self._transcribe_audio(audio_data, is_partial=True)
            
            if transcript and transcript != self.last_partial_transcript:
                self.last_partial_transcript = transcript
                self.last_partial_hash = audio_hash
                self.last_partial_time = time.time()
                self.transcription_count += 1
                
                logger.info(f"ASR: New partial result #{self.transcription_count}: '{transcript}'")
                return transcript
            else:
                logger.debug(f"ASR: Partial result unchanged or empty (transcript: '{transcript}')")
                return None
                
        except Exception as e:
            logger.error(f"ASR: Error in partial processing: {e}")
            return None
    
    def is_session_active(self) -> bool:
        """Check if there's an active session that can be finalized."""
        return len(self.audio_buffer) > 0 and not self.finalized
    
    def reset_session(self):
        """Reset the ASR session - call this after each finalize."""
        logger.info("ASR: Resetting session")
        self.reset()  # This already exists in your code

    def finalize(self) -> str:
        """
        Process all accumulated audio and return final transcript.
        This should only be called once per audio session.
        """
        if self.finalized:
            logger.warning("ASR: Finalize called on already finalized session")
            return self.last_final_transcript
        
        if len(self.audio_buffer) == 0:
            logger.warning("ASR: No audio in buffer to finalize")
            self.finalized = True
            return ""
        
        try:
            # Convert entire buffer to audio
            audio_data = np.frombuffer(self.audio_buffer, dtype=np.int16).astype(np.float32) / 32768.0
            
            logger.info(f"ASR: Finalizing {len(audio_data)} samples ({len(audio_data)/self.sample_rate:.2f}s)")
            
            # FIXED: Validate the entire accumulated buffer, not individual chunks
            buffer_duration = len(audio_data) / self.sample_rate
            if buffer_duration < self.min_audio_duration:
                logger.warning(f"ASR: Buffer too short for finalization: {buffer_duration:.2f}s < {self.min_audio_duration}s")
                # Return last partial result as fallback
                self.finalized = True
                return self.last_partial_transcript
            
            # Check for silence in the entire buffer
            rms = np.sqrt(np.mean(audio_data ** 2))
            if rms < self.silence_threshold:
                logger.warning(f"ASR: Buffer contains only silence (RMS={rms:.4f})")
                # Return last partial result as fallback
                self.finalized = True
                return self.last_partial_transcript
            
            # Normalize audio
            audio_data = self._normalize_audio(audio_data)
            
            # FIXED: Always attempt final transcription, even without partial results
            if self.ultra_fast_mode:
                transcript, processing_time = self._transcribe_audio_ultra_fast(audio_data, is_partial=False)
            else:
                transcript, processing_time = self._transcribe_audio(audio_data, is_partial=False)
            
            # Use final result or fallback to partial
            if transcript:
                self.last_final_transcript = transcript
                logger.info(f"ASR: Final transcription complete: '{transcript}' (processing_time={processing_time:.3f}s)")
            else:
                # FIXED: If no final transcript, try to generate a partial result now
                logger.info("ASR: No final transcript, attempting partial transcription...")
                if self.ultra_fast_mode:
                    partial_transcript, _ = self._transcribe_audio_ultra_fast(audio_data, is_partial=True)
                else:
                    partial_transcript, _ = self._transcribe_audio(audio_data, is_partial=True)
                if partial_transcript:
                    self.last_final_transcript = partial_transcript
                    logger.info(f"ASR: Using partial as final: '{partial_transcript}'")
                else:
                    self.last_final_transcript = self.last_partial_transcript
                    logger.info(f"ASR: Using last partial as final: '{self.last_final_transcript}'")
            
            self.finalized = True
            return self.last_final_transcript
            
        except Exception as e:
            logger.error(f"ASR: Final transcription error: {e}")
            self.finalized = True
            return self.last_partial_transcript
    
    def is_finalized(self) -> bool:
        """Check if current session has been finalized."""
        return self.finalized
    
    def get_stats(self) -> dict:
        """Get ASR statistics for monitoring."""
        buffer_duration = len(self.audio_buffer) / (self.sample_rate * self.bytes_per_sample)
        
        return {
            "buffer_duration_seconds": buffer_duration,
            "buffer_size_bytes": len(self.audio_buffer),
            "transcription_count": self.transcription_count,
            "last_partial_transcript": self.last_partial_transcript,
            "last_final_transcript": self.last_final_transcript,
            "is_finalized": self.finalized,
            "last_partial_time": self.last_partial_time
        }
    
    def force_partial_update(self) -> Optional[str]:
        """Force generation of partial transcript (ignoring time interval)."""
        if len(self.audio_buffer) == 0:
            return None
        
        old_time = self.last_partial_time
        self.last_partial_time = 0  # Reset time to force update
        
        result = self.feed_audio(b'')  # Feed empty bytes to trigger processing
        
        if result is None:
            self.last_partial_time = old_time  # Restore time if no result
        
        return result
