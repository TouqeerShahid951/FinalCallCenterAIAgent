from typing import Optional
import numpy as np
import torch
import time
import logging
from collections import deque

logger = logging.getLogger(__name__)

class VadWrapper:
    """Improved wrapper around Silero VAD with better state management and performance."""

    def __init__(self, 
                 threshold: Optional[float] = None, 
                 max_tail_ms: int = 2000,  # FIXED: Increased from 1000ms to 2000ms for more natural speech
                 sample_rate: int = 16000,
                 min_chunk_size: int = 256,
                 enable_audio_monitoring: bool = False,
                 batch_processing: bool = True):
        logger.info("🎤 Initializing Silero VAD...")
        
        # Load Silero VAD model
        self.model, utils = torch.hub.load(repo_or_dir='snakers4/silero-vad',
                                          model='silero_vad',
                                          force_reload=False,
                                          onnx=False)
        (self.get_speech_timestamps, self.save_audio, self.read_audio, 
         self.VADIterator, self.collect_chunks) = utils
        
        self.sample_rate = sample_rate
        self.threshold = threshold or 0.3
        self.max_tail_ms = max_tail_ms
        self.min_chunk_size = min_chunk_size
        self.enable_audio_monitoring = enable_audio_monitoring
        self.batch_processing = batch_processing
        
        # Pre-allocate tensor for common chunk sizes to reduce overhead
        self._tensor_cache = {}
        self._audio_buffer = deque(maxlen=1000)  # Buffer for small chunks
        self._accumulated_samples = 0
        
        # NEW: Predictive VAD parameters
        self.speech_momentum = 0.0
        self.predictive_threshold = 0.5  # REDUCED from 0.7 to 0.5 for more conservative triggering
        self.recent_probabilities = deque(maxlen=10)  # Track recent speech probabilities
        
        logger.info(f"VAD configured: threshold={self.threshold}, tail={max_tail_ms}ms, "
                   f"sample_rate={sample_rate}, min_chunk_size={min_chunk_size}")
        logger.info(f"🎯 Predictive VAD enabled: threshold={self.predictive_threshold}")
        
        self.reset()

    def reset(self):
        """Reset VAD state for new audio session."""
        self.end_of_utterance = False
        self.last_speech_time = 0
        self.silence_start = None
        self._was_speaking = False
        self._last_speech_result = False
        self._utterance_processed = False
        self._audio_buffer.clear()
        self._accumulated_samples = 0
        logger.debug("VAD: State reset")
        
    def _get_or_create_tensor(self, wav: np.ndarray) -> torch.Tensor:
        """Get cached tensor or create new one to reduce overhead."""
        size = len(wav)
        if size not in self._tensor_cache:
            self._tensor_cache[size] = torch.zeros(size, dtype=torch.float32)
        
        tensor = self._tensor_cache[size]
        tensor.copy_(torch.from_numpy(wav))
        return tensor
    
    def _monitor_audio_levels(self, wav: np.ndarray) -> None:
        """Monitor audio levels for debugging (optional)."""
        if not self.enable_audio_monitoring or len(wav) == 0:
            return
            
        rms = np.sqrt(np.mean(wav**2))
        peak = np.max(np.abs(wav))
        
        if rms < 0.01:
            logger.warning(f"VAD: Very quiet audio (RMS={rms:.4f}) - speak louder!")
        elif rms < 0.05:
            logger.debug(f"VAD: Quiet audio (RMS={rms:.4f})")
        else:
            logger.debug(f"VAD: Good levels (RMS={rms:.4f}, Peak={peak:.4f})")
    
    def _process_vad_inference(self, wav: np.ndarray) -> float:
        """Run VAD inference on audio chunk."""
        wav_tensor = self._get_or_create_tensor(wav)
        
        try:
            speech_prob = self.model(wav_tensor, self.sample_rate).item()
            return speech_prob
        except Exception as e:
            logger.error(f"VAD inference failed: {e}")
            return 0.0  # Assume silence on error
    
    def is_speech(self, pcm_bytes: bytes) -> bool:
        """
        Check if audio chunk contains speech.
        Splits large chunks into VAD-compatible sizes for optimal processing.
        
        Args:
            pcm_bytes: Raw PCM audio bytes (16-bit, mono)
            
        Returns:
            bool: True if speech is detected
        """
        if len(pcm_bytes) == 0:
            logger.warning("VAD: Empty audio chunk received")
            return self._last_speech_result
        
        # Target: 1024 bytes = 512 samples for 16kHz VAD
        target_chunk_size = 1024
        
        # Split large chunk into smaller ones
        speech_detected = False
        
        for i in range(0, len(pcm_bytes), target_chunk_size):
            chunk = pcm_bytes[i:i + target_chunk_size]
            
            # Only process complete 1024-byte chunks
            if len(chunk) == target_chunk_size:
                # Convert to audio array
                wav = np.frombuffer(chunk, dtype=np.int16).astype(np.float32) / 32768.0
                
                # Create tensor (512 samples with batch dimension)
                wav_tensor = torch.from_numpy(wav).float().unsqueeze(0)
                
                # VAD inference
                try:
                    with torch.no_grad():
                        speech_prob = self.model(wav_tensor, self.sample_rate).item()
                    
                    is_speech = speech_prob > self.threshold
                    
                    if is_speech:
                        speech_detected = True
                        # Update your state tracking here
                        self._update_speech_state(True, speech_prob)
                        break  # Found speech, no need to check remaining chunks
                        
                except Exception as e:
                    logger.error(f"VAD inference failed: {e}")
                    continue
        
        # If no speech found in any chunk
        if not speech_detected:
            self._update_speech_state(False, 0.0)
        
        # Update last result for consistency
        self._last_speech_result = speech_detected
        
        return speech_detected
    
    def mark_utterance_processed(self):
        """
        Mark the current utterance as processed by the pipeline.
        Call this after processing an end-of-utterance to prevent repeated triggers.
        """
        self._utterance_processed = True
        logger.debug("VAD: Utterance marked as processed")
    
    def force_end_utterance(self):
        """Force end of current utterance (useful for manual triggers)."""
        if self._was_speaking and not self._utterance_processed:
            self.end_of_utterance = True
            self._was_speaking = False
            self._utterance_processed = True
            logger.info("VAD: Forced end of utterance")
    
    def get_stats(self) -> dict:
        """Get current VAD statistics for monitoring."""
        current_time = time.time() * 1000
        silence_duration = 0
        
        if self.silence_start is not None:
            silence_duration = current_time - self.silence_start
            
        return {
            'is_speaking': self._was_speaking,
            'end_of_utterance': self.end_of_utterance,
            'last_speech_time': self.last_speech_time,
            'silence_duration_ms': silence_duration,
            'utterance_processed': self._utterance_processed,
            'buffered_samples': self._accumulated_samples,
            'threshold': self.threshold
        }
    
    def update_threshold(self, new_threshold: float):
        """Dynamically update VAD threshold."""
        old_threshold = self.threshold
        self.threshold = max(0.0, min(1.0, new_threshold))  # Clamp to valid range
        logger.info(f"VAD: Threshold updated from {old_threshold} to {self.threshold}")
    
    def clear_cache(self):
        """Clear tensor cache (useful for memory management)."""
        self._tensor_cache.clear()
        logger.debug("VAD: Tensor cache cleared")
    
    def get_optimal_chunk_size(self) -> int:
        """Get the optimal chunk size in bytes for VAD processing."""
        return 1024  # 512 samples * 2 bytes per sample for 16-bit audio

    def should_trigger_early_processing(self, recent_probabilities=None) -> bool:
        """Predict end of speech before full silence for faster processing."""
        if recent_probabilities is None:
            recent_probabilities = self.recent_probabilities
            
        # FIXED: Require more data for more stable prediction
        if len(recent_probabilities) < 8:  # INCREASED from 5 to 8 for more stability
            return False
            
        # Look for declining speech probability trend
        # Convert deque to list for proper slicing
        recent_probs = list(recent_probabilities)
        
        # FIXED: Use more recent samples for trend analysis
        recent_trend = sum(recent_probs[-5:]) / 5  # INCREASED from 3 to 5 samples
        
        # FIXED: More conservative threshold check
        if recent_trend < self.predictive_threshold and recent_trend < 0.3:  # Additional safety check
            logger.debug(f"🎯 Predictive VAD: trend={recent_trend:.3f} < {self.predictive_threshold}")
            return True
            
        return False
    
    def _update_speech_state(self, is_speech: bool, speech_prob: float) -> None:
        """Update internal speech state and end-of-utterance detection with predictive tracking."""
        current_time = time.time() * 1000  # milliseconds
        
        # NEW: Track speech probabilities for predictive analysis
        self.recent_probabilities.append(speech_prob)
        
        logger.debug(f"VAD: prob={speech_prob:.3f}, threshold={self.threshold}, "
                    f"is_speech={is_speech}, was_speaking={self._was_speaking}")
        
        if is_speech:
            # Speech detected
            if not self._was_speaking:
                # Start of new utterance
                self._was_speaking = True
                self.end_of_utterance = False
                self._utterance_processed = False
                self.silence_start = None
                logger.debug("VAD: Speech started")
            
            self.last_speech_time = current_time
            
        else:
            # Silence detected
            if self._was_speaking and not self._utterance_processed:
                # First silence after speech
                if self.silence_start is None:
                    self.silence_start = current_time
                    logger.debug("VAD: Silence started after speech")
                
                # Check if silence duration exceeds threshold
                silence_duration = current_time - self.silence_start
                if silence_duration >= self.max_tail_ms:
                    # End of utterance detected
                    self.end_of_utterance = True
                    self._was_speaking = False
                    logger.info(f"VAD: End of utterance detected after {silence_duration:.0f}ms silence")
                    
        # Update speech momentum for predictive analysis
        if len(self.recent_probabilities) >= 3:
            # Convert deque to list for proper slicing
            recent_probs = list(self.recent_probabilities)
            recent_avg = sum(recent_probs[-3:]) / 3
            self.speech_momentum = recent_avg - speech_prob  # Positive = declining speech
