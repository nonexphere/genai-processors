# Leonidas v2 Refactoring Specification

## Mission Statement

Transform the current Leonidas "commentator" into a modular, fluid conversational agent that thinks, acts, and collaborates like a human partner using genai-processors architecture.

## Current State Analysis

The existing system is a monolithic `LeonidasAgent` that:
- Manages complex state machine logic internally
- Handles event detection, live API communication, and audio processing in one class
- Acts as a "commentator" rather than a collaborative partner
- Has tightly coupled I/O and business logic

## Target Architecture

### Core Principles
1. **Modular Design**: Separate concerns into specialized processors
2. **Model Autonomy**: Give Gemini model control over its own state and behavior
3. **THINK-ACT Cycle**: Force explicit reasoning before actions
4. **Fluid Conversation**: Natural, contextually aware interactions
5. **Future-Ready**: Prepare for multi-feed, robotics, and advanced features

### Architecture Components

```
InputManager → LeonidasOrchestrator → OutputManager
     ↓              ↓                    ↓
  Hardware      Gemini Live API      Hardware
  Abstraction   + Tools/State        Abstraction
```

## Detailed Requirements

### 1. InputManager Processor
- **Purpose**: Abstract hardware input sources
- **Current**: Direct video/audio capture
- **Target**: Modular input abstraction ready for multi-feed
- **Implementation**: Encapsulate `video.VideoIn()` + `audio_io.PyAudioIn()`

### 2. LeonidasOrchestrator Processor  
- **Purpose**: Core intelligence and conversation management
- **Current**: Complex state machine in LeonidasAgent
- **Target**: Simple tool executor, let model manage its own state
- **Key Features**:
  - Gemini Live API integration
  - Tool execution (think, speak, change_state, get_context, get_time)
  - Conversation history management
  - Model-driven state control

### 3. OutputManager Processor
- **Purpose**: Abstract hardware output destinations  
- **Current**: Direct audio output
- **Target**: Modular output abstraction ready for multi-modal
- **Implementation**: Encapsulate `rate_limit_audio.RateLimitAudio()` + `audio_io.PyAudioOut()`

### 4. Enhanced Tool System
- **think**: Force model to externalize reasoning before acting
- **speak**: Explicit speech control with natural language
- **change_state**: Model controls its own behavior (listening/commentating/paused)
- **get_context**: Retrieve conversation history and system info
- **get_time**: Access current date/time information
- **google_search**: Leverage native search capabilities

### 5. Advanced Prompt Engineering
Create the most comprehensive, human-like prompt that:
- Establishes Leonidas as a collaborative software architect
- Defines clear operational cycles (PERCEIVE → THINK → ACT)
- Encourages natural, contextual responses
- Leverages all available model capabilities
- Maintains professional, analytical tone in Portuguese BR

## Implementation Plan

### Phase 1: Core Refactoring
1. Create modular processor architecture
2. Implement basic tool system
3. Develop comprehensive prompt
4. Test basic functionality

### Phase 2: Enhanced Intelligence
1. Add advanced tools (time, search integration)
2. Implement conversation memory
3. Optimize state management
4. Performance tuning

### Phase 3: Future Preparation
1. Prepare multi-feed architecture hooks
2. Add extensibility points for robotics
3. Implement advanced context management
4. Production hardening

## Success Criteria

1. **Modularity**: Clear separation of concerns with swappable components
2. **Fluidity**: Natural conversation flow without robotic responses
3. **Intelligence**: Model demonstrates reasoning through think tool
4. **Autonomy**: Model manages its own state and behavior
5. **Extensibility**: Easy to add new capabilities and I/O sources
6. **Performance**: Maintains or improves current response times
7. **Reliability**: Robust error handling and recovery

## Technical Specifications

- **Language**: Python 3.11+
- **Framework**: genai-processors
- **Model**: gemini-live-2.5-flash-preview
- **Audio**: 16kHz input, 24kHz output
- **Language**: Portuguese Brazilian
- **Voice**: Kore (professional, clear)
- **Architecture**: Async/await throughout
- **Error Handling**: Graceful degradation
- **Logging**: Comprehensive debug information

This refactoring establishes a solid foundation for future enhancements while immediately improving conversation quality and system maintainability.