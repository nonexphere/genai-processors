# Gemini State Machine & Event-Driven Patterns

## **STATE MACHINE & EVENT-DRIVEN ARCHITECTURE GUIDE**

This steering rule provides comprehensive patterns for implementing sophisticated state machines and event-driven architectures in Gemini Live API applications, based on analysis of Leonidas and production implementations.

## **STATE MACHINE ARCHITECTURE**

### **1. Conversational Agent State Machine**

#### **Core State Machine Implementation**
```python
import enum
import dataclasses
import time
from typing import Any, Optional

class AgentState(enum.Enum):
    """Core states for conversational agents."""
    OFF = "off"
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    SPEAKING = "speaking"
    WAITING_FOR_USER = "waiting_for_user"
    INTERRUPTED = "interrupted"
    ERROR = "error"

class AgentAction(enum.Enum):
    """Actions that trigger state transitions."""
    START = "start"
    STOP = "stop"
    USER_SPEECH_DETECTED = "user_speech_detected"
    USER_SPEECH_ENDED = "user_speech_ended"
    START_PROCESSING = "start_processing"
    START_SPEAKING = "start_speaking"
    FINISH_SPEAKING = "finish_speaking"
    INTERRUPT = "interrupt"
    WAIT_FOR_USER = "wait_for_user"
    USER_RESPONDED = "user_responded"
    ERROR_OCCURRED = "error_occurred"
    RECOVER = "recover"

@dataclasses.dataclass
class StateTransition:
    """Represents a state transition with metadata."""
    from_state: AgentState
    action: AgentAction
    to_state: AgentState
    timestamp: float
    metadata: dict = dataclasses.field(default_factory=dict)

class ConversationalStateMachine:
    """Advanced state machine for conversational agents."""
    
    def __init__(self, initial_state: AgentState = AgentState.OFF):
        self.current_state = initial_state
        self.previous_state = None
        self.state_history = collections.deque(maxlen=100)
        self.transition_handlers = {}
        self.state_entry_handlers = {}
        self.state_exit_handlers = {}
        
        # State timing
        self.state_start_time = time.time()
        self.state_durations = collections.defaultdict(list)
        
        # Define valid transitions
        self.valid_transitions = {
            (AgentState.OFF, AgentAction.START): AgentState.IDLE,
            (AgentState.IDLE, AgentAction.USER_SPEECH_DETECTED): AgentState.LISTENING,
            (AgentState.IDLE, AgentAction.START_PROCESSING): AgentState.PROCESSING,
            (AgentState.LISTENING, AgentAction.USER_SPEECH_ENDED): AgentState.PROCESSING,
            (AgentState.LISTENING, AgentAction.INTERRUPT): AgentState.INTERRUPTED,
            (AgentState.PROCESSING, AgentAction.START_SPEAKING): AgentState.SPEAKING,
            (AgentState.PROCESSING, AgentAction.WAIT_FOR_USER): AgentState.WAITING_FOR_USER,
            (AgentState.PROCESSING, AgentAction.INTERRUPT): AgentState.INTERRUPTED,
            (AgentState.SPEAKING, AgentAction.FINISH_SPEAKING): AgentState.IDLE,
            (AgentState.SPEAKING, AgentAction.INTERRUPT): AgentState.INTERRUPTED,
            (AgentState.WAITING_FOR_USER, AgentAction.USER_RESPONDED): AgentState.PROCESSING,
            (AgentState.WAITING_FOR_USER, AgentAction.INTERRUPT): AgentState.INTERRUPTED,
            (AgentState.INTERRUPTED, AgentAction.RECOVER): AgentState.IDLE,
            # Error handling
            (AgentState.LISTENING, AgentAction.ERROR_OCCURRED): AgentState.ERROR,
            (AgentState.PROCESSING, AgentAction.ERROR_OCCURRED): AgentState.ERROR,
            (AgentState.SPEAKING, AgentAction.ERROR_OCCURRED): AgentState.ERROR,
            (AgentState.ERROR, AgentAction.RECOVER): AgentState.IDLE,
            # Stop from any state
            (AgentState.IDLE, AgentAction.STOP): AgentState.OFF,
            (AgentState.LISTENING, AgentAction.STOP): AgentState.OFF,
            (AgentState.PROCESSING, AgentAction.STOP): AgentState.OFF,
            (AgentState.SPEAKING, AgentAction.STOP): AgentState.OFF,
            (AgentState.WAITING_FOR_USER, AgentAction.STOP): AgentState.OFF,
            (AgentState.INTERRUPTED, AgentAction.STOP): AgentState.OFF,
            (AgentState.ERROR, AgentAction.STOP): AgentState.OFF,
        }
    
    async def transition(self, action: AgentAction, metadata: dict = None) -> bool:
        """Execute state transition."""
        transition_key = (self.current_state, action)
        
        if transition_key not in self.valid_transitions:
            logging.warning(f"Invalid transition: {self.current_state} + {action}")
            return False
        
        new_state = self.valid_transitions[transition_key]
        
        # Record state duration
        current_time = time.time()
        duration = current_time - self.state_start_time
        self.state_durations[self.current_state].append(duration)
        
        # Create transition record
        transition = StateTransition(
            from_state=self.current_state,
            action=action,
            to_state=new_state,
            timestamp=current_time,
            metadata=metadata or {}
        )
        
        # Execute exit handler for current state
        await self._execute_exit_handler(self.current_state, transition)
        
        # Execute transition handler
        await self._execute_transition_handler(transition)
        
        # Update state
        self.previous_state = self.current_state
        self.current_state = new_state
        self.state_start_time = current_time
        self.state_history.append(transition)
        
        # Execute entry handler for new state
        await self._execute_entry_handler(new_state, transition)
        
        logging.debug(f"State transition: {transition.from_state} -> {transition.to_state} ({action})")
        return True
    
    def register_transition_handler(self, from_state: AgentState, action: AgentAction, handler):
        """Register handler for specific transition."""
        key = (from_state, action)
        self.transition_handlers[key] = handler
    
    def register_state_entry_handler(self, state: AgentState, handler):
        """Register handler for state entry."""
        self.state_entry_handlers[state] = handler
    
    def register_state_exit_handler(self, state: AgentState, handler):
        """Register handler for state exit."""
        self.state_exit_handlers[state] = handler
    
    async def _execute_transition_handler(self, transition: StateTransition):
        """Execute transition-specific handler."""
        key = (transition.from_state, transition.action)
        if key in self.transition_handlers:
            try:
                await self.transition_handlers[key](transition)
            except Exception as e:
                logging.error(f"Transition handler error: {e}")
    
    async def _execute_entry_handler(self, state: AgentState, transition: StateTransition):
        """Execute state entry handler."""
        if state in self.state_entry_handlers:
            try:
                await self.state_entry_handlers[state](transition)
            except Exception as e:
                logging.error(f"State entry handler error: {e}")
    
    async def _execute_exit_handler(self, state: AgentState, transition: StateTransition):
        """Execute state exit handler."""
        if state in self.state_exit_handlers:
            try:
                await self.state_exit_handlers[state](transition)
            except Exception as e:
                logging.error(f"State exit handler error: {e}")
    
    def get_state_analytics(self) -> dict:
        """Get analytics about state machine behavior."""
        total_transitions = len(self.state_history)
        
        if total_transitions == 0:
            return {'status': 'no_data'}
        
        # Calculate state distribution
        state_counts = collections.defaultdict(int)
        for transition in self.state_history:
            state_counts[transition.from_state] += 1
        
        # Calculate average state durations
        avg_durations = {}
        for state, durations in self.state_durations.items():
            if durations:
                avg_durations[state.value] = sum(durations) / len(durations)
        
        # Find most common transitions
        transition_counts = collections.defaultdict(int)
        for transition in self.state_history:
            key = f"{transition.from_state.value} -> {transition.to_state.value}"
            transition_counts[key] += 1
        
        most_common_transitions = sorted(
            transition_counts.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:5]
        
        return {
            'current_state': self.current_state.value,
            'total_transitions': total_transitions,
            'state_distribution': {state.value: count for state, count in state_counts.items()},
            'average_state_durations': avg_durations,
            'most_common_transitions': most_common_transitions,
            'error_rate': state_counts[AgentState.ERROR] / total_transitions if total_transitions > 0 else 0
        }
```

### **2. Leonidas-Style Advanced State Machine**

#### **Production-Ready State Machine**
```python
class LeonidasStateMachine:
    """Advanced state machine based on Leonidas implementation patterns."""
    
    def __init__(self):
        self.state = AgentState.OFF
        self.generation_request_info = None
        self.ttft_history = collections.deque(maxlen=50)
        self.agent_id = None
        
        # Performance tracking
        self.performance_metrics = {
            'generation_count': 0,
            'interruption_count': 0,
            'error_count': 0,
            'average_ttft': 0.0
        }
    
    async def handle_generation_start(self, generation_type: str, metadata: dict = None):
        """Handle start of model generation."""
        self.generation_request_info = {
            'generation_start_time': time.time(),
            'generation_type': generation_type,
            'ttft': None,
            'audio_duration': 0.0,
            'metadata': metadata or {}
        }
        
        self.performance_metrics['generation_count'] += 1
        
        # Transition based on generation type
        if generation_type == 'user_request':
            await self.transition(AgentAction.START_PROCESSING, {'type': 'user_request'})
        elif generation_type == 'comment':
            await self.transition(AgentAction.START_PROCESSING, {'type': 'comment'})
        elif generation_type == 'interruption':
            await self.transition(AgentAction.INTERRUPT, {'type': 'interruption'})
    
    async def handle_first_audio_chunk(self, audio_data: bytes):
        """Handle first audio chunk (TTFT measurement)."""
        if self.generation_request_info and self.generation_request_info['ttft'] is None:
            current_time = time.time()
            ttft = current_time - self.generation_request_info['generation_start_time']
            
            self.generation_request_info['ttft'] = ttft
            self.ttft_history.append(ttft)
            
            # Update average TTFT
            self.performance_metrics['average_ttft'] = sum(self.ttft_history) / len(self.ttft_history)
            
            # Transition to speaking
            await self.transition(AgentAction.START_SPEAKING, {'ttft': ttft})
    
    async def handle_interruption(self):
        """Handle interruption event."""
        self.performance_metrics['interruption_count'] += 1
        await self.transition(AgentAction.INTERRUPT)
    
    async def handle_error(self, error: Exception):
        """Handle error condition."""
        self.performance_metrics['error_count'] += 1
        await self.transition(AgentAction.ERROR_OCCURRED, {'error': str(error)})
    
    def predict_next_ttft(self) -> float:
        """Predict next TTFT based on history."""
        if not self.ttft_history:
            return 0.5  # Default prediction
        
        import numpy as np
        avg = np.mean(self.ttft_history)
        std = np.std(self.ttft_history)
        
        # Conservative prediction (subtract std dev for lower bound)
        return max(0.1, avg - std)
    
    def get_tentative_trigger_time(self) -> Optional[float]:
        """Calculate when to trigger next comment."""
        if (self.state == AgentState.SPEAKING and 
            self.generation_request_info and 
            self.generation_request_info['ttft'] is not None):
            
            # Calculate when current speech will end
            speech_end_time = (
                self.generation_request_info['generation_start_time'] +
                self.generation_request_info['ttft'] +
                self.generation_request_info['audio_duration']
            )
            
            # Subtract predicted TTFT to trigger next comment early
            return speech_end_time - self.predict_next_ttft()
        
        return None
```

## **EVENT-DRIVEN ARCHITECTURE**

### **1. Event Detection and Processing**

#### **Advanced Event Detection System**
```python
class EventType(enum.Enum):
    """Types of events that can be detected."""
    USER_PRESENT = "user_present"
    USER_ABSENT = "user_absent"
    SCREEN_VISIBLE = "screen_visible"
    VISUAL_CHANGE = "visual_change"
    AUDIO_ACTIVITY = "audio_activity"
    INTERRUPTION_REQUEST = "interruption_request"
    FUNCTION_CALL = "function_call"
    ERROR = "error"

@dataclasses.dataclass
class Event:
    """Represents a detected event."""
    event_type: EventType
    timestamp: float
    confidence: float
    metadata: dict = dataclasses.field(default_factory=dict)
    source: str = "unknown"

class EventDetectionSystem:
    """Advanced event detection and processing system."""
    
    def __init__(self, detection_model: str = "gemini-2.5-flash-lite-preview-06-17"):
        self.detection_model = detection_model
        self.event_queue = asyncio.Queue(maxsize=1000)
        self.event_handlers = {}
        self.event_history = collections.deque(maxlen=1000)
        
        # Detection configuration
        self.detection_config = {
            'sensitivity': 'medium',
            'debounce_time': 0.5,  # seconds
            'confidence_threshold': 0.7
        }
        
        # Debouncing
        self.last_event_times = {}
        
        # Performance metrics
        self.detection_metrics = {
            'events_detected': 0,
            'events_processed': 0,
            'false_positives': 0,
            'processing_latency': collections.deque(maxlen=100)
        }
    
    async def detect_events(self, visual_input, audio_input=None) -> list[Event]:
        """Detect events from visual and audio input."""
        events = []
        detection_start = time.time()
        
        try:
            # Visual event detection
            if visual_input:
                visual_events = await self._detect_visual_events(visual_input)
                events.extend(visual_events)
            
            # Audio event detection
            if audio_input:
                audio_events = await self._detect_audio_events(audio_input)
                events.extend(audio_events)
            
            # Apply debouncing
            debounced_events = self._apply_debouncing(events)
            
            # Filter by confidence
            filtered_events = [
                event for event in debounced_events 
                if event.confidence >= self.detection_config['confidence_threshold']
            ]
            
            # Update metrics
            processing_time = time.time() - detection_start
            self.detection_metrics['processing_latency'].append(processing_time)
            self.detection_metrics['events_detected'] += len(filtered_events)
            
            return filtered_events
            
        except Exception as e:
            logging.error(f"Event detection error: {e}")
            return []
    
    async def _detect_visual_events(self, visual_input) -> list[Event]:
        """Detect events from visual input."""
        # This would integrate with the actual Gemini model
        # For now, we'll simulate the detection logic
        
        events = []
        current_time = time.time()
        
        # Simulate different types of visual events
        # In practice, this would call the Gemini model with appropriate prompts
        
        # Example: User presence detection
        user_present_confidence = await self._check_user_presence(visual_input)
        if user_present_confidence > 0.5:
            events.append(Event(
                event_type=EventType.USER_PRESENT,
                timestamp=current_time,
                confidence=user_present_confidence,
                metadata={'detection_method': 'visual'},
                source='visual_detector'
            ))
        
        # Example: Screen visibility detection
        screen_visible_confidence = await self._check_screen_visibility(visual_input)
        if screen_visible_confidence > 0.5:
            events.append(Event(
                event_type=EventType.SCREEN_VISIBLE,
                timestamp=current_time,
                confidence=screen_visible_confidence,
                metadata={'detection_method': 'visual'},
                source='visual_detector'
            ))
        
        return events
    
    async def _detect_audio_events(self, audio_input) -> list[Event]:
        """Detect events from audio input."""
        events = []
        current_time = time.time()
        
        # Example: Audio activity detection
        audio_activity_confidence = await self._check_audio_activity(audio_input)
        if audio_activity_confidence > 0.5:
            events.append(Event(
                event_type=EventType.AUDIO_ACTIVITY,
                timestamp=current_time,
                confidence=audio_activity_confidence,
                metadata={'detection_method': 'audio'},
                source='audio_detector'
            ))
        
        return events
    
    def _apply_debouncing(self, events: list[Event]) -> list[Event]:
        """Apply debouncing to prevent event spam."""
        debounced_events = []
        current_time = time.time()
        
        for event in events:
            event_key = f"{event.event_type}_{event.source}"
            last_time = self.last_event_times.get(event_key, 0)
            
            if current_time - last_time >= self.detection_config['debounce_time']:
                debounced_events.append(event)
                self.last_event_times[event_key] = current_time
        
        return debounced_events
    
    async def process_event(self, event: Event):
        """Process a detected event."""
        processing_start = time.time()
        
        try:
            # Add to history
            self.event_history.append(event)
            
            # Execute event handlers
            if event.event_type in self.event_handlers:
                handler = self.event_handlers[event.event_type]
                await handler(event)
            
            # Update metrics
            self.detection_metrics['events_processed'] += 1
            
        except Exception as e:
            logging.error(f"Event processing error: {e}")
        finally:
            processing_time = time.time() - processing_start
            self.detection_metrics['processing_latency'].append(processing_time)
    
    def register_event_handler(self, event_type: EventType, handler):
        """Register handler for specific event type."""
        self.event_handlers[event_type] = handler
    
    async def _check_user_presence(self, visual_input) -> float:
        """Check for user presence in visual input."""
        # Placeholder - would use actual Gemini model
        return 0.8  # Simulated confidence
    
    async def _check_screen_visibility(self, visual_input) -> float:
        """Check for screen visibility in visual input."""
        # Placeholder - would use actual Gemini model
        return 0.7  # Simulated confidence
    
    async def _check_audio_activity(self, audio_input) -> float:
        """Check for audio activity."""
        # Placeholder - would analyze audio data
        return 0.6  # Simulated confidence
```

### **2. Event-Driven State Coordination**

#### **Event-State Coordinator**
```python
class EventStateCoordinator:
    """Coordinates events with state machine transitions."""
    
    def __init__(self, state_machine: ConversationalStateMachine, event_system: EventDetectionSystem):
        self.state_machine = state_machine
        self.event_system = event_system
        self.coordination_rules = {}
        self.event_state_history = []
        
        # Register default coordination rules
        self._setup_default_rules()
    
    def _setup_default_rules(self):
        """Setup default event-to-state coordination rules."""
        # User presence events
        self.add_coordination_rule(
            EventType.USER_PRESENT,
            {AgentState.OFF: AgentAction.START, AgentState.IDLE: None}
        )
        
        # Audio activity events
        self.add_coordination_rule(
            EventType.AUDIO_ACTIVITY,
            {
                AgentState.IDLE: AgentAction.USER_SPEECH_DETECTED,
                AgentState.SPEAKING: AgentAction.INTERRUPT,
                AgentState.WAITING_FOR_USER: AgentAction.USER_RESPONDED
            }
        )
        
        # Visual change events
        self.add_coordination_rule(
            EventType.VISUAL_CHANGE,
            {
                AgentState.SPEAKING: AgentAction.INTERRUPT,
                AgentState.WAITING_FOR_USER: AgentAction.USER_RESPONDED
            }
        )
    
    def add_coordination_rule(self, event_type: EventType, state_action_map: dict):
        """Add coordination rule for event type."""
        self.coordination_rules[event_type] = state_action_map
    
    async def coordinate_event(self, event: Event):
        """Coordinate event with state machine."""
        current_state = self.state_machine.current_state
        
        if event.event_type in self.coordination_rules:
            state_action_map = self.coordination_rules[event.event_type]
            
            if current_state in state_action_map:
                action = state_action_map[current_state]
                
                if action is not None:
                    # Execute state transition
                    success = await self.state_machine.transition(
                        action, 
                        {'triggered_by_event': event.event_type.value, 'event_confidence': event.confidence}
                    )
                    
                    # Record coordination
                    self.event_state_history.append({
                        'timestamp': time.time(),
                        'event': event,
                        'state_before': current_state,
                        'action': action,
                        'state_after': self.state_machine.current_state,
                        'success': success
                    })
                    
                    return success
        
        return False
    
    async def start_coordination_loop(self):
        """Start the event-state coordination loop."""
        while True:
            try:
                # Get next event from event system
                event = await self.event_system.event_queue.get()
                
                # Coordinate with state machine
                await self.coordinate_event(event)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"Coordination loop error: {e}")
    
    def get_coordination_analytics(self) -> dict:
        """Get analytics about event-state coordination."""
        if not self.event_state_history:
            return {'status': 'no_data'}
        
        total_coordinations = len(self.event_state_history)
        successful_coordinations = len([h for h in self.event_state_history if h['success']])
        
        # Event type distribution
        event_type_counts = collections.defaultdict(int)
        for history in self.event_state_history:
            event_type_counts[history['event'].event_type.value] += 1
        
        # Most common event-action pairs
        event_action_counts = collections.defaultdict(int)
        for history in self.event_state_history:
            key = f"{history['event'].event_type.value} -> {history['action'].value}"
            event_action_counts[key] += 1
        
        return {
            'total_coordinations': total_coordinations,
            'success_rate': successful_coordinations / total_coordinations,
            'event_type_distribution': dict(event_type_counts),
            'common_event_actions': dict(sorted(event_action_counts.items(), key=lambda x: x[1], reverse=True)[:5])
        }
```

## 🔄 **ADVANCED PATTERNS**

### **Hierarchical State Machines**
```python
class HierarchicalStateMachine:
    """Hierarchical state machine with nested states."""
    
    def __init__(self):
        self.main_state_machine = ConversationalStateMachine()
        self.sub_state_machines = {}
        self.active_sub_machine = None
    
    def add_sub_state_machine(self, parent_state: AgentState, sub_machine: ConversationalStateMachine):
        """Add sub-state machine for a parent state."""
        self.sub_state_machines[parent_state] = sub_machine
    
    async def transition(self, action: AgentAction, metadata: dict = None):
        """Execute hierarchical state transition."""
        # Try sub-state machine first
        if self.active_sub_machine:
            if await self.active_sub_machine.transition(action, metadata):
                return True
        
        # Try main state machine
        old_state = self.main_state_machine.current_state
        success = await self.main_state_machine.transition(action, metadata)
        
        if success:
            new_state = self.main_state_machine.current_state
            
            # Activate sub-state machine if entering a state that has one
            if new_state in self.sub_state_machines:
                self.active_sub_machine = self.sub_state_machines[new_state]
            elif old_state in self.sub_state_machines:
                # Deactivate sub-state machine if leaving a state that had one
                self.active_sub_machine = None
        
        return success
```

This comprehensive state machine and event-driven architecture guide provides all the patterns needed for sophisticated real-time applications with proper state management and event coordination.
