# Leonidas v2 - Modular Conversational AI Agent 🤖

Leonidas v2 is a complete refactoring of the original commentator into a modular, fluid conversational agent that thinks, acts, and collaborates like a human partner.

## 🎯 Key Improvements

### From Commentator to Collaborator
- **Before**: Proactive commentator that talks continuously
- **After**: Thoughtful collaborator that listens, thinks, and responds contextually

### Modular Architecture
- **InputManager**: Hardware input abstraction (camera, microphone)
- **LeonidasOrchestrator**: Core intelligence with advanced tool system
- **OutputManager**: Hardware output abstraction (speakers, future displays)

### Advanced Intelligence
- **THINK-ACT Cycle**: Model must think before acting
- **Self-State Management**: Model controls its own behavior
- **Rich Tool System**: think, speak, change_state, get_context, get_time
- **Contextual Awareness**: Maintains conversation history and adapts

## 🏗️ Architecture

```
┌─────────────┐    ┌──────────────────────┐    ┌──────────────┐
│InputManager │ -> │LeonidasOrchestrator  │ -> │OutputManager │
│             │    │                      │    │              │
│• Camera     │    │• Gemini Live API     │    │• Speakers    │
│• Microphone │    │• Tool Execution      │    │• Rate Limit  │
│• Future I/O │    │• State Management    │    │• Future I/O  │
└─────────────┘    │• Conversation Memory │    └──────────────┘
                   └──────────────────────┘
```

## 🛠️ Tool System

Leonidas v2 has an advanced tool system that gives the model full control:

### Core Tools
- **`think`**: 🧠 Mandatory reasoning before actions
- **`speak`**: 🗣️ Direct communication with user
- **`change_state`**: 🔄 Self-behavior control (listening/commentating/paused/analyzing)
- **`get_context`**: 📋 Access conversation history and system status
- **`get_time`**: 🕐 Current date/time information

### Future Extensions
- **`google_search`**: 🔍 Web search capabilities (native Gemini feature)
- **`execute_code`**: 💻 Code execution (native Gemini feature)
- **Custom tools**: Easy to add domain-specific capabilities

## 🚀 Getting Started

### Prerequisites
```bash
pip install genai-processors pyaudio
export GOOGLE_API_KEY="your_api_key_here"
```

### Basic Usage
```bash
# Camera mode (default)
python leonidas/leonidas_v2_cli.py

# Screen capture mode
python leonidas/leonidas_v2_cli.py --mode screen

# Debug mode
python leonidas/leonidas_v2_cli.py --debug
```

### Programmatic Usage
```python
import asyncio
from leonidas import leonidas_v2

async def main():
    api_key = "your_api_key"
    agent = leonidas_v2.create_leonidas_agent_v2(api_key)
    
    # Run the agent
    async for part in agent(input_stream):
        # Handle responses
        pass

asyncio.run(main())
```

## 💬 Conversation Examples

### Natural Interaction
```
User: "Olá Leonidas, como você está?"

Leonidas: [THINKING] Analysis: User is greeting me and asking about my status. 
          Reasoning: This is a friendly opening, I should respond warmly and 
          briefly indicate my readiness to help.
          Next Action: Respond with greeting and offer assistance.

Leonidas: [SPEAKING] Olá! Estou muito bem e pronto para colaborar. 
          Como posso ajudá-lo hoje?
```

### Technical Collaboration
```
User: "Preciso revisar esta arquitetura de microserviços"

Leonidas: [THINKING] Analysis: User wants architecture review. I can see their 
          screen and should analyze what's visible.
          Reasoning: This requires careful analysis and structured feedback.
          Next Action: Change to analyzing state and provide detailed review.

Leonidas: [STATE CHANGE] listening → analyzing (Architecture review requested)

Leonidas: [SPEAKING] Perfeito! Vou analisar a arquitetura que você está 
          mostrando. Vejo alguns pontos interessantes aqui...
```

## 🔧 Configuration

### Model Settings
- **Model**: `gemini-live-2.5-flash-preview`
- **Language**: Portuguese Brazilian
- **Voice**: Kore (professional, clear)
- **Audio**: 16kHz input, 24kHz output
- **Resolution**: Medium (balanced quality/performance)

### Behavioral States
- **listening**: Default state, responds when addressed
- **commentating**: Proactive analysis and suggestions
- **paused**: Temporarily inactive
- **analyzing**: Deep focus on specific task

## 🎛️ Advanced Features

### Conversation Memory
- Maintains history of interactions
- Context-aware responses
- Topic continuity across sessions

### Performance Monitoring
- Tool usage statistics
- State change tracking
- Response time metrics
- Conversation turn counting

### Extensibility
- Easy to add new tools
- Modular I/O system
- Plugin architecture ready
- Future-proof design

## 🔍 Debugging

### Console Output
```
🧠 LEONIDAS THINKING:
   Analysis: User is asking about code optimization
   Reasoning: I should analyze the visible code and provide specific suggestions
   Next Action: Provide structured optimization recommendations

🗣️ LEONIDAS SPEAKING (analytical): Vejo algumas oportunidades de otimização...

🔄 STATE CHANGE: listening → analyzing (Code optimization focus)

📋 CONTEXT REQUEST (conversation_history): {...}
```

### Debug Mode
```bash
python leonidas/leonidas_v2_cli.py --debug
```

## 🚧 Migration from v1

### Key Differences
1. **No more proactive commenting** - Model decides when to speak
2. **Tool-based interaction** - All actions go through tools
3. **Modular architecture** - Easy to extend and modify
4. **Self-managed state** - Model controls its own behavior
5. **Explicit thinking** - Reasoning is externalized

### Compatibility
- Same API key and basic setup
- Same audio/video requirements
- Improved conversation quality
- Better resource usage

## 🔮 Future Roadmap

### Phase 1 (Current)
- ✅ Modular architecture
- ✅ Advanced tool system
- ✅ THINK-ACT cycle
- ✅ Self-state management

### Phase 2 (Planned)
- 🔄 Multi-feed input support
- 🔄 Advanced memory system
- 🔄 Custom tool plugins
- 🔄 Performance optimizations

### Phase 3 (Future)
- 📋 Robotics integration hooks
- 📋 Multi-modal output
- 📋 Distributed processing
- 📋 Advanced AI capabilities

## 🤝 Contributing

Leonidas v2 is designed for extensibility:

1. **Adding Tools**: Extend the tool system in `LeonidasOrchestrator`
2. **Input Sources**: Modify `InputManager` for new input types
3. **Output Destinations**: Extend `OutputManager` for new outputs
4. **Prompt Engineering**: Enhance `LEONIDAS_SYSTEM_PROMPT`

## 📄 License

Licensed under the Apache License, Version 2.0. See the original license headers in the source files.

---

**Leonidas v2** - Where AI collaboration meets human-like intelligence. 🚀