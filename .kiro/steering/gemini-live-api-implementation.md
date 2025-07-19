# Gemini Live API Implementation Patterns

## 📋 **GEMINI LIVE API COMPLETE IMPLEMENTATION GUIDE**

This steering rule provides comprehensive implementation patterns, best practices, and code templates for integrating Gemini Live API in real-time applications like Leonidas.

## 🏗️ **CORE ARCHITECTURE PATTERNS**

### **1. WebSocket Connection Management**

#### **Basic Connection Pattern**
```python
import asyncio
from google import genai
from google.genai import types

class LiveAPIManager:
    def __init__(self, api_key: str, model: str):
        self.client = genai.Client(api_key=api_key)
        self.model = model
        self.session = None
        self.is_connected = False
    
    async def connect(self, config: types.LiveConnectConfig):
        """Establish connection with retry logic."""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                self.session = await self.client.aio.live.connect(
                    model=self.model, 
                    config=config
                )
                self.is_connected = True
                return self.session
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)
    
    async def disconnect(self):
        """Graceful disconnection."""
        if self.session and self.is_connected:
            await self.session.close()
            self.is_connected = False
```

#### **Robust Session Management**
```python
class RobustLiveSession:
    def __init__(self, api_key: str, model: str, config: types.LiveConnectConfig):
        self.api_key = api_key
        self.model = model
        self.config = config
        self.client = genai.Client(api_key=api_key)
        self.session = None
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
    
    async def __aenter__(self):
        await self._connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def _connect(self):
        """Connect with exponential backoff."""
        while self.reconnect_attempts < self.max_reconnect_attempts:
            try:
                self.session = await self.client.aio.live.connect(
                    model=self.model,
                    config=self.config
                )
                self.reconnect_attempts = 0  # Reset on successful connection
                return
            except Exception as e:
                self.reconnect_attempts += 1
                wait_time = min(30, 2 ** self.reconnect_attempts)
                await asyncio.sleep(wait_time)
        
        raise ConnectionError("Failed to establish connection after maximum retries")
    
    async def send_audio(self, audio_data: bytes, mime_type: str = "audio/pcm;rate=16000"):
        """Send audio with automatic reconnection."""
        try:
            await self.session.send_realtime_input(
                audio=types.Blob(data=audio_data, mime_type=mime_type)
            )
        except Exception as e:
            await self._handle_connection_error(e)
    
    async def _handle_connection_error(self, error):
        """Handle connection errors with reconnection."""
        print(f"Connection error: {error}")
        await self._connect()
```

### **2. Audio Processing Patterns**

#### **Real-time Audio Streaming**
```python
import pyaudio
import asyncio
from collections import deque

class RealTimeAudioProcessor:
    def __init__(self, sample_rate: int = 16000, chunk_size: int = 1024):
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.audio_queue = asyncio.Queue(maxsize=100)
        self.is_recording = False
        
        # PyAudio setup
        self.pyaudio = pyaudio.PyAudio()
        self.input_stream = None
        self.output_stream = None
    
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """PyAudio callback for input."""
        if self.is_recording:
            try:
                self.audio_queue.put_nowait(in_data)
            except asyncio.QueueFull:
                pass  # Drop frames if queue is full
        return (None, pyaudio.paContinue)
    
    async def start_recording(self):
        """Start audio recording."""
        self.input_stream = self.pyaudio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.chunk_size,
            stream_callback=self._audio_callback
        )
        self.is_recording = True
        self.input_stream.start_stream()
    
    async def stop_recording(self):
        """Stop audio recording."""
        self.is_recording = False
        if self.input_stream:
            self.input_stream.stop_stream()
            self.input_stream.close()
    
    async def get_audio_chunk(self) -> bytes:
        """Get next audio chunk."""
        return await self.audio_queue.get()
    
    def setup_output_stream(self):
        """Setup audio output stream."""
        self.output_stream = self.pyaudio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=24000,  # Gemini outputs at 24kHz
            output=True,
            frames_per_buffer=1024
        )
    
    def play_audio(self, audio_data: bytes):
        """Play audio data."""
        if self.output_stream:
            self.output_stream.write(audio_data)
```

#### **Audio Format Conversion**
```python
import librosa
import soundfile as sf
import io

class AudioConverter:
    @staticmethod
    def convert_to_pcm_16khz(audio_file_path: str) -> bytes:
        """Convert audio file to PCM 16kHz format."""
        # Load audio file
        y, sr = librosa.load(audio_file_path, sr=16000)
        
        # Convert to PCM format
        buffer = io.BytesIO()
        sf.write(buffer, y, sr, format='RAW', subtype='PCM_16')
        buffer.seek(0)
        return buffer.read()
    
    @staticmethod
    def save_pcm_as_wav(pcm_data: bytes, output_path: str, sample_rate: int = 24000):
        """Save PCM data as WAV file."""
        import wave
        
        with wave.open(output_path, 'wb') as wf:
            wf.setnchannels(1)  # Mono
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(sample_rate)
            wf.writeframes(pcm_data)
    
    @staticmethod
    def calculate_audio_duration(audio_data: bytes, sample_rate: int) -> float:
        """Calculate audio duration in seconds."""
        # 2 bytes per sample (16-bit), 1 channel
        return len(audio_data) / (2 * sample_rate)
```

### **3. Voice Activity Detection (VAD) Patterns**

#### **Custom VAD Configuration**
```python
def create_vad_config(sensitivity: str = "medium") -> dict:
    """Create VAD configuration based on sensitivity level."""
    
    sensitivity_configs = {
        "high": {
            "start_of_speech_sensitivity": types.StartSensitivity.START_SENSITIVITY_HIGH,
            "end_of_speech_sensitivity": types.EndSensitivity.END_SENSITIVITY_HIGH,
            "prefix_padding_ms": 10,
            "silence_duration_ms": 50
        },
        "medium": {
            "start_of_speech_sensitivity": types.StartSensitivity.START_SENSITIVITY_MEDIUM,
            "end_of_speech_sensitivity": types.EndSensitivity.END_SENSITIVITY_MEDIUM,
            "prefix_padding_ms": 20,
            "silence_duration_ms": 100
        },
        "low": {
            "start_of_speech_sensitivity": types.StartSensitivity.START_SENSITIVITY_LOW,
            "end_of_speech_sensitivity": types.EndSensitivity.END_SENSITIVITY_LOW,
            "prefix_padding_ms": 50,
            "silence_duration_ms": 200
        }
    }
    
    return {
        "realtime_input_config": {
            "automatic_activity_detection": {
                "disabled": False,
                **sensitivity_configs[sensitivity]
            }
        }
    }
```

#### **Manual VAD Control**
```python
class ManualVADController:
    def __init__(self, session):
        self.session = session
        self.is_speaking = False
    
    async def start_speaking(self):
        """Signal start of speech."""
        if not self.is_speaking:
            await self.session.send_realtime_input(
                activity_start=types.ActivityStart()
            )
            self.is_speaking = True
    
    async def end_speaking(self):
        """Signal end of speech."""
        if self.is_speaking:
            await self.session.send_realtime_input(
                activity_end=types.ActivityEnd()
            )
            self.is_speaking = False
    
    async def send_audio_with_activity(self, audio_data: bytes):
        """Send audio with manual activity control."""
        await self.start_speaking()
        await self.session.send_realtime_input(
            audio=types.Blob(data=audio_data, mime_type="audio/pcm;rate=16000")
        )
        # Note: Call end_speaking() when done with audio stream
```

### **4. Function Calling Patterns**

#### **Async Function Implementation**
```python
class AsyncFunctionHandler:
    def __init__(self, session):
        self.session = session
        self.active_functions = {}
    
    async def register_function(self, name: str, description: str, behavior: str = "NON_BLOCKING"):
        """Register an async function."""
        return types.FunctionDeclaration(
            name=name,
            description=description,
            behavior=behavior
        )
    
    async def handle_function_call(self, function_call):
        """Handle incoming function call."""
        function_name = function_call.name
        function_id = function_call.id
        
        # Store active function
        self.active_functions[function_id] = {
            'name': function_name,
            'start_time': time.time()
        }
        
        # Execute function based on name
        if function_name == "start_commentating":
            await self._handle_start_commentating(function_id, function_call.args)
        elif function_name == "wait_for_user":
            await self._handle_wait_for_user(function_id)
        else:
            await self._handle_unknown_function(function_id, function_name)
    
    async def _handle_start_commentating(self, function_id: str, args: dict):
        """Handle start_commentating function."""
        message = args.get('message', 'Continue analysis...')
        
        # Send function response
        await self.session.send_tool_response(
            function_responses=[
                types.FunctionResponse(
                    id=function_id,
                    name='start_commentating',
                    response={'output': message}
                )
            ]
        )
    
    async def _handle_wait_for_user(self, function_id: str):
        """Handle wait_for_user function."""
        # Send silent response
        await self.session.send_tool_response(
            function_responses=[
                types.FunctionResponse(
                    id=function_id,
                    name='wait_for_user',
                    response={}
                )
            ]
        )
    
    async def cancel_function(self, function_id: str):
        """Cancel an active function."""
        if function_id in self.active_functions:
            del self.active_functions[function_id]
```

#### **Function Response Scheduling**
```python
class FunctionScheduler:
    def __init__(self, session):
        self.session = session
        self.scheduled_functions = {}
    
    async def schedule_function_response(
        self, 
        function_id: str, 
        response: dict, 
        scheduling: types.FunctionResponseScheduling = types.FunctionResponseScheduling.WHEN_IDLE,
        delay_seconds: float = 0
    ):
        """Schedule a function response."""
        
        if delay_seconds > 0:
            await asyncio.sleep(delay_seconds)
        
        await self.session.send_tool_response(
            function_responses=[
                types.FunctionResponse(
                    id=function_id,
                    name=self.scheduled_functions.get(function_id, {}).get('name', 'unknown'),
                    response=response,
                    scheduling=scheduling
                )
            ]
        )
    
    def get_scheduling_strategy(self, function_name: str) -> types.FunctionResponseScheduling:
        """Get appropriate scheduling strategy for function."""
        strategies = {
            'start_commentating': types.FunctionResponseScheduling.WHEN_IDLE,
            'wait_for_user': types.FunctionResponseScheduling.SILENT,
            'interrupt_current': types.FunctionResponseScheduling.INTERRUPT,
            'immediate_response': types.FunctionResponseScheduling.IMMEDIATE
        }
        
        return strategies.get(function_name, types.FunctionResponseScheduling.WHEN_IDLE)
```

### **5. Interruption Handling Patterns**

#### **Graceful Interruption Management**
```python
class InterruptionManager:
    def __init__(self):
        self.current_generation = None
        self.audio_queue = deque()
        self.is_playing = False
    
    async def handle_interruption(self, response):
        """Handle interruption from server."""
        if response.server_content.interrupted:
            # Stop current audio playback
            await self.stop_current_playback()
            
            # Clear audio queue
            self.audio_queue.clear()
            
            # Reset generation state
            self.current_generation = None
            
            print("Generation interrupted - ready for new input")
    
    async def stop_current_playback(self):
        """Stop current audio playback."""
        self.is_playing = False
        # Implementation depends on audio system
        # For PyAudio: stop and clear stream
    
    async def queue_audio_chunk(self, audio_data: bytes):
        """Queue audio chunk for playback."""
        if not self.is_playing:
            return  # Don't queue if interrupted
        
        self.audio_queue.append(audio_data)
    
    async def start_new_generation(self, generation_id: str):
        """Start tracking new generation."""
        self.current_generation = {
            'id': generation_id,
            'start_time': time.time(),
            'chunks_received': 0
        }
        self.is_playing = True
```

#### **Interruption Recovery**
```python
class InterruptionRecovery:
    def __init__(self, session):
        self.session = session
        self.conversation_state = []
        self.last_complete_turn = None
    
    async def save_conversation_state(self, turn_data):
        """Save conversation state for recovery."""
        self.conversation_state.append({
            'timestamp': time.time(),
            'turn_data': turn_data,
            'completed': False
        })
    
    async def mark_turn_complete(self):
        """Mark current turn as complete."""
        if self.conversation_state:
            self.conversation_state[-1]['completed'] = True
            self.last_complete_turn = self.conversation_state[-1]
    
    async def recover_from_interruption(self):
        """Recover conversation state after interruption."""
        # Find last complete turn
        complete_turns = [turn for turn in self.conversation_state if turn['completed']]
        
        if complete_turns:
            # Restore context from last complete turn
            last_turn = complete_turns[-1]
            await self._restore_context(last_turn['turn_data'])
    
    async def _restore_context(self, turn_data):
        """Restore conversation context."""
        # Send context restoration message
        await self.session.send_client_content(
            turns=turn_data,
            turn_complete=False
        )
```

### **6. Multi-Modal Processing Patterns**

#### **Audio + Video Processing**
```python
class MultiModalProcessor:
    def __init__(self, session):
        self.session = session
        self.video_processor = None
        self.audio_processor = None
    
    async def process_audio_video_stream(self, audio_stream, video_stream):
        """Process combined audio and video streams."""
        audio_task = asyncio.create_task(self._process_audio_stream(audio_stream))
        video_task = asyncio.create_task(self._process_video_stream(video_stream))
        
        try:
            await asyncio.gather(audio_task, video_task)
        except Exception as e:
            audio_task.cancel()
            video_task.cancel()
            raise
    
    async def _process_audio_stream(self, audio_stream):
        """Process audio stream."""
        async for audio_chunk in audio_stream:
            await self.session.send_realtime_input(
                audio=types.Blob(
                    data=audio_chunk,
                    mime_type="audio/pcm;rate=16000"
                )
            )
    
    async def _process_video_stream(self, video_stream):
        """Process video stream."""
        async for video_frame in video_stream:
            # Convert frame to appropriate format
            frame_data = self._convert_video_frame(video_frame)
            
            await self.session.send_realtime_input(
                video=types.Blob(
                    data=frame_data,
                    mime_type="image/jpeg"
                )
            )
    
    def _convert_video_frame(self, frame) -> bytes:
        """Convert video frame to bytes."""
        # Implementation depends on video source
        # For OpenCV: cv2.imencode('.jpg', frame)[1].tobytes()
        pass
```

#### **Context Management for Long Sessions**
```python
class SessionContextManager:
    def __init__(self, max_context_tokens: int = 32000):
        self.max_context_tokens = max_context_tokens
        self.context_history = []
        self.current_token_count = 0
    
    async def add_to_context(self, content, estimated_tokens: int):
        """Add content to context with token management."""
        # Check if we need to compress context
        if self.current_token_count + estimated_tokens > self.max_context_tokens:
            await self._compress_context()
        
        self.context_history.append({
            'content': content,
            'tokens': estimated_tokens,
            'timestamp': time.time()
        })
        self.current_token_count += estimated_tokens
    
    async def _compress_context(self):
        """Compress older context to make room."""
        # Keep recent 50% of context
        keep_count = len(self.context_history) // 2
        
        if keep_count > 0:
            # Create summary of older context
            old_context = self.context_history[:-keep_count]
            summary = await self._create_context_summary(old_context)
            
            # Replace old context with summary
            self.context_history = [summary] + self.context_history[-keep_count:]
            self.current_token_count = sum(item['tokens'] for item in self.context_history)
    
    async def _create_context_summary(self, context_items) -> dict:
        """Create summary of context items."""
        # Simple summarization - in practice, use a summarization model
        total_tokens = sum(item['tokens'] for item in context_items)
        
        return {
            'content': f"[Summary of {len(context_items)} previous interactions]",
            'tokens': min(100, total_tokens // 10),  # Compressed representation
            'timestamp': time.time(),
            'is_summary': True
        }
```

## 🎯 **COMPLETE IMPLEMENTATION EXAMPLE**

### **Production-Ready Live API Client**
```python
class ProductionLiveAPIClient:
    def __init__(self, api_key: str, model: str = "gemini-live-2.5-flash-preview"):
        self.api_key = api_key
        self.model = model
        self.client = genai.Client(api_key=api_key)
        
        # Components
        self.audio_processor = RealTimeAudioProcessor()
        self.interruption_manager = InterruptionManager()
        self.function_handler = AsyncFunctionHandler(None)
        self.context_manager = SessionContextManager()
        
        # State
        self.session = None
        self.is_active = False
        self.metrics = {
            'messages_sent': 0,
            'messages_received': 0,
            'interruptions': 0,
            'function_calls': 0
        }
    
    async def start_session(self, config: types.LiveConnectConfig):
        """Start a new Live API session."""
        try:
            # Establish connection
            self.session = await self.client.aio.live.connect(
                model=self.model,
                config=config
            )
            
            # Setup function handler
            self.function_handler.session = self.session
            
            # Start audio processing
            await self.audio_processor.start_recording()
            self.audio_processor.setup_output_stream()
            
            self.is_active = True
            
            # Start processing loops
            await asyncio.gather(
                self._audio_input_loop(),
                self._response_processing_loop(),
                return_exceptions=True
            )
            
        except Exception as e:
            await self.stop_session()
            raise
    
    async def _audio_input_loop(self):
        """Process audio input continuously."""
        while self.is_active:
            try:
                audio_chunk = await self.audio_processor.get_audio_chunk()
                
                await self.session.send_realtime_input(
                    audio=types.Blob(
                        data=audio_chunk,
                        mime_type="audio/pcm;rate=16000"
                    )
                )
                
                self.metrics['messages_sent'] += 1
                
            except Exception as e:
                print(f"Audio input error: {e}")
                break
    
    async def _response_processing_loop(self):
        """Process responses from the API."""
        async for response in self.session.receive():
            try:
                await self._handle_response(response)
                self.metrics['messages_received'] += 1
                
            except Exception as e:
                print(f"Response processing error: {e}")
    
    async def _handle_response(self, response):
        """Handle different types of responses."""
        # Handle interruptions
        if response.server_content.interrupted:
            await self.interruption_manager.handle_interruption(response)
            self.metrics['interruptions'] += 1
            return
        
        # Handle function calls
        if response.tool_call:
            await self.function_handler.handle_function_call(response.tool_call)
            self.metrics['function_calls'] += 1
            return
        
        # Handle audio output
        if response.data:
            self.audio_processor.play_audio(response.data)
        
        # Handle text output
        if response.text:
            print(f"Model: {response.text}")
        
        # Handle transcriptions
        if response.server_content.output_transcription:
            print(f"Transcript: {response.server_content.output_transcription.text}")
    
    async def stop_session(self):
        """Stop the current session gracefully."""
        self.is_active = False
        
        if self.audio_processor:
            await self.audio_processor.stop_recording()
        
        if self.session:
            await self.session.close()
        
        print(f"Session ended. Metrics: {self.metrics}")

# Usage example
async def main():
    config = types.LiveConnectConfig(
        response_modalities=["AUDIO"],
        system_instruction="You are a helpful AI assistant.",
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
            turn_coverage='TURN_INCLUDES_ALL_INPUT'
        )
    )
    
    client = ProductionLiveAPIClient(api_key="your_api_key")
    await client.start_session(config)

if __name__ == "__main__":
    asyncio.run(main())
```

This comprehensive implementation guide provides all the patterns and code templates needed for robust Gemini Live API integration in production applications.