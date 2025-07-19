# GenAI Processors Integration Guidelines

## External Service Integration

### API Integration Patterns
```python
class ExternalAPIProcessor(processor.Processor):
  """Template for integrating external APIs with proper error handling and rate limiting."""
  
  def __init__(self, api_key: str, base_url: str, rate_limit: int = 10):
    self.api_key = api_key
    self.base_url = base_url
    self.rate_limiter = RateLimiter(rate_limit)
    self.http_client = httpx.AsyncClient(
      timeout=httpx.Timeout(30.0),
      limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
    )
  
  async def call(self, content: AsyncIterable[content_api.ProcessorPart]) -> AsyncIterable[content_api.ProcessorPartTypes]:
    async for part in content:
      try:
        # Rate limiting
        await self.rate_limiter.acquire()
        
        # Prepare API request
        request_data = self._prepare_request(part)
        
        # Make API call with retry logic
        response_data = await self._make_api_call_with_retry(request_data)
        
        # Process response
        result_part = self._process_response(response_data, part)
        yield result_part
        
      except APIError as e:
        yield processor.debug(f"API error: {e}")
        # Yield original part or error part based on strategy
        yield self._handle_api_error(part, e)
      except Exception as e:
        yield processor.status(f"Unexpected error: {e}")
        raise
  
  async def _make_api_call_with_retry(self, request_data: dict, max_retries: int = 3) -> dict:
    """Make API call with exponential backoff retry."""
    for attempt in range(max_retries):
      try:
        response = await self.http_client.post(
          f"{self.base_url}/api/process",
          json=request_data,
          headers={"Authorization": f"Bearer {self.api_key}"}
        )
        response.raise_for_status()
        return response.json()
        
      except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:  # Rate limited
          wait_time = 2 ** attempt
          await asyncio.sleep(wait_time)
          continue
        elif e.response.status_code >= 500:  # Server error
          if attempt == max_retries - 1:
            raise APIError(f"Server error after {max_retries} attempts")
          await asyncio.sleep(2 ** attempt)
          continue
        else:
          raise APIError(f"HTTP {e.response.status_code}: {e.response.text}")
      
      except httpx.RequestError as e:
        if attempt == max_retries - 1:
          raise APIError(f"Request failed after {max_retries} attempts: {e}")
        await asyncio.sleep(2 ** attempt)
```

### Database Integration
```python
class DatabaseProcessor(processor.Processor):
  """Integrate with databases for data storage and retrieval."""
  
  def __init__(self, connection_string: str, table_name: str):
    self.connection_string = connection_string
    self.table_name = table_name
    self.connection_pool = None
  
  async def __aenter__(self):
    """Initialize database connection pool."""
    self.connection_pool = await asyncpg.create_pool(
      self.connection_string,
      min_size=1,
      max_size=10
    )
    return self
  
  async def __aexit__(self, exc_type, exc_val, exc_tb):
    """Close database connections."""
    if self.connection_pool:
      await self.connection_pool.close()
  
  async def call(self, content: AsyncIterable[content_api.ProcessorPart]) -> AsyncIterable[content_api.ProcessorPartTypes]:
    async for part in content:
      try:
        # Store input data
        storage_id = await self._store_input(part)
        
        # Process the part
        processed_part = await self._process_part(part)
        
        # Store results
        await self._store_result(storage_id, processed_part)
        
        # Add database metadata
        processed_part.metadata['storage_id'] = storage_id
        processed_part.metadata['stored_at'] = time.time()
        
        yield processed_part
        
      except DatabaseError as e:
        yield processor.debug(f"Database error: {e}")
        # Continue processing without storage
        yield await self._process_part(part)
  
  async def _store_input(self, part: content_api.ProcessorPart) -> str:
    """Store input part in database."""
    async with self.connection_pool.acquire() as conn:
      storage_id = str(uuid.uuid4())
      await conn.execute(
        f"INSERT INTO {self.table_name}_inputs (id, content, mimetype, metadata, created_at) VALUES ($1, $2, $3, $4, $5)",
        storage_id, part.text or part.bytes, part.mimetype, json.dumps(part.metadata), datetime.utcnow()
      )
      return storage_id
```

### Message Queue Integration
```python
class MessageQueueProcessor(processor.Processor):
  """Integrate with message queues for asynchronous processing."""
  
  def __init__(self, queue_url: str, queue_name: str):
    self.queue_url = queue_url
    self.queue_name = queue_name
    self.publisher = None
    self.subscriber = None
  
  async def call(self, content: AsyncIterable[content_api.ProcessorPart]) -> AsyncIterable[content_api.ProcessorPartTypes]:
    async for part in content:
      # Publish to queue for async processing
      message_id = await self._publish_message(part)
      
      # Create a tracking part
      tracking_part = content_api.ProcessorPart(
        f"Processing queued with ID: {message_id}",
        role=part.role,
        metadata={
          **part.metadata,
          'message_id': message_id,
          'queue_name': self.queue_name,
          'status': 'queued'
        }
      )
      
      yield tracking_part
  
  async def _publish_message(self, part: content_api.ProcessorPart) -> str:
    """Publish part to message queue."""
    message = {
      'id': str(uuid.uuid4()),
      'content': part.to_dict(),
      'timestamp': time.time(),
      'processor_type': self.__class__.__name__
    }
    
    # Publish to queue (implementation depends on queue system)
    await self.publisher.publish(self.queue_name, json.dumps(message))
    return message['id']
```

## Cloud Service Integration

### Google Cloud Integration
```python
class GoogleCloudProcessor(processor.Processor):
  """Integration with Google Cloud services."""
  
  def __init__(self, project_id: str, credentials_path: str = None):
    self.project_id = project_id
    self.credentials_path = credentials_path
    self._init_clients()
  
  def _init_clients(self):
    """Initialize Google Cloud service clients."""
    if self.credentials_path:
      os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = self.credentials_path
    
    self.storage_client = storage.Client(project=self.project_id)
    self.translate_client = translate.Client(project=self.project_id)
    self.vision_client = vision.ImageAnnotatorClient()
  
  async def call(self, content: AsyncIterable[content_api.ProcessorPart]) -> AsyncIterable[content_api.ProcessorPartTypes]:
    async for part in content:
      if content_api.is_image(part.mimetype):
        # Process with Vision API
        async for result in self._process_with_vision(part):
          yield result
      elif content_api.is_text(part.mimetype):
        # Process with Translation API if needed
        async for result in self._process_with_translation(part):
          yield result
      else:
        # Store in Cloud Storage and return reference
        storage_url = await self._store_in_cloud_storage(part)
        reference_part = content_api.ProcessorPart(
          f"Content stored at: {storage_url}",
          metadata={**part.metadata, 'cloud_storage_url': storage_url}
        )
        yield reference_part
```

### AWS Integration
```python
class AWSProcessor(processor.Processor):
  """Integration with AWS services."""
  
  def __init__(self, aws_access_key: str, aws_secret_key: str, region: str = 'us-east-1'):
    self.session = boto3.Session(
      aws_access_key_id=aws_access_key,
      aws_secret_access_key=aws_secret_key,
      region_name=region
    )
    self.s3_client = self.session.client('s3')
    self.comprehend_client = self.session.client('comprehend')
    self.rekognition_client = self.session.client('rekognition')
  
  async def call(self, content: AsyncIterable[content_api.ProcessorPart]) -> AsyncIterable[content_api.ProcessorPartTypes]:
    async for part in content:
      if content_api.is_text(part.mimetype):
        # Process with Comprehend
        sentiment_result = await self._analyze_sentiment(part.text)
        
        enhanced_part = content_api.ProcessorPart(
          part.text,
          role=part.role,
          metadata={
            **part.metadata,
            'aws_sentiment': sentiment_result
          }
        )
        yield enhanced_part
        
      elif content_api.is_image(part.mimetype):
        # Process with Rekognition
        labels = await self._detect_labels(part.bytes)
        
        analysis_part = content_api.ProcessorPart(
          f"Detected labels: {', '.join(labels)}",
          role='model',
          metadata={
            **part.metadata,
            'aws_labels': labels
          }
        )
        yield analysis_part
```

## Third-Party AI Service Integration

### OpenAI Integration
```python
class OpenAIProcessor(processor.Processor):
  """Integration with OpenAI services."""
  
  def __init__(self, api_key: str, model: str = "gpt-4"):
    self.client = openai.AsyncOpenAI(api_key=api_key)
    self.model = model
  
  async def call(self, content: AsyncIterable[content_api.ProcessorPart]) -> AsyncIterable[content_api.ProcessorPartTypes]:
    # Collect all parts for context
    parts = []
    async for part in content:
      parts.append(part)
    
    # Convert to OpenAI format
    messages = self._convert_to_openai_format(parts)
    
    try:
      # Make API call
      response = await self.client.chat.completions.create(
        model=self.model,
        messages=messages,
        stream=True
      )
      
      # Stream response
      accumulated_text = ""
      async for chunk in response:
        if chunk.choices[0].delta.content:
          accumulated_text += chunk.choices[0].delta.content
          
          # Yield incremental updates
          yield content_api.ProcessorPart(
            accumulated_text,
            role='model',
            metadata={'openai_model': self.model, 'streaming': True}
          )
      
      # Final complete response
      yield content_api.ProcessorPart(
        accumulated_text,
        role='model',
        metadata={'openai_model': self.model, 'streaming': False, 'complete': True}
      )
      
    except openai.APIError as e:
      yield processor.debug(f"OpenAI API error: {e}")
      yield content_api.ProcessorPart(
        f"Error processing with OpenAI: {e}",
        role='system',
        metadata={'error': True, 'error_type': 'openai_api_error'}
      )
```

### Anthropic Claude Integration
```python
class ClaudeProcessor(processor.Processor):
  """Integration with Anthropic Claude."""
  
  def __init__(self, api_key: str, model: str = "claude-3-sonnet-20240229"):
    self.client = anthropic.AsyncAnthropic(api_key=api_key)
    self.model = model
  
  async def call(self, content: AsyncIterable[content_api.ProcessorPart]) -> AsyncIterable[content_api.ProcessorPartTypes]:
    # Collect and format content
    messages = []
    system_message = ""
    
    async for part in content:
      if part.role.lower() == 'system':
        system_message += part.text + "\n"
      else:
        messages.append({
          "role": part.role.lower() if part.role.lower() in ['user', 'assistant'] else 'user',
          "content": part.text
        })
    
    try:
      # Make API call
      response = await self.client.messages.create(
        model=self.model,
        max_tokens=4000,
        system=system_message if system_message else None,
        messages=messages
      )
      
      # Process response
      for content_block in response.content:
        if content_block.type == 'text':
          yield content_api.ProcessorPart(
            content_block.text,
            role='assistant',
            metadata={
              'claude_model': self.model,
              'usage': response.usage.dict() if response.usage else None
            }
          )
    
    except anthropic.APIError as e:
      yield processor.debug(f"Claude API error: {e}")
      yield content_api.ProcessorPart(
        f"Error processing with Claude: {e}",
        role='system',
        metadata={'error': True, 'error_type': 'claude_api_error'}
      )
```

## Integration Utilities

### Service Discovery and Load Balancing
```python
class ServiceDiscoveryProcessor(processor.Processor):
  """Discover and load balance across multiple service instances."""
  
  def __init__(self, service_registry: dict[str, list[str]]):
    self.service_registry = service_registry
    self.health_checker = HealthChecker()
    self.load_balancer = RoundRobinLoadBalancer()
  
  async def call(self, content: AsyncIterable[content_api.ProcessorPart]) -> AsyncIterable[content_api.ProcessorPartTypes]:
    async for part in content:
      # Determine required service
      service_type = self._determine_service_type(part)
      
      # Get healthy service instances
      available_services = await self._get_healthy_services(service_type)
      
      if not available_services:
        yield processor.debug(f"No healthy services available for type: {service_type}")
        yield part  # Pass through unchanged
        continue
      
      # Select service instance
      selected_service = self.load_balancer.select(available_services)
      
      # Process with selected service
      try:
        service_processor = self._create_service_processor(selected_service)
        async for result in service_processor(streams.stream_content([part])):
          result.metadata['processed_by_service'] = selected_service
          yield result
      
      except ServiceUnavailableError:
        # Mark service as unhealthy and retry with another
        self.health_checker.mark_unhealthy(selected_service)
        yield processor.debug(f"Service {selected_service} marked as unhealthy")
        
        # Retry with next available service
        remaining_services = [s for s in available_services if s != selected_service]
        if remaining_services:
          retry_service = self.load_balancer.select(remaining_services)
          service_processor = self._create_service_processor(retry_service)
          async for result in service_processor(streams.stream_content([part])):
            result.metadata['processed_by_service'] = retry_service
            result.metadata['retry_after_failure'] = True
            yield result
        else:
          yield processor.status("All services unavailable")
          yield part
```

### Configuration Management
```python
class ConfigurableProcessor(processor.Processor):
  """Base class for processors with external configuration."""
  
  def __init__(self, config_source: str, config_key: str):
    self.config_source = config_source
    self.config_key = config_key
    self.config = self._load_config()
    self.config_watcher = ConfigWatcher(config_source, self._on_config_change)
  
  def _load_config(self) -> dict:
    """Load configuration from external source."""
    if self.config_source.startswith('http'):
      # Load from HTTP endpoint
      response = requests.get(f"{self.config_source}/{self.config_key}")
      return response.json()
    elif self.config_source.startswith('file://'):
      # Load from file
      file_path = self.config_source[7:]  # Remove 'file://' prefix
      with open(file_path, 'r') as f:
        all_config = json.load(f)
        return all_config.get(self.config_key, {})
    else:
      raise ValueError(f"Unsupported config source: {self.config_source}")
  
  async def _on_config_change(self, new_config: dict):
    """Handle configuration changes."""
    self.config = new_config
    await self._reconfigure()
  
  async def _reconfigure(self):
    """Reconfigure processor with new settings."""
    # Override in subclasses
    pass
```

### Monitoring and Observability Integration
```python
class ObservabilityProcessor(processor.Processor):
  """Add comprehensive observability to any processor."""
  
  def __init__(self, wrapped_processor: processor.Processor, 
               metrics_endpoint: str = None, 
               tracing_endpoint: str = None):
    self.wrapped_processor = wrapped_processor
    self.metrics_client = MetricsClient(metrics_endpoint) if metrics_endpoint else None
    self.tracer = TracingClient(tracing_endpoint) if tracing_endpoint else None
  
  async def call(self, content: AsyncIterable[content_api.ProcessorPart]) -> AsyncIterable[content_api.ProcessorPartTypes]:
    async for part in content:
      # Start tracing
      trace_id = str(uuid.uuid4())
      span = self.tracer.start_span(f"{self.wrapped_processor.__class__.__name__}.process", trace_id) if self.tracer else None
      
      start_time = time.time()
      
      try:
        # Process with wrapped processor
        results = []
        async for result in self.wrapped_processor(streams.stream_content([part])):
          results.append(result)
          yield result
        
        # Record success metrics
        processing_time = time.time() - start_time
        
        if self.metrics_client:
          await self.metrics_client.record_counter(
            'processor.requests.success',
            tags={'processor': self.wrapped_processor.__class__.__name__}
          )
          await self.metrics_client.record_histogram(
            'processor.processing_time',
            processing_time,
            tags={'processor': self.wrapped_processor.__class__.__name__}
          )
        
        if span:
          span.set_attribute('success', True)
          span.set_attribute('processing_time', processing_time)
          span.set_attribute('output_count', len(results))
      
      except Exception as e:
        # Record error metrics
        processing_time = time.time() - start_time
        
        if self.metrics_client:
          await self.metrics_client.record_counter(
            'processor.requests.error',
            tags={
              'processor': self.wrapped_processor.__class__.__name__,
              'error_type': type(e).__name__
            }
          )
        
        if span:
          span.set_attribute('success', False)
          span.set_attribute('error', str(e))
          span.set_attribute('processing_time', processing_time)
        
        raise
      
      finally:
        if span:
          span.finish()
```

These integration patterns provide robust, production-ready approaches for connecting GenAI Processors with external services, cloud platforms, and monitoring systems while maintaining the library's asynchronous, stream-based architecture.