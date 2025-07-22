# GenAI Processors Core

## 🏗️ **ARCHITECTURE**
Stream-based async processing: `AsyncIterable[ProcessorPart]` → `AsyncIterable[ProcessorPart]`

## 🔧 **KEY COMPONENTS**

### **ProcessorPart**
```python
ProcessorPart(content, role="user", mimetype="text/plain", metadata={})
# Properties: .text, .bytes, .pil_image, .function_call, .function_response
```

### **Base Classes**
```python
class Processor(abc.ABC):
    async def call(self, content: AsyncIterable[ProcessorPart]) -> AsyncIterable[ProcessorPart]
    def __add__(self, other) -> ChainProcessor  # Chain with +

class PartProcessor(abc.ABC):
    async def call(self, part: ProcessorPart) -> AsyncIterable[ProcessorPart]
    def match(self, part: ProcessorPart) -> bool
    def __floordiv__(self, other) -> ParallelPartProcessor  # Parallel with //
```

## 🎯 **COMPOSITION PATTERNS**

### **Sequential Chaining**
```python
pipeline = input_processor + model_processor + output_processor
```

### **Parallel Processing**
```python
parallel = text_processor // image_processor // audio_processor
```

### **Function Decorators**
```python
@processor.processor_function
async def custom_processor(content: AsyncIterable[ProcessorPart]) -> AsyncIterable[ProcessorPart]:
    async for part in content:
        yield processed_part
```

## 📚 **ESSENTIAL PROCESSORS**

### **AI Models**
- `GenaiModel` - Gemini API wrapper
- `LiveProcessor` - Gemini Live API
- `LiveModelProcessor` - Turn-based to real-time

### **Audio**
- `PyAudioIn/Out` - Audio I/O
- `RateLimitAudio` - Natural playback speed
- `SpeechToText/TextToSpeech` - Google Cloud APIs

### **Visual**
- `VideoIn` - Camera/video capture
- `EventDetection` - Image-based event detection

### **Utilities**
- `MatchProcessor` - Pattern matching
- `JinjaTemplate` - Template processing
- `CachedPartProcessor` - Automatic caching

## 🔄 **STREAMS**
```python
# Core operations
streams.split(content, n=2) -> tuple[AsyncIterable, ...]
streams.concat(*contents) -> AsyncIterable
streams.merge(streams) -> AsyncIterable
streams.gather_stream(content) -> list
```

## 💾 **CACHING**
```python
cache = InMemoryCache(ttl_hours=12, max_items=1000)
cached_processor = CachedPartProcessor(processor, default_cache=cache)
```

## 🐛 **DEBUG**
```python
yield processor.debug("Debug message")
yield processor.status("Status update")
```