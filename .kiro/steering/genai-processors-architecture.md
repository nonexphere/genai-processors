# GenAI Processors Architecture & Design Patterns

## Core Concepts

### Processor Architecture
- **Processor**: Base class for stream-based processing units that take `AsyncIterable[ProcessorPart]` as input and return `AsyncIterable[ProcessorPartTypes]` as output
- **PartProcessor**: Specialized processor that operates on individual `ProcessorPart` objects, enabling higher concurrency
- **ProcessorPart**: Wrapper around `genai.types.Part` with metadata (role, substream_name, mimetype, custom metadata)
- **ProcessorContent**: Collection wrapper for multiple `ProcessorPart` objects with convenience methods

### Stream Processing Principles
- All processing is asynchronous and stream-based using Python's `asyncio`
- Processors can be chained (`+`), parallelized (`//`), or composed into complex workflows
- Content flows through processors as streams of `ProcessorPart` objects
- Support for multiple content types: text, images, audio, video, custom JSON, dataclasses

## Design Patterns

### 1. Processor Composition
```python
# Chain processors sequentially
workflow = processor1 + processor2 + processor3

# Run processors in parallel (PartProcessors only)
parallel_processing = processor1 // processor2 // processor3

# Combine chaining and parallelization
complex_workflow = (input_processor + parallel_processing) + output_processor
```

### 2. Content Filtering and Routing
```python
@processor.create_filter
def filter_text_only(part: ProcessorPart) -> bool:
    return content_api.is_text(part.mimetype)

# Apply filters before processing
filtered_workflow = filter_text_only + text_processor
```

### 3. Substream Management
- Use `substream_name` to organize different types of content (e.g., 'debug', 'status', main content)
- Reserved substreams: `DEBUG_STREAM`, `STATUS_STREAM`, `PROMPT_STREAM`
- Custom substreams for organizing parallel content flows

### 4. Context and Task Management
- Always use `async with context():` for proper task group management
- Use `context.create_task()` for background tasks within processor context
- Proper error propagation and cancellation handling through task groups

### 5. Real-time Processing Patterns
```python
# Live processing with interruption support
live_processor = realtime.LiveModelProcessor(
    turn_processor=model_processor + response_processor
)

# Rate-limited streaming for audio/video
rate_limited = rate_limit_audio.RateLimitAudio(
    sample_rate=24000,
    delay_other_parts=True
)
```

## Implementation Guidelines

### Processor Development
1. **Inherit from appropriate base class**: `Processor` for stream processing, `PartProcessor` for individual part processing
2. **Implement `call()` method**: Core processing logic, never call directly (use `__call__()`)
3. **Handle async properly**: Use `async def` and `AsyncIterable` return types
4. **Implement `match()` for PartProcessors**: Determine which parts should be processed
5. **Set meaningful `key_prefix`**: For caching and debugging purposes

### Content Handling
1. **Use ProcessorPart constructors**: `ProcessorPart(content, role=..., mimetype=..., metadata=...)`
2. **Leverage content type detection**: Use `content_api.is_text()`, `is_image()`, etc.
3. **Handle multiple content types**: Check mimetype before processing
4. **Preserve metadata**: Pass through or enhance metadata as content flows through processors

### Error Handling and Debugging
1. **Use debug and status streams**: `processor.debug()`, `processor.status()`
2. **Implement proper exception handling**: Catch and re-raise with context
3. **Use logging appropriately**: `absl.logging` for structured logging
4. **Test with various content types**: Ensure robustness across different inputs

### Performance Considerations
1. **Prefer PartProcessors for parallelizable work**: Higher concurrency than stream processors
2. **Use appropriate queue sizes**: Balance memory usage and throughput (default: 10,000 for parts)
3. **Implement caching strategically**: 
   - Use `InMemoryCache` with TTL for expensive operations
   - Leverage `@functools.cached_property` for processor metadata
   - Use deterministic hashing with `xxhash` for cache keys
4. **Consider streaming vs buffering**: Stream when possible, buffer when necessary (e.g., for API calls)
5. **Optimize concurrent execution**: Use `map_processor` for tree-based parallel processing
6. **Rate limiting for real-time**: Use `RateLimitAudio` for natural playback speed

## Common Patterns for Complex Workflows

### Multi-Modal Processing
```python
# Separate processing paths for different content types
text_processor = create_filter(is_text) + text_analysis_processor
image_processor = create_filter(is_image) + image_analysis_processor
audio_processor = create_filter(is_audio) + audio_analysis_processor

# Combine results
multi_modal = parallel_concat([text_processor, image_processor, audio_processor])
```

### Conversational Agents
```python
# Input processing
input_chain = audio_input + speech_to_text + conversation_filter

# Core conversation logic
conversation_processor = genai_model + response_enhancement

# Output processing  
output_chain = text_to_speech + rate_limit_audio + audio_output

# Complete agent
agent = input_chain + conversation_processor + output_chain
```

### Research and Analysis Workflows
```python
# Multi-step research process
research_workflow = (
    query_processor +
    parallel([web_search, document_retrieval, knowledge_base_query]) +
    synthesis_processor +
    report_generator
)
```

### Real-time Monitoring and Response
```python
# Event detection and response
monitoring_system = (
    video_input +
    event_detection +
    parallel([alert_processor, logging_processor, response_processor]) +
    action_dispatcher
)
```

## Advanced Topics

### Caching and Performance
For detailed caching strategies and performance optimization techniques, see:
- **genai-processors-caching.md**: Comprehensive caching system documentation
- **InMemoryCache**: TTL-based caching with deterministic hashing
- **Map Processor**: Tree-based concurrent execution patterns
- **Performance Monitoring**: Metrics collection and analysis

### Real-time Processing
For real-time and live processing capabilities, see:
- **genai-processors-realtime.md**: Real-time processing patterns and LiveProcessor usage
- **Rolling Prompts**: Intelligent context management for continuous streams
- **Audio Rate Limiting**: Natural playback speed for streaming audio
- **Event-driven Processing**: React to real-time events and triggers

### Debugging and Observability
For comprehensive debugging and monitoring, see:
- **genai-processors-debugging.md**: Debug streams, tracing, and error handling
- **Debug Streams**: Built-in debugging with reserved substreams
- **Performance Tracing**: Detailed execution path analysis
- **Resilient Processing**: Error recovery and fallback strategies

## Best Practices

### Code Organization
- Group related processors in modules by functionality
- Use clear, descriptive names for processors and their parameters
- Document processor behavior, especially for complex workflows
- Implement comprehensive tests for each processor
- Follow the established patterns from core processors

### Resource Management
- Always use context managers for external resources (files, network connections)
- Implement proper cleanup in processor destructors
- Monitor memory usage for long-running streams with rolling windows
- Use appropriate timeouts for external API calls
- Implement backpressure handling for high-volume streams

### Configuration Management
- Use environment variables for API keys and sensitive configuration
- Implement configuration validation with clear error messages
- Support both development and production configurations
- Document all configuration options with examples
- Use dataclasses for structured configuration

### Testing and Validation
- Test processors individually and in combination
- Use mock data for unit tests with realistic content types
- Implement integration tests with real data and external services
- Test error conditions and edge cases thoroughly
- Validate performance under load with appropriate metrics
- Test interruption and recovery scenarios for real-time processors

### Production Deployment
- Implement comprehensive monitoring and alerting
- Use structured logging with correlation IDs
- Set up health checks and circuit breakers
- Monitor cache hit rates and performance metrics
- Implement graceful shutdown and cleanup procedures