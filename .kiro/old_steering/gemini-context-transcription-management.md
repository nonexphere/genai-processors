# Gemini Context Management & Real-time Transcription

## **CONTEXT MANAGEMENT & TRANSCRIPTION COMPLETE GUIDE**

This steering rule provides comprehensive patterns for managing context and real-time transcription in Gemini Live API applications, based on analysis of Leonidas and production implementations.

## **CONTEXT MANAGEMENT ARCHITECTURE**

### **1. Rolling Context Windows**

#### **Intelligent Context Compression**
```python
class IntelligentContextManager:
    def __init__(self, max_context_tokens: int = 32000, compression_threshold: float = 0.8):
        self.max_context_tokens = max_context_tokens
        self.compression_threshold = compression_threshold
        self.context_buffer = collections.deque(maxlen=1000)
        self.compressed_summaries = []
        self.current_token_count = 0
        self.importance_classifier = ImportanceClassifier()
    
    async def add_context_item(self, content: dict, estimated_tokens: int, importance: str = "normal"):
        """Add context item with intelligent management."""
        # Check if compression is needed
        if self.current_token_count + estimated_tokens > self.max_context_tokens * self.compression_threshold:
            await self._intelligent_compression()
        
        # Add importance metadata
        content['importance'] = importance
        content['timestamp'] = time.time()
        content['tokens'] = estimated_tokens
        
        self.context_buffer.append(content)
        self.current_token_count += estimated_tokens
    
    async def _intelligent_compression(self):
        """Compress context using importance-based selection."""
        if not self.context_buffer:
            return
        
        # Classify items by importance
        high_importance = []
        medium_importance = []
        low_importance = []
        
        for item in self.context_buffer:
            importance = await self.importance_classifier.classify(item)
            if importance == "high":
                high_importance.append(item)
            elif importance == "medium":
                medium_importance.append(item)
            else:
                low_importance.append(item)
        
        # Compress low importance items first
        items_to_compress = low_importance
        if len(items_to_compress) < len(self.context_buffer) * 0.3:
            # If not enough low importance items, add some medium importance
            items_to_compress.extend(medium_importance[:len(medium_importance)//2])
        
        if items_to_compress:
            # Create compressed summary
            summary = await self._create_intelligent_summary(items_to_compress)
            
            # Remove compressed items from buffer
            for item in items_to_compress:
                if item in self.context_buffer:
                    self.context_buffer.remove(item)
                    self.current_token_count -= item['tokens']
            
            # Add summary
            self.compressed_summaries.append(summary)
            self.current_token_count += summary['tokens']
    
    async def _create_intelligent_summary(self, items: list) -> dict:
        """Create intelligent summary preserving key information."""
        # Group items by type and importance
        conversations = [item for item in items if item.get('type') == 'conversation']
        events = [item for item in items if item.get('type') == 'event']
        functions = [item for item in items if item.get('type') == 'function_call']
        
        summary_parts = []
        
        # Summarize conversations
        if conversations:
            conv_summary = await self._summarize_conversations(conversations)
            summary_parts.append(conv_summary)
        
        # Preserve all events (they're usually important)
        if events:
            summary_parts.extend([f"Event: {event['content']}" for event in events])
        
        # Preserve function call results
        if functions:
            summary_parts.extend([f"Function: {func['name']} -> {func['result']}" for func in functions])
        
        summary_text = "\n".join(summary_parts)
        estimated_tokens = len(summary_text) // 4  # Rough estimation
        
        return {
            'type': 'compressed_summary',
            'content': summary_text,
            'original_count': len(items),
            'tokens': estimated_tokens,
            'timestamp': time.time(),
            'importance': 'high'  # Summaries are always important
        }
    
    async def _summarize_conversations(self, conversations: list) -> str:
        """Summarize conversation items preserving key points."""
        if not conversations:
            return ""
        
        # Extract key themes and decisions
        key_points = []
        for conv in conversations:
            content = conv.get('content', '')
            # Simple keyword extraction (in production, use a summarization model)
            if any(keyword in content.lower() for keyword in ['decision', 'important', 'remember', 'todo']):
                key_points.append(content[:100] + "..." if len(content) > 100 else content)
        
        if key_points:
            return f"Key conversation points: {'; '.join(key_points)}"
        else:
            return f"General conversation covering {len(conversations)} topics"
    
    def get_context_for_prompt(self) -> str:
        """Get formatted context for model prompt."""
        context_parts = []
        
        # Add compressed summaries
        for summary in self.compressed_summaries:
            context_parts.append(f"[SUMMARY] {summary['content']}")
        
        # Add recent context items
        recent_items = list(self.context_buffer)[-20:]  # Last 20 items
        for item in recent_items:
            if item.get('type') == 'conversation':
                context_parts.append(f"[CONV] {item['content']}")
            elif item.get('type') == 'event':
                context_parts.append(f"[EVENT] {item['content']}")
            elif item.get('type') == 'function_call':
                context_parts.append(f"[FUNC] {item['name']}: {item['result']}")
        
        return "\n".join(context_parts)

class ImportanceClassifier:
    """Classify context items by importance."""
    
    def __init__(self):
        self.high_importance_keywords = [
            'error', 'critical', 'important', 'remember', 'decision', 
            'todo', 'action', 'problem', 'issue', 'warning'
        ]
        self.function_importance = {
            'start_commentating': 'high',
            'wait_for_user': 'medium',
            'system_message': 'high'
        }
    
    async def classify(self, item: dict) -> str:
        """Classify item importance."""
        content = item.get('content', '').lower()
        item_type = item.get('type', '')
        
        # Function calls have predefined importance
        if item_type == 'function_call':
            func_name = item.get('name', '')
            return self.function_importance.get(func_name, 'medium')
        
        # Events are usually important
        if item_type == 'event':
            return 'high'
        
        # Check for high importance keywords
        if any(keyword in content for keyword in self.high_importance_keywords):
            return 'high'
        
        # Check content length (longer content might be more important)
        if len(content) > 200:
            return 'medium'
        
        return 'low'
```

### **2. Session State Management**

#### **Persistent Session Context**
```python
class PersistentSessionManager:
    def __init__(self, session_id: str, storage_backend: str = "memory"):
        self.session_id = session_id
        self.storage_backend = storage_backend
        self.session_data = {
            'context_history': [],
            'user_preferences': {},
            'conversation_state': {},
            'function_call_history': [],
            'performance_metrics': {}
        }
        self.last_checkpoint = time.time()
        self.checkpoint_interval = 300  # 5 minutes
    
    async def save_checkpoint(self):
        """Save session checkpoint."""
        checkpoint_data = {
            'session_id': self.session_id,
            'timestamp': time.time(),
            'data': self.session_data.copy()
        }
        
        if self.storage_backend == "file":
            await self._save_to_file(checkpoint_data)
        elif self.storage_backend == "database":
            await self._save_to_database(checkpoint_data)
        else:
            # Memory storage - just keep in memory
            pass
        
        self.last_checkpoint = time.time()
    
    async def restore_session(self) -> bool:
        """Restore session from checkpoint."""
        try:
            if self.storage_backend == "file":
                data = await self._load_from_file()
            elif self.storage_backend == "database":
                data = await self._load_from_database()
            else:
                return False
            
            if data:
                self.session_data = data['data']
                return True
        except Exception as e:
            logging.error(f"Failed to restore session: {e}")
        
        return False
    
    async def update_context(self, context_item: dict):
        """Update session context."""
        self.session_data['context_history'].append({
            'timestamp': time.time(),
            'item': context_item
        })
        
        # Limit context history size
        if len(self.session_data['context_history']) > 1000:
            self.session_data['context_history'] = self.session_data['context_history'][-800:]
        
        # Auto-checkpoint if needed
        if time.time() - self.last_checkpoint > self.checkpoint_interval:
            await self.save_checkpoint()
    
    async def _save_to_file(self, data: dict):
        """Save checkpoint to file."""
        import json
        checkpoint_file = f"session_{self.session_id}_checkpoint.json"
        with open(checkpoint_file, 'w') as f:
            json.dump(data, f, default=str)
    
    async def _load_from_file(self) -> dict:
        """Load checkpoint from file."""
        import json
        checkpoint_file = f"session_{self.session_id}_checkpoint.json"
        try:
            with open(checkpoint_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return None
```

## 🎙️ **REAL-TIME TRANSCRIPTION MANAGEMENT**

### **1. Bidirectional Transcription Handler**

#### **Advanced Transcription Manager**
```python
class AdvancedTranscriptionManager:
    def __init__(self, enable_input_transcription: bool = True, enable_output_transcription: bool = True):
        self.enable_input_transcription = enable_input_transcription
        self.enable_output_transcription = enable_output_transcription
        
        # Transcription buffers
        self.input_transcription_buffer = collections.deque(maxlen=100)
        self.output_transcription_buffer = collections.deque(maxlen=100)
        
        # Real-time processing
        self.transcription_queue = asyncio.Queue()
        self.processing_task = None
        
        # Quality metrics
        self.transcription_metrics = {
            'input_words_per_minute': 0,
            'output_words_per_minute': 0,
            'accuracy_score': 0.0,
            'latency_ms': 0
        }
    
    def get_live_config_with_transcription(self, base_config: dict) -> dict:
        """Add transcription configuration to Live API config."""
        config = base_config.copy()
        
        if self.enable_input_transcription:
            config['input_audio_transcription'] = {}
        
        if self.enable_output_transcription:
            config['output_audio_transcription'] = {}
        
        return config
    
    async def process_transcription_response(self, response):
        """Process transcription from Live API response."""
        transcription_data = None
        
        # Handle input transcription
        if (hasattr(response, 'server_content') and 
            response.server_content and 
            response.server_content.input_transcription):
            
            transcription_data = {
                'type': 'input',
                'text': response.server_content.input_transcription.text,
                'timestamp': time.time(),
                'is_final': getattr(response.server_content.input_transcription, 'is_final', True)
            }
        
        # Handle output transcription
        elif (hasattr(response, 'server_content') and 
              response.server_content and 
              response.server_content.output_transcription):
            
            transcription_data = {
                'type': 'output',
                'text': response.server_content.output_transcription.text,
                'timestamp': time.time(),
                'is_final': True  # Output transcriptions are always final
            }
        
        if transcription_data:
            await self._process_transcription_data(transcription_data)
            return transcription_data
        
        return None
    
    async def _process_transcription_data(self, transcription_data: dict):
        """Process and store transcription data."""
        if transcription_data['type'] == 'input':
            self.input_transcription_buffer.append(transcription_data)
        else:
            self.output_transcription_buffer.append(transcription_data)
        
        # Update metrics
        await self._update_transcription_metrics(transcription_data)
        
        # Queue for real-time processing
        await self.transcription_queue.put(transcription_data)
    
    async def _update_transcription_metrics(self, transcription_data: dict):
        """Update transcription quality metrics."""
        text = transcription_data['text']
        word_count = len(text.split())
        
        # Calculate words per minute (rough estimation)
        if transcription_data['type'] == 'input':
            # Estimate based on recent input transcriptions
            recent_inputs = [t for t in self.input_transcription_buffer if time.time() - t['timestamp'] < 60]
            if recent_inputs:
                total_words = sum(len(t['text'].split()) for t in recent_inputs)
                self.transcription_metrics['input_words_per_minute'] = total_words
        else:
            # Estimate based on recent output transcriptions
            recent_outputs = [t for t in self.output_transcription_buffer if time.time() - t['timestamp'] < 60]
            if recent_outputs:
                total_words = sum(len(t['text'].split()) for t in recent_outputs)
                self.transcription_metrics['output_words_per_minute'] = total_words
    
    async def get_conversation_transcript(self, last_n_minutes: int = 10) -> str:
        """Get formatted conversation transcript."""
        cutoff_time = time.time() - (last_n_minutes * 60)
        
        # Combine input and output transcriptions
        all_transcriptions = []
        
        # Add input transcriptions
        for t in self.input_transcription_buffer:
            if t['timestamp'] > cutoff_time and t['is_final']:
                all_transcriptions.append({
                    'timestamp': t['timestamp'],
                    'speaker': 'User',
                    'text': t['text']
                })
        
        # Add output transcriptions
        for t in self.output_transcription_buffer:
            if t['timestamp'] > cutoff_time:
                all_transcriptions.append({
                    'timestamp': t['timestamp'],
                    'speaker': 'Assistant',
                    'text': t['text']
                })
        
        # Sort by timestamp
        all_transcriptions.sort(key=lambda x: x['timestamp'])
        
        # Format as readable transcript
        transcript_lines = []
        for t in all_transcriptions:
            timestamp_str = time.strftime('%H:%M:%S', time.localtime(t['timestamp']))
            transcript_lines.append(f"[{timestamp_str}] {t['speaker']}: {t['text']}")
        
        return "\n".join(transcript_lines)
    
    async def start_real_time_processing(self):
        """Start real-time transcription processing."""
        if self.processing_task is None:
            self.processing_task = asyncio.create_task(self._real_time_processor())
    
    async def stop_real_time_processing(self):
        """Stop real-time transcription processing."""
        if self.processing_task:
            self.processing_task.cancel()
            self.processing_task = None
    
    async def _real_time_processor(self):
        """Real-time transcription processor."""
        while True:
            try:
                transcription_data = await self.transcription_queue.get()
                
                # Process transcription in real-time
                await self._handle_real_time_transcription(transcription_data)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"Real-time transcription processing error: {e}")
    
    async def _handle_real_time_transcription(self, transcription_data: dict):
        """Handle real-time transcription processing."""
        text = transcription_data['text']
        transcription_type = transcription_data['type']
        
        # Example: Detect keywords or commands
        if transcription_type == 'input':
            await self._process_user_speech(text)
        else:
            await self._process_assistant_speech(text)
    
    async def _process_user_speech(self, text: str):
        """Process user speech transcription."""
        # Example: Detect interruption keywords
        interruption_keywords = ['stop', 'wait', 'pause', 'hold on']
        if any(keyword in text.lower() for keyword in interruption_keywords):
            # Signal potential interruption
            logging.info(f"Potential interruption detected: {text}")
    
    async def _process_assistant_speech(self, text: str):
        """Process assistant speech transcription."""
        # Example: Monitor for completion phrases
        completion_phrases = ['that\'s all', 'finished', 'complete', 'done']
        if any(phrase in text.lower() for phrase in completion_phrases):
            logging.info(f"Completion phrase detected: {text}")
```

### **2. Transcription Quality Monitoring**

#### **Quality Assessment System**
```python
class TranscriptionQualityMonitor:
    def __init__(self):
        self.quality_metrics = {
            'word_error_rate': 0.0,
            'confidence_scores': collections.deque(maxlen=100),
            'latency_measurements': collections.deque(maxlen=100),
            'partial_transcription_accuracy': 0.0
        }
        
        self.reference_transcriptions = {}  # For quality comparison
        self.quality_thresholds = {
            'min_confidence': 0.8,
            'max_latency_ms': 500,
            'max_word_error_rate': 0.1
        }
    
    async def assess_transcription_quality(self, transcription_data: dict) -> dict:
        """Assess quality of transcription."""
        quality_assessment = {
            'overall_score': 0.0,
            'confidence': 0.0,
            'latency_ms': 0.0,
            'issues': [],
            'recommendations': []
        }
        
        text = transcription_data['text']
        timestamp = transcription_data['timestamp']
        
        # Assess confidence (if available)
        confidence = transcription_data.get('confidence', 0.8)  # Default confidence
        quality_assessment['confidence'] = confidence
        self.quality_metrics['confidence_scores'].append(confidence)
        
        # Assess latency
        processing_latency = time.time() - timestamp
        quality_assessment['latency_ms'] = processing_latency * 1000
        self.quality_metrics['latency_measurements'].append(processing_latency)
        
        # Check quality thresholds
        if confidence < self.quality_thresholds['min_confidence']:
            quality_assessment['issues'].append(f"Low confidence: {confidence:.2f}")
            quality_assessment['recommendations'].append("Consider improving audio quality")
        
        if processing_latency > self.quality_thresholds['max_latency_ms'] / 1000:
            quality_assessment['issues'].append(f"High latency: {processing_latency*1000:.0f}ms")
            quality_assessment['recommendations'].append("Optimize transcription pipeline")
        
        # Calculate overall score
        confidence_score = min(1.0, confidence / self.quality_thresholds['min_confidence'])
        latency_score = max(0.0, 1.0 - (processing_latency / (self.quality_thresholds['max_latency_ms'] / 1000)))
        
        quality_assessment['overall_score'] = (confidence_score + latency_score) / 2
        
        return quality_assessment
    
    def get_quality_report(self) -> dict:
        """Generate comprehensive quality report."""
        if not self.quality_metrics['confidence_scores']:
            return {'status': 'no_data'}
        
        avg_confidence = sum(self.quality_metrics['confidence_scores']) / len(self.quality_metrics['confidence_scores'])
        avg_latency = sum(self.quality_metrics['latency_measurements']) / len(self.quality_metrics['latency_measurements'])
        
        return {
            'average_confidence': avg_confidence,
            'average_latency_ms': avg_latency * 1000,
            'quality_grade': self._calculate_quality_grade(avg_confidence, avg_latency),
            'recommendations': self._generate_quality_recommendations(avg_confidence, avg_latency)
        }
    
    def _calculate_quality_grade(self, avg_confidence: float, avg_latency: float) -> str:
        """Calculate overall quality grade."""
        if avg_confidence > 0.9 and avg_latency < 0.3:
            return 'A'
        elif avg_confidence > 0.8 and avg_latency < 0.5:
            return 'B'
        elif avg_confidence > 0.7 and avg_latency < 0.8:
            return 'C'
        else:
            return 'D'
    
    def _generate_quality_recommendations(self, avg_confidence: float, avg_latency: float) -> list:
        """Generate quality improvement recommendations."""
        recommendations = []
        
        if avg_confidence < 0.8:
            recommendations.append("Improve audio input quality (reduce background noise)")
            recommendations.append("Use better microphone or audio preprocessing")
        
        if avg_latency > 0.5:
            recommendations.append("Optimize network connection")
            recommendations.append("Consider using lower media resolution for faster processing")
        
        return recommendations
```

## 🔄 **CONTEXT SYNCHRONIZATION PATTERNS**

### **Multi-Modal Context Sync**
```python
class MultiModalContextSynchronizer:
    def __init__(self):
        self.audio_context = collections.deque(maxlen=50)
        self.video_context = collections.deque(maxlen=20)
        self.text_context = collections.deque(maxlen=100)
        self.sync_timestamps = {}
    
    async def add_audio_context(self, audio_data: dict):
        """Add audio context with timestamp sync."""
        timestamp = time.time()
        audio_data['sync_timestamp'] = timestamp
        self.audio_context.append(audio_data)
        self.sync_timestamps[timestamp] = 'audio'
    
    async def add_video_context(self, video_data: dict):
        """Add video context with timestamp sync."""
        timestamp = time.time()
        video_data['sync_timestamp'] = timestamp
        self.video_context.append(video_data)
        self.sync_timestamps[timestamp] = 'video'
    
    async def add_text_context(self, text_data: dict):
        """Add text context with timestamp sync."""
        timestamp = time.time()
        text_data['sync_timestamp'] = timestamp
        self.text_context.append(text_data)
        self.sync_timestamps[timestamp] = 'text'
    
    async def get_synchronized_context(self, time_window_seconds: float = 30.0) -> dict:
        """Get synchronized context from all modalities."""
        current_time = time.time()
        cutoff_time = current_time - time_window_seconds
        
        # Filter contexts by time window
        recent_audio = [ctx for ctx in self.audio_context if ctx['sync_timestamp'] > cutoff_time]
        recent_video = [ctx for ctx in self.video_context if ctx['sync_timestamp'] > cutoff_time]
        recent_text = [ctx for ctx in self.text_context if ctx['sync_timestamp'] > cutoff_time]
        
        # Create synchronized timeline
        timeline = []
        
        for ctx in recent_audio:
            timeline.append({
                'timestamp': ctx['sync_timestamp'],
                'type': 'audio',
                'data': ctx
            })
        
        for ctx in recent_video:
            timeline.append({
                'timestamp': ctx['sync_timestamp'],
                'type': 'video',
                'data': ctx
            })
        
        for ctx in recent_text:
            timeline.append({
                'timestamp': ctx['sync_timestamp'],
                'type': 'text',
                'data': ctx
            })
        
        # Sort by timestamp
        timeline.sort(key=lambda x: x['timestamp'])
        
        return {
            'timeline': timeline,
            'summary': self._create_multimodal_summary(timeline),
            'time_window': time_window_seconds,
            'total_events': len(timeline)
        }
    
    def _create_multimodal_summary(self, timeline: list) -> str:
        """Create summary of multimodal context."""
        if not timeline:
            return "No recent context available"
        
        summary_parts = []
        
        # Count events by type
        audio_count = len([e for e in timeline if e['type'] == 'audio'])
        video_count = len([e for e in timeline if e['type'] == 'video'])
        text_count = len([e for e in timeline if e['type'] == 'text'])
        
        if audio_count > 0:
            summary_parts.append(f"{audio_count} audio events")
        if video_count > 0:
            summary_parts.append(f"{video_count} video events")
        if text_count > 0:
            summary_parts.append(f"{text_count} text events")
        
        return f"Recent context: {', '.join(summary_parts)} over {len(timeline)} total events"
```

This comprehensive context management and transcription guide provides all the patterns needed for sophisticated real-time applications with proper context handling and transcription management.
