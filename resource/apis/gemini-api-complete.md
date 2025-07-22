# Gemini API - Complete API Specification

## 🔵 **GEMINI API - ESPECIFICAÇÃO COMPLETA DA API**

Este arquivo documenta **todas** as capacidades, endpoints, padrões e limitações da API do Google Gemini, complementando as especificações dos modelos.

---

## 📊 **API OVERVIEW**

### **🎯 API Architecture**
```yaml
API Name: "Google Generative AI API (Gemini)"
Base URL: "https://generativelanguage.googleapis.com"
Current Version: "v1beta" (stable), "v1alpha" (preview features)
Protocol: "REST + WebSocket (Live API)"
Authentication: "API Key, OAuth 2.0, Service Account"
SDKs Available: ["Python", "Node.js", "Go", "REST"]

API Categories:
  completion_api: "Text/multimodal generation"
  live_api: "Real-time bidirectional streaming"
  files_api: "File upload and management"
  models_api: "Model information and capabilities"
  tuning_api: "Model fine-tuning (limited)"
```

### **🔑 Authentication Methods**
```yaml
API Key Authentication:
  method: "API Key in header or query parameter"
  header: "x-goog-api-key: YOUR_API_KEY"
  query: "?key=YOUR_API_KEY"
  scope: "Full API access"
  recommended_for: "Development, simple applications"

OAuth 2.0:
  method: "Bearer token"
  header: "Authorization: Bearer ACCESS_TOKEN"
  scopes: ["https://www.googleapis.com/auth/generative-language"]
  recommended_for: "User-facing applications"

Service Account:
  method: "JWT token"
  header: "Authorization: Bearer JWT_TOKEN"
  recommended_for: "Server-to-server, production"
```

---

## 🎙️ **LIVE API (Real-time Streaming)**

### **🚀 WebSocket Connection**
```yaml
Endpoint: "wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1alpha.GenerativeService.StreamGenerateContent"
Protocol: "WebSocket with Protocol Buffers"
Connection Type: "Bidirectional streaming"
Session Management: "Stateful connections"

Connection Flow:
  1. "Establish WebSocket connection"
  2. "Send LiveConnectConfig"
  3. "Receive connection confirmation"
  4. "Bidirectional message exchange"
  5. "Graceful connection termination"
```

#### **Connection Configuration**
```python
# Complete Live API connection setup
import google.genai as genai
from google.genai import types

async def establish_live_connection():
    client = genai.Client(api_key=api_key)
    
    config = types.LiveConnectConfig(
        # Response configuration
        response_modalities=["AUDIO"],  # or ["TEXT"] or ["AUDIO", "TEXT"]
        
        # Model and system setup
        model="gemini-live-2.5-flash-preview",
        system_instruction="Your system prompt here",
        
        # Audio configuration
        speech_config=types.SpeechConfig(
            language_code='pt-BR',
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(
                    voice_name='Kore'
                )
            )
        ),
        
        # Input configuration
        realtime_input_config=types.RealtimeInputConfig(
            turn_coverage='TURN_INCLUDES_ALL_INPUT',
            automatic_activity_detection=types.AutomaticActivityDetection(
                disabled=False,
                start_of_speech_sensitivity=types.StartSensitivity.START_SENSITIVITY_MEDIUM,
                end_of_speech_sensitivity=types.EndSensitivity.END_SENSITIVITY_MEDIUM,
                prefix_padding_ms=20,
                silence_duration_ms=100
            )
        ),
        
        # Generation configuration
        generation_config=types.GenerationConfig(
            media_resolution=types.MediaResolution.MEDIA_RESOLUTION_MEDIUM,
            temperature=0.7,
            max_output_tokens=2048
        ),
        
        # Tools and functions
        tools=[
            types.Tool(function_declarations=[
                types.FunctionDeclaration(
                    name="function_name",
                    description="Function description",
                    behavior="NON_BLOCKING",  # or "BLOCKING"
                    parameters={
                        "type": "object",
                        "properties": {
                            "param1": {"type": "string", "description": "Parameter description"}
                        },
                        "required": ["param1"]
                    }
                )
            ])
        ],
        
        # Transcription
        output_audio_transcription=types.OutputAudioTranscription(),
        input_audio_transcription=types.InputAudioTranscription()
    )
    
    # Establish connection
    session = await client.aio.live.connect(config=config)
    return session
```

### **📨 Message Types**

#### **Input Messages**
```python
# Audio input
await session.send_realtime_input(
    audio=types.Blob(
        data=audio_bytes,
        mime_type="audio/pcm;rate=16000"
    )
)

# Text input
await session.send_realtime_input(
    text="Your text message here"
)

# Image input
await session.send_realtime_input(
    image=types.Blob(
        data=image_bytes,
        mime_type="image/jpeg"
    )
)

# Video input
await session.send_realtime_input(
    video=types.Blob(
        data=video_bytes,
        mime_type="video/mp4"
    )
)

# Activity control
await session.send_realtime_input(
    activity_start=types.ActivityStart()
)

await session.send_realtime_input(
    activity_end=types.ActivityEnd()
)

# Function responses
await session.send_tool_response(
    function_responses=[
        types.FunctionResponse(
            id="function_call_id",
            name="function_name",
            response={"result": "function result"},
            scheduling=types.FunctionResponseScheduling.WHEN_IDLE
        )
    ]
)
```

#### **Output Messages**
```python
# Receiving messages
async for response in session.receive():
    # Audio output
    if response.data:
        audio_data = response.data
        # Play audio
    
    # Text output
    if response.text:
        text_content = response.text
        # Display text
    
    # Function calls
    if response.tool_call:
        function_call = response.tool_call
        function_name = function_call.name
        function_id = function_call.id
        function_args = function_call.args
        # Execute function
    
    # Server content (metadata)
    if response.server_content:
        server_content = response.server_content
        
        # Interruption handling
        if server_content.interrupted:
            # Handle interruption
            pass
        
        # Turn completion
        if server_content.model_turn:
            # Model finished speaking
            pass
        
        # Transcriptions
        if server_content.input_transcription:
            input_text = server_content.input_transcription.text
            is_final = server_content.input_transcription.is_final
        
        if server_content.output_transcription:
            output_text = server_content.output_transcription.text
    
    # Usage metadata
    if response.usage_metadata:
        usage = response.usage_metadata
        total_tokens = usage.total_token_count
        # Track usage
```

### **🎛️ Advanced Live API Features**

#### **Voice Activity Detection (VAD)**
```python
# VAD Configuration Options
vad_config = types.AutomaticActivityDetection(
    disabled=False,  # Enable/disable VAD
    
    # Sensitivity settings
    start_of_speech_sensitivity=types.StartSensitivity.START_SENSITIVITY_HIGH,  # HIGH, MEDIUM, LOW
    end_of_speech_sensitivity=types.EndSensitivity.END_SENSITIVITY_MEDIUM,
    
    # Timing settings
    prefix_padding_ms=50,      # Audio before speech start
    silence_duration_ms=200    # Silence duration to end speech
)

# Manual activity control (alternative to VAD)
await session.send_realtime_input(activity_start=types.ActivityStart())
# Send audio chunks
await session.send_realtime_input(activity_end=types.ActivityEnd())
```

#### **Function Calling Behaviors**
```python
# Function behaviors
BLOCKING_FUNCTION = types.FunctionDeclaration(
    name="blocking_function",
    description="Function that blocks model generation",
    behavior="BLOCKING",  # Model waits for response
    parameters=function_schema
)

NON_BLOCKING_FUNCTION = types.FunctionDeclaration(
    name="non_blocking_function", 
    description="Function that doesn't block model",
    behavior="NON_BLOCKING",  # Model continues while function executes
    parameters=function_schema
)

# Function response scheduling
await session.send_tool_response(
    function_responses=[
        types.FunctionResponse(
            id=function_id,
            name=function_name,
            response=result,
            scheduling=types.FunctionResponseScheduling.WHEN_IDLE  # WHEN_IDLE, INTERRUPT, SILENT
        )
    ]
)
```

#### **Multi-modal Input Handling**
```python
# Simultaneous multi-modal input
await session.send_realtime_input(
    audio=types.Blob(data=audio_data, mime_type="audio/pcm;rate=16000"),
    image=types.Blob(data=image_data, mime_type="image/jpeg"),
    text="Analyze this audio and image together"
)

# Sequential multi-modal input
await session.send_realtime_input(image=image_blob)
await session.send_realtime_input(text="What do you see in this image?")
await session.send_realtime_input(audio=audio_blob)
```

---

## 💬 **COMPLETION API (REST)**

### **🌐 REST Endpoints**

#### **Generate Content**
```yaml
Endpoint: "POST /v1beta/models/{model}/generateContent"
Purpose: "Single-turn content generation"
Input: "Text, images, audio, video"
Output: "Generated content"
Streaming: "Optional via generateContentStream"
```

```python
# Basic completion
import google.generativeai as genai

genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-2.5-flash')

# Text generation
response = model.generate_content("Your prompt here")
print(response.text)

# Streaming generation
response = model.generate_content("Your prompt here", stream=True)
for chunk in response:
    print(chunk.text, end='')

# Multi-modal generation
response = model.generate_content([
    "Describe this image:",
    genai.upload_file("path/to/image.jpg")
])
```

#### **Chat Completions**
```python
# Multi-turn conversation
chat = model.start_chat(history=[])

response = chat.send_message("Hello, how are you?")
print(response.text)

response = chat.send_message("What did I just ask you?")
print(response.text)

# Chat with history
chat = model.start_chat(history=[
    {"role": "user", "parts": ["Hello"]},
    {"role": "model", "parts": ["Hi there! How can I help you today?"]}
])
```

#### **Function Calling**
```python
# Define functions
functions = [
    genai.FunctionDeclaration(
        name="get_weather",
        description="Get weather information for a location",
        parameters={
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "City name"},
                "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]}
            },
            "required": ["location"]
        }
    )
]

# Create model with tools
model = genai.GenerativeModel(
    'gemini-2.5-flash',
    tools=[genai.Tool(function_declarations=functions)]
)

# Generate with function calling
response = model.generate_content("What's the weather in São Paulo?")

# Handle function calls
for part in response.parts:
    if part.function_call:
        function_name = part.function_call.name
        function_args = dict(part.function_call.args)
        
        # Execute function
        result = execute_function(function_name, function_args)
        
        # Send result back
        response = model.generate_content([
            genai.Part.from_function_response(
                name=function_name,
                response=result
            )
        ])
```

### **📊 Request/Response Formats**

#### **Request Structure**
```json
{
  "contents": [
    {
      "role": "user",
      "parts": [
        {"text": "Your prompt here"},
        {
          "inline_data": {
            "mime_type": "image/jpeg",
            "data": "base64_encoded_image"
          }
        }
      ]
    }
  ],
  "generationConfig": {
    "temperature": 0.7,
    "maxOutputTokens": 2048,
    "topP": 0.9,
    "topK": 40
  },
  "safetySettings": [
    {
      "category": "HARM_CATEGORY_HARASSMENT",
      "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    }
  ]
}
```

#### **Response Structure**
```json
{
  "candidates": [
    {
      "content": {
        "role": "model",
        "parts": [
          {"text": "Generated response text"}
        ]
      },
      "finishReason": "STOP",
      "safetyRatings": [
        {
          "category": "HARM_CATEGORY_HARASSMENT",
          "probability": "NEGLIGIBLE"
        }
      ]
    }
  ],
  "usageMetadata": {
    "promptTokenCount": 123,
    "candidatesTokenCount": 456,
    "totalTokenCount": 579
  }
}
```

---

## 📁 **FILES API**

### **📤 File Upload and Management**
```python
# Upload file
uploaded_file = genai.upload_file("path/to/file.pdf")
print(f"File uploaded: {uploaded_file.name}")

# List files
files = genai.list_files()
for file in files:
    print(f"File: {file.name}, Size: {file.size_bytes}")

# Get file info
file_info = genai.get_file("files/file_id")
print(f"File state: {file_info.state}")

# Delete file
genai.delete_file("files/file_id")

# Use uploaded file in generation
response = model.generate_content([
    "Summarize this document:",
    uploaded_file
])
```

### **📋 Supported File Types**
```yaml
Documents:
  - "PDF (.pdf)"
  - "Text (.txt)"
  - "Markdown (.md)"
  - "HTML (.html)"
  - "CSV (.csv)"

Images:
  - "JPEG (.jpg, .jpeg)"
  - "PNG (.png)"
  - "WebP (.webp)"
  - "HEIC (.heic)"
  - "HEIF (.heif)"

Audio:
  - "WAV (.wav)"
  - "MP3 (.mp3)"
  - "AIFF (.aiff)"
  - "AAC (.aac)"
  - "OGG (.ogg)"
  - "FLAC (.flac)"

Video:
  - "MP4 (.mp4)"
  - "MPEG (.mpeg)"
  - "MOV (.mov)"
  - "AVI (.avi)"
  - "FLV (.flv)"
  - "MPG (.mpg)"
  - "WebM (.webm)"
  - "WMV (.wmv)"
  - "3GPP (.3gpp)"

Limits:
  max_file_size: "2GB"
  max_files_per_request: "16"
  retention_period: "48 hours"
```

---

## 🔧 **MODELS API**

### **📋 Model Information**
```python
# List available models
models = genai.list_models()
for model in models:
    print(f"Model: {model.name}")
    print(f"Description: {model.description}")
    print(f"Input token limit: {model.input_token_limit}")
    print(f"Output token limit: {model.output_token_limit}")
    print(f"Supported methods: {model.supported_generation_methods}")

# Get specific model info
model_info = genai.get_model("models/gemini-2.5-flash")
print(f"Model version: {model_info.version}")
print(f"Temperature range: {model_info.temperature}")
```

### **🎛️ Model Capabilities**
```python
# Check model capabilities
def check_model_capabilities(model_name: str):
    model_info = genai.get_model(f"models/{model_name}")
    
    capabilities = {
        'text_generation': 'generateContent' in model_info.supported_generation_methods,
        'chat': 'generateContent' in model_info.supported_generation_methods,
        'function_calling': hasattr(model_info, 'function_calling_config'),
        'multimodal': model_info.input_token_limit > 30000,  # Heuristic
        'streaming': 'generateContentStream' in model_info.supported_generation_methods
    }
    
    return capabilities
```

---

## 🚦 **RATE LIMITS & QUOTAS**

### **📊 API-Level Rate Limits**
```yaml
Global Limits:
  requests_per_minute: "Varies by model and tier"
  requests_per_day: "Varies by model and tier"
  concurrent_requests: "10 (free tier), 1000 (paid tier)"

Live API Specific:
  concurrent_sessions: "1 (free tier), 100 (paid tier)"
  session_duration: "15 minutes max (audio), 2 minutes (video)"
  websocket_connections: "Limited by concurrent sessions"

Files API:
  uploads_per_minute: "60"
  uploads_per_day: "1000"
  storage_duration: "48 hours"
  max_file_size: "2GB"

Models API:
  list_requests_per_minute: "1000"
  get_requests_per_minute: "1000"
```

### **🔍 Quota Monitoring**
```python
# Monitor usage (conceptual - actual implementation varies)
class GeminiUsageMonitor:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.usage_tracking = {}
    
    def track_request(self, model: str, tokens_used: int, request_type: str):
        """Track API usage"""
        today = datetime.now().strftime('%Y-%m-%d')
        key = f"{model}_{today}"
        
        if key not in self.usage_tracking:
            self.usage_tracking[key] = {
                'requests': 0,
                'tokens': 0,
                'audio_minutes': 0
            }
        
        self.usage_tracking[key]['requests'] += 1
        self.usage_tracking[key]['tokens'] += tokens_used
    
    def check_quota_status(self, model: str) -> dict:
        """Check current quota status"""
        # This would integrate with actual Google Cloud monitoring
        return {
            'requests_used': 0,
            'requests_limit': 1500,
            'tokens_used': 0,
            'tokens_limit': 1000000,
            'percentage_used': 0.0
        }
```

---

## 🛡️ **SAFETY & CONTENT FILTERING**

### **🔒 Safety Settings**
```python
# Configure safety settings
safety_settings = [
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH", 
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    }
]

# Apply to model
model = genai.GenerativeModel(
    'gemini-2.5-flash',
    safety_settings=safety_settings
)

# Handle blocked content
try:
    response = model.generate_content("Your prompt")
    print(response.text)
except genai.types.BlockedPromptException:
    print("Content was blocked by safety filters")
except genai.types.StopCandidateException:
    print("Generation was stopped")
```

### **📋 Safety Categories**
```yaml
Available Categories:
  HARM_CATEGORY_HARASSMENT: "Harassment content"
  HARM_CATEGORY_HATE_SPEECH: "Hate speech"
  HARM_CATEGORY_SEXUALLY_EXPLICIT: "Sexually explicit content"
  HARM_CATEGORY_DANGEROUS_CONTENT: "Dangerous content"

Threshold Levels:
  BLOCK_NONE: "Don't block any content"
  BLOCK_ONLY_HIGH: "Block only high-probability harmful content"
  BLOCK_MEDIUM_AND_ABOVE: "Block medium and high-probability harmful content"
  BLOCK_LOW_AND_ABOVE: "Block low, medium, and high-probability harmful content"
```

---

## 🚨 **ERROR HANDLING**

### **📋 Common Error Codes**
```yaml
HTTP Status Codes:
  400: "Bad Request - Invalid request format"
  401: "Unauthorized - Invalid API key"
  403: "Forbidden - Insufficient permissions"
  404: "Not Found - Model or resource not found"
  429: "Too Many Requests - Rate limit exceeded"
  500: "Internal Server Error - Google server error"
  503: "Service Unavailable - Temporary service issue"

Gemini-Specific Errors:
  INVALID_ARGUMENT: "Invalid request parameters"
  PERMISSION_DENIED: "API key lacks required permissions"
  RESOURCE_EXHAUSTED: "Quota exceeded"
  INTERNAL: "Internal Google error"
  UNAVAILABLE: "Service temporarily unavailable"
```

### **🛠️ Error Handling Patterns**
```python
import time
import random
from google.generativeai.types import (
    BlockedPromptException,
    StopCandidateException,
    BrokenResponseError
)

class RobustGeminiClient:
    def __init__(self, api_key: str, max_retries: int = 3):
        self.api_key = api_key
        self.max_retries = max_retries
        genai.configure(api_key=api_key)
    
    async def generate_with_retry(self, model_name: str, prompt: str, **kwargs):
        """Generate content with retry logic"""
        model = genai.GenerativeModel(model_name)
        
        for attempt in range(self.max_retries):
            try:
                response = model.generate_content(prompt, **kwargs)
                return response.text
                
            except BlockedPromptException:
                # Content blocked - don't retry
                return "Content blocked by safety filters"
                
            except StopCandidateException:
                # Generation stopped - don't retry
                return "Generation stopped by model"
                
            except BrokenResponseError:
                # Malformed response - retry
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise
                
            except Exception as e:
                error_str = str(e).lower()
                
                if "429" in error_str or "quota" in error_str:
                    # Rate limit - exponential backoff
                    wait_time = (2 ** attempt) + random.uniform(0, 1)
                    await asyncio.sleep(wait_time)
                    continue
                    
                elif "503" in error_str or "unavailable" in error_str:
                    # Service unavailable - retry with backoff
                    wait_time = (2 ** attempt) + random.uniform(0, 1)
                    await asyncio.sleep(wait_time)
                    continue
                    
                elif "500" in error_str or "internal" in error_str:
                    # Internal error - retry
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(2 ** attempt)
                        continue
                    raise
                    
                else:
                    # Other errors - don't retry
                    raise
        
        raise Exception(f"Failed after {self.max_retries} attempts")
```

---

## 📊 **PERFORMANCE OPTIMIZATION**

### **⚡ Best Practices**
```python
class GeminiOptimizer:
    def __init__(self):
        self.cache = {}
        self.request_times = collections.deque(maxlen=100)
    
    def optimize_prompt(self, prompt: str) -> str:
        """Optimize prompt for better performance"""
        # Remove redundant words
        optimized = self._remove_redundancy(prompt)
        
        # Limit length if too long
        if len(optimized) > 8000:  # ~2000 tokens
            optimized = optimized[:8000] + "..."
        
        return optimized
    
    def batch_requests(self, prompts: list[str], model_name: str) -> list[str]:
        """Batch multiple requests for efficiency"""
        model = genai.GenerativeModel(model_name)
        results = []
        
        # Process in batches of 5
        for i in range(0, len(prompts), 5):
            batch = prompts[i:i+5]
            batch_results = []
            
            for prompt in batch:
                try:
                    response = model.generate_content(prompt)
                    batch_results.append(response.text)
                except Exception as e:
                    batch_results.append(f"Error: {e}")
            
            results.extend(batch_results)
            
            # Rate limiting between batches
            time.sleep(0.1)
        
        return results
    
    def cache_response(self, prompt: str, response: str, ttl: int = 3600):
        """Cache responses to reduce API calls"""
        import hashlib
        
        cache_key = hashlib.md5(prompt.encode()).hexdigest()
        self.cache[cache_key] = {
            'response': response,
            'timestamp': time.time(),
            'ttl': ttl
        }
    
    def get_cached_response(self, prompt: str) -> str | None:
        """Get cached response if available"""
        import hashlib
        
        cache_key = hashlib.md5(prompt.encode()).hexdigest()
        
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if time.time() - cached['timestamp'] < cached['ttl']:
                return cached['response']
            else:
                del self.cache[cache_key]
        
        return None
```

---

## 🔗 **SDK & INTEGRATION**

### **🐍 Python SDK**
```bash
# Installation
pip install google-generativeai

# Optional dependencies
pip install google-generativeai[dev]  # Development tools
pip install google-generativeai[all]  # All optional dependencies
```

### **📚 SDK Usage Patterns**
```python
# Basic setup
import google.generativeai as genai
import os

# Configure API key
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

# List available models
for model in genai.list_models():
    if 'generateContent' in model.supported_generation_methods:
        print(f"Available model: {model.name}")

# Create model instance
model = genai.GenerativeModel('gemini-2.5-flash')

# Generate content
response = model.generate_content("Hello, world!")
print(response.text)
```

### **🌐 REST API Direct Usage**
```python
import requests
import json

class DirectGeminiAPI:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://generativelanguage.googleapis.com"
    
    def generate_content(self, model: str, prompt: str) -> dict:
        """Direct REST API call"""
        url = f"{self.base_url}/v1beta/models/{model}:generateContent"
        
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key
        }
        
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}]
                }
            ]
        }
        
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        
        return response.json()
```

---

## 📚 **RESOURCES & DOCUMENTATION**

### **🔗 Official Documentation**
- **Main API Docs**: [ai.google.dev/api](https://ai.google.dev/api)
- **Live API Guide**: [ai.google.dev/api/live](https://ai.google.dev/api/live)
- **Python SDK**: [ai.google.dev/tutorials/python_quickstart](https://ai.google.dev/tutorials/python_quickstart)
- **REST API Reference**: [ai.google.dev/api/rest](https://ai.google.dev/api/rest)

### **🛠️ Development Tools**
- **API Explorer**: [ai.google.dev/api-explorer](https://ai.google.dev/api-explorer)
- **Prompt Gallery**: [ai.google.dev/prompts](https://ai.google.dev/prompts)
- **Cookbook**: [ai.google.dev/examples](https://ai.google.dev/examples)

### **📊 Monitoring & Support**
- **Google Cloud Console**: [console.cloud.google.com](https://console.cloud.google.com)
- **Status Page**: [status.cloud.google.com](https://status.cloud.google.com)
- **Support**: [cloud.google.com/support](https://cloud.google.com/support)

---

**🔵 GEMINI API COMPLETE - Sua referência definitiva para a API Gemini**

*Última atualização: 2025-01-22*
*Próxima revisão: Mensal (toda primeira segunda-feira do mês)*