# GenAI Processors Development Standards

## Code Style and Standards

### Python Code Style
- Follow Google Python Style Guide with pyink formatting (line length: 80, indentation: 2 spaces)
- Use type hints for all function parameters and return values
- Prefer descriptive variable names over comments
- Use `async def` for all processor methods that handle streams

### Import Organization
```python
# Standard library imports
import asyncio
from collections.abc import AsyncIterable
from typing import Any

# Third-party imports  
from absl import logging
from google.genai import types as genai_types

# Local imports
from genai_processors import content_api
from genai_processors import processor
```

### Documentation Standards
- Include comprehensive docstrings for all processors and public methods
- Document processor behavior, input/output expectations, and side effects
- Provide usage examples in docstrings
- Document any external dependencies or API requirements

## Processor Implementation Patterns

### Basic Processor Template
```python
class CustomProcessor(processor.Processor):
  """Brief description of what this processor does.
  
  Longer description with usage examples and important notes.
  """
  
  def __init__(self, param1: str, param2: int = 10):
    """Initialize the processor.
    
    Args:
      param1: Description of parameter
      param2: Description with default value
    """
    self._param1 = param1
    self._param2 = param2
  
  async def call(
      self, content: AsyncIterable[content_api.ProcessorPart]
  ) -> AsyncIterable[content_api.ProcessorPartTypes]:
    """Process the input stream.
    
    Args:
      content: Input stream of ProcessorParts
      
    Yields:
      Processed ProcessorParts
    """
    async for part in content:
      # Processing logic here
      yield self._process_part(part)
  
  def _process_part(self, part: content_api.ProcessorPart) -> content_api.ProcessorPart:
    """Helper method for processing individual parts."""
    # Implementation details
    return part
  
  @functools.cached_property
  def key_prefix(self) -> str:
    """Unique identifier for caching purposes."""
    return f'{self.__class__.__qualname__}:{self._param1}:{self._param2}'
```

### PartProcessor Template
```python
class CustomPartProcessor(processor.PartProcessor):
  """Process individual parts with high concurrency."""
  
  async def call(
      self, part: content_api.ProcessorPart
  ) -> AsyncIterable[content_api.ProcessorPartTypes]:
    """Process a single part."""
    if not self.match(part):
      yield part
      return
      
    # Process the part
    processed_part = await self._async_process(part)
    yield processed_part
  
  def match(self, part: content_api.ProcessorPart) -> bool:
    """Determine if this processor should handle the part."""
    return content_api.is_text(part.mimetype)
  
  async def _async_process(self, part: content_api.ProcessorPart) -> content_api.ProcessorPart:
    """Async processing logic."""
    # Implementation
    return part
```

### Function-based Processor
```python
@processor.part_processor_function
async def simple_text_processor(
    part: content_api.ProcessorPart
) -> AsyncIterable[content_api.ProcessorPart]:
  """Simple function-based processor for text content."""
  if content_api.is_text(part.mimetype):
    # Process text
    processed_text = part.text.upper()
    yield content_api.ProcessorPart(processed_text, role=part.role)
  else:
    yield part
```

## Error Handling Patterns

### Robust Error Handling
```python
async def call(self, content: AsyncIterable[content_api.ProcessorPart]) -> AsyncIterable[content_api.ProcessorPartTypes]:
  """Process content with proper error handling."""
  async for part in content:
    try:
      result = await self._process_with_retry(part)
      yield result
    except ProcessingError as e:
      # Log error and yield debug information
      logging.error(f"Processing failed for part {part}: {e}")
      yield processor.debug(f"Processing error: {e}")
      # Optionally yield original part or error part
      yield part
    except Exception as e:
      # Handle unexpected errors
      logging.exception(f"Unexpected error processing part {part}")
      yield processor.status(f"Unexpected error: {type(e).__name__}")
      raise  # Re-raise for proper error propagation

async def _process_with_retry(self, part: content_api.ProcessorPart, max_retries: int = 3) -> content_api.ProcessorPart:
  """Process with exponential backoff retry."""
  for attempt in range(max_retries):
    try:
      return await self._process_part(part)
    except RetryableError as e:
      if attempt == max_retries - 1:
        raise
      wait_time = 2 ** attempt
      await asyncio.sleep(wait_time)
      logging.warning(f"Retry {attempt + 1}/{max_retries} after {wait_time}s: {e}")
```

### Context Management
```python
async def call(self, content: AsyncIterable[content_api.ProcessorPart]) -> AsyncIterable[content_api.ProcessorPartTypes]:
  """Use context for proper resource management."""
  async with context.context() as ctx:
    # Create background tasks within context
    background_task = ctx.create_task(self._background_processing())
    
    try:
      async for part in content:
        result = await self._process_part(part)
        yield result
    finally:
      # Cleanup is handled by context manager
      background_task.cancel()
```

## Testing Patterns

### Unit Testing Template
```python
import unittest
from unittest import mock
import asyncio

from genai_processors import content_api
from genai_processors import processor
from genai_processors import streams

class TestCustomProcessor(unittest.TestCase):
  
  def setUp(self):
    """Set up test fixtures."""
    self.processor = CustomProcessor(param1="test", param2=5)
  
  async def test_basic_processing(self):
    """Test basic processor functionality."""
    input_parts = [
      content_api.ProcessorPart("Hello"),
      content_api.ProcessorPart("World")
    ]
    input_stream = streams.stream_content(input_parts)
    
    results = []
    async for part in self.processor(input_stream):
      results.append(part)
    
    self.assertEqual(len(results), 2)
    self.assertEqual(results[0].text, "Expected output")
  
  async def test_error_handling(self):
    """Test processor error handling."""
    # Test with invalid input
    invalid_part = content_api.ProcessorPart(b"binary data", mimetype="application/octet-stream")
    input_stream = streams.stream_content([invalid_part])
    
    results = await streams.gather_stream(self.processor(input_stream))
    # Verify error handling behavior
    
  def test_sync_processing(self):
    """Test synchronous processing."""
    input_parts = [content_api.ProcessorPart("test")]
    results = processor.apply_sync(self.processor, input_parts)
    self.assertIsInstance(results, list)

if __name__ == '__main__':
  asyncio.run(unittest.main())
```

### Integration Testing
```python
async def test_processor_chain():
  """Test processor chaining."""
  processor1 = TextProcessor()
  processor2 = AnalysisProcessor()
  
  chain = processor1 + processor2
  
  input_data = [content_api.ProcessorPart("test input")]
  results = await processor.apply_async(chain, input_data)
  
  # Verify end-to-end behavior
  assert len(results) > 0
  assert results[0].text == "expected output"
```

## Performance Optimization

### Efficient Stream Processing
```python
async def call(self, content: AsyncIterable[content_api.ProcessorPart]) -> AsyncIterable[content_api.ProcessorPartTypes]:
  """Optimize for streaming performance."""
  # Use bounded queues to prevent memory issues
  output_queue = asyncio.Queue(maxsize=100)
  
  async def process_stream():
    try:
      async for part in content:
        processed = await self._process_part(part)
        await output_queue.put(processed)
    finally:
      await output_queue.put(None)  # Signal end
  
  # Start processing in background
  task = context.create_task(process_stream())
  
  try:
    while True:
      part = await output_queue.get()
      if part is None:
        break
      yield part
  finally:
    await task
```

### Caching Strategies
```python
class CachedProcessor(processor.Processor):
  """Processor with intelligent caching."""
  
  def __init__(self, cache_size: int = 1000):
    self._cache = {}
    self._cache_size = cache_size
  
  async def call(self, content: AsyncIterable[content_api.ProcessorPart]) -> AsyncIterable[content_api.ProcessorPartTypes]:
    async for part in content:
      cache_key = self._get_cache_key(part)
      
      if cache_key in self._cache:
        yield self._cache[cache_key]
      else:
        result = await self._expensive_processing(part)
        self._update_cache(cache_key, result)
        yield result
  
  def _get_cache_key(self, part: content_api.ProcessorPart) -> str:
    """Generate cache key for part."""
    return f"{part.mimetype}:{hash(part.text if part.text else part.bytes)}"
```

## Security Considerations

### Input Validation
```python
def _validate_input(self, part: content_api.ProcessorPart) -> bool:
  """Validate input part for security."""
  # Check file size limits
  if part.bytes and len(part.bytes) > self.max_file_size:
    raise ValueError(f"File too large: {len(part.bytes)} bytes")
  
  # Validate content type
  if part.mimetype not in self.allowed_mimetypes:
    raise ValueError(f"Unsupported content type: {part.mimetype}")
  
  # Additional validation logic
  return True
```

### API Key Management
```python
class SecureProcessor(processor.Processor):
  """Processor with secure API key handling."""
  
  def __init__(self, api_key_env_var: str):
    self._api_key = os.environ.get(api_key_env_var)
    if not self._api_key:
      raise ValueError(f"API key not found in environment variable: {api_key_env_var}")
  
  @property
  def key_prefix(self) -> str:
    # Don't include API key in cache key
    return f"{self.__class__.__qualname__}:secure"
```

## Deployment Considerations

### Configuration Management
```python
@dataclasses.dataclass
class ProcessorConfig:
  """Configuration for processor deployment."""
  api_key: str
  model_name: str
  max_concurrent_requests: int = 10
  timeout_seconds: int = 30
  retry_attempts: int = 3
  
  @classmethod
  def from_env(cls) -> 'ProcessorConfig':
    """Load configuration from environment variables."""
    return cls(
      api_key=os.environ['API_KEY'],
      model_name=os.environ.get('MODEL_NAME', 'default-model'),
      max_concurrent_requests=int(os.environ.get('MAX_CONCURRENT', '10')),
      timeout_seconds=int(os.environ.get('TIMEOUT', '30')),
      retry_attempts=int(os.environ.get('RETRY_ATTEMPTS', '3'))
    )
```

### Monitoring and Observability
```python
class MonitoredProcessor(processor.Processor):
  """Processor with built-in monitoring."""
  
  def __init__(self):
    self._metrics = {
      'processed_count': 0,
      'error_count': 0,
      'processing_time': []
    }
  
  async def call(self, content: AsyncIterable[content_api.ProcessorPart]) -> AsyncIterable[content_api.ProcessorPartTypes]:
    async for part in content:
      start_time = time.time()
      try:
        result = await self._process_part(part)
        self._metrics['processed_count'] += 1
        yield result
      except Exception as e:
        self._metrics['error_count'] += 1
        logging.error(f"Processing error: {e}")
        raise
      finally:
        processing_time = time.time() - start_time
        self._metrics['processing_time'].append(processing_time)
  
  def get_metrics(self) -> dict:
    """Get processor performance metrics."""
    return self._metrics.copy()
```