# Leonidas Core v2 - Requirements Document

## Introduction

This document outlines the requirements for refactoring the Leonidas agent from a "live commentator" architecture to a modular, fluid conversational AI system. The goal is to create a human-like conversational partner that can think, act, and collaborate naturally using the genai-processors architecture as the foundation.

The current system is based on a monolithic "commentator" pattern that continuously generates commentary. The new system should behave more like a thoughtful human collaborator - observing, listening, thinking, and only speaking when it has something valuable to contribute or when directly engaged.

## Requirements

### Requirement 1: Modular Architecture

**User Story:** As a developer, I want the system to be built with modular, composable processors so that I can easily extend, modify, and maintain different aspects of the agent's behavior.

#### Acceptance Criteria

1. WHEN the system is initialized THEN it SHALL be composed of three distinct processor layers: InputManager, LeonidasOrchestrator, and OutputManager
2. WHEN a processor needs to be modified THEN the system SHALL allow hot-swapping of individual processors without affecting others
3. WHEN new capabilities are added THEN they SHALL integrate through the existing processor pipeline without requiring monolithic changes
4. WHEN the system processes content THEN each processor SHALL have a single, well-defined responsibility
5. WHEN processors communicate THEN they SHALL use the genai-processors stream-based architecture exclusively

### Requirement 2: Intelligent Conversation Flow

**User Story:** As a user, I want to interact with an AI that behaves like a thoughtful human partner, not a chatty commentator, so that our conversations feel natural and productive.

#### Acceptance Criteria

1. WHEN the user is not actively engaging THEN the agent SHALL remain in listening mode without generating unprompted commentary
2. WHEN the user speaks or asks a question THEN the agent SHALL respond appropriately and naturally
3. WHEN the agent needs to think about a complex topic THEN it SHALL use an explicit thinking process before responding
4. WHEN the agent changes its behavior mode THEN it SHALL do so through self-directed state management
5. WHEN the conversation requires context THEN the agent SHALL access and utilize relevant historical information

### Requirement 3: Advanced Tool Integration

**User Story:** As a user, I want the AI to have access to various tools and capabilities so that it can provide comprehensive assistance and information.

#### Acceptance Criteria

1. WHEN the agent needs to think through a problem THEN it SHALL use a dedicated 'think' tool to externalize its reasoning process
2. WHEN the agent needs to speak THEN it SHALL use a 'speak' tool with explicit text content
3. WHEN the agent needs to change its operational mode THEN it SHALL use a 'change_state' tool with valid state transitions
4. WHEN the agent needs contextual information THEN it SHALL use a 'get_context' tool to retrieve conversation history
5. WHEN the agent needs current information THEN it SHALL use available tools like 'get_current_time' for real-time data
6. WHEN the agent has access to Google Search THEN it SHALL utilize it appropriately for information gathering
7. WHEN tools are executed THEN they SHALL return structured responses that the agent can process and act upon

### Requirement 4: State Management and Consciousness

**User Story:** As a user, I want the AI to be aware of its own state and behavior so that it can adapt appropriately to different situations and contexts.

#### Acceptance Criteria

1. WHEN the system starts THEN the agent SHALL begin in a 'listening' state
2. WHEN the agent is actively providing commentary or analysis THEN it SHALL be in a 'commentating' state
3. WHEN the agent needs to pause and wait THEN it SHALL be in a 'paused' state
4. WHEN the agent transitions between states THEN it SHALL do so through explicit self-directed commands
5. WHEN the agent is in any state THEN it SHALL be able to respond to direct user input appropriately

### Requirement 5: Context Awareness and Memory

**User Story:** As a user, I want the AI to remember our conversation and maintain context so that our interactions build upon previous exchanges.

#### Acceptance Criteria

1. WHEN conversations occur THEN the system SHALL maintain a rolling context window of recent interactions
2. WHEN the agent needs to reference previous information THEN it SHALL be able to access conversation history
3. WHEN context becomes too large THEN the system SHALL intelligently compress older information while preserving key details
4. WHEN the agent provides responses THEN they SHALL be informed by relevant contextual information
5. WHEN multiple conversation threads exist THEN the system SHALL maintain appropriate context separation

### Requirement 6: Multi-Modal Input Processing

**User Story:** As a user, I want to interact with the AI through multiple channels (audio, video, screen sharing) so that it can understand my full context and provide better assistance.

#### Acceptance Criteria

1. WHEN audio input is provided THEN the system SHALL process it through the InputManager with appropriate format conversion
2. WHEN video input is provided THEN the system SHALL process visual information and integrate it with conversation context
3. WHEN screen sharing is active THEN the system SHALL understand visual content and reference it appropriately
4. WHEN multiple input modalities are active THEN the system SHALL synchronize and correlate information across channels
5. WHEN input processing fails THEN the system SHALL gracefully handle errors without breaking the conversation flow

### Requirement 7: Natural Audio Output

**User Story:** As a user, I want the AI's speech to sound natural and be properly timed so that conversations feel smooth and human-like.

#### Acceptance Criteria

1. WHEN the agent speaks THEN audio output SHALL be rate-limited to natural speaking speed
2. WHEN the user interrupts THEN the agent SHALL stop speaking immediately and listen
3. WHEN audio is generated THEN it SHALL be processed through the OutputManager for consistent delivery
4. WHEN multiple audio streams exist THEN the system SHALL manage them without conflicts or overlaps
5. WHEN audio processing fails THEN the system SHALL provide appropriate fallback behavior

### Requirement 8: Extensibility and Future-Proofing

**User Story:** As a developer, I want the architecture to support future enhancements like robotics integration and multiple data feeds without requiring complete rewrites.

#### Acceptance Criteria

1. WHEN new input sources are added THEN they SHALL integrate through the InputManager interface
2. WHEN new output capabilities are needed THEN they SHALL integrate through the OutputManager interface
3. WHEN new cognitive capabilities are required THEN they SHALL integrate through the processor pipeline
4. WHEN the system needs to scale THEN the modular architecture SHALL support horizontal scaling
5. WHEN integration with external systems is needed THEN the tool system SHALL provide appropriate extension points

### Requirement 9: Performance and Reliability

**User Story:** As a user, I want the AI to respond quickly and reliably so that conversations feel natural and productive.

#### Acceptance Criteria

1. WHEN the user speaks THEN the agent SHALL respond within reasonable time limits (< 2 seconds for simple responses)
2. WHEN processing complex requests THEN the agent SHALL provide feedback about its thinking process
3. WHEN errors occur THEN the system SHALL handle them gracefully without breaking the conversation
4. WHEN the system is under load THEN it SHALL maintain responsive behavior through appropriate resource management
5. WHEN network issues occur THEN the system SHALL provide appropriate fallback behavior and recovery

### Requirement 10: Portuguese Language Excellence

**User Story:** As a Portuguese-speaking user, I want the AI to communicate fluently and naturally in Brazilian Portuguese with appropriate cultural context.

#### Acceptance Criteria

1. WHEN the agent communicates THEN it SHALL use fluent Brazilian Portuguese with proper grammar and idioms
2. WHEN technical concepts are discussed THEN the agent SHALL use appropriate Portuguese technical terminology
3. WHEN the agent's personality is expressed THEN it SHALL reflect Brazilian cultural communication patterns
4. WHEN formal or informal communication is needed THEN the agent SHALL adapt its language register appropriately
5. WHEN the agent makes mistakes THEN it SHALL acknowledge and correct them in natural Portuguese