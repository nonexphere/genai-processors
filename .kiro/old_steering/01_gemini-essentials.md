# Gemini Essentials

## 🎯 **MODELS FOR LEONIDAS**

### **Primary: `gemini-2.0-flash-live-001`** (Production)
- Real-time bidirectional streaming
- Function calling with NON_BLOCKING behavior
- Portuguese support with Kore voice
- 32K context, 15min sessions

### **Event Detection: `gemini-2.5-flash-lite-preview-06-17`**
- Ultra-low latency for visual events
- Structured enum responses
- Cost-effective for frequent calls

## 🔧 **LIVE API PATTERNS**

### **Basic Connection**
```python
async with client.aio.live.connect(model="gemini-2.0-flash-live-001", config=config) as session:
    # Send audio
    await session.send_realtime_input(audio=types.Blob(data=audio_data, mime_type="audio/pcm;rate=16000"))
    
    # Receive responses
    async for response in session.receive():
        if response.data: play_audio(response.data)
        if response.tool_call: await handle_function_call(response.tool_call)
```

### **Function Calling**
```python
tools = [types.Tool(function_declarations=[
    types.FunctionDeclaration(name="think", description="Reasoning process", behavior="NON_BLOCKING"),
    types.FunctionDeclaration(name="change_state", description="State management", behavior="NON_BLOCKING")
])]
```

### **Error Handling**
```python
async def robust_session(model, config, max_retries=3):
    for attempt in range(max_retries):
        try:
            async with client.aio.live.connect(model=model, config=config) as session:
                async for response in session.receive():
                    yield response
            break
        except ConnectionError:
            if attempt == max_retries - 1: raise
            await asyncio.sleep(2 ** attempt)
```

## ⚡ **PERFORMANCE**
- **Latency**: Use MEDIA_RESOLUTION_LOW for speed
- **Quality**: Use MEDIA_RESOLUTION_HIGH for quality
- **VAD**: MEDIUM sensitivity for balanced detection
- **Interruption**: Handle `response.server_content.interrupted`

## 🌍 **PORTUGUESE CONFIG**
```python
speech_config={
    'language_code': 'pt-BR',
    'voice_config': {'prebuilt_voice_config': {'voice_name': 'Kore'}}
}
```