# Real-time Patterns

## 🎙️ **AUDIO PROCESSING**

### **Pipeline Setup**
```python
class AudioPipeline:
    def __init__(self):
        self.input_rate = 16000   # Gemini input
        self.output_rate = 24000  # Gemini output
        self.chunk_size = 1024
        
    async def start_recording(self, callback):
        self.input_stream = pyaudio.open(rate=self.input_rate, input=True, 
                                       stream_callback=self._input_callback)
    
    async def start_playback(self):
        self.output_stream = pyaudio.open(rate=self.output_rate, output=True)
```

### **Rate Limiting**
```python
class RateLimiter:
    async def process_audio_stream(self, audio_queue, output_callback):
        target_time = time.time()
        while True:
            chunk = await audio_queue.get()
            duration = len(chunk) / (2 * self.sample_rate)  # 16-bit
            
            wait_time = max(0, target_time - time.time())
            if wait_time > 0: await asyncio.sleep(wait_time)
            
            await output_callback(chunk)
            target_time += duration
```

## 🔄 **STATE MANAGEMENT**

### **State Machine**
```python
class AgentState(enum.Enum):
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    SPEAKING = "speaking"
    INTERRUPTED = "interrupted"

class StateMachine:
    async def transition(self, action, metadata=None):
        if (self.current_state, action) in self.valid_transitions:
            self.current_state = self.valid_transitions[(self.current_state, action)]
            await self._execute_handlers(action, metadata)
```

## 🧠 **FUNCTION CALLING**

### **Advanced Patterns**
```python
async def handle_function_call(self, function_call):
    if function_call.name == "think":
        await self._handle_think(function_call.id, function_call.args)
    elif function_call.name == "change_state":
        await self._handle_state_change(function_call.id, function_call.args)
    
    # Send response
    await session.send_tool_response(function_responses=[
        types.FunctionResponse(id=function_call.id, name=function_call.name, 
                             response=result, scheduling=types.FunctionResponseScheduling.WHEN_IDLE)
    ])
```

### **Scheduling Types**
- `WHEN_IDLE` - Wait for natural pause
- `INTERRUPT` - Interrupt current speech
- `SILENT` - No audio response
- `IMMEDIATE` - Send immediately

## 🎯 **INTERRUPTION HANDLING**
```python
async def handle_interruption(self, response):
    if response.server_content.interrupted:
        self.stop_current_playback()
        self.audio_queue.clear()
        self.current_generation = None
        await self.state_machine.transition(AgentAction.INTERRUPT)
```

## 💭 **CONTEXT MANAGEMENT**
```python
class ContextManager:
    def __init__(self, max_tokens=32000):
        self.context_buffer = collections.deque(maxlen=1000)
        self.current_tokens = 0
        
    async def add_context(self, content, tokens):
        if self.current_tokens + tokens > self.max_tokens:
            await self._compress_context()
        self.context_buffer.append({'content': content, 'tokens': tokens})
```