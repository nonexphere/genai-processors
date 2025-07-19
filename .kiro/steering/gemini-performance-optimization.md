# Gemini Models Performance Optimization & Monitoring

## 📋 **GEMINI PERFORMANCE OPTIMIZATION COMPLETE GUIDE**

This steering rule provides comprehensive performance optimization strategies, monitoring patterns, and troubleshooting guides for Gemini models in real-time applications.

## ⚡ **PERFORMANCE OPTIMIZATION STRATEGIES**

### **1. Latency Optimization**

#### **Model Selection for Minimum Latency**
```python
# Latency-optimized model hierarchy (fastest to slowest)
LATENCY_OPTIMIZED_MODELS = {
    'event_detection': 'gemini-2.5-flash-lite-preview-06-17',  # ~50-100ms
    'real_time_conversation': 'gemini-2.0-flash-live-001',     # ~200-400ms
    'high_quality_conversation': 'gemini-live-2.5-flash-preview',  # ~300-500ms
    'native_audio': 'gemini-2.5-flash-preview-native-audio-dialog'  # ~400-600ms
}
```

#### **Configuration for Minimum Latency**
```python
def create_low_latency_config():
    return types.LiveConnectConfig(
        response_modalities=["AUDIO"],
        
        # Optimize media resolution for speed
        generation_config=types.GenerationConfig(
            media_resolution=types.MediaResolution.MEDIA_RESOLUTION_LOW,
            max_output_tokens=100,  # Limit response length
            temperature=0.7,  # Slightly lower for faster generation
        ),
        
        # Aggressive VAD settings
        realtime_input_config=types.RealtimeInputConfig(
            turn_coverage='TURN_INCLUDES_ALL_INPUT',
            automatic_activity_detection={
                'disabled': False,
                'start_of_speech_sensitivity': types.StartSensitivity.START_SENSITIVITY_HIGH,
                'end_of_speech_sensitivity': types.EndSensitivity.END_SENSITIVITY_HIGH,
                'prefix_padding_ms': 10,  # Minimal padding
                'silence_duration_ms': 50   # Quick detection
            }
        ),
        
        # Minimal system instruction
        system_instruction="Be concise and direct.",
        
        # Disable transcription if not needed
        # output_audio_transcription={},  # Comment out to disable
    )
```

#### **Connection Optimization**
```python
class OptimizedConnection:
    def __init__(self, api_key: str):
        # Use connection pooling
        self.client = genai.Client(
            api_key=api_key,
            http_options={
                'api_version': 'v1alpha',  # Latest version
                'timeout': 30,
                'max_retries': 3,
                'retry_delay': 0.5
            }
        )
        
        # Pre-warm connection
        self._connection_pool = {}
    
    async def get_optimized_session(self, model: str, config: types.LiveConnectConfig):
        """Get pre-warmed session for minimum connection time."""
        session_key = f"{model}_{hash(str(config))}"
        
        if session_key not in self._connection_pool:
            # Create new session
            session = await self.client.aio.live.connect(model=model, config=config)
            self._connection_pool[session_key] = session
        
        return self._connection_pool[session_key]
```

### **2. Throughput Optimization**

#### **Batch Processing for High Volume**
```python
class HighThroughputProcessor:
    def __init__(self, api_key: str, max_concurrent_sessions: int = 10):
        self.api_key = api_key
        self.max_concurrent_sessions = max_concurrent_sessions
        self.session_pool = asyncio.Queue(maxsize=max_concurrent_sessions)
        self.active_sessions = {}
        
    async def initialize_session_pool(self, model: str, config: types.LiveConnectConfig):
        """Pre-create session pool for high throughput."""
        client = genai.Client(api_key=self.api_key)
        
        for i in range(self.max_concurrent_sessions):
            session = await client.aio.live.connect(model=model, config=config)
            await self.session_pool.put(session)
    
    async def process_request(self, audio_data: bytes) -> bytes:
        """Process request using session pool."""
        # Get session from pool
        session = await self.session_pool.get()
        
        try:
            # Process request
            await session.send_realtime_input(
                audio=types.Blob(data=audio_data, mime_type="audio/pcm;rate=16000")
            )
            
            # Collect response
            response_audio = b""
            async for response in session.receive():
                if response.data:
                    response_audio += response.data
                if response.server_content.model_turn:
                    break
            
            return response_audio
            
        finally:
            # Return session to pool
            await self.session_pool.put(session)
```

#### **Parallel Processing Pattern**
```python
class ParallelGeminiProcessor:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.semaphore = asyncio.Semaphore(5)  # Limit concurrent requests
    
    async def process_multiple_requests(self, requests: list) -> list:
        """Process multiple requests in parallel."""
        tasks = []
        
        for request in requests:
            task = asyncio.create_task(
                self._process_single_request(request)
            )
            tasks.append(task)
        
        # Wait for all tasks with timeout
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=30.0
            )
            return results
        except asyncio.TimeoutError:
            # Cancel remaining tasks
            for task in tasks:
                if not task.done():
                    task.cancel()
            raise
    
    async def _process_single_request(self, request):
        """Process single request with rate limiting."""
        async with self.semaphore:
            # Process request
            return await self._make_api_call(request)
```

### **3. Memory Optimization**

#### **Efficient Context Management**
```python
class MemoryOptimizedContextManager:
    def __init__(self, max_memory_mb: int = 100):
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.context_buffer = collections.deque(maxlen=1000)
        self.current_memory_usage = 0
        self.compression_ratio = 0.3
    
    def add_context_item(self, item: dict) -> bool:
        """Add context item with memory management."""
        item_size = self._estimate_size(item)
        
        # Check memory limit
        if self.current_memory_usage + item_size > self.max_memory_bytes:
            self._compress_old_context()
        
        # Add item
        self.context_buffer.append(item)
        self.current_memory_usage += item_size
        
        return True
    
    def _compress_old_context(self):
        """Compress older context items."""
        if not self.context_buffer:
            return
        
        # Calculate items to compress
        compress_count = int(len(self.context_buffer) * self.compression_ratio)
        
        if compress_count > 0:
            # Remove old items
            compressed_items = []
            for _ in range(compress_count):
                if self.context_buffer:
                    item = self.context_buffer.popleft()
                    compressed_items.append(item)
                    self.current_memory_usage -= self._estimate_size(item)
            
            # Create compressed summary
            if compressed_items:
                summary = self._create_compressed_summary(compressed_items)
                self.context_buffer.appendleft(summary)
                self.current_memory_usage += self._estimate_size(summary)
    
    def _estimate_size(self, item: dict) -> int:
        """Estimate memory size of item."""
        return len(str(item).encode('utf-8'))
    
    def _create_compressed_summary(self, items: list) -> dict:
        """Create compressed summary of items."""
        return {
            'type': 'compressed_summary',
            'item_count': len(items),
            'summary': f"Summary of {len(items)} context items",
            'timestamp': time.time()
        }
```

#### **Audio Buffer Management**
```python
class OptimizedAudioBuffer:
    def __init__(self, max_buffer_size: int = 1024 * 1024):  # 1MB
        self.max_buffer_size = max_buffer_size
        self.audio_chunks = collections.deque()
        self.current_size = 0
        self.lock = asyncio.Lock()
    
    async def add_audio_chunk(self, chunk: bytes) -> bool:
        """Add audio chunk with size management."""
        async with self.lock:
            chunk_size = len(chunk)
            
            # Remove old chunks if buffer is full
            while (self.current_size + chunk_size > self.max_buffer_size 
                   and self.audio_chunks):
                old_chunk = self.audio_chunks.popleft()
                self.current_size -= len(old_chunk)
            
            # Add new chunk
            self.audio_chunks.append(chunk)
            self.current_size += chunk_size
            
            return True
    
    async def get_audio_data(self, max_duration_sec: float = 5.0) -> bytes:
        """Get audio data up to specified duration."""
        async with self.lock:
            # Calculate max bytes for duration
            sample_rate = 16000
            max_bytes = int(max_duration_sec * sample_rate * 2)  # 16-bit
            
            result = b""
            while self.audio_chunks and len(result) < max_bytes:
                chunk = self.audio_chunks.popleft()
                remaining_space = max_bytes - len(result)
                
                if len(chunk) <= remaining_space:
                    result += chunk
                    self.current_size -= len(chunk)
                else:
                    # Partial chunk
                    result += chunk[:remaining_space]
                    # Put remainder back
                    self.audio_chunks.appendleft(chunk[remaining_space:])
                    break
            
            return result
```

## 📊 **PERFORMANCE MONITORING**

### **1. Comprehensive Metrics Collection**

#### **Real-time Performance Tracker**
```python
class GeminiPerformanceTracker:
    def __init__(self):
        self.metrics = {
            'requests': {
                'total': 0,
                'successful': 0,
                'failed': 0,
                'timeouts': 0
            },
            'latency': {
                'ttft': collections.deque(maxlen=1000),  # Time to first token
                'total_response': collections.deque(maxlen=1000),
                'connection': collections.deque(maxlen=100)
            },
            'throughput': {
                'requests_per_second': collections.deque(maxlen=100),
                'tokens_per_second': collections.deque(maxlen=100),
                'audio_chunks_per_second': collections.deque(maxlen=100)
            },
            'quality': {
                'interruptions': 0,
                'successful_function_calls': 0,
                'failed_function_calls': 0,
                'audio_quality_scores': collections.deque(maxlen=100)
            },
            'resource_usage': {
                'memory_usage_mb': collections.deque(maxlen=100),
                'cpu_usage_percent': collections.deque(maxlen=100),
                'network_bytes_sent': 0,
                'network_bytes_received': 0
            }
        }
        
        self.start_time = time.time()
        self.last_metrics_update = time.time()
    
    def record_request_start(self, request_id: str):
        """Record start of a request."""
        self.metrics['requests']['total'] += 1
        return {
            'request_id': request_id,
            'start_time': time.time(),
            'ttft': None,
            'end_time': None
        }
    
    def record_first_token(self, request_context: dict):
        """Record time to first token."""
        if request_context['ttft'] is None:
            ttft = time.time() - request_context['start_time']
            request_context['ttft'] = ttft
            self.metrics['latency']['ttft'].append(ttft)
    
    def record_request_complete(self, request_context: dict, success: bool = True):
        """Record completion of a request."""
        end_time = time.time()
        request_context['end_time'] = end_time
        
        total_time = end_time - request_context['start_time']
        self.metrics['latency']['total_response'].append(total_time)
        
        if success:
            self.metrics['requests']['successful'] += 1
        else:
            self.metrics['requests']['failed'] += 1
    
    def record_interruption(self):
        """Record an interruption event."""
        self.metrics['quality']['interruptions'] += 1
    
    def record_function_call(self, success: bool):
        """Record function call result."""
        if success:
            self.metrics['quality']['successful_function_calls'] += 1
        else:
            self.metrics['quality']['failed_function_calls'] += 1
    
    def update_resource_usage(self):
        """Update resource usage metrics."""
        import psutil
        
        # Memory usage
        memory_mb = psutil.Process().memory_info().rss / 1024 / 1024
        self.metrics['resource_usage']['memory_usage_mb'].append(memory_mb)
        
        # CPU usage
        cpu_percent = psutil.Process().cpu_percent()
        self.metrics['resource_usage']['cpu_usage_percent'].append(cpu_percent)
    
    def calculate_throughput(self):
        """Calculate current throughput metrics."""
        current_time = time.time()
        time_window = current_time - self.last_metrics_update
        
        if time_window > 0:
            # Requests per second
            recent_requests = self.metrics['requests']['total']
            rps = recent_requests / (current_time - self.start_time)
            self.metrics['throughput']['requests_per_second'].append(rps)
        
        self.last_metrics_update = current_time
    
    def get_performance_summary(self) -> dict:
        """Get comprehensive performance summary."""
        # Calculate averages
        avg_ttft = (
            sum(self.metrics['latency']['ttft']) / len(self.metrics['latency']['ttft'])
            if self.metrics['latency']['ttft'] else 0
        )
        
        avg_response_time = (
            sum(self.metrics['latency']['total_response']) / len(self.metrics['latency']['total_response'])
            if self.metrics['latency']['total_response'] else 0
        )
        
        success_rate = (
            self.metrics['requests']['successful'] / max(1, self.metrics['requests']['total'])
        )
        
        current_rps = (
            self.metrics['throughput']['requests_per_second'][-1]
            if self.metrics['throughput']['requests_per_second'] else 0
        )
        
        return {
            'performance': {
                'avg_ttft_ms': avg_ttft * 1000,
                'avg_response_time_ms': avg_response_time * 1000,
                'success_rate': success_rate,
                'current_rps': current_rps,
                'total_requests': self.metrics['requests']['total']
            },
            'quality': {
                'interruption_rate': (
                    self.metrics['quality']['interruptions'] / 
                    max(1, self.metrics['requests']['total'])
                ),
                'function_call_success_rate': (
                    self.metrics['quality']['successful_function_calls'] /
                    max(1, self.metrics['quality']['successful_function_calls'] + 
                        self.metrics['quality']['failed_function_calls'])
                )
            },
            'resource_usage': {
                'avg_memory_mb': (
                    sum(self.metrics['resource_usage']['memory_usage_mb']) /
                    max(1, len(self.metrics['resource_usage']['memory_usage_mb']))
                ),
                'avg_cpu_percent': (
                    sum(self.metrics['resource_usage']['cpu_usage_percent']) /
                    max(1, len(self.metrics['resource_usage']['cpu_usage_percent']))
                )
            },
            'recommendations': self._generate_recommendations()
        }
    
    def _generate_recommendations(self) -> list:
        """Generate performance optimization recommendations."""
        recommendations = []
        
        # Check TTFT
        if self.metrics['latency']['ttft']:
            avg_ttft = sum(self.metrics['latency']['ttft']) / len(self.metrics['latency']['ttft'])
            if avg_ttft > 1.0:  # > 1 second
                recommendations.append("High TTFT detected - consider using faster model or optimizing prompts")
        
        # Check success rate
        success_rate = (
            self.metrics['requests']['successful'] / max(1, self.metrics['requests']['total'])
        )
        if success_rate < 0.95:
            recommendations.append("Low success rate - review error handling and retry logic")
        
        # Check interruption rate
        interruption_rate = (
            self.metrics['quality']['interruptions'] / 
            max(1, self.metrics['requests']['total'])
        )
        if interruption_rate > 0.1:
            recommendations.append("High interruption rate - consider adjusting VAD sensitivity")
        
        # Check memory usage
        if self.metrics['resource_usage']['memory_usage_mb']:
            avg_memory = (
                sum(self.metrics['resource_usage']['memory_usage_mb']) /
                len(self.metrics['resource_usage']['memory_usage_mb'])
            )
            if avg_memory > 500:  # > 500MB
                recommendations.append("High memory usage - implement context compression")
        
        return recommendations
```

### **2. Real-time Dashboard**

#### **Performance Dashboard**
```python
class PerformanceDashboard:
    def __init__(self, tracker: GeminiPerformanceTracker):
        self.tracker = tracker
        self.dashboard_data = {}
        self.update_interval = 5.0  # seconds
    
    async def start_dashboard(self):
        """Start real-time performance dashboard."""
        while True:
            try:
                # Update metrics
                self.tracker.update_resource_usage()
                self.tracker.calculate_throughput()
                
                # Generate dashboard data
                self.dashboard_data = self._generate_dashboard_data()
                
                # Display dashboard
                self._display_dashboard()
                
                await asyncio.sleep(self.update_interval)
                
            except Exception as e:
                print(f"Dashboard error: {e}")
                await asyncio.sleep(self.update_interval)
    
    def _generate_dashboard_data(self) -> dict:
        """Generate current dashboard data."""
        summary = self.tracker.get_performance_summary()
        
        return {
            'timestamp': time.time(),
            'uptime': time.time() - self.tracker.start_time,
            'performance': summary['performance'],
            'quality': summary['quality'],
            'resource_usage': summary['resource_usage'],
            'recent_latency': list(self.tracker.metrics['latency']['ttft'])[-10:],
            'recommendations': summary['recommendations']
        }
    
    def _display_dashboard(self):
        """Display dashboard in console."""
        import os
        os.system('clear' if os.name == 'posix' else 'cls')
        
        data = self.dashboard_data
        
        print("=" * 80)
        print("GEMINI PERFORMANCE DASHBOARD")
        print("=" * 80)
        print(f"Uptime: {data['uptime']:.1f}s")
        print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Performance metrics
        perf = data['performance']
        print("PERFORMANCE METRICS:")
        print(f"  Average TTFT: {perf['avg_ttft_ms']:.1f}ms")
        print(f"  Average Response Time: {perf['avg_response_time_ms']:.1f}ms")
        print(f"  Success Rate: {perf['success_rate']:.2%}")
        print(f"  Current RPS: {perf['current_rps']:.1f}")
        print(f"  Total Requests: {perf['total_requests']}")
        print()
        
        # Quality metrics
        quality = data['quality']
        print("QUALITY METRICS:")
        print(f"  Interruption Rate: {quality['interruption_rate']:.2%}")
        print(f"  Function Call Success: {quality['function_call_success_rate']:.2%}")
        print()
        
        # Resource usage
        resources = data['resource_usage']
        print("RESOURCE USAGE:")
        print(f"  Memory: {resources['avg_memory_mb']:.1f}MB")
        print(f"  CPU: {resources['avg_cpu_percent']:.1f}%")
        print()
        
        # Recent latency trend
        if data['recent_latency']:
            print("RECENT LATENCY (last 10 requests):")
            latencies = [f"{l*1000:.0f}ms" for l in data['recent_latency']]
            print(f"  {' -> '.join(latencies)}")
            print()
        
        # Recommendations
        if data['recommendations']:
            print("RECOMMENDATIONS:")
            for i, rec in enumerate(data['recommendations'], 1):
                print(f"  {i}. {rec}")
            print()
        
        print("=" * 80)
```

### **3. Alerting System**

#### **Performance Alerting**
```python
class PerformanceAlerting:
    def __init__(self, tracker: GeminiPerformanceTracker):
        self.tracker = tracker
        self.alert_thresholds = {
            'ttft_ms': 2000,           # 2 seconds
            'response_time_ms': 5000,  # 5 seconds
            'success_rate': 0.90,      # 90%
            'memory_mb': 1000,         # 1GB
            'cpu_percent': 80,         # 80%
            'interruption_rate': 0.15  # 15%
        }
        
        self.alert_history = collections.deque(maxlen=100)
        self.alert_cooldown = {}  # Prevent spam
        self.cooldown_duration = 300  # 5 minutes
    
    async def check_alerts(self):
        """Check for alert conditions."""
        summary = self.tracker.get_performance_summary()
        current_time = time.time()
        
        alerts = []
        
        # Check TTFT
        if summary['performance']['avg_ttft_ms'] > self.alert_thresholds['ttft_ms']:
            alerts.append({
                'type': 'high_ttft',
                'severity': 'warning',
                'message': f"High TTFT: {summary['performance']['avg_ttft_ms']:.1f}ms",
                'value': summary['performance']['avg_ttft_ms'],
                'threshold': self.alert_thresholds['ttft_ms']
            })
        
        # Check success rate
        if summary['performance']['success_rate'] < self.alert_thresholds['success_rate']:
            alerts.append({
                'type': 'low_success_rate',
                'severity': 'critical',
                'message': f"Low success rate: {summary['performance']['success_rate']:.2%}",
                'value': summary['performance']['success_rate'],
                'threshold': self.alert_thresholds['success_rate']
            })
        
        # Check memory usage
        if summary['resource_usage']['avg_memory_mb'] > self.alert_thresholds['memory_mb']:
            alerts.append({
                'type': 'high_memory',
                'severity': 'warning',
                'message': f"High memory usage: {summary['resource_usage']['avg_memory_mb']:.1f}MB",
                'value': summary['resource_usage']['avg_memory_mb'],
                'threshold': self.alert_thresholds['memory_mb']
            })
        
        # Check interruption rate
        if summary['quality']['interruption_rate'] > self.alert_thresholds['interruption_rate']:
            alerts.append({
                'type': 'high_interruption_rate',
                'severity': 'warning',
                'message': f"High interruption rate: {summary['quality']['interruption_rate']:.2%}",
                'value': summary['quality']['interruption_rate'],
                'threshold': self.alert_thresholds['interruption_rate']
            })
        
        # Process alerts
        for alert in alerts:
            await self._process_alert(alert, current_time)
    
    async def _process_alert(self, alert: dict, current_time: float):
        """Process and potentially send alert."""
        alert_key = f"{alert['type']}_{alert['severity']}"
        
        # Check cooldown
        if alert_key in self.alert_cooldown:
            if current_time - self.alert_cooldown[alert_key] < self.cooldown_duration:
                return  # Still in cooldown
        
        # Send alert
        await self._send_alert(alert)
        
        # Update cooldown
        self.alert_cooldown[alert_key] = current_time
        
        # Store in history
        alert['timestamp'] = current_time
        self.alert_history.append(alert)
    
    async def _send_alert(self, alert: dict):
        """Send alert notification."""
        # Console alert
        severity_colors = {
            'info': '\033[94m',      # Blue
            'warning': '\033[93m',   # Yellow
            'critical': '\033[91m',  # Red
        }
        
        color = severity_colors.get(alert['severity'], '\033[0m')
        reset_color = '\033[0m'
        
        print(f"{color}[ALERT - {alert['severity'].upper()}] {alert['message']}{reset_color}")
        
        # Here you could add integrations with:
        # - Slack/Discord webhooks
        # - Email notifications
        # - PagerDuty/Opsgenie
        # - Custom monitoring systems
```

## 🔧 **TROUBLESHOOTING GUIDE**

### **Common Performance Issues**

#### **High Latency Troubleshooting**
```python
class LatencyTroubleshooter:
    def __init__(self, tracker: GeminiPerformanceTracker):
        self.tracker = tracker
    
    def diagnose_high_latency(self) -> dict:
        """Diagnose high latency issues."""
        diagnosis = {
            'issues_found': [],
            'recommendations': [],
            'severity': 'info'
        }
        
        # Check TTFT distribution
        ttft_values = list(self.tracker.metrics['latency']['ttft'])
        if ttft_values:
            avg_ttft = sum(ttft_values) / len(ttft_values)
            max_ttft = max(ttft_values)
            
            if avg_ttft > 1.0:  # > 1 second
                diagnosis['issues_found'].append(f"High average TTFT: {avg_ttft:.2f}s")
                diagnosis['recommendations'].extend([
                    "Consider using gemini-2.0-flash-live-001 for better latency",
                    "Reduce system instruction length",
                    "Use MEDIA_RESOLUTION_LOW for faster processing",
                    "Limit max_output_tokens to reduce generation time"
                ])
                diagnosis['severity'] = 'warning'
            
            if max_ttft > 5.0:  # > 5 seconds
                diagnosis['issues_found'].append(f"Very high max TTFT: {max_ttft:.2f}s")
                diagnosis['recommendations'].append("Check network connectivity and API quotas")
                diagnosis['severity'] = 'critical'
        
        # Check connection latency
        connection_times = list(self.tracker.metrics['latency']['connection'])
        if connection_times:
            avg_connection = sum(connection_times) / len(connection_times)
            if avg_connection > 2.0:  # > 2 seconds
                diagnosis['issues_found'].append(f"Slow connection establishment: {avg_connection:.2f}s")
                diagnosis['recommendations'].extend([
                    "Use connection pooling",
                    "Check network latency to Google APIs",
                    "Consider using regional API endpoints"
                ])
        
        return diagnosis
```

#### **Memory Leak Detection**
```python
class MemoryLeakDetector:
    def __init__(self, tracker: GeminiPerformanceTracker):
        self.tracker = tracker
        self.baseline_memory = None
        self.memory_growth_threshold = 100  # MB
    
    def detect_memory_leaks(self) -> dict:
        """Detect potential memory leaks."""
        memory_usage = list(self.tracker.metrics['resource_usage']['memory_usage_mb'])
        
        if len(memory_usage) < 10:
            return {'status': 'insufficient_data'}
        
        # Set baseline if not set
        if self.baseline_memory is None:
            self.baseline_memory = memory_usage[0]
        
        # Check for consistent growth
        recent_memory = memory_usage[-5:]  # Last 5 measurements
        memory_trend = self._calculate_trend(recent_memory)
        
        current_memory = memory_usage[-1]
        memory_growth = current_memory - self.baseline_memory
        
        result = {
            'current_memory_mb': current_memory,
            'baseline_memory_mb': self.baseline_memory,
            'memory_growth_mb': memory_growth,
            'trend': memory_trend,
            'leak_detected': False,
            'recommendations': []
        }
        
        # Detect leak
        if memory_growth > self.memory_growth_threshold and memory_trend > 0:
            result['leak_detected'] = True
            result['recommendations'].extend([
                "Implement context compression",
                "Clear audio buffers regularly",
                "Check for unclosed sessions",
                "Review object lifecycle management"
            ])
        
        return result
    
    def _calculate_trend(self, values: list) -> float:
        """Calculate trend in values (positive = increasing)."""
        if len(values) < 2:
            return 0
        
        # Simple linear trend
        n = len(values)
        sum_x = sum(range(n))
        sum_y = sum(values)
        sum_xy = sum(i * values[i] for i in range(n))
        sum_x2 = sum(i * i for i in range(n))
        
        # Linear regression slope
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        return slope
```

This comprehensive performance optimization and monitoring guide provides all the tools needed to maintain optimal Gemini model performance in production environments.