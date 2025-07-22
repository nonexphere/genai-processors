# GenAI Processors Real-time & Live Processing

## Real-time Processing Architecture

### Core Real-time Concepts
The GenAI Processors library provides sophisticated real-time processing capabilities through several key components:

1. **LiveModelProcessor**: Converts turn-based models into real-time streaming processors
2. **LiveProcessor**: Direct integration with Gemini Live API for server-side streaming
3. **Rolling Prompts**: Intelligent prompt management for continuous conversations
4. **Event-driven Processing**: React to real-time events and triggers
5. **Audio Rate Limiting**: Natural playback speed for streaming audio

### LiveModelProcessor - Client-side Real-time
```python
from genai_processors.core import realtime

class CustomRealTimeAgent(processor.Processor):
    """Custom real-time agent with advanced features."""
    
    def __init__(self, base_model: processor.Processor):
        # Create turn-based processor chain
        turn_processor = (
            input_filter +
            base_model +
            response_enhancer +
            output_formatter
        )
        
        # Wrap in live processor with custom settings
        self.live_processor = realtime.LiveModelProcessor(
            turn_processor=turn_processor,
            duration_prompt_sec=300,  # 5 minutes rolling window
            trigger_model_mode=realtime.AudioTriggerMode.FINAL_TRANSCRIPTION
        )
    
    async def call(self, content: AsyncIterable[content_api.ProcessorPart]) -> AsyncIterable[content_api.ProcessorPartTypes]:
        async for result in self.live_processor(content):
            # Add real-time metadata
            result.metadata['realtime_processed'] = True
            result.metadata['timestamp'] = time.time()
            yield result
```

### Rolling Prompt Management
```python
class AdvancedRollingPrompt:
    """Enhanced rolling prompt with intelligent context management."""
    
    def __init__(self, 
                 duration_sec: float = 600,
                 max_parts: int = 1000,
                 compression_enabled: bool = True):
        self.duration_sec = duration_sec
        self.max_parts = max_parts
        self.compression_enabled = compression_enabled
        
        # Core storage
        self.conversation_history = collections.deque(maxlen=max_parts)
        self.part_timestamps = collections.deque(maxlen=max_parts)
        self.stashed_parts = []
        
        # Context management
        self.context_summary = ""
        self.important_parts = []  # High-priority parts to retain
        
        # Current prompt queue
        self.pending_queue = asyncio.Queue()
    
    def add_part(self, part: content_api.ProcessorPart, priority: str = "normal"):
        """Add part with priority classification."""
        current_time = time.perf_counter()
        
        # Classify part importance
        if self._is_important_part(part) or priority == "high":
            self.important_parts.append((part, current_time))
        
        # Add to main history
        self.conversation_history.append(part)
        self.part_timestamps.append(current_time)
        
        # Add to pending queue
        self.pending_queue.put_nowait(part)
        
        # Trigger compression if needed
        if self.compression_enabled and len(self.conversation_history) > self.max_parts * 0.8:
            self._compress_old_context()
    
    def _is_important_part(self, part: content_api.ProcessorPart) -> bool:
        """Determine if a part should be retained longer."""
        # Keep system messages
        if part.role.lower() == 'system':
            return True
        
        # Keep parts with specific metadata
        if part.metadata.get('important', False):
            return True
        
        # Keep function calls and responses
        if part.function_call or part.function_response:
            return True
        
        # Keep parts with high engagement indicators
        if content_api.is_text(part.mimetype):
            text = part.text.lower()
            important_keywords = ['error', 'warning', 'critical', 'important', 'remember']
            if any(keyword in text for keyword in important_keywords):
                return True
        
        return False
    
    def _compress_old_context(self):
        """Compress older conversation parts while preserving important information."""
        if not self.conversation_history:
            return
        
        # Calculate cutoff time
        current_time = time.perf_counter()
        cutoff_time = current_time - (self.duration_sec * 0.5)  # Compress older half
        
        # Separate parts to compress vs keep
        parts_to_compress = []
        parts_to_keep = []
        
        for part, timestamp in zip(self.conversation_history, self.part_timestamps):
            if timestamp < cutoff_time and not self._is_important_part(part):
                parts_to_compress.append(part)
            else:
                parts_to_keep.append((part, timestamp))
        
        if parts_to_compress:
            # Create compressed summary
            summary = self._create_intelligent_summary(parts_to_compress)
            summary_part = content_api.ProcessorPart(
                summary,
                role='system',
                metadata={
                    'compressed': True,
                    'original_count': len(parts_to_compress),
                    'compression_time': current_time
                }
            )
            
            # Update history with compressed version
            self.conversation_history.clear()
            self.part_timestamps.clear()
            
            # Add compressed summary first
            self.conversation_history.append(summary_part)
            self.part_timestamps.append(current_time)
            
            # Add remaining parts
            for part, timestamp in parts_to_keep:
                self.conversation_history.append(part)
                self.part_timestamps.append(timestamp)
    
    def _create_intelligent_summary(self, parts: list[content_api.ProcessorPart]) -> str:
        """Create an intelligent summary of conversation parts."""
        if not parts:
            return "[Empty conversation segment]"
        
        # Separate by content type
        text_parts = []
        other_parts = []
        
        for part in parts:
            if content_api.is_text(part.mimetype) and part.text.strip():
                text_parts.append(f"{part.role}: {part.text}")
            else:
                other_parts.append(f"{part.role}: [{part.mimetype}]")
        
        # Create summary
        summary_lines = []
        
        if text_parts:
            # Simple extractive summarization
            if len(text_parts) <= 3:
                summary_lines.extend(text_parts)
            else:
                # Take first, last, and middle parts
                summary_lines.append(text_parts[0])
                if len(text_parts) > 2:
                    summary_lines.append(f"[... {len(text_parts) - 2} messages ...]")
                summary_lines.append(text_parts[-1])
        
        if other_parts:
            summary_lines.append(f"[{len(other_parts)} non-text parts]")
        
        return "\n".join(summary_lines)
```

## Audio Processing and Rate Limiting

### Advanced Audio Rate Limiting
```python
class IntelligentAudioRateLimiter(processor.Processor):
    """Advanced audio rate limiter with adaptive behavior."""
    
    def __init__(self, 
                 sample_rate: int = 24000,
                 adaptive_chunking: bool = True,
                 interruption_detection: bool = True):
        self.sample_rate = sample_rate
        self.adaptive_chunking = adaptive_chunking
        self.interruption_detection = interruption_detection
        
        # Adaptive parameters
        self.current_chunk_size = 0.05  # Start with 50ms chunks
        self.min_chunk_size = 0.02      # 20ms minimum
        self.max_chunk_size = 0.2       # 200ms maximum
        
        # Interruption detection
        self.last_user_activity = 0
        self.interruption_threshold = 0.5  # 500ms
        
        # Performance tracking
        self.playback_metrics = {
            'chunks_played': 0,
            'interruptions': 0,
            'buffer_underruns': 0
        }
    
    async def call(self, content: AsyncIterable[content_api.ProcessorPart]) -> AsyncIterable[content_api.ProcessorPartTypes]:
        audio_queue = asyncio.Queue(maxsize=1000)
        output_queue = asyncio.Queue(maxsize=10)
        
        # Start audio processing pipeline
        consume_task = context.create_task(self._consume_content(content, audio_queue))
        process_task = context.create_task(self._process_audio_stream(audio_queue, output_queue))
        
        try:
            # Yield processed audio with timing
            while True:
                part = await output_queue.get()
                if part is None:
                    break
                yield part
        finally:
            consume_task.cancel()
            process_task.cancel()
    
    async def _consume_content(self, content: AsyncIterable[content_api.ProcessorPart], audio_queue: asyncio.Queue):
        """Consume and classify incoming content."""
        async for part in content:
            if content_api.is_audio(part.mimetype):
                # Detect if this is user audio (potential interruption)
                if part.role.lower() == 'user':
                    self.last_user_activity = time.time()
                    await audio_queue.put(('interruption_check', part))
                else:
                    await audio_queue.put(('audio', part))
            else:
                await audio_queue.put(('passthrough', part))
        
        await audio_queue.put(('end', None))
    
    async def _process_audio_stream(self, audio_queue: asyncio.Queue, output_queue: asyncio.Queue):
        """Process audio with intelligent rate limiting."""
        playback_start_time = time.time() - 3600  # Start in the past
        
        while True:
            queue_item = await audio_queue.get()
            item_type, part = queue_item
            
            if item_type == 'end':
                break
            elif item_type == 'passthrough':
                await output_queue.put(part)
            elif item_type == 'interruption_check':
                # Handle potential interruption
                if self._should_interrupt():
                    await self._flush_audio_buffer(output_queue)
                    self.playback_metrics['interruptions'] += 1
                await output_queue.put(part)
            elif item_type == 'audio':
                # Process audio with adaptive chunking
                async for audio_chunk in self._split_audio_adaptively(part):
                    # Calculate when this chunk should be played
                    chunk_duration = self._calculate_audio_duration(audio_chunk)
                    
                    # Wait for proper timing
                    current_time = time.time()
                    sleep_time = max(0, playback_start_time - current_time)
                    
                    if sleep_time > 0:
                        await asyncio.sleep(sleep_time)
                    
                    # Update playback timing
                    playback_start_time = max(current_time, playback_start_time) + chunk_duration
                    
                    # Yield the chunk
                    await output_queue.put(audio_chunk)
                    self.playback_metrics['chunks_played'] += 1
        
        await output_queue.put(None)
    
    def _should_interrupt(self) -> bool:
        """Determine if audio playback should be interrupted."""
        if not self.interruption_detection:
            return False
        
        time_since_user_activity = time.time() - self.last_user_activity
        return time_since_user_activity < self.interruption_threshold
    
    async def _split_audio_adaptively(self, audio_part: content_api.ProcessorPart) -> AsyncIterable[content_api.ProcessorPart]:
        """Split audio into chunks with adaptive sizing."""
        if not audio_part.bytes:
            yield audio_part
            return
        
        audio_data = audio_part.bytes
        total_duration = len(audio_data) / (2 * self.sample_rate)  # 16-bit audio
        
        # Adapt chunk size based on total duration
        if self.adaptive_chunking:
            if total_duration < 1.0:  # Short audio - smaller chunks for responsiveness
                chunk_duration = max(self.min_chunk_size, total_duration / 10)
            elif total_duration > 10.0:  # Long audio - larger chunks for efficiency
                chunk_duration = min(self.max_chunk_size, total_duration / 20)
            else:
                chunk_duration = self.current_chunk_size
        else:
            chunk_duration = self.current_chunk_size
        
        # Split audio into chunks
        chunk_size_bytes = int(chunk_duration * self.sample_rate * 2)  # 16-bit
        
        for i in range(0, len(audio_data), chunk_size_bytes):
            chunk_data = audio_data[i:i + chunk_size_bytes]
            if chunk_data:
                chunk_part = content_api.ProcessorPart(
                    chunk_data,
                    mimetype=audio_part.mimetype,
                    role=audio_part.role,
                    metadata={
                        **audio_part.metadata,
                        'chunk_index': i // chunk_size_bytes,
                        'chunk_duration': len(chunk_data) / (2 * self.sample_rate)
                    }
                )
                yield chunk_part
```

## Event-Driven Real-time Processing

### Real-time Event Detection
```python
class RealTimeEventProcessor(processor.Processor):
    """Process events in real-time with minimal latency."""
    
    def __init__(self, 
                 event_detectors: dict[str, processor.Processor],
                 debounce_time: float = 0.1,
                 max_concurrent_detections: int = 5):
        self.event_detectors = event_detectors
        self.debounce_time = debounce_time
        self.max_concurrent_detections = max_concurrent_detections
        
        # Event state tracking
        self.last_events = {}
        self.event_counts = collections.defaultdict(int)
        self.detection_semaphore = asyncio.Semaphore(max_concurrent_detections)
        
        # Performance metrics
        self.metrics = {
            'events_detected': 0,
            'events_debounced': 0,
            'detection_latency': collections.deque(maxlen=100)
        }
    
    async def call(self, content: AsyncIterable[content_api.ProcessorPart]) -> AsyncIterable[content_api.ProcessorPartTypes]:
        event_queue = asyncio.Queue()
        
        # Start event detection pipeline
        detection_task = context.create_task(
            self._detect_events_continuously(content, event_queue)
        )
        
        try:
            # Yield events as they're detected
            while True:
                event = await event_queue.get()
                if event is None:
                    break
                yield event
        finally:
            detection_task.cancel()
    
    async def _detect_events_continuously(self, 
                                        content: AsyncIterable[content_api.ProcessorPart], 
                                        event_queue: asyncio.Queue):
        """Continuously detect events from incoming content."""
        async for part in content:
            # Always pass through original content
            await event_queue.put(part)
            
            # Trigger event detection for relevant content types
            if self._should_detect_events(part):
                # Use semaphore to limit concurrent detections
                async with self.detection_semaphore:
                    detection_start = time.time()
                    
                    # Run all applicable event detectors
                    detection_tasks = []
                    for detector_name, detector in self.event_detectors.items():
                        if self._detector_matches_content(detector_name, part):
                            task = context.create_task(
                                self._run_single_detector(detector, part, detector_name)
                            )
                            detection_tasks.append(task)
                    
                    # Wait for all detections to complete
                    if detection_tasks:
                        results = await asyncio.gather(*detection_tasks, return_exceptions=True)
                        
                        # Process detection results
                        for result in results:
                            if isinstance(result, Exception):
                                await event_queue.put(processor.debug(f"Detection error: {result}"))
                            elif result:
                                # Apply debouncing
                                if self._should_emit_event(result):
                                    await event_queue.put(result)
                                    self.metrics['events_detected'] += 1
                                else:
                                    self.metrics['events_debounced'] += 1
                        
                        # Record detection latency
                        detection_time = time.time() - detection_start
                        self.metrics['detection_latency'].append(detection_time)
        
        await event_queue.put(None)
    
    def _should_detect_events(self, part: content_api.ProcessorPart) -> bool:
        """Determine if event detection should be triggered for this part."""
        # Skip if part is too old (for real-time processing)
        part_age = time.time() - part.metadata.get('timestamp', time.time())
        if part_age > 5.0:  # Skip parts older than 5 seconds
            return False
        
        # Detect events for images, audio, and substantial text
        if content_api.is_image(part.mimetype):
            return True
        elif content_api.is_audio(part.mimetype):
            return True
        elif content_api.is_text(part.mimetype) and len(part.text) > 50:
            return True
        
        return False
    
    async def _run_single_detector(self, 
                                 detector: processor.Processor, 
                                 part: content_api.ProcessorPart,
                                 detector_name: str) -> content_api.ProcessorPart | None:
        """Run a single event detector on a part."""
        try:
            results = []
            async for result in detector(streams.stream_content([part])):
                results.append(result)
            
            # Return the most significant result
            if results:
                best_result = max(results, key=lambda r: r.metadata.get('confidence', 0))
                best_result.metadata['detector'] = detector_name
                best_result.metadata['detection_time'] = time.time()
                return best_result
        
        except Exception as e:
            return processor.debug(f"Detector {detector_name} failed: {e}")
        
        return None
    
    def _should_emit_event(self, event: content_api.ProcessorPart) -> bool:
        """Apply debouncing logic to prevent event spam."""
        event_type = event.metadata.get('event_type', 'unknown')
        current_time = time.time()
        
        # Check debounce timing
        last_time = self.last_events.get(event_type, 0)
        if current_time - last_time < self.debounce_time:
            return False
        
        # Update last event time
        self.last_events[event_type] = current_time
        self.event_counts[event_type] += 1
        
        return True
```

## Live Streaming Integration

### Gemini Live API Integration
```python
class EnhancedLiveProcessor(processor.Processor):
    """Enhanced Live API processor with advanced features."""
    
    def __init__(self, 
                 api_key: str,
                 model_name: str,
                 realtime_config: dict = None,
                 stream_management: bool = True):
        self.base_processor = live_model.LiveProcessor(
            api_key=api_key,
            model_name=model_name,
            realtime_config=realtime_config
        )
        self.stream_management = stream_management
        
        # Stream management
        self.active_streams = {}
        self.stream_metrics = collections.defaultdict(dict)
        
    async def call(self, content: AsyncIterable[content_api.ProcessorPart]) -> AsyncIterable[content_api.ProcessorPartTypes]:
        if self.stream_management:
            # Enhanced stream with management features
            managed_stream = self._add_stream_management(content)
            async for result in self.base_processor(managed_stream):
                yield self._enhance_result(result)
        else:
            # Direct passthrough
            async for result in self.base_processor(content):
                yield result
    
    async def _add_stream_management(self, content: AsyncIterable[content_api.ProcessorPart]) -> AsyncIterable[content_api.ProcessorPart]:
        """Add stream management capabilities."""
        stream_id = f"stream_{time.time()}"
        self.active_streams[stream_id] = {
            'start_time': time.time(),
            'part_count': 0,
            'last_activity': time.time()
        }
        
        try:
            async for part in content:
                # Update stream metrics
                self.active_streams[stream_id]['part_count'] += 1
                self.active_streams[stream_id]['last_activity'] = time.time()
                
                # Add stream metadata
                part.metadata['stream_id'] = stream_id
                part.metadata['stream_part_index'] = self.active_streams[stream_id]['part_count']
                
                yield part
        finally:
            # Clean up stream tracking
            if stream_id in self.active_streams:
                stream_info = self.active_streams.pop(stream_id)
                self.stream_metrics[stream_id] = {
                    'duration': time.time() - stream_info['start_time'],
                    'total_parts': stream_info['part_count']
                }
    
    def _enhance_result(self, result: content_api.ProcessorPart) -> content_api.ProcessorPart:
        """Enhance results with additional metadata."""
        result.metadata['enhanced_live_processing'] = True
        result.metadata['processing_timestamp'] = time.time()
        
        # Add quality metrics if available
        if 'confidence' in result.metadata:
            confidence = result.metadata['confidence']
            result.metadata['quality_tier'] = (
                'high' if confidence > 0.8 else
                'medium' if confidence > 0.5 else
                'low'
            )
        
        return result
```

## Real-time Performance Monitoring

### Live Performance Metrics
```python
class RealTimeMetrics:
    """Comprehensive real-time performance monitoring."""
    
    def __init__(self, window_size: int = 1000):
        self.window_size = window_size
        
        # Timing metrics
        self.processing_times = collections.deque(maxlen=window_size)
        self.latency_measurements = collections.deque(maxlen=window_size)
        
        # Throughput metrics
        self.parts_processed = 0
        self.start_time = time.time()
        self.throughput_history = collections.deque(maxlen=100)
        
        # Quality metrics
        self.quality_scores = collections.deque(maxlen=window_size)
        self.error_count = 0
        
        # Real-time specific metrics
        self.interruption_count = 0
        self.buffer_underruns = 0
        self.stream_continuity = 1.0
    
    def record_processing(self, 
                         processing_time: float,
                         latency: float = None,
                         quality_score: float = None):
        """Record processing metrics."""
        self.processing_times.append(processing_time)
        self.parts_processed += 1
        
        if latency is not None:
            self.latency_measurements.append(latency)
        
        if quality_score is not None:
            self.quality_scores.append(quality_score)
        
        # Update throughput every 100 parts
        if self.parts_processed % 100 == 0:
            current_time = time.time()
            elapsed = current_time - self.start_time
            throughput = self.parts_processed / elapsed
            self.throughput_history.append(throughput)
    
    def record_interruption(self):
        """Record an interruption event."""
        self.interruption_count += 1
        # Interruptions affect stream continuity
        self.stream_continuity *= 0.99
    
    def record_error(self):
        """Record an error event."""
        self.error_count += 1
    
    def get_real_time_report(self) -> dict:
        """Generate comprehensive real-time performance report."""
        current_time = time.time()
        elapsed = current_time - self.start_time
        
        # Calculate averages
        avg_processing_time = (
            sum(self.processing_times) / len(self.processing_times)
            if self.processing_times else 0
        )
        
        avg_latency = (
            sum(self.latency_measurements) / len(self.latency_measurements)
            if self.latency_measurements else 0
        )
        
        avg_quality = (
            sum(self.quality_scores) / len(self.quality_scores)
            if self.quality_scores else 0
        )
        
        current_throughput = self.parts_processed / elapsed if elapsed > 0 else 0
        
        # Real-time specific metrics
        interruption_rate = self.interruption_count / max(1, self.parts_processed)
        error_rate = self.error_count / max(1, self.parts_processed)
        
        return {
            'performance': {
                'avg_processing_time_ms': avg_processing_time * 1000,
                'avg_latency_ms': avg_latency * 1000,
                'current_throughput_pps': current_throughput,  # parts per second
                'total_parts_processed': self.parts_processed
            },
            'quality': {
                'avg_quality_score': avg_quality,
                'stream_continuity': self.stream_continuity,
                'error_rate': error_rate
            },
            'real_time': {
                'interruption_rate': interruption_rate,
                'buffer_underruns': self.buffer_underruns,
                'is_real_time_capable': avg_latency < 0.1 and current_throughput > 10
            },
            'recommendations': self._generate_recommendations(
                avg_processing_time, avg_latency, current_throughput, error_rate
            )
        }
    
    def _generate_recommendations(self, 
                                avg_processing_time: float,
                                avg_latency: float, 
                                throughput: float,
                                error_rate: float) -> list[str]:
        """Generate performance optimization recommendations."""
        recommendations = []
        
        if avg_latency > 0.2:
            recommendations.append("High latency detected - consider optimizing processing pipeline")
        
        if throughput < 5:
            recommendations.append("Low throughput - consider increasing concurrency or optimizing algorithms")
        
        if error_rate > 0.05:
            recommendations.append("High error rate - review error handling and input validation")
        
        if self.interruption_count > self.parts_processed * 0.1:
            recommendations.append("Frequent interruptions - consider improving interruption handling")
        
        if avg_processing_time > 0.1:
            recommendations.append("Slow processing - consider caching or algorithm optimization")
        
        return recommendations
```

## Best Practices for Real-time Processing

### Design Principles
1. **Minimize Latency**: Keep processing pipelines as short as possible
2. **Handle Interruptions**: Design for graceful interruption and resumption
3. **Manage Memory**: Use rolling windows and compression for long-running streams
4. **Monitor Performance**: Track latency, throughput, and quality metrics
5. **Adaptive Behavior**: Adjust processing based on real-time conditions

### Implementation Guidelines
1. **Use appropriate queue sizes**: Balance responsiveness vs stability
2. **Implement proper debouncing**: Prevent event spam in real-time scenarios
3. **Cache strategically**: Cache expensive operations but with short TTLs
4. **Handle backpressure**: Implement flow control for high-volume streams
5. **Test under load**: Validate performance under realistic conditions

### Common Patterns
1. **Event-driven architecture**: React to real-time events and triggers
2. **Rolling context windows**: Maintain relevant context without memory bloat
3. **Adaptive processing**: Adjust behavior based on stream characteristics
4. **Graceful degradation**: Maintain functionality under resource constraints
5. **Stream multiplexing**: Handle multiple concurrent real-time streams