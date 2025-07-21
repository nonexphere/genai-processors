# Gemini Models Complete Reference & Steering Rules

## **COMPLETE GEMINI MODELS DIAGNOSTIC**

This steering rule provides comprehensive context about all available Gemini models, their capabilities, configurations, and optimal usage patterns for the Leonidas project and similar real-time AI applications.

## **GEMINI LIVE API MODELS**

### **1. Gemini 2.5 Flash Live Preview (`gemini-live-2.5-flash-preview`)**
**Architecture**: Half-cascade (native audio input + text-to-speech output)
**Primary Use**: Production-ready real-time conversations with tool support

#### **Core Capabilities**
- ✅ **Real-time bidirectional streaming** via WebSockets
- ✅ **Voice Activity Detection (VAD)** with configurable sensitivity
- ✅ **Function calling** with async non-blocking behavior
- ✅ **Code execution** support
- ✅ **Google Search** integration
- ✅ **URL context** processing
- ✅ **Multi-language support** (24+ languages)
- ✅ **Audio transcription** (input/output)
- ✅ **Interruption handling** with graceful recovery

#### **Technical Specifications**
```python
# Audio Configuration
INPUT_SAMPLE_RATE = 16000  # Hz (auto-resampled if different)
OUTPUT_SAMPLE_RATE = 24000  # Hz (fixed)
AUDIO_FORMAT = "PCM 16-bit little-endian"
CONTEXT_WINDOW = 32000  # tokens
SESSION_DURATION = 15  # minutes (audio-only), 2 minutes (audio+video)

# Supported Response Modalities
RESPONSE_MODALITIES = ["TEXT", "AUDIO"]  # One per session
```

#### **Voice Options**
Available voices: `Puck`, `Charon`, `Kore`, `Fenrir`, `Aoede`, `Leda`, `Orus`, `Zephyr`

#### **Configuration Example**
```python
config = types.LiveConnectConfig(
    response_modalities=["AUDIO"],
    tools=[function_declarations],
    system_instruction="Your system prompt here",
    output_audio_transcription={},
    realtime_input_config=types.RealtimeInputConfig(
        turn_coverage='TURN_INCLUDES_ALL_INPUT'
    ),
    speech_config={
        'language_code': 'pt-BR',
        'voice_config': {'prebuilt_voice_config': {'voice_name': 'Kore'}}
    },
    generation_config=types.GenerationConfig(
        media_resolution=types.MediaResolution.MEDIA_RESOLUTION_MEDIUM
    )
)
```

### **2. Gemini 2.0 Flash Live (`gemini-2.0-flash-live-001`)**
**Architecture**: Half-cascade (native audio input + text-to-speech output)
**Primary Use**: Stable production deployment with proven reliability

#### **Core Capabilities**
- ✅ **All capabilities of 2.5 Flash Live Preview**
- ✅ **Enhanced stability** for production environments
- ✅ **Optimized performance** for high-volume applications
- ✅ **Better tool integration** reliability

#### **Key Differences from 2.5 Preview**
- More stable function calling behavior
- Better error recovery mechanisms
- Optimized for production workloads
- Same technical specifications as 2.5 Preview

### **3. Gemini 2.5 Flash Native Audio Dialog (`gemini-2.5-flash-preview-native-audio-dialog`)**
**Architecture**: Native audio (end-to-end audio processing)
**Primary Use**: Most natural conversational experiences

#### **Core Capabilities**
- ✅ **Native audio processing** (most natural speech)
- ✅ **Affective dialog** (emotion-aware responses)
- ✅ **Proactive audio** (selective response behavior)
- ✅ **Enhanced multilingual** performance
- ✅ **Function calling** (basic support)
- ⚠️ **Limited tool support** (no code execution, no URL context)

#### **Technical Specifications**
```python
CONTEXT_WINDOW = 128000  # tokens (4x larger than half-cascade)
SESSION_DURATION = 15  # minutes (audio-only), 2 minutes (audio+video)
VOICE_SELECTION = "Automatic"  # Cannot set explicit voice
LANGUAGE_DETECTION = "Automatic"  # Cannot set explicit language
```

#### **Advanced Features**
```python
# Affective Dialog Configuration
config = types.LiveConnectConfig(
    response_modalities=["AUDIO"],
    enable_affective_dialog=True,  # Emotion-aware responses
    proactivity={'proactive_audio': True}  # Selective responses
)

# Requires API version v1alpha
client = genai.Client(http_options={"api_version": "v1alpha"})
```

### **4. Gemini 2.5 Flash Native Audio Thinking (`gemini-2.5-flash-exp-native-audio-thinking-dialog`)**
**Architecture**: Native audio with thinking capabilities
**Primary Use**: Complex reasoning with audible thought process

#### **Core Capabilities**
- ✅ **All native audio capabilities**
- ✅ **Thinking out loud** (audible reasoning process)
- ✅ **Enhanced problem-solving** approach
- ⚠️ **No function calling** support
- ⚠️ **Experimental status** (subject to changes)

## 🎯 **GEMINI TTS MODELS**

### **1. Gemini 2.5 Flash TTS Preview (`gemini-2.5-flash-preview-tts`)**
**Primary Use**: High-quality text-to-speech with style control

#### **Core Capabilities**
- ✅ **Single speaker** TTS
- ✅ **Multi-speaker** TTS (up to 2 speakers)
- ✅ **Style control** via natural language commands
- ✅ **30 voice options** available
- ✅ **24 language support**
- ✅ **Controllable speech** (tone, pace, accent, style)

#### **Voice Options (30 Available)**
```python
VOICES = [
    # Bright/Energetic
    "Zephyr", "Puck", "Autonoe", "Laomedeia",
    
    # Professional/Clear
    "Kore", "Orus", "Iapetus", "Erinome", "Alnilam",
    
    # Warm/Friendly
    "Charon", "Leda", "Callirrhoe", "Achird", "Sulafat",
    
    # Smooth/Mature
    "Fenrir", "Aoede", "Algieba", "Despina", "Achernar", "Gacrux",
    
    # Specialized
    "Enceladus",  # Breathy
    "Algenib",    # Gravelly
    "Schedar",    # Even
    "Zubenelgenubi", # Casual
    "Sadachbia",  # Lively
    "Sadaltager", # Knowledgeable
    "Vindemiatrix", # Gentle
    "Rasalgethi", # Informative
    "Umbriel",    # Calm
    "Pulcherrima" # Forward
]
```

#### **Multi-Speaker Configuration**
```python
config = types.GenerateContentConfig(
    response_modalities=["AUDIO"],
    speech_config=types.SpeechConfig(
        multi_speaker_voice_config=types.MultiSpeakerVoiceConfig(
            speaker_voice_configs=[
                types.SpeakerVoiceConfig(
                    speaker='Speaker1',
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name='Kore'
                        )
                    )
                ),
                types.SpeakerVoiceConfig(
                    speaker='Speaker2',
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name='Puck'
                        )
                    )
                )
            ]
        )
    )
)
```

### **2. Gemini 2.5 Pro TTS Preview (`gemini-2.5-pro-preview-tts`)**
**Primary Use**: Premium TTS with enhanced quality and capabilities

#### **Core Capabilities**
- ✅ **All Flash TTS capabilities**
- ✅ **Enhanced audio quality**
- ✅ **Better style control**
- ✅ **Improved multilingual performance**

## 🎯 **EVENT DETECTION MODELS**

### **1. Gemini 2.5 Flash Lite Preview (`gemini-2.5-flash-lite-preview-06-17`)**
**Primary Use**: Fast visual event detection for real-time applications

#### **Core Capabilities**
- ✅ **Ultra-low latency** image processing
- ✅ **Structured responses** (enum/JSON)
- ✅ **Optimized for simple tasks**
- ✅ **High throughput** processing
- ✅ **Cost-effective** for frequent calls

#### **Optimal Configuration**
```python
config = genai_types.GenerateContentConfig(
    system_instruction="Event detection prompt",
    max_output_tokens=10,
    response_mime_type='text/x.enum',
    response_schema=EventTypes,
    media_resolution=genai_types.MediaResolution.MEDIA_RESOLUTION_MEDIUM
)
```

## **CONFIGURATION PATTERNS**

### **Real-time Conversation Setup**
```python
def create_live_conversation_config():
    return types.LiveConnectConfig(
        # Core settings
        response_modalities=["AUDIO"],
        
        # Tools and functions
        tools=[
            types.Tool(function_declarations=[
                types.FunctionDeclaration(
                    name='function_name',
                    description='Function description',
                    behavior='NON_BLOCKING'  # For async execution
                )
            ])
        ],
        
        # System instruction
        system_instruction=[
            "You are a helpful AI assistant...",
            "Respond in Portuguese Brazilian...",
            "Be concise and natural..."
        ],
        
        # Audio configuration
        output_audio_transcription={},
        speech_config={
            'language_code': 'pt-BR',
            'voice_config': {
                'prebuilt_voice_config': {
                    'voice_name': 'Kore'
                }
            }
        },
        
        # Input configuration
        realtime_input_config=types.RealtimeInputConfig(
            turn_coverage='TURN_INCLUDES_ALL_INPUT',
            automatic_activity_detection={
                'disabled': False,
                'start_of_speech_sensitivity': types.StartSensitivity.START_SENSITIVITY_MEDIUM,
                'end_of_speech_sensitivity': types.EndSensitivity.END_SENSITIVITY_MEDIUM,
                'prefix_padding_ms': 20,
                'silence_duration_ms': 100
            }
        ),
        
        # Media settings
        generation_config=types.GenerationConfig(
            media_resolution=types.MediaResolution.MEDIA_RESOLUTION_MEDIUM
        )
    )
```

### **Event Detection Setup**
```python
def create_event_detection_config():
    return genai_types.GenerateContentConfig(
        system_instruction="Detect events in video feed...",
        max_output_tokens=10,
        response_mime_type='text/x.enum',
        response_schema=EventTypes,
        media_resolution=genai_types.MediaResolution.MEDIA_RESOLUTION_LOW  # For speed
    )
```

## 🌍 **LANGUAGE SUPPORT**

### **Live API Supported Languages (24)**
```python
LIVE_API_LANGUAGES = {
    'pt-BR': 'Portuguese (Brazil)',
    'en-US': 'English (US)',
    'en-GB': 'English (UK)',
    'en-AU': 'English (Australia)',
    'en-IN': 'English (India)',
    'es-US': 'Spanish (US)',
    'es-ES': 'Spanish (Spain)',
    'fr-FR': 'French (France)',
    'fr-CA': 'French (Canada)',
    'de-DE': 'German (Germany)',
    'it-IT': 'Italian (Italy)',
    'ja-JP': 'Japanese (Japan)',
    'ko-KR': 'Korean (South Korea)',
    'cmn-CN': 'Mandarin Chinese (China)',
    'hi-IN': 'Hindi (India)',
    'ar-XA': 'Arabic (Generic)',
    'id-ID': 'Indonesian (Indonesia)',
    'tr-TR': 'Turkish (Turkey)',
    'vi-VN': 'Vietnamese (Vietnam)',
    'th-TH': 'Thai (Thailand)',
    'nl-NL': 'Dutch (Netherlands)',
    'pl-PL': 'Polish (Poland)',
    'ru-RU': 'Russian (Russia)',
    'bn-IN': 'Bengali (India)',
    'gu-IN': 'Gujarati (India)',
    'kn-IN': 'Kannada (India)',
    'mr-IN': 'Marathi (India)',
    'ml-IN': 'Malayalam (India)',
    'ta-IN': 'Tamil (India)',
    'te-IN': 'Telugu (India)'
}
```

## **PERFORMANCE OPTIMIZATION**

### **Model Selection Guidelines**

#### **For Real-time Conversations**
1. **Production**: `gemini-2.0-flash-live-001` (most stable)
2. **Latest Features**: `gemini-live-2.5-flash-preview` (cutting edge)
3. **Natural Speech**: `gemini-2.5-flash-preview-native-audio-dialog` (best quality)
4. **Complex Reasoning**: `gemini-2.5-flash-exp-native-audio-thinking-dialog` (experimental)

#### **For Event Detection**
1. **Primary**: `gemini-2.5-flash-lite-preview-06-17` (optimized for speed)
2. **Fallback**: `gemini-2.0-flash-lite` (stable alternative)

#### **For TTS Generation**
1. **Standard**: `gemini-2.5-flash-preview-tts` (balanced)
2. **Premium**: `gemini-2.5-pro-preview-tts` (highest quality)

### **Latency Optimization**
```python
# For minimum latency
OPTIMIZATION_CONFIG = {
    'media_resolution': types.MediaResolution.MEDIA_RESOLUTION_LOW,
    'max_output_tokens': 150,  # Limit response length
    'automatic_activity_detection': {
        'start_of_speech_sensitivity': types.StartSensitivity.START_SENSITIVITY_HIGH,
        'end_of_speech_sensitivity': types.EndSensitivity.END_SENSITIVITY_HIGH,
        'silence_duration_ms': 50  # Faster detection
    }
}
```

### **Quality Optimization**
```python
# For maximum quality
QUALITY_CONFIG = {
    'media_resolution': types.MediaResolution.MEDIA_RESOLUTION_HIGH,
    'automatic_activity_detection': {
        'start_of_speech_sensitivity': types.StartSensitivity.START_SENSITIVITY_LOW,
        'end_of_speech_sensitivity': types.EndSensitivity.END_SENSITIVITY_LOW,
        'prefix_padding_ms': 100,  # More context
        'silence_duration_ms': 200  # More natural pauses
    }
}
```

## **SECURITY & AUTHENTICATION**

### **Server-to-Server (Recommended for Production)**
```python
client = genai.Client(api_key="your_api_key")
```

### **Client-to-Server (with Ephemeral Tokens)**
```python
# Generate ephemeral token on server
ephemeral_token = generate_ephemeral_token()

# Use on client
client = genai.Client(api_key=ephemeral_token)
```

## **USAGE MONITORING**

### **Token Counting**
```python
async for message in session.receive():
    if message.usage_metadata:
        usage = message.usage_metadata
        print(f"Total tokens: {usage.total_token_count}")
        for detail in usage.response_tokens_details:
            if isinstance(detail, types.ModalityTokenCount):
                print(f"{detail.modality}: {detail.token_count}")
```

### **Performance Metrics**
```python
class ModelPerformanceTracker:
    def __init__(self):
        self.ttft_measurements = []  # Time to first token
        self.total_latency = []
        self.token_throughput = []
    
    def record_response(self, start_time, first_token_time, end_time, token_count):
        ttft = first_token_time - start_time
        total_time = end_time - start_time
        throughput = token_count / total_time if total_time > 0 else 0
        
        self.ttft_measurements.append(ttft)
        self.total_latency.append(total_time)
        self.token_throughput.append(throughput)
```

## **ERROR HANDLING PATTERNS**

### **Connection Recovery**
```python
async def robust_live_session(model, config):
    max_retries = 3
    retry_delay = 1.0
    
    for attempt in range(max_retries):
        try:
            async with client.aio.live.connect(model=model, config=config) as session:
                async for response in session.receive():
                    yield response
            break
        except ConnectionError as e:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(retry_delay * (2 ** attempt))
```

### **Interruption Handling**
```python
async def handle_interruptions(session):
    async for response in session.receive():
        if response.server_content.interrupted:
            # Stop current audio playback
            stop_audio_playback()
            # Clear audio queue
            clear_audio_queue()
            # Continue processing
        yield response
```

## **BEST PRACTICES FOR LEONIDAS PROJECT**

### **Model Architecture Recommendations**
1. **Main Agent**: `gemini-live-2.5-flash-preview` (balanced features + stability)
2. **Event Detection**: `gemini-2.5-flash-lite-preview-06-17` (optimized speed)
3. **TTS Generation**: `gemini-2.5-flash-preview-tts` (when needed)

### **Configuration for Portuguese Brazilian**
```python
LEONIDAS_OPTIMAL_CONFIG = types.LiveConnectConfig(
    response_modalities=["AUDIO"],
    system_instruction=LEONIDAS_PROMPT_PARTS,
    speech_config={
        'language_code': 'pt-BR',
        'voice_config': {
            'prebuilt_voice_config': {
                'voice_name': 'Kore'  # Professional, clear voice
            }
        }
    },
    output_audio_transcription={},
    realtime_input_config=types.RealtimeInputConfig(
        turn_coverage='TURN_INCLUDES_ALL_INPUT',
        automatic_activity_detection={
            'disabled': False,
            'start_of_speech_sensitivity': types.StartSensitivity.START_SENSITIVITY_MEDIUM,
            'end_of_speech_sensitivity': types.EndSensitivity.END_SENSITIVITY_MEDIUM,
            'prefix_padding_ms': 20,
            'silence_duration_ms': 100
        }
    ),
    generation_config=types.GenerationConfig(
        media_resolution=types.MediaResolution.MEDIA_RESOLUTION_MEDIUM
    ),
    tools=LEONIDAS_TOOLS
)
```

### **Function Calling Best Practices**
```python
# Use NON_BLOCKING behavior for real-time responsiveness
LEONIDAS_TOOLS = [
    types.Tool(function_declarations=[
        types.FunctionDeclaration(
            name='start_commentating',
            description='Starts collaborative analysis',
            behavior='NON_BLOCKING'  # Critical for real-time
        ),
        types.FunctionDeclaration(
            name='wait_for_user',
            description='Waits for user response',
            behavior='NON_BLOCKING'  # Enables silent responses
        )
    ])
]
```

This comprehensive reference provides complete context for all Gemini models and their optimal usage patterns for the Leonidas project and similar real-time AI applications.
