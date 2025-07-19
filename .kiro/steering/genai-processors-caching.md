# GenAI Processors Caching & Performance Optimization

## Caching System Architecture

### InMemoryCache Implementation
The GenAI Processors library provides a sophisticated caching system specifically designed for `ProcessorContent` objects:

```python
from genai_processors import cache

# Basic cache with TTL and size limits
processor_cache = cache.InMemoryCache(
    ttl_hours=12,        # Time-to-live: 12 hours
    max_items=1000,      # Maximum cached items
    hash_fn=None         # Uses default deterministic hashing
)

# Cache with custom key prefix for processor isolation
prefixed_cache = processor_cache.with_key_prefix("MyProcessor:")
```

### Cache Key Generation
- **Deterministic Hashing**: Uses `xxhash.xxh128()` for fast, consistent hash generation
- **JSON Serialization**: Parts are serialized to JSON with sorted keys for consistency
- **Order Sensitivity**: Hash respects the order of parts in ProcessorContent
- **Metadata Inclusion**: All part metadata is included in hash calculation

```python
def custom_hash_function(content: ProcessorContentTypes) -> str | None:
    """Custom hash function that excludes timestamps from caching."""
    processed_content = ProcessorContent(content)
    
    # Filter out parts with timestamps for consistent caching
    filtered_parts = []
    for part in processed_content.all_parts:
        if 'timestamp' not in part.metadata:
            filtered_parts.append(part)
    
    if not filtered_parts:
        return None  # Not cacheable
    
    return cache.default_processor_content_hash(filtered_parts)
```

### Cache Integration Patterns

#### Processor-Level Caching
```python
class CachedProcessor(processor.Processor):
    """Processor with built-in caching capabilities."""
    
    def __init__(self, cache_instance: cache.CacheBase = None):
        self.cache = cache_instance or cache.InMemoryCache(
            ttl_hours=6,
            max_items=500
        ).with_key_prefix(f"{self.__class__.__name__}:")
    
    async def call(self, content: AsyncIterable[content_api.ProcessorPart]) -> AsyncIterable[content_api.ProcessorPartTypes]:
        # Collect input for cache lookup
        input_parts = []
        async for part in content:
            input_parts.append(part)
        
        # Check cache first
        cache_result = await self.cache.lookup(input_parts)
        if cache_result is not cache.CacheMiss:
            for cached_part in cache_result.all_parts:
                cached_part.metadata['from_cache'] = True
                yield cached_part
            return
        
        # Process and cache results
        results = []
        async for result in self._process_uncached(input_parts):
            results.append(result)
            yield result
        
        # Store in cache
        await self.cache.put(input_parts, results)
    
    async def _process_uncached(self, parts: list[content_api.ProcessorPart]) -> AsyncIterable[content_api.ProcessorPart]:
        """Override this method with actual processing logic."""
        for part in parts:
            yield part
```

#### Selective Caching with Conditions
```python
class ConditionalCacheProcessor(processor.Processor):
    """Cache only specific types of content or under certain conditions."""
    
    def __init__(self):
        self.text_cache = cache.InMemoryCache(ttl_hours=24, max_items=1000)
        self.image_cache = cache.InMemoryCache(ttl_hours=1, max_items=100)  # Shorter TTL for images
    
    async def call(self, content: AsyncIterable[content_api.ProcessorPart]) -> AsyncIterable[content_api.ProcessorPartTypes]:
        async for part in content:
            selected_cache = None
            
            if content_api.is_text(part.mimetype) and len(part.text) > 100:
                # Cache only substantial text content
                selected_cache = self.text_cache
            elif content_api.is_image(part.mimetype):
                # Cache image processing results
                selected_cache = self.image_cache
            
            if selected_cache:
                cached_result = await selected_cache.lookup([part])
                if cached_result is not cache.CacheMiss:
                    for cached_part in cached_result.all_parts:
                        yield cached_part
                    continue
            
            # Process uncached content
            processed_parts = []
            async for result in self._process_part(part):
                processed_parts.append(result)
                yield result
            
            # Cache the results if applicable
            if selected_cache and processed_parts:
                await selected_cache.put([part], processed_parts)
```

## Performance Optimization Strategies

### Map Processor for Concurrent Execution
The `map_processor` module provides advanced concurrent processing capabilities:

```python
from genai_processors import map_processor

# Convert part function to stream function with concurrency
@map_processor.map_part_function
async def concurrent_text_processor(part: content_api.ProcessorPart) -> AsyncIterable[content_api.ProcessorPart]:
    if content_api.is_text(part.mimetype):
        # Expensive text processing
        processed_text = await expensive_nlp_operation(part.text)
        yield content_api.ProcessorPart(processed_text, role=part.role)
    else:
        yield part

# Chain multiple part functions with tree-based execution
def create_analysis_chain():
    return map_processor.chain_part_functions([
        extract_entities,
        analyze_sentiment, 
        generate_summary
    ])

# Parallel execution with match functions
def create_multimodal_processor():
    return map_processor.parallel_part_functions(
        fns=[text_processor, image_processor, audio_processor],
        match_fns=[
            lambda p: content_api.is_text(p.mimetype),
            lambda p: content_api.is_image(p.mimetype),
            lambda p: content_api.is_audio(p.mimetype)
        ],
        with_default_output=True  # Pass through unmatched parts
    )
```

### Queue Size Optimization
```python
class OptimizedStreamProcessor(processor.Processor):
    """Processor with optimized queue sizes for different scenarios."""
    
    def __init__(self, processing_mode: str = "balanced"):
        if processing_mode == "high_throughput":
            self.queue_size = 50000  # Large queue for high volume
            self.batch_size = 100
        elif processing_mode == "low_latency":
            self.queue_size = 10      # Small queue for quick response
            self.batch_size = 1
        else:  # balanced
            self.queue_size = 1000
            self.batch_size = 10
    
    async def call(self, content: AsyncIterable[content_api.ProcessorPart]) -> AsyncIterable[content_api.ProcessorPartTypes]:
        processing_queue = asyncio.Queue(maxsize=self.queue_size)
        
        async def batch_processor():
            batch = []
            async for part in content:
                batch.append(part)
                if len(batch) >= self.batch_size:
                    await self._process_batch(batch, processing_queue)
                    batch = []
            
            if batch:  # Process remaining items
                await self._process_batch(batch, processing_queue)
            
            await processing_queue.put(None)  # Signal completion
        
        # Start batch processing in background
        context.create_task(batch_processor())
        
        # Yield results as they become available
        while (result := await processing_queue.get()) is not None:
            yield result
```

### Memory Management for Large Streams
```python
class MemoryEfficientProcessor(processor.Processor):
    """Processor optimized for large data streams with memory constraints."""
    
    def __init__(self, max_memory_mb: int = 100):
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.current_memory_usage = 0
        self.memory_lock = asyncio.Lock()
    
    async def call(self, content: AsyncIterable[content_api.ProcessorPart]) -> AsyncIterable[content_api.ProcessorPartTypes]:
        async for part in content:
            part_size = self._estimate_part_size(part)
            
            # Wait for memory to be available
            async with self.memory_lock:
                while self.current_memory_usage + part_size > self.max_memory_bytes:
                    await asyncio.sleep(0.01)  # Brief pause to allow memory cleanup
                
                self.current_memory_usage += part_size
            
            try:
                async for result in self._process_part_with_cleanup(part):
                    yield result
            finally:
                async with self.memory_lock:
                    self.current_memory_usage -= part_size
    
    def _estimate_part_size(self, part: content_api.ProcessorPart) -> int:
        """Estimate memory usage of a ProcessorPart."""
        size = 0
        if part.text:
            size += len(part.text.encode('utf-8'))
        if part.bytes:
            size += len(part.bytes)
        size += len(str(part.metadata)) * 2  # Rough estimate for metadata
        return size
```

## Real-time Processing Optimizations

### Rolling Prompt Management
```python
class OptimizedRollingPrompt:
    """Enhanced rolling prompt with intelligent memory management."""
    
    def __init__(self, max_parts: int = 1000, compression_ratio: float = 0.5):
        self.max_parts = max_parts
        self.compression_ratio = compression_ratio
        self.parts_buffer = collections.deque(maxlen=max_parts)
        self.compressed_history = []
        self.compression_threshold = int(max_parts * 0.8)
    
    def add_part(self, part: content_api.ProcessorPart):
        """Add part with automatic compression when threshold is reached."""
        self.parts_buffer.append(part)
        
        if len(self.parts_buffer) >= self.compression_threshold:
            self._compress_history()
    
    def _compress_history(self):
        """Compress older parts to maintain memory efficiency."""
        parts_to_compress = int(len(self.parts_buffer) * self.compression_ratio)
        
        # Extract parts for compression
        compressed_parts = []
        for _ in range(parts_to_compress):
            if self.parts_buffer:
                compressed_parts.append(self.parts_buffer.popleft())
        
        # Create compressed summary
        if compressed_parts:
            summary_text = self._create_summary(compressed_parts)
            summary_part = content_api.ProcessorPart(
                summary_text,
                role='system',
                metadata={'compressed': True, 'original_count': len(compressed_parts)}
            )
            self.compressed_history.append(summary_part)
    
    def _create_summary(self, parts: list[content_api.ProcessorPart]) -> str:
        """Create intelligent summary of compressed parts."""
        text_parts = [p.text for p in parts if content_api.is_text(p.mimetype) and p.text]
        
        if not text_parts:
            return f"[Compressed {len(parts)} non-text parts]"
        
        # Simple summarization - in practice, use a summarization model
        combined_text = " ".join(text_parts)
        if len(combined_text) > 500:
            return f"[Summary of {len(parts)} parts]: {combined_text[:400]}..."
        return combined_text
```

### Event-Driven Processing with Caching
```python
class CachedEventProcessor(processor.Processor):
    """Event processor with intelligent caching of detection results."""
    
    def __init__(self, event_cache_ttl: int = 300):  # 5 minutes
        self.event_cache = cache.InMemoryCache(
            ttl_hours=event_cache_ttl / 3600,
            max_items=10000
        )
        self.detection_debounce = {}  # Debounce rapid events
        self.last_detection_time = {}
    
    async def call(self, content: AsyncIterable[content_api.ProcessorPart]) -> AsyncIterable[content_api.ProcessorPartTypes]:
        async for part in content:
            # Always pass through the original part
            yield part
            
            if content_api.is_image(part.mimetype):
                await self._process_image_for_events(part)
    
    async def _process_image_for_events(self, image_part: content_api.ProcessorPart):
        """Process image for event detection with caching and debouncing."""
        # Create cache key based on image content hash
        image_hash = hashlib.md5(image_part.bytes).hexdigest()
        cache_key = f"event_detection:{image_hash}"
        
        # Check cache first
        cached_events = await self.event_cache.lookup([image_part])
        if cached_events is not cache.CacheMiss:
            for event in cached_events.all_parts:
                if self._should_emit_event(event):
                    yield event
            return
        
        # Perform event detection
        detected_events = []
        async for event in self._detect_events(image_part):
            detected_events.append(event)
            if self._should_emit_event(event):
                yield event
        
        # Cache the results
        if detected_events:
            await self.event_cache.put([image_part], detected_events)
    
    def _should_emit_event(self, event: content_api.ProcessorPart) -> bool:
        """Debounce rapid event emissions."""
        event_type = event.metadata.get('event_type', 'unknown')
        current_time = time.time()
        
        last_time = self.last_detection_time.get(event_type, 0)
        if current_time - last_time < 1.0:  # 1 second debounce
            return False
        
        self.last_detection_time[event_type] = current_time
        return True
```

## Cache Monitoring and Analytics

### Cache Performance Tracking
```python
class CacheAnalytics:
    """Monitor and analyze cache performance."""
    
    def __init__(self):
        self.metrics = {
            'hits': 0,
            'misses': 0,
            'puts': 0,
            'evictions': 0,
            'total_requests': 0
        }
        self.hit_rate_history = collections.deque(maxlen=1000)
    
    def record_hit(self):
        self.metrics['hits'] += 1
        self.metrics['total_requests'] += 1
        self._update_hit_rate()
    
    def record_miss(self):
        self.metrics['misses'] += 1
        self.metrics['total_requests'] += 1
        self._update_hit_rate()
    
    def _update_hit_rate(self):
        if self.metrics['total_requests'] > 0:
            hit_rate = self.metrics['hits'] / self.metrics['total_requests']
            self.hit_rate_history.append(hit_rate)
    
    def get_performance_report(self) -> dict:
        """Generate comprehensive cache performance report."""
        total_requests = self.metrics['total_requests']
        if total_requests == 0:
            return {'status': 'no_data'}
        
        current_hit_rate = self.metrics['hits'] / total_requests
        avg_hit_rate = sum(self.hit_rate_history) / len(self.hit_rate_history) if self.hit_rate_history else 0
        
        return {
            'current_hit_rate': current_hit_rate,
            'average_hit_rate': avg_hit_rate,
            'total_requests': total_requests,
            'cache_efficiency': 'excellent' if current_hit_rate > 0.8 else 'good' if current_hit_rate > 0.6 else 'needs_improvement',
            'recommendations': self._generate_recommendations(current_hit_rate)
        }
    
    def _generate_recommendations(self, hit_rate: float) -> list[str]:
        """Generate optimization recommendations based on cache performance."""
        recommendations = []
        
        if hit_rate < 0.3:
            recommendations.append("Consider increasing cache size or TTL")
            recommendations.append("Review cache key generation for better hit rates")
        elif hit_rate < 0.6:
            recommendations.append("Analyze cache eviction patterns")
            recommendations.append("Consider implementing cache warming strategies")
        
        return recommendations
```

## Best Practices for Caching

### Cache Strategy Selection
1. **High-frequency, expensive operations**: Use long TTL (hours to days)
2. **Real-time data**: Use short TTL (minutes) or conditional caching
3. **Large objects**: Implement size-based eviction policies
4. **User-specific data**: Use prefixed caches with user identifiers

### Cache Key Design
1. **Include all relevant parameters** that affect output
2. **Exclude volatile data** like timestamps unless necessary
3. **Use consistent serialization** for complex objects
4. **Consider cache invalidation** strategies for dependent data

### Memory Management
1. **Monitor cache memory usage** in production
2. **Implement cache size limits** based on available memory
3. **Use appropriate TTL values** to prevent memory leaks
4. **Consider cache partitioning** for different data types

### Performance Monitoring
1. **Track hit/miss ratios** for cache effectiveness
2. **Monitor cache eviction rates** to optimize size
3. **Measure cache lookup latency** for performance impact
4. **Implement cache warming** for critical data paths