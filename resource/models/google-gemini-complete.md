# Google Gemini Models - Complete Specification

## 🔵 **GOOGLE GEMINI - ESPECIFICAÇÃO COMPLETA**

Este arquivo centraliza **todas** as informações sobre modelos Google/Gemini, organizadas por categoria e com foco nas necessidades do projeto Leonidas.

---

## 📊 **OVERVIEW GERAL DOS MODELOS GEMINI**

### **🎯 Categorização por Uso**
```yaml
Real-time/Live Models:
  primary: "gemini-live-2.5-flash-preview"
  stable: "gemini-2.0-flash-live-001"
  native_audio: "gemini-2.5-flash-native-audio-dialog"
  thinking: "gemini-2.5-flash-native-audio-thinking"

Completion Models:
  flagship: "gemini-2.5-pro"
  balanced: "gemini-2.5-flash"
  legacy_stable: "gemini-1.5-pro"
  legacy_fast: "gemini-1.5-flash"

Specialized Models:
  event_detection: "gemini-2.5-flash-lite-preview-06-17"
  text_to_speech: "gemini-2.5-flash-preview-tts"
  premium_tts: "gemini-2.5-pro-preview-tts"
  code_assist: "gemini-code-assist"

Experimental Models:
  latest_exp: "gemini-exp-1206"
  thinking_exp: "gemini-2.5-flash-thinking-exp"
  learning: "gemini-learnlm-1.5-pro-experimental"
```

### **💰 Pricing Overview (Free vs Paid)**
```yaml
Free Tier Limits:
  live_models:
    requests_per_minute: 60
    audio_minutes_per_day: 1000
    concurrent_sessions: 1
  
  completion_models:
    requests_per_minute: 15
    requests_per_day: 1500
    tokens_per_minute: 32000
  
  flash_lite:
    requests_per_minute: 1000
    requests_per_day: 50000

Paid Tier Pricing:
  gemini_2_5_flash: "$0.075 input, $0.30 output per 1M tokens"
  gemini_2_5_pro: "$1.25 input, $5.00 output per 1M tokens"
  gemini_live: "$0.075 input, $0.30 output per 1M tokens + $0.40/min audio"
  gemini_flash_lite: "$0.00025 per request"
```

---

## 🎙️ **REAL-TIME/LIVE MODELS**

### **🚀 gemini-live-2.5-flash-preview - ATUALIZADO JULHO 2025**
```yaml
Model ID: "gemini-live-2.5-flash-preview"
Status: "Preview - Latest Features"
Type: "Real-time/Live (Audio-to-Audio)"
Architecture: "Otimizado para diálogos de baixa latência com compreensão e geração nativa de áudio"
Release Date: "Junho 2025 (Última atualização)"
Recommended For: "Development, Latest Features"

Core Capabilities:
  ✅ Real-time bidirectional streaming
  ✅ Voice Activity Detection (VAD) para ignorar ruído de fundo (Proactive Audio)
  ✅ Function calling support durante o diálogo
  ✅ Multi-modal input (áudio/vídeo/texto)
  ✅ Interruption handling (capacidade de ser interrompido e responder)
  ✅ Audio transcription (input) / Audio generation (output)
  ✅ Emotional Intelligence (Affective Dialog)
  ✅ Context Awareness (filtra conversas de fundo)

Technical Specs:
  context_window: "1,048,576 tokens" # MASSIVAMENTE AUMENTADO de 32K
  max_output_tokens: "8,192 tokens"
  input_audio_formats: ["audio/flac", "audio/mp3", "audio/wav", "audio/opus", "audio/m4a"]
  max_input_length: "Aproximadamente 8.4 horas por arquivo"
  output_audio: "Vozes em alta definição, com expressividade e prosódia naturais"
  typical_latency: "Latência muito baixa, projetada para conversas fluidas"
  
Language Support:
  primary: "Suporte para mais de 24 idiomas"
  voices: "Mais de 30 vozes em HD disponíveis"
  voice_control: "Controlável por prompts de texto (tom, sotaque, emoção, sussurros)"
  regional_variants: "Suporta troca de idiomas e sotaques durante a mesma conversa"
  recommended_voice: "Kore" # Clear, professional

Free Tier Limits - JULHO 2025:
  requests_per_minute: "N/A"
  tokens_per_minute: 1,000,000 # MASSIVAMENTE AUMENTADO
  requests_per_day: "N/A"
  concurrent_sessions: 3 # AUMENTADO de 1

Unique Features:
  proactive_audio: "Sabe quando não deve falar (filtra ruído de fundo)"
  affective_dialog: "Detecta emoção na voz e responde apropriadamente"
  voice_customization: "Controle por prompts naturais (ex: 'sotaque britânico entusiasmado')"
```

#### **Configuration for Leonidas**
```python
LEONIDAS_LIVE_CONFIG = types.LiveConnectConfig(
    response_modalities=["AUDIO"],
    system_instruction=LEONIDAS_SYSTEM_PROMPT,
    speech_config={
        'language_code': 'pt-BR',
        'voice_config': {
            'prebuilt_voice_config': {
                'voice_name': 'Kore'
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

### **🛡️ gemini-2.0-flash-live-001**
```yaml
Model ID: "gemini-2.0-flash-live-001"
Status: "Stable - Production Ready"
Architecture: "Half-cascade"
Release Date: "2024-11-XX"
Recommended For: "Production, Stability"

Key Differences from 2.5 Preview:
  ✅ More stable function calling
  ✅ Better error recovery
  ✅ Proven reliability
  ✅ Same technical specs as 2.5
  ⚠️ Fewer cutting-edge features

Migration Strategy:
  development: "Use 2.5 preview for latest features"
  production: "Use 2.0 for stability"
  fallback: "2.0 as backup when 2.5 has issues"
```

### **🎵 gemini-2.5-flash-native-audio-dialog**
```yaml
Model ID: "gemini-2.5-flash-native-audio-dialog"
Status: "Preview - Native Audio"
Architecture: "Native audio (end-to-end)"
Recommended For: "Highest quality conversations"

Unique Features:
  ✅ Native audio processing (most natural)
  ✅ Affective dialog (emotion-aware)
  ✅ Proactive audio (selective responses)
  ✅ Enhanced multilingual performance
  ⚠️ Limited tool support (basic function calling only)
  ❌ No code execution
  ❌ No URL context

Technical Specs:
  context_window: "128,000 tokens" # 4x larger
  voice_selection: "Automatic" # Cannot set explicit voice
  language_detection: "Automatic"
  api_version_required: "v1alpha"

When to Use:
  ✅ Highest quality conversation needed
  ✅ Natural speech patterns important
  ❌ Function calling critical
  ❌ Tool integration required
```

### **🧠 gemini-2.5-flash-native-audio-thinking**
```yaml
Model ID: "gemini-2.5-flash-exp-native-audio-thinking-dialog"
Status: "Experimental - Thinking Mode"
Architecture: "Native audio with thinking"
Recommended For: "Complex reasoning with audible thought"

Unique Features:
  ✅ Thinking out loud (audible reasoning)
  ✅ Enhanced problem-solving approach
  ✅ All native audio capabilities
  ❌ No function calling support
  ⚠️ Experimental status (may change)

Use Cases:
  ✅ Complex technical discussions
  ✅ Problem-solving sessions
  ✅ Educational content
  ❌ Production applications
```

---

## 💬 **COMPLETION MODELS**

### **🏆 gemini-2.5-pro - ATUALIZADO JULHO 2025**
```yaml
Model ID: "gemini-2.5-pro"
Status: "Stable - Flagship Model"
Type: "Completion"
Architecture: "Transformer, Multimodal, Thinking Engine"
Release Date: "Junho 2025 (Última atualização)"
Recommended For: "Complex reasoning, high-quality output"

Core Capabilities:
  ✅ Function calling support
  ✅ Multi-modal input (audio/video/text/PDF)
  ✅ Code Execution
  ✅ Structured Outputs (JSON Mode)
  ✅ Advanced reasoning and analysis
  ✅ Complex problem solving

Technical Specs:
  context_window: "1,048,576 tokens" # ~1M tokens (ATUALIZADO)
  max_output_tokens: "65,536 tokens" # SIGNIFICATIVAMENTE AUMENTADO
  max_images: "3,600 per request"
  typical_latency: "Otimizado para máxima precisão e desempenho de ponta"
  throughput: "20-40 tokens/second"

Free Tier Limits - JULHO 2025:
  requests_per_minute: 5 # AUMENTADO de 2
  requests_per_day: 100 # AUMENTADO de 50
  tokens_per_minute: 250,000 # MASSIVAMENTE AUMENTADO de 32K

Paid Tier Pricing:
  input: "$1.25 per 1M tokens"
  output: "$5.00 per 1M tokens"
  images: "$0.00265 per image"

Leonidas Integration:
  primary_use: "Complex analysis and reasoning tasks"
  fallback_for: "When highest quality reasoning needed"
  configuration: "Premium reasoning config"
```

### **⚡ gemini-2.5-flash - ATUALIZADO JULHO 2025**
```yaml
Model ID: "gemini-2.5-flash"
Status: "Stable - Balanced Performance"
Type: "Completion"
Architecture: "Transformer, Multimodal, Thinking Engine"
Release Date: "Junho 2025 (Última atualização)"
Recommended For: "General purpose, balanced speed/quality"

Core Capabilities:
  ✅ Function calling support
  ✅ Multi-modal input (audio/video/text)
  ✅ Code Execution
  ✅ Structured Outputs (JSON Mode)
  ✅ Fast generation
  ✅ Good reasoning quality
  ✅ Cost effective

Technical Specs:
  context_window: "1,048,576 tokens" # ~1M tokens
  max_output_tokens: "65,536 tokens" # SIGNIFICATIVAMENTE AUMENTADO
  max_images: "3,600 per request"
  typical_latency: "Otimizado para excelente custo-benefício e tarefas de baixa latência e alto volume"
  throughput: "40-80 tokens/second"

Free Tier Limits - JULHO 2025:
  requests_per_minute: 10 # REDUZIDO de 15 mas com TPM muito maior
  requests_per_day: 250 # REDUZIDO de 1,500 mas com TPM compensando
  tokens_per_minute: 250,000 # MASSIVAMENTE AUMENTADO de 1M

Paid Tier Pricing:
  input: "$0.075 per 1M tokens"
  output: "$0.30 per 1M tokens"
  images: "$0.00265 per image"

Leonidas Usage:
  primary_use: "Text analysis and generation"
  fallback_for: "When live models unavailable"
  configuration: "Standard completion config"
  advantage: "Melhor custo-benefício com novos limites"
```

### **🏛️ gemini-1.5-pro & gemini-1.5-flash**
```yaml
Legacy Models: "Still supported but not recommended for new projects"

gemini-1.5-pro:
  status: "Stable but superseded by 2.5-pro"
  context_window: "2,097,152 tokens"
  use_case: "Fallback for compatibility"

gemini-1.5-flash:
  status: "Stable but superseded by 2.5-flash"
  context_window: "1,048,576 tokens"
  use_case: "Fallback for compatibility"

Migration Recommendation:
  from_1_5_pro: "Migrate to gemini-2.5-pro"
  from_1_5_flash: "Migrate to gemini-2.5-flash"
  timeline: "Before Q2 2025"
```

---

## 🎯 **SPECIALIZED MODELS**

### **👁️ gemini-2.5-flash-lite-preview-06-17 - ATUALIZADO JULHO 2025**
```yaml
Model ID: "gemini-2.5-flash-lite-preview-06-17"
Status: "Preview - Optimized for Speed"
Type: "Completion"
Architecture: "Transformer, Multimodal, Thinking Engine"
Release Date: "Junho 2025 (Última atualização)"
Recommended For: "Event detection, real-time analysis"

Core Capabilities:
  ✅ Function calling support
  ✅ Multi-modal input (audio/video/text)
  ✅ Code Execution
  ✅ Structured Outputs (JSON Mode)
  ✅ Context from URL
  ✅ Ultra-low latency optimization
  ✅ High throughput
  ✅ Cost effective

Technical Specs:
  context_window: "1,000,000 tokens" # MASSIVAMENTE AUMENTADO de 32K
  max_output_tokens: "64,000 tokens" # MASSIVAMENTE AUMENTADO de 1K
  typical_latency: "Otimizado para máxima eficiência de custo e a mais baixa latência entre os modelos de completion"
  throughput: "100+ tokens/second"

Free Tier Limits - JULHO 2025:
  requests_per_minute: 15 # REDUZIDO de 1,000 mas com contexto muito maior
  requests_per_day: 1,000 # REDUZIDO de 50,000 mas com capacidades expandidas
  tokens_per_minute: 250,000 # NOVO LIMITE TPM

Paid Tier Pricing:
  cost: "$0.00025 per request"

Leonidas Usage:
  primary_use: "Visual event detection e análise em tempo real"
  configuration: "Enum responses for speed + expanded capabilities"
  optimization: "MEDIA_RESOLUTION_LOW"
  advantage: "Agora com contexto de 1M tokens para análises mais complexas"
```

#### **Event Detection Configuration**
```python
EVENT_DETECTION_CONFIG = genai_types.GenerateContentConfig(
    system_instruction="Detect events in video feed. Respond with enum only.",
    max_output_tokens=10,
    response_mime_type='text/x.enum',
    response_schema=EventTypes,
    media_resolution=genai_types.MediaResolution.MEDIA_RESOLUTION_LOW
)
```

### **🎤 gemini-2.5-flash-preview-tts**
```yaml
Model ID: "gemini-2.5-flash-preview-tts"
Status: "Preview - Text-to-Speech"
Type: "Specialized TTS"
Recommended For: "High-quality speech synthesis"

Core Capabilities:
  ✅ Single speaker TTS
  ✅ Multi-speaker TTS (up to 2 speakers)
  ✅ Style control via natural language
  ✅ 30 voice options
  ✅ 24 language support
  ✅ Controllable speech (tone, pace, style)

Voice Options (Selected):
  professional: ["Kore", "Orus", "Iapetus", "Alnilam"]
  warm_friendly: ["Charon", "Leda", "Callirrhoe", "Achird"]
  energetic: ["Zephyr", "Puck", "Autonoe", "Laomedeia"]
  specialized: ["Enceladus" (breathy), "Algenib" (gravelly)]

Technical Specs:
  output_format: "24kHz PCM 16-bit"
  max_input_length: "5,000 characters"
  typical_latency: "1-3 seconds"
  supported_languages: 24

Future Integration:
  leonidas_use: "Planned for v3"
  voice_consistency: "Use Kore to match live models"
  use_cases: ["Offline TTS", "Batch audio generation"]
```

### **🎓 gemini-code-assist**
```yaml
Model ID: "gemini-code-assist"
Status: "Specialized - Code Focus"
Type: "Code Completion/Analysis"
Recommended For: "Programming tasks, code review"

Specialized Features:
  ✅ Code completion
  ✅ Code explanation
  ✅ Bug detection
  ✅ Code review
  ✅ Refactoring suggestions
  ✅ 50+ programming languages

Supported Languages:
  primary: ["Python", "JavaScript", "TypeScript", "Java", "C++"]
  web: ["HTML", "CSS", "React", "Vue", "Angular"]
  data: ["SQL", "R", "MATLAB", "Jupyter"]
  systems: ["Rust", "Go", "C", "Assembly"]

Integration Potential:
  leonidas_use: "Code analysis and generation"
  use_cases: ["Code review", "Architecture analysis", "Bug detection"]
```

---

## 🧪 **EXPERIMENTAL MODELS**

### **🔬 gemini-exp-1206**
```yaml
Model ID: "gemini-exp-1206"
Status: "Experimental - Latest Research"
Type: "Advanced Reasoning"
Release Date: "2024-12-06"
Recommended For: "Cutting-edge capabilities testing"

Experimental Features:
  ✅ Advanced reasoning
  ✅ Complex problem solving
  ✅ Novel capabilities
  ⚠️ Unstable API
  ⚠️ May change without notice
  ⚠️ No SLA guarantees

Usage Guidelines:
  ✅ Research and experimentation
  ✅ Feature preview
  ❌ Production applications
  ❌ Critical workflows

Access:
  availability: "Limited"
  requirements: "Special access may be required"
```

### **💭 gemini-2.5-flash-thinking-exp**
```yaml
Model ID: "gemini-2.5-flash-thinking-exp"
Status: "Experimental - Thinking Mode"
Type: "Reasoning with Visible Thought Process"
Recommended For: "Complex problem solving with transparency"

Unique Features:
  ✅ Visible reasoning process
  ✅ Step-by-step thinking
  ✅ Enhanced problem solving
  ✅ Educational value
  ⚠️ Longer response times
  ⚠️ More verbose output

Use Cases:
  ✅ Complex technical problems
  ✅ Educational content
  ✅ Debugging assistance
  ✅ Architecture decisions
```

---

## 🔧 **CONFIGURATION PATTERNS**

### **🎛️ Standard Configurations**

#### **Basic Text Completion**
```python
def create_basic_completion_config():
    return genai.GenerationConfig(
        temperature=0.7,
        max_output_tokens=2048,
        top_p=0.9,
        top_k=40
    )
```

#### **Function Calling Setup**
```python
def create_function_calling_config(functions: list):
    tools = [
        genai.Tool(function_declarations=functions)
    ]
    
    return genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        tools=tools,
        generation_config=genai.GenerationConfig(
            temperature=0.3,  # Lower for more consistent function calls
            max_output_tokens=1024
        )
    )
```

#### **JSON Mode Configuration**
```python
def create_json_mode_config(schema: dict):
    return genai.GenerationConfig(
        response_mime_type="application/json",
        response_schema=schema,
        temperature=0.1,  # Very low for consistent JSON
        max_output_tokens=2048
    )
```

#### **Multi-modal Configuration**
```python
def create_multimodal_config():
    return genai.GenerationConfig(
        temperature=0.7,
        max_output_tokens=2048,
        # Image processing settings
        media_resolution=genai.MediaResolution.MEDIA_RESOLUTION_MEDIUM
    )
```

---

## 🚦 **RATE LIMITS & QUOTAS DETALHADOS**

### **📊 Free Tier Limits (Per API Key) - ATUALIZADO JULHO 2025**
```yaml
Completion Models:
  gemini_2_5_pro:
    requests_per_minute: 5
    tokens_per_minute: 250000
    requests_per_day: 100
    concurrent_sessions: "N/A"
  
  gemini_2_5_flash:
    requests_per_minute: 10
    tokens_per_minute: 250000
    requests_per_day: 250
    concurrent_sessions: "N/A"
  
  gemini_2_5_flash_lite:
    requests_per_minute: 15
    tokens_per_minute: 250000
    requests_per_day: 1000
    concurrent_sessions: "N/A"

Live Models:
  gemini_2_5_flash_live:
    requests_per_minute: "N/A"
    tokens_per_minute: 1000000
    requests_per_day: "N/A"
    concurrent_sessions: 3

OBSERVAÇÃO IMPORTANTE:
  - Limites SIGNIFICATIVAMENTE AUMENTADOS em julho 2025
  - TPM (Tokens per Minute) muito mais generosos
  - Flash-Lite agora com 1000 RPD vs 50K anteriores
  - Live API com 3 sessões concorrentes vs 1 anterior
```

### **💰 Paid Tier Pricing**
```yaml
Live Models:
  base_pricing: "$0.075 input, $0.30 output per 1M tokens"
  audio_pricing: "$0.40 per minute"
  
Completion Models:
  gemini_2_5_pro: "$1.25 input, $5.00 output per 1M tokens"
  gemini_2_5_flash: "$0.075 input, $0.30 output per 1M tokens"
  
Specialized Models:
  gemini_flash_lite: "$0.00025 per request"
  gemini_tts: "$16 per 1M characters"

Additional Costs:
  images: "$0.00265 per image"
  videos: "$0.00265 per second"
  audio_input: "Included in base pricing"
```

---

## 🔍 **MODEL SELECTION GUIDE**

### **🎯 Decision Matrix**
```yaml
Real-time Conversation:
  development: "gemini-live-2.5-flash-preview"
  production: "gemini-2.0-flash-live-001"
  highest_quality: "gemini-2.5-flash-native-audio-dialog"
  complex_reasoning: "gemini-2.5-flash-native-audio-thinking"

Text Processing:
  complex_tasks: "gemini-2.5-pro"
  general_purpose: "gemini-2.5-flash"
  speed_critical: "gemini-2.5-flash-lite-preview"

Specialized Tasks:
  event_detection: "gemini-2.5-flash-lite-preview-06-17"
  code_tasks: "gemini-code-assist"
  speech_synthesis: "gemini-2.5-flash-preview-tts"

Experimental:
  research: "gemini-exp-1206"
  transparent_reasoning: "gemini-2.5-flash-thinking-exp"
```

### **🚀 Performance Comparison**
```yaml
Latency (TTFT):
  fastest: "gemini-2.5-flash-lite-preview (50-100ms)"
  fast: "gemini-2.5-flash (200-800ms)"
  medium: "gemini-live-2.5-flash-preview (200-500ms)"
  slow: "gemini-2.5-pro (1-3s)"

Quality:
  highest: "gemini-2.5-pro"
  high: "gemini-2.5-flash"
  specialized: "gemini-live models (for conversation)"
  optimized: "gemini-2.5-flash-lite (for specific tasks)"

Cost Efficiency:
  most_efficient: "gemini-2.5-flash-lite-preview"
  balanced: "gemini-2.5-flash"
  premium: "gemini-2.5-pro"
  specialized: "gemini-live (for real-time)"
```

---

## 🛠️ **TROUBLESHOOTING GUIDE**

### **🚨 Common Issues**

#### **Rate Limit Errors**
```python
# Error: 429 Too Many Requests
# Solution: Implement key rotation
def handle_rate_limit():
    try:
        response = model.generate_content(prompt)
    except Exception as e:
        if "429" in str(e) or "quota" in str(e).lower():
            # Rotate to next key
            key_manager.rotate_key()
            # Retry with new key
            response = model.generate_content(prompt)
    return response
```

#### **Authentication Errors**
```python
# Error: 401 Unauthorized
# Solution: Verify API key
def verify_api_key(api_key: str) -> bool:
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content("Test")
        return True
    except:
        return False
```

#### **Model Unavailable**
```python
# Error: Model not found or unavailable
# Solution: Use fallback model
MODEL_FALLBACKS = {
    'gemini-live-2.5-flash-preview': 'gemini-2.0-flash-live-001',
    'gemini-2.5-pro': 'gemini-2.5-flash',
    'gemini-exp-1206': 'gemini-2.5-pro'
}

def get_model_with_fallback(preferred_model: str):
    try:
        return genai.GenerativeModel(preferred_model)
    except:
        fallback = MODEL_FALLBACKS.get(preferred_model)
        if fallback:
            return genai.GenerativeModel(fallback)
        raise
```

---

## 📚 **RESOURCES & DOCUMENTATION**

### **🔗 Official Links**
- **Main Documentation**: [ai.google.dev](https://ai.google.dev)
- **API Reference**: [ai.google.dev/api](https://ai.google.dev/api)
- **Live API Docs**: [ai.google.dev/api/live](https://ai.google.dev/api/live)
- **Pricing**: [ai.google.dev/pricing](https://ai.google.dev/pricing)
- **Quotas**: [ai.google.dev/docs/quota](https://ai.google.dev/docs/quota)

### **🛠️ Development Tools**
- **Python SDK**: `pip install google-generativeai`
- **API Explorer**: [ai.google.dev/api-explorer](https://ai.google.dev/api-explorer)
- **Prompt Gallery**: [ai.google.dev/prompts](https://ai.google.dev/prompts)

### **📊 Monitoring & Analytics**
- **Usage Dashboard**: Google Cloud Console
- **Quota Monitoring**: API & Services → Quotas
- **Billing**: Google Cloud Billing

---

**🔵 GOOGLE GEMINI COMPLETE - Sua referência definitiva para modelos Gemini**

*Última atualização: 2025-01-22*
*Próxima revisão: Mensal (toda primeira segunda-feira do mês)*