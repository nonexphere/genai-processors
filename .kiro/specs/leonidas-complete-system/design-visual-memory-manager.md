# Visual Memory Manager - Design Specification

## 📋 **OVERVIEW**

The Visual Memory Manager implements an advanced associative visual memory system for Leonidas, enabling persistent recognition and memory of objects, people, scenes, and visual patterns. This system provides contextual visual understanding and builds long-term visual associations for enhanced user interaction.

## 🎯 **CORE OBJECTIVES**

### **Primary Goals**
- **Visual Recognition**: Persistent object and person recognition across sessions
- **Associative Memory**: Build contextual relationships between visual elements
- **Scene Understanding**: Comprehensive scene analysis and memory
- **Temporal Tracking**: Track visual changes and patterns over time
- **Context Integration**: Integrate visual memory with conversational context

### **Key Capabilities**
- Face recognition and person identification with privacy protection
- Object detection, classification, and persistent tracking
- Scene analysis and environmental understanding
- Visual pattern recognition and anomaly detection
- Associative memory linking visual elements to conversations

## 🏗️ **ARCHITECTURE DESIGN**

### **Component Structure**
```
VisualMemoryManager/
├── RecognitionEngine/          # Core recognition capabilities
│   ├── FaceRecognizer          # Face detection and recognition
│   ├── ObjectDetector          # Object detection and classification
│   ├── SceneAnalyzer          # Scene understanding and analysis
│   └── PatternRecognizer      # Visual pattern detection
├── MemoryStore/               # Persistent visual memory
│   ├── PersonMemory           # Person recognition database
│   ├── ObjectMemory           # Object and item memory
│   ├── SceneMemory            # Scene and location memory
│   └── AssociativeIndex       # Cross-reference relationships
├── ContextualProcessor/       # Context integration
│   ├── ConversationLinker     # Link visuals to conversations
│   ├── TemporalTracker        # Track changes over time
│   ├── SpatialMapper          # Spatial relationship mapping
│   └── EventCorrelator        # Correlate visual events
└── PrivacyFramework/         # Privacy and security
    ├── ConsentManager         # User consent for recognition
    ├── DataAnonymizer         # Anonymize sensitive data
    ├── AccessController       # Control memory access
    └── RetentionManager       # Data retention policies
```

## 🧠 **CORE IMPLEMENTATION**

### **1. Visual Memory Manager**

```python
class VisualMemoryManager:
    """
    Advanced visual memory system with associative capabilities.
    Provides persistent visual recognition and contextual memory.
    """
    
    def __init__(self, system_config: SystemConfig, signal_bus: SignalBus):
        self.system_config = system_config
        self.signal_bus = signal_bus
        
        # Core components
        self.recognition_engine = RecognitionEngine()
        self.memory_store = VisualMemoryStore()
        self.contextual_processor = ContextualProcessor()
        self.privacy_framework = PrivacyFramework()
        
        # Processing state
        self.active_recognitions = {}
        self.memory_cache = {}
        self.processing_queue = asyncio.Queue(maxsize=100)
        
        # Performance metrics
        self.metrics = {
            'recognitions_performed': 0,
            'memory_entries_created': 0,
            'associations_formed': 0,
            'cache_hit_rate': 0.0,
            'average_processing_time': 0.0
        }
        
        # Initialize recognition models
        self._initialize_recognition_models()
    
    async def process_visual_input(self, 
                                 image_data: bytes,
                                 context: dict,
                                 session_id: str) -> dict:
        """Process visual input and update memory."""
        
        processing_start = time.time()
        
        try:
            # Privacy check
            privacy_result = await self.privacy_framework.check_consent(
                context.get('user_id'), 'visual_recognition'
            )
            
            if not privacy_result['allowed']:
                return {
                    'success': False,
                    'error': 'Visual recognition not permitted',
                    'privacy_reason': privacy_result['reason']
                }
            
            # Perform recognition
            recognition_result = await self.recognition_engine.analyze_image(
                image_data, context
            )
            
            # Update memory with new information
            memory_updates = await self._update_visual_memory(
                recognition_result, context, session_id
            )
            
            # Create contextual associations
            associations = await self.contextual_processor.create_associations(
                recognition_result, context, memory_updates
            )
            
            # Update metrics
            self.metrics['recognitions_performed'] += 1
            self.metrics['memory_entries_created'] += len(memory_updates)
            self.metrics['associations_formed'] += len(associations)
            
            processing_time = time.time() - processing_start
            self._update_average_processing_time(processing_time)
            
            return {
                'success': True,
                'recognition': recognition_result,
                'memory_updates': memory_updates,
                'associations': associations,
                'processing_time_ms': processing_time * 1000
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Visual processing failed: {str(e)}',
                'processing_time_ms': (time.time() - processing_start) * 1000
            }
    
    async def query_visual_memory(self, 
                                query: dict,
                                context: dict) -> dict:
        """Query visual memory with contextual search."""
        
        try:
            # Parse query
            parsed_query = await self._parse_visual_query(query)
            
            # Search memory store
            search_results = await self.memory_store.search(
                parsed_query, context
            )
            
            # Rank results by relevance
            ranked_results = await self._rank_search_results(
                search_results, parsed_query, context
            )
            
            # Generate contextual response
            response = await self._generate_memory_response(
                ranked_results, parsed_query, context
            )
            
            return {
                'success': True,
                'results': ranked_results,
                'response': response,
                'query': parsed_query
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Memory query failed: {str(e)}'
            }
    
    async def _update_visual_memory(self, 
                                  recognition_result: dict,
                                  context: dict,
                                  session_id: str) -> list:
        """Update visual memory with recognition results."""
        
        memory_updates = []
        
        # Process detected persons
        for person in recognition_result.get('persons', []):
            person_update = await self._update_person_memory(
                person, context, session_id
            )
            if person_update:
                memory_updates.append(person_update)
        
        # Process detected objects
        for obj in recognition_result.get('objects', []):
            object_update = await self._update_object_memory(
                obj, context, session_id
            )
            if object_update:
                memory_updates.append(object_update)
        
        # Process scene information
        if 'scene' in recognition_result:
            scene_update = await self._update_scene_memory(
                recognition_result['scene'], context, session_id
            )
            if scene_update:
                memory_updates.append(scene_update)
        
        return memory_updates
    
    async def _update_person_memory(self, 
                                  person_data: dict,
                                  context: dict,
                                  session_id: str) -> dict:
        """Update person memory with new recognition."""
        
        # Check if person is already known
        person_id = await self.memory_store.find_person(person_data['features'])
        
        if person_id:
            # Update existing person record
            update_result = await self.memory_store.update_person(
                person_id, {
                    'last_seen': time.time(),
                    'session_id': session_id,
                    'context': context,
                    'appearance': person_data.get('appearance', {}),
                    'location': person_data.get('location', {}),
                    'confidence': person_data.get('confidence', 0.0)
                }
            )
            
            return {
                'type': 'person_update',
                'person_id': person_id,
                'action': 'updated',
                'data': update_result
            }
        else:
            # Create new person record (with consent)
            consent_result = await self.privacy_framework.request_person_consent(
                context.get('user_id'), person_data
            )
            
            if consent_result['granted']:
                person_id = await self.memory_store.create_person({
                    'features': person_data['features'],
                    'first_seen': time.time(),
                    'last_seen': time.time(),
                    'session_id': session_id,
                    'context': context,
                    'appearance': person_data.get('appearance', {}),
                    'location': person_data.get('location', {}),
                    'confidence': person_data.get('confidence', 0.0),
                    'consent_granted': True
                })
                
                return {
                    'type': 'person_create',
                    'person_id': person_id,
                    'action': 'created',
                    'consent': True
                }
        
        return None
    
    def _initialize_recognition_models(self):
        """Initialize recognition models and capabilities."""
        
        # Configure recognition settings
        recognition_config = {
            'face_recognition': {
                'enabled': self.system_config.get('visual_memory.face_recognition', True),
                'confidence_threshold': 0.8,
                'max_faces_per_image': 10
            },
            'object_detection': {
                'enabled': self.system_config.get('visual_memory.object_detection', True),
                'confidence_threshold': 0.6,
                'max_objects_per_image': 50
            },
            'scene_analysis': {
                'enabled': self.system_config.get('visual_memory.scene_analysis', True),
                'detail_level': 'medium'
            }
        }
        
        self.recognition_engine.configure(recognition_config)
```

### **2. Recognition Engine Implementation**

```python
class RecognitionEngine:
    """Advanced visual recognition engine using multiple AI models."""
    
    def __init__(self):
        # Recognition models (would integrate with actual AI models)
        self.face_recognizer = FaceRecognizer()
        self.object_detector = ObjectDetector()
        self.scene_analyzer = SceneAnalyzer()
        self.pattern_recognizer = PatternRecognizer()
        
        # Processing cache
        self.recognition_cache = {}
        self.model_cache = {}
        
        # Performance tracking
        self.recognition_metrics = {
            'face_recognitions': 0,
            'object_detections': 0,
            'scene_analyses': 0,
            'cache_hits': 0,
            'processing_times': collections.deque(maxlen=100)
        }
    
    async def analyze_image(self, image_data: bytes, context: dict) -> dict:
        """Comprehensive image analysis and recognition."""
        
        analysis_start = time.time()
        
        try:
            # Generate image hash for caching
            image_hash = hashlib.md5(image_data).hexdigest()
            
            # Check cache first
            if image_hash in self.recognition_cache:
                self.recognition_metrics['cache_hits'] += 1
                return self.recognition_cache[image_hash]
            
            # Perform parallel recognition tasks
            recognition_tasks = []
            
            # Face recognition
            if self.config.get('face_recognition', {}).get('enabled', True):
                face_task = asyncio.create_task(
                    self.face_recognizer.detect_faces(image_data)
                )
                recognition_tasks.append(('faces', face_task))
            
            # Object detection
            if self.config.get('object_detection', {}).get('enabled', True):
                object_task = asyncio.create_task(
                    self.object_detector.detect_objects(image_data)
                )
                recognition_tasks.append(('objects', object_task))
            
            # Scene analysis
            if self.config.get('scene_analysis', {}).get('enabled', True):
                scene_task = asyncio.create_task(
                    self.scene_analyzer.analyze_scene(image_data)
                )
                recognition_tasks.append(('scene', scene_task))
            
            # Wait for all recognition tasks
            recognition_results = {}
            for task_name, task in recognition_tasks:
                try:
                    result = await task
                    recognition_results[task_name] = result
                    
                    # Update metrics
                    if task_name == 'faces':
                        self.recognition_metrics['face_recognitions'] += 1
                    elif task_name == 'objects':
                        self.recognition_metrics['object_detections'] += 1
                    elif task_name == 'scene':
                        self.recognition_metrics['scene_analyses'] += 1
                        
                except Exception as e:
                    logging.error(f"Recognition task {task_name} failed: {e}")
                    recognition_results[task_name] = {'error': str(e)}
            
            # Combine results
            combined_result = {
                'timestamp': time.time(),
                'image_hash': image_hash,
                'persons': self._extract_persons(recognition_results.get('faces', {})),
                'objects': recognition_results.get('objects', {}).get('detections', []),
                'scene': recognition_results.get('scene', {}),
                'context': context,
                'processing_time': time.time() - analysis_start
            }
            
            # Cache result
            self.recognition_cache[image_hash] = combined_result
            
            # Update processing time metrics
            processing_time = time.time() - analysis_start
            self.recognition_metrics['processing_times'].append(processing_time)
            
            return combined_result
            
        except Exception as e:
            return {
                'error': f'Image analysis failed: {str(e)}',
                'timestamp': time.time(),
                'processing_time': time.time() - analysis_start
            }
    
    def _extract_persons(self, face_results: dict) -> list:
        """Extract person information from face recognition results."""
        
        persons = []
        
        for face in face_results.get('faces', []):
            person_data = {
                'face_id': face.get('id'),
                'features': face.get('features', []),
                'confidence': face.get('confidence', 0.0),
                'location': {
                    'bbox': face.get('bbox', {}),
                    'landmarks': face.get('landmarks', {})
                },
                'appearance': {
                    'age_estimate': face.get('age', None),
                    'gender_estimate': face.get('gender', None),
                    'emotion': face.get('emotion', None),
                    'attributes': face.get('attributes', {})
                }
            }
            persons.append(person_data)
        
        return persons
```

### **3. Visual Memory Store**

```python
class VisualMemoryStore:
    """Persistent storage for visual memory with associative indexing."""
    
    def __init__(self, storage_path: str = "visual_memory.db"):
        self.storage_path = storage_path
        self.db_connection = None
        self.memory_index = {}
        
        # Memory categories
        self.person_memory = PersonMemoryStore()
        self.object_memory = ObjectMemoryStore()
        self.scene_memory = SceneMemoryStore()
        self.associative_index = AssociativeIndex()
        
        # Initialize storage
        self._initialize_storage()
    
    async def create_person(self, person_data: dict) -> str:
        """Create new person memory entry."""
        
        person_id = str(uuid.uuid4())
        
        # Store person data
        await self.person_memory.create(person_id, {
            **person_data,
            'created_at': time.time(),
            'updated_at': time.time(),
            'recognition_count': 1
        })
        
        # Create associative index entries
        await self.associative_index.add_person_associations(
            person_id, person_data
        )
        
        return person_id
    
    async def find_person(self, features: list) -> str:
        """Find person by facial features."""
        
        # Search for similar features
        similar_persons = await self.person_memory.find_by_features(
            features, similarity_threshold=0.85
        )
        
        if similar_persons:
            # Return most similar person
            return similar_persons[0]['person_id']
        
        return None
    
    async def search(self, query: dict, context: dict) -> list:
        """Search visual memory with contextual relevance."""
        
        search_results = []
        
        # Search different memory types based on query
        if query.get('type') == 'person' or 'person' in query.get('keywords', []):
            person_results = await self.person_memory.search(query, context)
            search_results.extend(person_results)
        
        if query.get('type') == 'object' or 'object' in query.get('keywords', []):
            object_results = await self.object_memory.search(query, context)
            search_results.extend(object_results)
        
        if query.get('type') == 'scene' or 'scene' in query.get('keywords', []):
            scene_results = await self.scene_memory.search(query, context)
            search_results.extend(scene_results)
        
        # Use associative index for cross-references
        if query.get('associative', True):
            associative_results = await self.associative_index.search(
                query, context, search_results
            )
            search_results.extend(associative_results)
        
        return search_results
    
    def _initialize_storage(self):
        """Initialize persistent storage system."""
        
        # Initialize database schema
        schema_sql = """
        CREATE TABLE IF NOT EXISTS persons (
            id TEXT PRIMARY KEY,
            features BLOB,
            metadata TEXT,
            created_at REAL,
            updated_at REAL,
            recognition_count INTEGER
        );
        
        CREATE TABLE IF NOT EXISTS objects (
            id TEXT PRIMARY KEY,
            class_name TEXT,
            features BLOB,
            metadata TEXT,
            created_at REAL,
            updated_at REAL
        );
        
        CREATE TABLE IF NOT EXISTS scenes (
            id TEXT PRIMARY KEY,
            description TEXT,
            features BLOB,
            metadata TEXT,
            created_at REAL,
            updated_at REAL
        );
        
        CREATE TABLE IF NOT EXISTS associations (
            id TEXT PRIMARY KEY,
            source_type TEXT,
            source_id TEXT,
            target_type TEXT,
            target_id TEXT,
            relationship TEXT,
            strength REAL,
            created_at REAL
        );
        """
        
        # Execute schema creation
        # (Implementation would use actual database connection)
```

### **4. Contextual Processor**

```python
class ContextualProcessor:
    """Process visual information in context of conversations and interactions."""
    
    def __init__(self):
        self.conversation_linker = ConversationLinker()
        self.temporal_tracker = TemporalTracker()
        self.spatial_mapper = SpatialMapper()
        self.event_correlator = EventCorrelator()
        
        # Context state
        self.active_contexts = {}
        self.context_history = collections.deque(maxlen=1000)
    
    async def create_associations(self, 
                                recognition_result: dict,
                                context: dict,
                                memory_updates: list) -> list:
        """Create contextual associations from recognition results."""
        
        associations = []
        
        # Link to current conversation
        conversation_links = await self.conversation_linker.create_links(
            recognition_result, context
        )
        associations.extend(conversation_links)
        
        # Track temporal patterns
        temporal_associations = await self.temporal_tracker.analyze_patterns(
            recognition_result, context, memory_updates
        )
        associations.extend(temporal_associations)
        
        # Map spatial relationships
        spatial_associations = await self.spatial_mapper.map_relationships(
            recognition_result, context
        )
        associations.extend(spatial_associations)
        
        # Correlate with events
        event_correlations = await self.event_correlator.find_correlations(
            recognition_result, context
        )
        associations.extend(event_correlations)
        
        return associations
    
    async def analyze_visual_context(self, 
                                   recognition_result: dict,
                                   conversation_context: dict) -> dict:
        """Analyze visual information in conversation context."""
        
        context_analysis = {
            'relevance_score': 0.0,
            'conversation_links': [],
            'temporal_significance': 0.0,
            'spatial_context': {},
            'emotional_context': {},
            'action_implications': []
        }
        
        # Analyze conversation relevance
        if 'persons' in recognition_result:
            for person in recognition_result['persons']:
                relevance = await self._calculate_person_relevance(
                    person, conversation_context
                )
                context_analysis['relevance_score'] += relevance
        
        # Analyze temporal significance
        temporal_sig = await self.temporal_tracker.calculate_significance(
            recognition_result, conversation_context
        )
        context_analysis['temporal_significance'] = temporal_sig
        
        # Determine action implications
        actions = await self._determine_action_implications(
            recognition_result, conversation_context
        )
        context_analysis['action_implications'] = actions
        
        return context_analysis
    
    async def _calculate_person_relevance(self, 
                                        person_data: dict,
                                        conversation_context: dict) -> float:
        """Calculate relevance of person to current conversation."""
        
        relevance_score = 0.0
        
        # Check if person was mentioned in conversation
        conversation_text = conversation_context.get('recent_text', '').lower()
        
        # Look for person-related keywords
        person_keywords = ['pessoa', 'alguém', 'ele', 'ela', 'usuário', 'cliente']
        for keyword in person_keywords:
            if keyword in conversation_text:
                relevance_score += 0.3
        
        # Check if person appeared recently in conversation
        recent_appearances = conversation_context.get('recent_visual_persons', [])
        for appearance in recent_appearances:
            if self._are_same_person(person_data, appearance):
                relevance_score += 0.5
                break
        
        # Check emotional context
        if person_data.get('appearance', {}).get('emotion'):
            emotion = person_data['appearance']['emotion']
            if emotion in ['happy', 'surprised']:
                relevance_score += 0.2
            elif emotion in ['sad', 'angry']:
                relevance_score += 0.4  # Negative emotions are more significant
        
        return min(1.0, relevance_score)
```

## 🔧 **INTEGRATION SPECIFICATIONS**

### **Signal Bus Integration**
```python
# Signal types for visual memory
VISUAL_MEMORY_SIGNALS = {
    'PERSON_RECOGNIZED': 'visual_memory.person_recognized',
    'NEW_PERSON_DETECTED': 'visual_memory.new_person_detected',
    'OBJECT_IDENTIFIED': 'visual_memory.object_identified',
    'SCENE_ANALYZED': 'visual_memory.scene_analyzed',
    'MEMORY_UPDATED': 'visual_memory.memory_updated',
    'ASSOCIATION_CREATED': 'visual_memory.association_created'
}

# Integration with signal bus
async def integrate_with_signal_bus(self, signal_bus: SignalBus):
    """Integrate visual memory with signal bus."""
    
    # Subscribe to visual input signals
    await signal_bus.subscribe(
        'visual_perception.frame_analyzed',
        self._handle_visual_frame
    )
    
    await signal_bus.subscribe(
        'dialogue_analysis.person_mentioned',
        self._handle_person_mention
    )
    
    # Emit memory events
    await signal_bus.emit(VISUAL_MEMORY_SIGNALS['PERSON_RECOGNIZED'], {
        'person_id': person_id,
        'confidence': confidence,
        'context': context,
        'timestamp': time.time()
    })
```

### **Privacy Framework Integration**
```python
class PrivacyFramework:
    """Comprehensive privacy protection for visual memory."""
    
    def __init__(self):
        self.consent_manager = ConsentManager()
        self.data_anonymizer = DataAnonymizer()
        self.access_controller = AccessController()
        self.retention_manager = RetentionManager()
    
    async def check_consent(self, user_id: str, operation: str) -> dict:
        """Check user consent for visual recognition operations."""
        
        consent_status = await self.consent_manager.get_consent(
            user_id, operation
        )
        
        return {
            'allowed': consent_status.get('granted', False),
            'reason': consent_status.get('reason', 'No consent found'),
            'expires_at': consent_status.get('expires_at'),
            'restrictions': consent_status.get('restrictions', [])
        }
    
    async def anonymize_person_data(self, person_data: dict) -> dict:
        """Anonymize person data while preserving recognition capability."""
        
        anonymized_data = {
            'features': person_data['features'],  # Keep for recognition
            'appearance': {
                'age_range': self._anonymize_age(person_data.get('appearance', {}).get('age')),
                'general_attributes': self._generalize_attributes(
                    person_data.get('appearance', {}).get('attributes', {})
                )
            },
            'context': self._anonymize_context(person_data.get('context', {})),
            'anonymized': True,
            'anonymization_timestamp': time.time()
        }
        
        return anonymized_data
```

## 📊 **PERFORMANCE REQUIREMENTS**

### **Recognition Performance**
- **Face Recognition**: < 500ms per face
- **Object Detection**: < 300ms per image
- **Scene Analysis**: < 1s per image
- **Memory Query**: < 200ms for simple queries
- **Association Creation**: < 100ms per association

### **Accuracy Requirements**
- **Face Recognition**: > 95% accuracy for known persons
- **Object Detection**: > 90% accuracy for common objects
- **Scene Classification**: > 85% accuracy for scene types
- **Memory Retrieval**: > 95% accuracy for exact matches

### **Storage Requirements**
- **Person Records**: Support 1000+ unique persons
- **Object Memory**: Support 10,000+ object instances
- **Scene Memory**: Support 5,000+ scene records
- **Associations**: Support 50,000+ relationship records

## 🛡️ **PRIVACY & SECURITY**

### **Data Protection**
- **Consent Management**: Explicit consent for face recognition
- **Data Anonymization**: Remove identifying information when possible
- **Access Control**: Role-based access to memory data
- **Retention Policies**: Automatic deletion of old data
- **Encryption**: Encrypt sensitive biometric data

### **Compliance Features**
- **GDPR Compliance**: Right to be forgotten implementation
- **Data Portability**: Export user's visual memory data
- **Audit Logging**: Track all access to visual memory
- **Consent Withdrawal**: Remove person from memory on request

## 🧪 **TESTING STRATEGY**

### **Recognition Testing**
```python
class TestVisualMemoryManager(unittest.TestCase):
    
    def setUp(self):
        self.system_config = MockSystemConfig()
        self.signal_bus = MockSignalBus()
        self.visual_memory = VisualMemoryManager(
            self.system_config, self.signal_bus
        )
    
    async def test_person_recognition_and_memory(self):
        """Test person recognition and memory creation."""
        
        # First encounter - should create new person
        result1 = await self.visual_memory.process_visual_input(
            self.load_test_image('person1.jpg'),
            {'user_id': 'test_user', 'session_id': 'session1'},
            'session1'
        )
        
        self.assertTrue(result1['success'])
        self.assertEqual(len(result1['memory_updates']), 1)
        self.assertEqual(result1['memory_updates'][0]['action'], 'created')
        
        # Second encounter - should recognize existing person
        result2 = await self.visual_memory.process_visual_input(
            self.load_test_image('person1_different_angle.jpg'),
            {'user_id': 'test_user', 'session_id': 'session2'},
            'session2'
        )
        
        self.assertTrue(result2['success'])
        self.assertEqual(result2['memory_updates'][0]['action'], 'updated')
    
    async def test_privacy_consent_enforcement(self):
        """Test privacy consent enforcement."""
        
        # Process without consent
        result = await self.visual_memory.process_visual_input(
            self.load_test_image('person1.jpg'),
            {'user_id': 'no_consent_user'},
            'session1'
        )
        
        self.assertFalse(result['success'])
        self.assertIn('not permitted', result['error'])
```

This Visual Memory Manager provides comprehensive visual recognition and memory capabilities while maintaining strict privacy protection and user consent management. The system enables Leonidas to build persistent visual understanding and contextual associations for enhanced user interaction.