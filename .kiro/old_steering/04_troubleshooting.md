# Troubleshooting

## 🐛 **COMMON ISSUES**

### **Connection Problems**
```python
# Retry with exponential backoff
async def robust_connect(model, config, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await client.aio.live.connect(model=model, config=config)
        except ConnectionError:
            if attempt == max_retries - 1: raise
            await asyncio.sleep(2 ** attempt)
```

### **Audio Issues**
- **No audio input**: Check microphone permissions
- **Choppy playback**: Increase buffer size or reduce sample rate
- **High latency**: Use MEDIA_RESOLUTION_LOW
- **Echo/feedback**: Implement echo cancellation

### **Function Call Errors**
```python
# Proper error handling
async def safe_function_call(session, function_response):
    try:
        await session.send_tool_response(function_responses=[function_response])
    except Exception as e:
        logger.error(f"Function call failed: {e}")
        # Send error response
        await session.send_tool_response(function_responses=[
            types.FunctionResponse(id=function_response.id, name=function_response.name, 
                                 response={'error': str(e)})
        ])
```

## ⚡ **PERFORMANCE OPTIMIZATION**

### **Latency Reduction**
- Use `gemini-2.0-flash-live-001` for stability
- Set `media_resolution=MEDIA_RESOLUTION_LOW`
- Optimize VAD sensitivity
- Implement connection pooling

### **Memory Management**
```python
# Context compression
async def compress_context(self):
    if len(self.context_buffer) > 800:
        # Keep recent 500 items, compress older ones
        old_items = list(self.context_buffer)[:300]
        summary = self._create_summary(old_items)
        self.context_buffer = collections.deque([summary] + list(self.context_buffer)[300:])
```

### **Error Recovery**
```python
# Graceful degradation
async def handle_model_error(self, error):
    if "rate_limit" in str(error).lower():
        await asyncio.sleep(60)  # Wait 1 minute
        return await self.retry_request()
    elif "quota" in str(error).lower():
        logger.error("Quota exceeded - switching to fallback")
        return await self.use_fallback_model()
    else:
        raise error
```

## 📊 **MONITORING**

### **Key Metrics**
- **TTFT** (Time to First Token): < 500ms
- **Audio latency**: < 200ms
- **Success rate**: > 95%
- **Memory usage**: < 500MB

### **Logging**
```python
# Structured logging
logger.info("Session started", extra={
    'session_id': session_id,
    'model': model_name,
    'user_id': user_id,
    'timestamp': time.time()
})
```

## 🔧 **DEBUG TOOLS**

### **Audio Debug**
```python
# Save audio for debugging
def save_debug_audio(audio_data, filename):
    with wave.open(f"debug_{filename}.wav", 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(audio_data)
```

### **State Debug**
```python
# State machine debugging
def log_state_transition(self, from_state, action, to_state):
    logger.debug("State transition", extra={
        'from_state': from_state.value,
        'action': action.value,
        'to_state': to_state.value,
        'timestamp': time.time()
    })
```