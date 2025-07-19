---
inclusion: always
---

# Leonidas-Gemini Integration Patterns

## Core Integration Principles

This guide provides specific integration patterns, configurations, and optimizations for the Leonidas project using Gemini models, based on the current codebase architecture.

## Current Architecture

### Model Configuration
- **Main Agent**: `gemini-2.5-flash-live-preview` (real-time conversation)
- **Event Detection**: `gemini-2.5-flash-lite-preview-06-17` (visual perception)
- **Audio**: 24kHz sample rate, medium resolution
- **Language**: Portuguese Brazilian with professional, collaborative tone

### Component Pipeline
```
EventDetection → LeonidasAgent → RateLimitAudio
```

## Model Selection Strategy

### Environment-Based Configuration
```python
LEONIDAS_MODELS = {
    "production": {
        'main_agent': 'gemini-2.0-flash-live-001',  # Stable
        'visual_perception': 'gemini-2.5-flash-lite-preview-06-17',
        'cognitive_analyzer': 'gemini-2.0-flash'
    },
    "development": {
        'main_agent': 'gemini-live-2.5-flash-preview',  # Latest features
        'visual_perception': 'gemini-2.5-flash-lite-preview-06-17',
        'cognitive_analyzer': 'gemini-2.5-flash-preview'
    }
}
```

## Live API Configuration

### Core Configuration Pattern
```python
def create_leonidas_config() -> types.LiveConnectConfig:
    return types.LiveConnectConfig(
        response_modalities=["AUDIO"],
        system_instruction=LEONIDAS_PROMPT_PARTS,
        speech_config={
            'language_code': 'pt-BR',
            'voice_config': {'prebuilt_voice_config': {'voice_name': 'Kore'}}
        },
        output_audio_transcription={},
        realtime_input_config=types.RealtimeInputConfig(
            turn_coverage='TURN_INCLUDES_ALL_INPUT',
            automatic_activity_detection={
                'start_of_speech_sensitivity': types.StartSensitivity.START_SENSITIVITY_MEDIUM,
                'end_of_speech_sensitivity': types.EndSensitivity.END_SENSITIVITY_MEDIUM,
                'prefix_padding_ms': 30,
                'silence_duration_ms': 150
            }
        ),
        generation_config=types.GenerationConfig(
            media_resolution=types.MediaResolution.MEDIA_RESOLUTION_MEDIUM,
            max_output_tokens=200,
            temperature=0.8
        ),
        tools=LEONIDAS_TOOLS
    )
```

### System Prompts
```python
LEONIDAS_PROMPT_PARTS = [
    "Você é Leonidas, uma IA colaborativa especializada em arquitetura de software, "
    "especificação de sistemas e desenvolvimento colaborativo.",
    
    "Comunique-se em português brasileiro com tom profissional, analítico e colaborativo. "
    "Seja direto e objetivo, mas mantenha um tom acolhedor.",
    
    "Princípios: (1) Arquitetura limpa e primeiros princípios, "
    "(2) Perguntas esclarecedoras antes de assumir requisitos, "
    "(3) Soluções incrementais e testáveis, "
    "(4) Considere escalabilidade, manutenibilidade e performance.",
    
    "Você pode ser interrompido a qualquer momento. Quando interrompido, pare e ouça. "
    "Use ferramentas (start_commentating, wait_for_user) para gerenciar o fluxo da conversa."
]
```

### Function Declarations
```python
LEONIDAS_TOOLS = [
    types.Tool(function_declarations=[
        types.FunctionDeclaration(
            name='start_commentating',
            description='Inicia análise colaborativa do contexto atual',
            behavior='NON_BLOCKING',
            parameters={
                'type': 'object',
                'properties': {
                    'analysis_type': {
                        'type': 'string',
                        'enum': ['code_review', 'architecture_analysis', 'debugging', 'general_collaboration']
                    }
                }
            }
        ),
        types.FunctionDeclaration(
            name='wait_for_user',
            description='Aguarda resposta ou ação do usuário',
            behavior='NON_BLOCKING',
            parameters={
                'type': 'object',
                'properties': {
                    'wait_reason': {
                        'type': 'string',
                        'enum': ['question_response', 'action_required', 'user_input']
                    }
                }
            }
        )
    ])
]
```

## Event Detection Configuration

### Visual Perception Prompt
```python
EVENT_DETECTION_PROMPT = (
    "Sistema de percepção visual para contexto de desenvolvimento. Detecte:\n"
    "BÁSICO: Pessoa engajada + tela visível = DETECTION\n"
    "INTERRUPÇÃO: Mudança significativa no código/erro/usuário apontando = INTERRUPTION\n"
    "Priorize: IDEs, editores, terminais, documentação técnica"
)

def create_event_detection_config():
    return genai_types.GenerateContentConfig(
        system_instruction=EVENT_DETECTION_PROMPT,
        max_output_tokens=10,
        response_mime_type='text/x.enum',
        response_schema=EventTypes,
        temperature=0.3
    )
```

## Cognitive Analysis Pattern

### Background Analysis Processor
```python
class LeonidasCognitiveAnalyzer(processor.Processor):
    """Background cognitive analysis for Leonidas."""
    
    def __init__(self, api_key: str, model: str = "gemini-2.5-flash-preview"):
        self.client = genai.Client(api_key=api_key)
        self.model = model
        self.conversation_buffer = collections.deque(maxlen=50)
        self.intervention_threshold = 0.7
        self.min_intervention_interval = 30
    
    async def _perform_cognitive_analysis(self) -> dict:
        analysis_prompt = self._create_analysis_prompt()
        response = await self.client.aio.models.generate_content(
            model=self.model,
            contents=analysis_prompt,
            config=genai_types.GenerateContentConfig(
                max_output_tokens=300,
                temperature=0.6,
                response_mime_type='application/json'
            )
        )
        return json.loads(response.candidates[0].content.parts[0].text)
    
    def _create_analysis_prompt(self) -> str:
        return (
            "Analise a conversa recente do Leonidas. Identifique:\n"
            "1. Insights técnicos importantes\n"
            "2. Possíveis problemas\n"
            "3. Sugestões de melhoria\n"
            "4. Necessidade de intervenção\n"
            "Responda em JSON estruturado."
        )
```

## Session Management

### Session Logger Pattern
```python
class LeonidasSessionLogger(processor.Processor):
    """Session logging with structured data capture."""
    
    def __init__(self, log_directory: str = "logs"):
        self.log_directory = Path(log_directory)
        self.session_id = f"leonidas_{int(time.time())}"
        self.conversation_log = []
        self.visual_context_log = []
        self.cognitive_insights_log = []
    
    async def _log_part(self, part: content_api.ProcessorPart):
        log_entry = {
            'timestamp': time.time(),
            'substream': part.substream_name,
            'role': part.role,
            'content': part.text if content_api.is_text(part.mimetype) else None,
            'content_size': len(part.bytes) if part.bytes else 0
        }
        
        # Categorize by substream
        if part.substream_name == 'realtime':
            self.conversation_log.append(log_entry)
        elif part.substream_name == 'visual_context':
            self.visual_context_log.append(log_entry)
```

## Agent Factory Pattern

### Complete Integration Factory
```python
def create_leonidas_agent(
    api_key: str,
    environment: str = "production",
    enable_cognitive_analysis: bool = True,
    chattiness: float = 0.8
) -> processor.Processor:
    """Create complete Leonidas agent with all components."""
    
    models = LEONIDAS_MODELS[environment]
    
    # Event detection
    event_detection = event_detection.EventDetection(
        api_key=api_key,
        model=models['visual_perception'],
        config=create_event_detection_config(),
        output_dict={
            ('*', EventTypes.DETECTION): [
                content_api.ProcessorPart('iniciar colaboração técnica', role='USER')
            ],
            (EventTypes.DETECTION, EventTypes.INTERRUPTION): [
                content_api.ProcessorPart('', role='USER', metadata={'interrupt_request': True})
            ]
        }
    )
    
    # Live API processor
    live_processor = live_model.LiveProcessor(
        api_key=api_key,
        model_name=models['main_agent'],
        realtime_config=create_leonidas_config()
    )
    
    # Main agent
    main_agent = LeonidasAgent(
        live_api_processor=live_processor,
        chattiness=chattiness
    )
    
    # Optional cognitive analysis
    if enable_cognitive_analysis:
        cognitive_analyzer = LeonidasCognitiveAnalyzer(api_key, models['cognitive_analyzer'])
        main_agent = main_agent // cognitive_analyzer
    
    # Complete pipeline
    return processor.chain([
        event_detection,
        main_agent,
        rate_limit_audio.RateLimitAudio(24000)
    ])
```

## Key Integration Principles

1. **Environment-based model selection** for stability vs features
2. **Portuguese Brazilian** language and professional tone
3. **NON_BLOCKING function behavior** for real-time responsiveness
4. **Event-driven architecture** with visual perception
5. **Cognitive analysis** running in parallel for insights
6. **Structured logging** for session management and debugging