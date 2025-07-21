# Gemini Audio Processing Pipeline & Rate Limiting

## **AUDIO PROCESSING PIPELINE COMPLETE GUIDE**

This steering rule provides comprehensive patterns for audio processing, rate limiting, and real-time audio management in Gemini Live API applications, based on analysis of production implementations.

## **AUDIO PROCESSING ARCHITECTURE**

### **1. Real-time Audio Pipeline**

#### **Production Audio Processing System**
```python
import pyaudio
import asyncio
import collections
import time
import threading
from typing import Optional, Callable

class RealTimeAudioPipeline:
    """Complete real-time audio processing pipeline."""
    
    def __init__(self, 
                 input_sample_rate: int = 16000,
                 output_sample_rate: int = 24000,
                 chunk_size: int = 1024,
                 buffer_size: int = 10):
        
        # Audio configuration
        self.input_sample_rate = input_sample_rate
        self.output_sample_rate = output_sample_rate
        self.chunk_size = chunk_size
        self.buffer_size = buffer_size
        
        # PyAudio setup
        self.pyaudio = pyaudio.PyAudio()
        self.input_stream = None
        self.output_stream = None
        
        # Audio queues
        self.input_queue = asyncio.Queue(maxsize=buffer_size)
        self.output_queue = asyncio.Queue(maxsize=buffer_size)
        
        # Processing state
        self.is_recording = False
        self.is_playing = False
        self.processing_tasks = []
        
        # Audio metrics
        self.metrics = {
            'input_chunks_processed': 0,
            'output_chunks_played': 0,
            'buffer_overruns': 0,
            'buffer_underruns': 0,
            'processing_latency': collections.deque(maxlen=100)
        }
        
        # Callbacks
        self.audio_input_callback = None
        self.audio_output_callback = None
    
    async def start_recording(self, callback: Optional[Callable] = None):
        """Start audio recording with optional callback."""
        if self.is_recording:
            return
        
        self.audio_input_callback = callback
        
        try:
            # Get default input device
            input_device_info = self.pyaudio.get_default_input_device_info()
            
            # Create input stream
            self.input_stream = self.pyaudio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self.input_sample_rate,
                input=True,
                input_device_index=input_device_info['index'],
                frames_per_buffer=self.chunk_size,
                stream_callback=self._input_stream_callback
            )
            
            self.is_recording = True
            self.input_stream.start_stream()
            
            # Start input processing task
            input_task = asyncio.create_task(self._process_input_audio())
            self.processing_tasks.append(input_task)
            
            logging.info(f"Audio recording started: {self.input_sample_rate}Hz, chunk_size={self.chunk_size}")
            
        except Exception as e:
            logging.error(f"Failed to start recording: {e}")
            raise
    
    async def start_playback(self, callback: Optional[Callable] = None):
        """Start audio playback with optional callback."""
        if self.is_playing:
            return
        
        self.audio_output_callback = callback
        
        try:
            # Create output stream
            self.output_stream = self.pyaudio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self.output_sample_rate,
                output=True,
                frames_per_buffer=self.chunk_size
            )
            
            self.is_playing = True
            
            # Start output processing task
            output_task = asyncio.create_task(self._process_output_audio())
            self.processing_tasks.append(output_task)
            
            logging.info(f"Audio playback started: {self.output_sample_rate}Hz")
            
        except Exception as e:
            logging.error(f"Failed to start playback: {e}")
            raise
    
    def _input_stream_callback(self, in_data, frame_count, time_info, status):
        """PyAudio input stream callback."""
        if status:
            logging.warning(f"Input stream status: {status}")
        
        if self.is_recording:
            try:
                # Non-blocking put to avoid blocking audio thread
                self.input_queue.put_nowait(in_data)
            except asyncio.QueueFull:
                self.metrics['buffer_overruns'] += 1
                # Drop oldest chunk to make room
                try:
                    self.input_queue.get_nowait()
                    self.input_queue.put_nowait(in_data)
                except asyncio.QueueEmpty:
                    pass
        
        return (None, pyaudio.paContinue)
    
    async def _process_input_audio(self):
        """Process input audio chunks."""
        while self.is_recording:
            try:
                # Get audio chunk with timeout
                audio_chunk = await asyncio.wait_for(
                    self.input_queue.get(), 
                    timeout=1.0
                )
                
                processing_start = time.time()
                
                # Call user callback if provided
                if self.audio_input_callback:
                    await self.audio_input_callback(audio_chunk)
                
                # Update metrics
                self.metrics['input_chunks_processed'] += 1
                processing_time = time.time() - processing_start
                self.metrics['processing_latency'].append(processing_time)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logging.error(f"Input processing error: {e}")
    
    async def _process_output_audio(self):
        """Process output audio chunks."""
        while self.is_playing:
            try:
                # Get audio chunk with timeout
                audio_chunk = await asyncio.wait_for(
                    self.output_queue.get(),
                    timeout=1.0
                )
                
                # Play audio chunk
                if self.output_stream and self.output_stream.is_active():
                    self.output_stream.write(audio_chunk)
                    self.metrics['output_chunks_played'] += 1
                
                # Call user callback if provided
                if self.audio_output_callback:
                    await self.audio_output_callback(audio_chunk)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logging.error(f"Output processing error: {e}")
    
    async def queue_output_audio(self, audio_data: bytes):
        """Queue audio data for playback."""
        if not self.is_playing:
            return False
        
        try:
            await self.output_queue.put(audio_data)
            return True
        except asyncio.QueueFull:
            self.metrics['buffer_underruns'] += 1
            return False
    
    async def stop_recording(self):
        """Stop audio recording."""
        if not self.is_recording:
            return
        
        self.is_recording = False
        
        if self.input_stream:
            self.input_stream.stop_stream()
            self.input_stream.close()
            self.input_stream = None
        
        logging.info("Audio recording stopped")
    
    async def stop_playback(self):
        """Stop audio playback."""
        if not self.is_playing:
            return
        
        self.is_playing = False
        
        if self.output_stream:
            self.output_stream.stop_stream()
            self.output_stream.close()
            self.output_stream = None
        
        logging.info("Audio playback stopped")
    
    async def stop_all(self):
        """Stop all audio processing."""
        await self.stop_recording()
        await self.stop_playback()
        
        # Cancel processing tasks
        for task in self.processing_tasks:
            if not task.done():
                task.cancel()
        
        # Wait for tasks to complete
        if self.processing_tasks:
            await asyncio.gather(*self.processing_tasks, return_exceptions=True)
        
        self.processing_tasks.clear()
        
        # Cleanup PyAudio
        if self.pyaudio:
            self.pyaudio.terminate()
    
    def get_audio_metrics(self) -> dict:
        """Get audio processing metrics."""
        avg_latency = (
            sum(self.metrics['processing_latency']) / len(self.metrics['processing_latency'])
            if self.metrics['processing_latency'] else 0
        )
        
        return {
            'input_chunks_processed': self.metrics['input_chunks_processed'],
            'output_chunks_played': self.metrics['output_chunks_played'],
            'buffer_overruns': self.metrics['buffer_overruns'],
            'buffer_underruns': self.metrics['buffer_underruns'],
            'average_processing_latency_ms': avg_latency * 1000,
            'input_queue_size': self.input_queue.qsize(),
            'output_queue_size': self.output_queue.qsize(),
            'is_recording': self.is_recording,
            'is_playing': self.is_playing
        }
```

### **2. Intelligent Rate Limiting**

#### **Advanced Rate Limiting System**
```python
class IntelligentRateLimiter:
    """Advanced rate limiting for natural audio playback."""
    
    def __init__(self, 
                 sample_rate: int = 24000,
                 adaptive_chunking: bool = True,
                 interruption_detection: bool = True):
        
        self.sample_rate = sample_rate
        self.adaptive_chunking = adaptive_chunking
        self.interruption_detection = interruption_detection
        
        # Chunking parameters
        self.base_chunk_duration = 0.05  # 50ms
        self.min_chunk_duration = 0.02   # 20ms
        self.max_chunk_duration = 0.2    # 200ms
        self.current_chunk_duration = self.base_chunk_duration
        
        # Playback state
        self.playback_start_time = None
        self.total_audio_duration = 0.0
        self.chunks_played = 0
        
        # Interruption handling
        self.last_user_activity = 0
        self.interruption_threshold = 0.5  # 500ms
        self.is_interrupted = False
        
        # Performance metrics
        self.rate_limit_metrics = {
            'chunks_processed': 0,
            'interruptions_detected': 0,
            'adaptive_adjustments': 0,
            'timing_accuracy': collections.deque(maxlen=100)
        }
    
    async def process_audio_stream(self, 
                                 audio_stream: asyncio.Queue,
                                 output_callback: Callable[[bytes], None]):
        """Process audio stream with intelligent rate limiting."""
        
        self.playback_start_time = time.time()
        target_playback_time = self.playback_start_time
        
        while True:
            try:
                # Get next audio chunk
                audio_chunk = await asyncio.wait_for(audio_stream.get(), timeout=1.0)
                
                if audio_chunk is None:  # End of stream
                    break
                
                # Check for interruption
                if self.interruption_detection and self._should_interrupt():
                    await self._handle_interruption()
                    break
                
                # Calculate chunk duration and timing
                chunk_duration = self._calculate_chunk_duration(audio_chunk)
                
                # Wait for proper timing
                current_time = time.time()
                wait_time = max(0, target_playback_time - current_time)
                
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
                
                # Play audio chunk
                actual_play_time = time.time()
                await output_callback(audio_chunk)
                
                # Update timing
                target_playback_time = max(actual_play_time, target_playback_time) + chunk_duration
                self.total_audio_duration += chunk_duration
                self.chunks_played += 1
                
                # Record timing accuracy
                timing_error = abs(actual_play_time - (target_playback_time - chunk_duration))
                self.rate_limit_metrics['timing_accuracy'].append(timing_error)
                
                # Adaptive chunking adjustment
                if self.adaptive_chunking:
                    await self._adjust_chunking_parameters(timing_error)
                
                self.rate_limit_metrics['chunks_processed'] += 1
                
            except asyncio.TimeoutError:
                # No more audio chunks
                break
            except Exception as e:
                logging.error(f"Rate limiting error: {e}")
                break
    
    def _calculate_chunk_duration(self, audio_chunk: bytes) -> float:
        """Calculate duration of audio chunk."""
        # 16-bit audio, 1 channel
        sample_count = len(audio_chunk) // 2
        return sample_count / self.sample_rate
    
    def _should_interrupt(self) -> bool:
        """Check if playback should be interrupted."""
        if not self.interruption_detection:
            return False
        
        current_time = time.time()
        time_since_user_activity = current_time - self.last_user_activity
        
        return time_since_user_activity < self.interruption_threshold
    
    async def _handle_interruption(self):
        """Handle playback interruption."""
        self.is_interrupted = True
        self.rate_limit_metrics['interruptions_detected'] += 1
        logging.info("Audio playback interrupted")
    
    async def _adjust_chunking_parameters(self, timing_error: float):
        """Adjust chunking parameters based on timing accuracy."""
        # If timing error is high, adjust chunk duration
        if timing_error > 0.01:  # 10ms error threshold
            if self.current_chunk_duration > self.min_chunk_duration:
                self.current_chunk_duration *= 0.9  # Reduce chunk size
                self.rate_limit_metrics['adaptive_adjustments'] += 1
        elif timing_error < 0.005:  # 5ms - very accurate
            if self.current_chunk_duration < self.max_chunk_duration:
                self.current_chunk_duration *= 1.1  # Increase chunk size
                self.rate_limit_metrics['adaptive_adjustments'] += 1
    
    def signal_user_activity(self):
        """Signal user activity for interruption detection."""
        self.last_user_activity = time.time()
    
    def reset_playback_state(self):
        """Reset playback state for new stream."""
        self.playback_start_time = None
        self.total_audio_duration = 0.0
        self.chunks_played = 0
        self.is_interrupted = False
        self.current_chunk_duration = self.base_chunk_duration
    
    def get_rate_limit_metrics(self) -> dict:
        """Get rate limiting performance metrics."""
        avg_timing_accuracy = (
            sum(self.rate_limit_metrics['timing_accuracy']) / 
            len(self.rate_limit_metrics['timing_accuracy'])
            if self.rate_limit_metrics['timing_accuracy'] else 0
        )
        
        return {
            'chunks_processed': self.rate_limit_metrics['chunks_processed'],
            'interruptions_detected': self.rate_limit_metrics['interruptions_detected'],
            'adaptive_adjustments': self.rate_limit_metrics['adaptive_adjustments'],
            'average_timing_accuracy_ms': avg_timing_accuracy * 1000,
            'current_chunk_duration_ms': self.current_chunk_duration * 1000,
            'total_audio_duration': self.total_audio_duration,
            'chunks_played': self.chunks_played,
            'is_interrupted': self.is_interrupted
        }
```

### **3. Audio Format Conversion & Processing**

#### **Advanced Audio Converter**
```python
import librosa
import soundfile as sf
import numpy as np
from scipy import signal

class AdvancedAudioConverter:
    """Advanced audio format conversion and processing."""
    
    def __init__(self):
        self.conversion_cache = {}
        self.processing_metrics = {
            'conversions_performed': 0,
            'cache_hits': 0,
            'processing_time': collections.deque(maxlen=100)
        }
    
    async def convert_to_gemini_format(self, 
                                     audio_data: bytes, 
                                     source_sample_rate: int,
                                     source_format: str = "int16") -> bytes:
        """Convert audio to Gemini-compatible format (PCM 16kHz)."""
        
        processing_start = time.time()
        
        try:
            # Create cache key
            cache_key = f"{len(audio_data)}_{source_sample_rate}_{source_format}"
            
            if cache_key in self.conversion_cache:
                self.processing_metrics['cache_hits'] += 1
                return self.conversion_cache[cache_key]
            
            # Convert bytes to numpy array
            if source_format == "int16":
                audio_array = np.frombuffer(audio_data, dtype=np.int16)
            elif source_format == "float32":
                audio_array = np.frombuffer(audio_data, dtype=np.float32)
            else:
                raise ValueError(f"Unsupported source format: {source_format}")
            
            # Convert to float for processing
            if source_format == "int16":
                audio_float = audio_array.astype(np.float32) / 32768.0
            else:
                audio_float = audio_array
            
            # Resample to 16kHz if needed
            if source_sample_rate != 16000:
                audio_resampled = librosa.resample(
                    audio_float, 
                    orig_sr=source_sample_rate, 
                    target_sr=16000
                )
            else:
                audio_resampled = audio_float
            
            # Convert back to int16
            audio_int16 = (audio_resampled * 32767).astype(np.int16)
            
            # Convert to bytes
            result_bytes = audio_int16.tobytes()
            
            # Cache result
            self.conversion_cache[cache_key] = result_bytes
            
            # Update metrics
            self.processing_metrics['conversions_performed'] += 1
            processing_time = time.time() - processing_start
            self.processing_metrics['processing_time'].append(processing_time)
            
            return result_bytes
            
        except Exception as e:
            logging.error(f"Audio conversion error: {e}")
            raise
    
    async def enhance_audio_quality(self, 
                                  audio_data: bytes, 
                                  sample_rate: int = 16000) -> bytes:
        """Enhance audio quality with noise reduction and normalization."""
        
        try:
            # Convert to numpy array
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            audio_float = audio_array.astype(np.float32) / 32768.0
            
            # Apply noise reduction (simple high-pass filter)
            audio_filtered = self._apply_noise_reduction(audio_float, sample_rate)
            
            # Normalize audio
            audio_normalized = self._normalize_audio(audio_filtered)
            
            # Convert back to int16
            audio_enhanced = (audio_normalized * 32767).astype(np.int16)
            
            return audio_enhanced.tobytes()
            
        except Exception as e:
            logging.error(f"Audio enhancement error: {e}")
            return audio_data  # Return original on error
    
    def _apply_noise_reduction(self, audio: np.ndarray, sample_rate: int) -> np.ndarray:
        """Apply simple noise reduction using high-pass filter."""
        # Design high-pass filter to remove low-frequency noise
        nyquist = sample_rate / 2
        cutoff = 80  # Hz
        normalized_cutoff = cutoff / nyquist
        
        b, a = signal.butter(4, normalized_cutoff, btype='high')
        filtered_audio = signal.filtfilt(b, a, audio)
        
        return filtered_audio
    
    def _normalize_audio(self, audio: np.ndarray) -> np.ndarray:
        """Normalize audio to prevent clipping."""
        max_amplitude = np.max(np.abs(audio))
        
        if max_amplitude > 0:
            # Normalize to 90% of maximum to prevent clipping
            normalized_audio = audio * (0.9 / max_amplitude)
        else:
            normalized_audio = audio
        
        return normalized_audio
    
    async def detect_silence(self, 
                           audio_data: bytes, 
                           sample_rate: int = 16000,
                           silence_threshold: float = 0.01) -> dict:
        """Detect silence periods in audio."""
        
        try:
            # Convert to numpy array
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            audio_float = np.abs(audio_array.astype(np.float32) / 32768.0)
            
            # Calculate RMS energy in windows
            window_size = int(0.1 * sample_rate)  # 100ms windows
            num_windows = len(audio_float) // window_size
            
            silence_periods = []
            current_silence_start = None
            
            for i in range(num_windows):
                start_idx = i * window_size
                end_idx = start_idx + window_size
                window_rms = np.sqrt(np.mean(audio_float[start_idx:end_idx] ** 2))
                
                if window_rms < silence_threshold:
                    if current_silence_start is None:
                        current_silence_start = start_idx / sample_rate
                else:
                    if current_silence_start is not None:
                        silence_end = start_idx / sample_rate
                        silence_periods.append({
                            'start': current_silence_start,
                            'end': silence_end,
                            'duration': silence_end - current_silence_start
                        })
                        current_silence_start = None
            
            # Handle silence at the end
            if current_silence_start is not None:
                silence_end = len(audio_float) / sample_rate
                silence_periods.append({
                    'start': current_silence_start,
                    'end': silence_end,
                    'duration': silence_end - current_silence_start
                })
            
            total_silence_duration = sum(period['duration'] for period in silence_periods)
            total_duration = len(audio_float) / sample_rate
            silence_ratio = total_silence_duration / total_duration if total_duration > 0 else 0
            
            return {
                'silence_periods': silence_periods,
                'total_silence_duration': total_silence_duration,
                'total_duration': total_duration,
                'silence_ratio': silence_ratio
            }
            
        except Exception as e:
            logging.error(f"Silence detection error: {e}")
            return {'silence_periods': [], 'total_silence_duration': 0, 'total_duration': 0, 'silence_ratio': 0}
```

## 🎛️ **AUDIO PIPELINE INTEGRATION**

### **Complete Audio System Integration**
```python
class GeminiAudioSystem:
    """Complete audio system for Gemini Live API integration."""
    
    def __init__(self, api_key: str, model: str = "gemini-live-2.5-flash-preview"):
        self.api_key = api_key
        self.model = model
        
        # Components
        self.audio_pipeline = RealTimeAudioPipeline()
        self.rate_limiter = IntelligentRateLimiter()
        self.audio_converter = AdvancedAudioConverter()
        
        # Gemini client
        self.client = genai.Client(api_key=api_key)
        self.session = None
        
        # Audio processing state
        self.is_active = False
        self.processing_tasks = []
        
        # System metrics
        self.system_metrics = {
            'session_duration': 0,
            'audio_chunks_sent': 0,
            'audio_chunks_received': 0,
            'total_latency': collections.deque(maxlen=100)
        }
    
    async def start_audio_session(self, config: dict):
        """Start complete audio session with Gemini."""
        
        try:
            # Connect to Gemini Live API
            self.session = await self.client.aio.live.connect(
                model=self.model,
                config=config
            )
            
            # Start audio pipeline
            await self.audio_pipeline.start_recording(self._handle_input_audio)
            await self.audio_pipeline.start_playback()
            
            # Start processing tasks
            self.is_active = True
            
            input_task = asyncio.create_task(self._process_gemini_responses())
            self.processing_tasks.append(input_task)
            
            session_start = time.time()
            
            logging.info("Gemini audio session started")
            
            # Keep session alive
            while self.is_active:
                await asyncio.sleep(1)
                self.system_metrics['session_duration'] = time.time() - session_start
            
        except Exception as e:
            logging.error(f"Audio session error: {e}")
            await self.stop_audio_session()
            raise
    
    async def _handle_input_audio(self, audio_chunk: bytes):
        """Handle input audio from microphone."""
        if not self.session:
            return
        
        try:
            # Convert audio to Gemini format
            converted_audio = await self.audio_converter.convert_to_gemini_format(
                audio_chunk, 
                self.audio_pipeline.input_sample_rate
            )
            
            # Send to Gemini
            await self.session.send_realtime_input(
                audio=types.Blob(
                    data=converted_audio,
                    mime_type="audio/pcm;rate=16000"
                )
            )
            
            self.system_metrics['audio_chunks_sent'] += 1
            
        except Exception as e:
            logging.error(f"Input audio handling error: {e}")
    
    async def _process_gemini_responses(self):
        """Process responses from Gemini."""
        if not self.session:
            return
        
        try:
            async for response in self.session.receive():
                response_start = time.time()
                
                # Handle audio output
                if response.data:
                    await self.audio_pipeline.queue_output_audio(response.data)
                    self.system_metrics['audio_chunks_received'] += 1
                
                # Handle interruptions
                if hasattr(response, 'server_content') and response.server_content.interrupted:
                    self.rate_limiter.signal_user_activity()
                    logging.info("Gemini response interrupted")
                
                # Handle text output
                if response.text:
                    logging.info(f"Gemini text: {response.text}")
                
                # Record latency
                response_time = time.time() - response_start
                self.system_metrics['total_latency'].append(response_time)
                
        except Exception as e:
            logging.error(f"Gemini response processing error: {e}")
    
    async def stop_audio_session(self):
        """Stop audio session and cleanup."""
        self.is_active = False
        
        # Stop audio pipeline
        await self.audio_pipeline.stop_all()
        
        # Cancel processing tasks
        for task in self.processing_tasks:
            if not task.done():
                task.cancel()
        
        if self.processing_tasks:
            await asyncio.gather(*self.processing_tasks, return_exceptions=True)
        
        # Close Gemini session
        if self.session:
            await self.session.close()
            self.session = None
        
        logging.info("Gemini audio session stopped")
    
    def get_system_metrics(self) -> dict:
        """Get comprehensive system metrics."""
        audio_metrics = self.audio_pipeline.get_audio_metrics()
        rate_limit_metrics = self.rate_limiter.get_rate_limit_metrics()
        
        avg_latency = (
            sum(self.system_metrics['total_latency']) / 
            len(self.system_metrics['total_latency'])
            if self.system_metrics['total_latency'] else 0
        )
        
        return {
            'session': {
                'duration': self.system_metrics['session_duration'],
                'chunks_sent': self.system_metrics['audio_chunks_sent'],
                'chunks_received': self.system_metrics['audio_chunks_received'],
                'average_latency_ms': avg_latency * 1000
            },
            'audio_pipeline': audio_metrics,
            'rate_limiting': rate_limit_metrics,
            'overall_health': self._calculate_system_health()
        }
    
    def _calculate_system_health(self) -> str:
        """Calculate overall system health."""
        audio_metrics = self.audio_pipeline.get_audio_metrics()
        
        # Check for issues
        issues = []
        
        if audio_metrics['buffer_overruns'] > 10:
            issues.append("High buffer overruns")
        
        if audio_metrics['buffer_underruns'] > 10:
            issues.append("High buffer underruns")
        
        if audio_metrics['average_processing_latency_ms'] > 100:
            issues.append("High processing latency")
        
        if not issues:
            return "healthy"
        elif len(issues) <= 2:
            return "degraded"
        else:
            return "unhealthy"
```

This comprehensive audio processing pipeline guide provides all the patterns needed for sophisticated real-time audio applications with proper rate limiting, format conversion, and quality enhancement.
