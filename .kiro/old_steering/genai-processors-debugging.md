# GenAI Processors Debugging & Observability

## Debugging Architecture

### Debug and Status Streams
GenAI Processors provides built-in debugging capabilities through reserved substreams:

```python
from genai_processors import processor, context

# Built-in debug utilities
def debug_processor_example():
    async def sample_processor(content: AsyncIterable[content_api.ProcessorPart]) -> AsyncIterable[content_api.ProcessorPartTypes]:
        async for part in content:
            # Emit debug information
            yield processor.debug(f"Processing part: {part.mimetype}")
            
            try:
                # Process the part
                result = await process_part(part)
                
                # Emit status updates
                yield processor.status(f"Successfully processed {part.mimetype}")
                yield result
                
            except Exception as e:
                # Emit error information
                yield processor.debug(f"Error processing part: {e}")
                yield processor.status("Processing failed")
                raise
```

### Advanced Debugging Processor
```python
class DebugProcessor(processor.Processor):
    """Comprehensive debugging wrapper for any processor."""
    
    def __init__(self, 
                 wrapped_processor: processor.Processor,
                 debug_level: str = "INFO",
                 capture_inputs: bool = True,
                 capture_outputs: bool = True,
                 performance_tracking: bool = True):
        self.wrapped_processor = wrapped_processor
        self.debug_level = debug_level
        self.capture_inputs = capture_inputs
        self.capture_outputs = capture_outputs
        self.performance_tracking = performance_tracking
        
        # Debug storage
        self.debug_history = collections.deque(maxlen=1000)
        self.performance_metrics = {}
        self.error_log = []
        
        # Unique session ID for this debug session
        self.session_id = f"debug_{time.time()}"
    
    async def call(self, content: AsyncIterable[content_api.ProcessorPart]) -> AsyncIterable[content_api.ProcessorPartTypes]:
        session_start = time.time()
        input_count = 0
        output_count = 0
        errors = []
        
        yield processor.debug(f"[{self.session_id}] Debug session started")
        
        try:
            # Capture input stream if enabled
            if self.capture_inputs:
                content = self._debug_input_stream(content)
            
            # Process with performance tracking
            if self.performance_tracking:
                async for result in self._track_performance(content):
                    if self.capture_outputs:
                        yield self._debug_output_part(result, output_count)
                    else:
                        yield result
                    output_count += 1
            else:
                async for result in self.wrapped_processor(content):
                    if self.capture_outputs:
                        yield self._debug_output_part(result, output_count)
                    else:
                        yield result
                    output_count += 1
        
        except Exception as e:
            error_info = {
                'error': str(e),
                'type': type(e).__name__,
                'timestamp': time.time(),
                'session_id': self.session_id
            }
            self.error_log.append(error_info)
            
            yield processor.debug(f"[{self.session_id}] Error: {e}")
            raise
        
        finally:
            session_duration = time.time() - session_start
            
            # Final debug summary
            summary = {
                'session_id': self.session_id,
                'duration': session_duration,
                'input_count': input_count,
                'output_count': output_count,
                'errors': len(errors),
                'processor': self.wrapped_processor.__class__.__name__
            }
            
            yield processor.status(f"Debug session complete: {summary}")
    
    async def _debug_input_stream(self, content: AsyncIterable[content_api.ProcessorPart]) -> AsyncIterable[content_api.ProcessorPart]:
        """Debug wrapper for input stream."""
        input_index = 0
        async for part in content:
            debug_info = {
                'index': input_index,
                'mimetype': part.mimetype,
                'role': part.role,
                'substream': part.substream_name,
                'metadata_keys': list(part.metadata.keys()),
                'timestamp': time.time()
            }
            
            if self.debug_level == "VERBOSE":
                if content_api.is_text(part.mimetype):
                    debug_info['text_preview'] = part.text[:100] + "..." if len(part.text) > 100 else part.text
                elif part.bytes:
                    debug_info['size_bytes'] = len(part.bytes)
            
            self.debug_history.append(('input', debug_info))
            yield processor.debug(f"[{self.session_id}] Input {input_index}: {debug_info}")
            yield part
            input_index += 1
    
    def _debug_output_part(self, part: content_api.ProcessorPart, index: int) -> content_api.ProcessorPart:
        """Add debug information to output part."""
        debug_info = {
            'index': index,
            'mimetype': part.mimetype,
            'role': part.role,
            'substream': part.substream_name,
            'timestamp': time.time()
        }
        
        self.debug_history.append(('output', debug_info))
        
        # Add debug metadata to the part
        part.metadata['debug_session'] = self.session_id
        part.metadata['debug_index'] = index
        part.metadata['debug_timestamp'] = time.time()
        
        return part
    
    async def _track_performance(self, content: AsyncIterable[content_api.ProcessorPart]) -> AsyncIterable[content_api.ProcessorPart]:
        """Track performance metrics during processing."""
        start_time = time.time()
        part_count = 0
        
        async for result in self.wrapped_processor(content):
            part_count += 1
            current_time = time.time()
            
            # Calculate metrics
            elapsed = current_time - start_time
            throughput = part_count / elapsed if elapsed > 0 else 0
            
            # Update performance metrics
            self.performance_metrics.update({
                'elapsed_time': elapsed,
                'parts_processed': part_count,
                'throughput_pps': throughput,
                'last_update': current_time
            })
            
            # Emit performance updates periodically
            if part_count % 100 == 0:
                yield processor.status(f"Performance: {throughput:.2f} parts/sec, {part_count} total")
            
            yield result
```

## Tracing and Profiling

### Execution Tracing
```python
class TracingProcessor(processor.Processor):
    """Detailed execution tracing for processor pipelines."""
    
    def __init__(self, 
                 wrapped_processor: processor.Processor,
                 trace_level: str = "BASIC",
                 export_traces: bool = False,
                 trace_file: str = None):
        self.wrapped_processor = wrapped_processor
        self.trace_level = trace_level
        self.export_traces = export_traces
        self.trace_file = trace_file or f"trace_{time.time()}.json"
        
        # Tracing data
        self.execution_trace = []
        self.call_stack = []
        self.timing_data = {}
        
    async def call(self, content: AsyncIterable[content_api.ProcessorPart]) -> AsyncIterable[content_api.ProcessorPartTypes]:
        trace_id = f"trace_{uuid.uuid4().hex[:8]}"
        
        # Start trace
        self._start_trace(trace_id, "processor_call")
        
        try:
            if self.trace_level == "DETAILED":
                async for result in self._detailed_trace(content, trace_id):
                    yield result
            else:
                async for result in self._basic_trace(content, trace_id):
                    yield result
        finally:
            self._end_trace(trace_id)
            
            if self.export_traces:
                await self._export_trace_data()
    
    def _start_trace(self, trace_id: str, operation: str):
        """Start a new trace operation."""
        trace_entry = {
            'trace_id': trace_id,
            'operation': operation,
            'start_time': time.time(),
            'processor': self.wrapped_processor.__class__.__name__,
            'thread_id': threading.get_ident(),
            'call_depth': len(self.call_stack)
        }
        
        self.call_stack.append(trace_entry)
        self.execution_trace.append(trace_entry)
    
    def _end_trace(self, trace_id: str):
        """End a trace operation."""
        if self.call_stack:
            trace_entry = self.call_stack.pop()
            trace_entry['end_time'] = time.time()
            trace_entry['duration'] = trace_entry['end_time'] - trace_entry['start_time']
    
    async def _detailed_trace(self, content: AsyncIterable[content_api.ProcessorPart], trace_id: str) -> AsyncIterable[content_api.ProcessorPart]:
        """Detailed tracing with full execution path."""
        part_index = 0
        
        async for part in content:
            part_trace_id = f"{trace_id}_part_{part_index}"
            self._start_trace(part_trace_id, f"process_part_{part_index}")
            
            try:
                # Trace input
                input_trace = {
                    'trace_id': part_trace_id,
                    'type': 'input',
                    'part_index': part_index,
                    'mimetype': part.mimetype,
                    'size': len(part.bytes) if part.bytes else len(part.text) if part.text else 0,
                    'timestamp': time.time()
                }
                self.execution_trace.append(input_trace)
                
                # Process through wrapped processor
                results = []
                async for result in self.wrapped_processor(streams.stream_content([part])):
                    results.append(result)
                
                # Trace outputs
                for i, result in enumerate(results):
                    output_trace = {
                        'trace_id': part_trace_id,
                        'type': 'output',
                        'part_index': part_index,
                        'output_index': i,
                        'mimetype': result.mimetype,
                        'timestamp': time.time()
                    }
                    self.execution_trace.append(output_trace)
                    yield result
                
            finally:
                self._end_trace(part_trace_id)
                part_index += 1
    
    async def _export_trace_data(self):
        """Export trace data to file."""
        trace_data = {
            'session_info': {
                'processor': self.wrapped_processor.__class__.__name__,
                'trace_level': self.trace_level,
                'start_time': min(t.get('start_time', float('inf')) for t in self.execution_trace),
                'end_time': max(t.get('end_time', 0) for t in self.execution_trace),
                'total_operations': len(self.execution_trace)
            },
            'execution_trace': self.execution_trace,
            'timing_summary': self._calculate_timing_summary()
        }
        
        with open(self.trace_file, 'w') as f:
            json.dump(trace_data, f, indent=2, default=str)
    
    def _calculate_timing_summary(self) -> dict:
        """Calculate timing statistics from trace data."""
        durations = [t.get('duration', 0) for t in self.execution_trace if 'duration' in t]
        
        if not durations:
            return {}
        
        return {
            'total_duration': sum(durations),
            'average_duration': sum(durations) / len(durations),
            'min_duration': min(durations),
            'max_duration': max(durations),
            'operation_count': len(durations)
        }
```

## Error Handling and Recovery

### Resilient Processor Wrapper
```python
class ResilientProcessor(processor.Processor):
    """Processor wrapper with advanced error handling and recovery."""
    
    def __init__(self, 
                 wrapped_processor: processor.Processor,
                 retry_attempts: int = 3,
                 retry_delay: float = 1.0,
                 fallback_processor: processor.Processor = None,
                 error_threshold: float = 0.1):
        self.wrapped_processor = wrapped_processor
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay
        self.fallback_processor = fallback_processor
        self.error_threshold = error_threshold
        
        # Error tracking
        self.error_count = 0
        self.total_attempts = 0
        self.error_history = collections.deque(maxlen=100)
        self.recovery_stats = {
            'successful_retries': 0,
            'fallback_activations': 0,
            'total_failures': 0
        }
    
    async def call(self, content: AsyncIterable[content_api.ProcessorPart]) -> AsyncIterable[content_api.ProcessorPartTypes]:
        async for part in content:
            self.total_attempts += 1
            
            # Try processing with retries
            success = False
            last_error = None
            
            for attempt in range(self.retry_attempts + 1):
                try:
                    async for result in self.wrapped_processor(streams.stream_content([part])):
                        yield result
                    success = True
                    break
                    
                except Exception as e:
                    last_error = e
                    self.error_count += 1
                    
                    error_info = {
                        'error': str(e),
                        'type': type(e).__name__,
                        'attempt': attempt + 1,
                        'timestamp': time.time(),
                        'part_info': {
                            'mimetype': part.mimetype,
                            'role': part.role
                        }
                    }
                    self.error_history.append(error_info)
                    
                    yield processor.debug(f"Processing failed (attempt {attempt + 1}): {e}")
                    
                    # Wait before retry (except on last attempt)
                    if attempt < self.retry_attempts:
                        await asyncio.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff
            
            # Handle final failure
            if not success:
                if self.fallback_processor:
                    yield processor.status("Primary processor failed, using fallback")
                    self.recovery_stats['fallback_activations'] += 1
                    
                    try:
                        async for result in self.fallback_processor(streams.stream_content([part])):
                            result.metadata['fallback_processed'] = True
                            yield result
                        success = True
                    except Exception as fallback_error:
                        yield processor.debug(f"Fallback processor also failed: {fallback_error}")
                
                if not success:
                    self.recovery_stats['total_failures'] += 1
                    
                    # Check if error rate exceeds threshold
                    error_rate = self.error_count / self.total_attempts
                    if error_rate > self.error_threshold:
                        yield processor.status(f"High error rate detected: {error_rate:.2%}")
                    
                    # Re-raise the last error
                    raise last_error
            else:
                if self.error_count > 0:  # This was a retry success
                    self.recovery_stats['successful_retries'] += 1
    
    def get_resilience_report(self) -> dict:
        """Generate resilience and error handling report."""
        error_rate = self.error_count / max(1, self.total_attempts)
        
        return {
            'error_statistics': {
                'total_attempts': self.total_attempts,
                'error_count': self.error_count,
                'error_rate': error_rate,
                'is_healthy': error_rate < self.error_threshold
            },
            'recovery_statistics': self.recovery_stats,
            'recent_errors': list(self.error_history)[-10:],  # Last 10 errors
            'recommendations': self._generate_resilience_recommendations(error_rate)
        }
    
    def _generate_resilience_recommendations(self, error_rate: float) -> list[str]:
        """Generate recommendations for improving resilience."""
        recommendations = []
        
        if error_rate > 0.2:
            recommendations.append("High error rate - consider reviewing input validation")
            recommendations.append("Consider implementing circuit breaker pattern")
        
        if self.recovery_stats['fallback_activations'] > self.total_attempts * 0.1:
            recommendations.append("Frequent fallback usage - primary processor may need optimization")
        
        if self.recovery_stats['successful_retries'] > 0:
            recommendations.append("Retries are helping - consider optimizing retry strategy")
        
        return recommendations
```

## Monitoring and Alerting

### Comprehensive Monitoring System
```python
class ProcessorMonitor:
    """Comprehensive monitoring system for processor pipelines."""
    
    def __init__(self, 
                 alert_thresholds: dict = None,
                 monitoring_interval: float = 60.0,
                 export_metrics: bool = True):
        self.alert_thresholds = alert_thresholds or {
            'error_rate': 0.05,
            'latency_ms': 1000,
            'throughput_pps': 1.0,
            'memory_mb': 500
        }
        self.monitoring_interval = monitoring_interval
        self.export_metrics = export_metrics
        
        # Metrics storage
        self.metrics = {
            'performance': collections.defaultdict(list),
            'errors': collections.defaultdict(int),
            'alerts': [],
            'health_checks': []
        }
        
        # Monitoring state
        self.monitoring_active = False
        self.last_alert_times = {}
        
    async def monitor_processor(self, 
                              processor: processor.Processor,
                              content: AsyncIterable[content_api.ProcessorPart]) -> AsyncIterable[content_api.ProcessorPart]:
        """Monitor a processor during execution."""
        self.monitoring_active = True
        
        # Start background monitoring
        monitor_task = context.create_task(self._background_monitoring())
        
        try:
            start_time = time.time()
            part_count = 0
            error_count = 0
            
            async for part in content:
                part_start = time.time()
                
                try:
                    async for result in processor(streams.stream_content([part])):
                        # Record processing metrics
                        processing_time = time.time() - part_start
                        self._record_metric('processing_time', processing_time)
                        self._record_metric('throughput', 1)
                        
                        yield result
                        part_count += 1
                        
                except Exception as e:
                    error_count += 1
                    self._record_error(type(e).__name__)
                    
                    # Check for alert conditions
                    await self._check_alert_conditions(part_count, error_count)
                    raise
        
        finally:
            self.monitoring_active = False
            monitor_task.cancel()
    
    def _record_metric(self, metric_name: str, value: float):
        """Record a metric value with timestamp."""
        self.metrics['performance'][metric_name].append({
            'value': value,
            'timestamp': time.time()
        })
        
        # Keep only recent metrics (last hour)
        cutoff_time = time.time() - 3600
        self.metrics['performance'][metric_name] = [
            m for m in self.metrics['performance'][metric_name]
            if m['timestamp'] > cutoff_time
        ]
    
    def _record_error(self, error_type: str):
        """Record an error occurrence."""
        self.metrics['errors'][error_type] += 1
    
    async def _check_alert_conditions(self, part_count: int, error_count: int):
        """Check if any alert conditions are met."""
        current_time = time.time()
        
        # Calculate current error rate
        error_rate = error_count / max(1, part_count)
        
        # Check error rate threshold
        if error_rate > self.alert_thresholds['error_rate']:
            await self._trigger_alert('high_error_rate', {
                'current_rate': error_rate,
                'threshold': self.alert_thresholds['error_rate'],
                'part_count': part_count,
                'error_count': error_count
            })
        
        # Check latency threshold
        recent_processing_times = [
            m['value'] for m in self.metrics['performance']['processing_time'][-10:]
        ]
        if recent_processing_times:
            avg_latency_ms = (sum(recent_processing_times) / len(recent_processing_times)) * 1000
            if avg_latency_ms > self.alert_thresholds['latency_ms']:
                await self._trigger_alert('high_latency', {
                    'current_latency_ms': avg_latency_ms,
                    'threshold_ms': self.alert_thresholds['latency_ms']
                })
    
    async def _trigger_alert(self, alert_type: str, alert_data: dict):
        """Trigger an alert with rate limiting."""
        current_time = time.time()
        
        # Rate limit alerts (max one per 5 minutes per type)
        last_alert = self.last_alert_times.get(alert_type, 0)
        if current_time - last_alert < 300:  # 5 minutes
            return
        
        alert = {
            'type': alert_type,
            'timestamp': current_time,
            'data': alert_data,
            'severity': self._determine_alert_severity(alert_type, alert_data)
        }
        
        self.metrics['alerts'].append(alert)
        self.last_alert_times[alert_type] = current_time
        
        # Log alert (in production, send to monitoring system)
        logging.warning(f"ALERT [{alert_type}]: {alert_data}")
    
    def _determine_alert_severity(self, alert_type: str, alert_data: dict) -> str:
        """Determine the severity level of an alert."""
        if alert_type == 'high_error_rate':
            error_rate = alert_data.get('current_rate', 0)
            if error_rate > 0.2:
                return 'critical'
            elif error_rate > 0.1:
                return 'warning'
            else:
                return 'info'
        
        elif alert_type == 'high_latency':
            latency = alert_data.get('current_latency_ms', 0)
            if latency > 5000:  # 5 seconds
                return 'critical'
            elif latency > 2000:  # 2 seconds
                return 'warning'
            else:
                return 'info'
        
        return 'info'
    
    async def _background_monitoring(self):
        """Background monitoring loop."""
        while self.monitoring_active:
            try:
                # Perform health checks
                health_status = await self._perform_health_check()
                self.metrics['health_checks'].append({
                    'timestamp': time.time(),
                    'status': health_status
                })
                
                # Export metrics if enabled
                if self.export_metrics:
                    await self._export_current_metrics()
                
                await asyncio.sleep(self.monitoring_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"Monitoring error: {e}")
    
    async def _perform_health_check(self) -> dict:
        """Perform comprehensive health check."""
        current_time = time.time()
        
        # Calculate recent metrics
        recent_errors = sum(self.metrics['errors'].values())
        recent_processing_times = [
            m['value'] for m in self.metrics['performance']['processing_time']
            if current_time - m['timestamp'] < 300  # Last 5 minutes
        ]
        
        avg_processing_time = (
            sum(recent_processing_times) / len(recent_processing_times)
            if recent_processing_times else 0
        )
        
        return {
            'status': 'healthy' if recent_errors == 0 and avg_processing_time < 1.0 else 'degraded',
            'recent_errors': recent_errors,
            'avg_processing_time': avg_processing_time,
            'active_alerts': len([a for a in self.metrics['alerts'] if current_time - a['timestamp'] < 3600])
        }
```

## Best Practices for Debugging

### Development Guidelines
1. **Use debug streams liberally** during development
2. **Implement comprehensive error handling** with context
3. **Add performance tracking** to identify bottlenecks
4. **Use tracing for complex pipelines** to understand execution flow
5. **Monitor key metrics** in production environments

### Production Debugging
1. **Implement structured logging** with correlation IDs
2. **Use sampling for high-volume streams** to reduce overhead
3. **Set up alerting** for critical error conditions
4. **Maintain debug history** for post-incident analysis
5. **Implement circuit breakers** for resilience

### Common Debugging Scenarios
1. **Performance Issues**: Use tracing and performance monitoring
2. **Memory Leaks**: Monitor memory usage and implement cleanup
3. **Concurrency Problems**: Use detailed tracing with thread information
4. **Integration Failures**: Implement retry logic with exponential backoff
5. **Data Quality Issues**: Add input validation and content inspection