# Leonidas Core Directive

## 🎯 **MISSION**
Leonidas = Real-time AI collaborator for software development. Focus: `leonidas/` folder only.

## 🏗️ **ARCHITECTURE**
```
leonidas/
├── leonidas.py          # Main implementation (933 lines)
├── leonidas_cli.py      # CLI interface
├── README.md           # Documentation
└── REQUIREMENTS.md     # Specifications
```

## ⚙️ **TECH STACK**
- **Model**: `gemini-live-2.5-flash-preview` → migrate to `gemini-2.0-flash-live-001`
- **Language**: Portuguese Brazilian
- **Voice**: Kore
- **Audio**: 16kHz input, 24kHz output
- **Framework**: genai-processors library

## 🔧 **CONFIG TEMPLATE**
```python
LEONIDAS_CONFIG = types.LiveConnectConfig(
    response_modalities=["AUDIO"],
    system_instruction=LEONIDAS_SYSTEM_PROMPT,
    speech_config={'language_code': 'pt-BR', 'voice_config': {'prebuilt_voice_config': {'voice_name': 'Kore'}}},
    tools=LEONIDAS_TOOLS,  # [think, change_state, get_context, get_time, shutdown_system]
    media_resolution=types.MediaResolution.MEDIA_RESOLUTION_MEDIUM
)
```

## 🚦 **DEVELOPMENT RULES**
1. **FOCUS**: Only work in `leonidas/` folder
2. **LANGUAGE**: Portuguese Brazilian only
3. **ARCHITECTURE**: InputManager → Orchestrator → OutputManager
4. **FUNCTIONS**: Always use `think()` for reasoning
5. **STATE**: Use state machine for conversation flow

## 📋 **CURRENT PHASE: 2**
- ✅ Phase 1: Basic real-time conversation (COMPLETE)
- 🔄 Phase 2: Cognitive system + session memory (CURRENT)
- 📋 Phase 3: Production readiness
- 🔮 Phase 4: Advanced features

## 🎯 **IMMEDIATE PRIORITIES**
1. Migrate to stable Gemini model
2. Implement CognitiveAnalyzer
3. Add session logging
4. Optimize performance

## 🚫 **AVOID**
- Working outside `leonidas/`
- English implementation
- Obsolete Gemini models
- Breaking modular architecture
- Reinventing genai-processors functionality