# System Configuration Manager - Design Specification

## 📋 **OVERVIEW**

The System Configuration Manager implements a comprehensive runtime configuration system for Leonidas, providing centralized configuration management, dynamic updates, validation, and persistence. This singleton module ensures consistent configuration access across all system components while supporting hot-reloading and environment-specific settings.

## 🎯 **CORE OBJECTIVES**

### **Primary Goals**
- **Centralized Configuration**: Single source of truth for all system settings
- **Runtime Updates**: Dynamic configuration changes without system restart
- **Environment Management**: Support for development, staging, and production environments
- **Validation & Safety**: Comprehensive configuration validation and rollback
- **Persistence**: Reliable configuration storage and recovery

### **Key Capabilities**
- Singleton pattern ensuring single configuration instance
- Hierarchical configuration with inheritance and overrides
- Real-time configuration monitoring and change notifications
- Configuration validation with schema enforcement
- Backup and rollback capabilities for configuration changes

## 🏗️ **ARCHITECTURE DESIGN**

### **Component Structure**
```
SystemConfigurationManager/
├── ConfigCore/                 # Core configuration management
│   ├── ConfigSingleton         # Singleton implementation
│   ├── ConfigStore             # Configuration storage
│   ├── ConfigValidator         # Schema validation
│   └── ConfigMerger            # Configuration merging logic
├── RuntimeManager/             # Runtime configuration handling
│   ├── HotReloader             # Dynamic configuration updates
│   ├── ChangeNotifier          # Configuration change notifications
│   ├── ValidationEngine        # Real-time validation
│   └── RollbackManager         # Configuration rollback
├── EnvironmentManager/         # Environment-specific configuration
│   ├── EnvironmentDetector     # Environment detection
│   ├── ProfileManager          # Configuration profiles
│   ├── OverrideHandler         # Environment overrides
│   └── SecretManager           # Secure configuration handling
└── PersistenceLayer/          # Configuration persistence
    ├── FileStorage             # File-based storage
    ├── DatabaseStorage         # Database storage option
    ├── BackupManager           # Configuration backups
    └── RecoveryManager         # Configuration recovery
```

## 🧠 **CORE IMPLEMENTATION**

### **1. System Configuration Manager (Singleton)**

```python
class SystemConfigurationManager:
    """
    Singleton configuration manager for Leonidas system.
    Provides centralized, validated, and persistent configuration management.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        # Core components
        self.config_store = ConfigStore()
        self.config_validator = ConfigValidator()
        self.runtime_manager = RuntimeManager()
        self.environment_manager = EnvironmentManager()
        self.persistence_layer = PersistenceLayer()
        
        # Configuration state
        self._config_data = {}
        self._config_schema = {}
        self._change_listeners = []
        self._validation_rules = {}
        
        # Runtime state
        self._environment = None
        self._profile = None
        self._last_update = time.time()
        self._change_history = collections.deque(maxlen=1000)
        
        # Performance metrics
        self.metrics = {
            'config_reads': 0,
            'config_writes': 0,
            'validation_checks': 0,
            'hot_reloads': 0,
            'rollbacks': 0
        }
        
        # Initialize configuration
        self._initialize_configuration()
        self._initialized = True
    
    async def initialize_async(self):
        """Async initialization for components requiring async setup."""
        
        # Initialize async components
        await self.runtime_manager.initialize()
        await self.persistence_layer.initialize()
        
        # Load configuration from persistence
        await self._load_persisted_configuration()
        
        # Start runtime monitoring
        await self.runtime_manager.start_monitoring()
    
    def get(self, key: str, default=None, validate: bool = True):
        """Get configuration value with optional validation."""
        
        self.metrics['config_reads'] += 1
        
        try:
            # Navigate nested keys
            keys = key.split('.')
            value = self._config_data
            
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default
            
            # Validate if requested
            if validate and key in self._validation_rules:
                validation_result = self.config_validator.validate_value(
                    key, value, self._validation_rules[key]
                )
                if not validation_result['valid']:
                    logging.warning(f"Configuration value validation failed for {key}: {validation_result['error']}")
                    return default
            
            return value
            
        except Exception as e:
            logging.error(f"Configuration get error for key {key}: {e}")
            return default
    
    async def set(self, key: str, value, validate: bool = True, persist: bool = True):
        """Set configuration value with validation and persistence."""
        
        self.metrics['config_writes'] += 1
        
        try:
            # Validate new value
            if validate:
                validation_result = await self._validate_configuration_change(key, value)
                if not validation_result['valid']:
                    raise ValueError(f"Configuration validation failed: {validation_result['error']}")
            
            # Store old value for rollback
            old_value = self.get(key, None, validate=False)
            
            # Set new value
            await self._set_nested_value(key, value)
            
            # Record change
            change_record = {
                'timestamp': time.time(),
                'key': key,
                'old_value': old_value,
                'new_value': value,
                'user': 'system',  # Could be enhanced with user tracking
                'validated': validate
            }
            self._change_history.append(change_record)
            
            # Persist if requested
            if persist:
                await self.persistence_layer.save_configuration(self._config_data)
            
            # Notify listeners
            await self._notify_configuration_change(key, old_value, value)
            
            # Update timestamp
            self._last_update = time.time()
            
            return True
            
        except Exception as e:
            logging.error(f"Configuration set error for key {key}: {e}")
            raise
    
    async def update_batch(self, updates: dict, validate: bool = True, persist: bool = True):
        """Update multiple configuration values atomically."""
        
        try:
            # Validate all changes first
            if validate:
                for key, value in updates.items():
                    validation_result = await self._validate_configuration_change(key, value)
                    if not validation_result['valid']:
                        raise ValueError(f"Batch validation failed for {key}: {validation_result['error']}")
            
            # Store old values for rollback
            old_values = {}
            for key in updates.keys():
                old_values[key] = self.get(key, None, validate=False)
            
            # Apply all changes
            for key, value in updates.items():
                await self._set_nested_value(key, value)
            
            # Record batch change
            batch_record = {
                'timestamp': time.time(),
                'type': 'batch_update',
                'changes': updates,
                'old_values': old_values,
                'validated': validate
            }
            self._change_history.append(batch_record)
            
            # Persist if requested
            if persist:
                await self.persistence_layer.save_configuration(self._config_data)
            
            # Notify listeners for each change
            for key, value in updates.items():
                await self._notify_configuration_change(key, old_values[key], value)
            
            self._last_update = time.time()
            return True
            
        except Exception as e:
            logging.error(f"Batch configuration update failed: {e}")
            # Rollback on failure
            await self._rollback_to_previous_state()
            raise
    
    def register_change_listener(self, callback: Callable, key_pattern: str = "*"):
        """Register callback for configuration changes."""
        
        listener = {
            'callback': callback,
            'pattern': key_pattern,
            'registered_at': time.time()
        }
        self._change_listeners.append(listener)
        
        return len(self._change_listeners) - 1  # Return listener ID
    
    def unregister_change_listener(self, listener_id: int):
        """Unregister configuration change listener."""
        
        if 0 <= listener_id < len(self._change_listeners):
            self._change_listeners[listener_id] = None
    
    async def reload_configuration(self, source: str = "file"):
        """Reload configuration from specified source."""
        
        try:
            # Load configuration based on source
            if source == "file":
                new_config = await self.persistence_layer.load_from_file()
            elif source == "database":
                new_config = await self.persistence_layer.load_from_database()
            else:
                raise ValueError(f"Unknown configuration source: {source}")
            
            # Validate new configuration
            validation_result = await self.config_validator.validate_full_configuration(new_config)
            if not validation_result['valid']:
                raise ValueError(f"Configuration validation failed: {validation_result['errors']}")
            
            # Store old configuration for rollback
            old_config = self._config_data.copy()
            
            # Apply new configuration
            self._config_data = new_config
            self.metrics['hot_reloads'] += 1
            
            # Record reload
            reload_record = {
                'timestamp': time.time(),
                'type': 'full_reload',
                'source': source,
                'old_config_hash': self._calculate_config_hash(old_config),
                'new_config_hash': self._calculate_config_hash(new_config)
            }
            self._change_history.append(reload_record)
            
            # Notify all listeners of reload
            await self._notify_configuration_reload(old_config, new_config)
            
            self._last_update = time.time()
            return True
            
        except Exception as e:
            logging.error(f"Configuration reload failed: {e}")
            raise
    
    async def _validate_configuration_change(self, key: str, value) -> dict:
        """Validate a configuration change."""
        
        self.metrics['validation_checks'] += 1
        
        # Check if validation rule exists
        if key not in self._validation_rules:
            return {'valid': True}
        
        # Perform validation
        validation_result = self.config_validator.validate_value(
            key, value, self._validation_rules[key]
        )
        
        return validation_result
    
    async def _set_nested_value(self, key: str, value):
        """Set value in nested configuration structure."""
        
        keys = key.split('.')
        current = self._config_data
        
        # Navigate to parent of target key
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        # Set the final value
        current[keys[-1]] = value
    
    async def _notify_configuration_change(self, key: str, old_value, new_value):
        """Notify registered listeners of configuration changes."""
        
        for listener in self._change_listeners:
            if listener is None:
                continue
            
            try:
                # Check if key matches listener pattern
                if self._key_matches_pattern(key, listener['pattern']):
                    if asyncio.iscoroutinefunction(listener['callback']):
                        await listener['callback'](key, old_value, new_value)
                    else:
                        listener['callback'](key, old_value, new_value)
                        
            except Exception as e:
                logging.error(f"Configuration change listener error: {e}")
    
    def _key_matches_pattern(self, key: str, pattern: str) -> bool:
        """Check if configuration key matches listener pattern."""
        
        if pattern == "*":
            return True
        
        # Simple wildcard matching
        if pattern.endswith("*"):
            prefix = pattern[:-1]
            return key.startswith(prefix)
        
        return key == pattern
    
    def _initialize_configuration(self):
        """Initialize default configuration structure."""
        
        # Default configuration schema
        self._config_data = {
            'system': {
                'name': 'Leonidas',
                'version': '1.0.0',
                'environment': 'development',
                'debug': True,
                'log_level': 'INFO'
            },
            'agents': {
                'visual_perception': {
                    'enabled': True,
                    'confidence_threshold': 0.8,
                    'processing_interval': 0.1
                },
                'dialogue_analysis': {
                    'enabled': True,
                    'language': 'pt-BR',
                    'speaker_diarization': True
                },
                'cognitive_reasoning': {
                    'enabled': True,
                    'thinking_mode': 'deep',
                    'intervention_threshold': 0.7
                }
            },
            'memory': {
                'visual_memory': {
                    'enabled': True,
                    'face_recognition': True,
                    'retention_days': 30
                },
                'conversation_memory': {
                    'enabled': True,
                    'max_entries': 10000,
                    'compression_enabled': True
                }
            },
            'api': {
                'gemini': {
                    'model': 'gemini-live-2.5-flash-preview',
                    'api_key': None,
                    'rate_limit': 60
                }
            },
            'security': {
                'encryption_enabled': True,
                'audit_logging': True,
                'access_control': True
            }
        }
        
        # Initialize validation rules
        self._setup_validation_rules()
    
    def _setup_validation_rules(self):
        """Setup validation rules for configuration values."""
        
        self._validation_rules = {
            'system.log_level': {
                'type': 'string',
                'allowed_values': ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
            },
            'agents.visual_perception.confidence_threshold': {
                'type': 'float',
                'min_value': 0.0,
                'max_value': 1.0
            },
            'agents.visual_perception.processing_interval': {
                'type': 'float',
                'min_value': 0.01,
                'max_value': 10.0
            },
            'memory.visual_memory.retention_days': {
                'type': 'integer',
                'min_value': 1,
                'max_value': 365
            },
            'api.gemini.rate_limit': {
                'type': 'integer',
                'min_value': 1,
                'max_value': 1000
            }
        }
```

### **2. Configuration Validator**

```python
class ConfigValidator:
    """Comprehensive configuration validation system."""
    
    def __init__(self):
        self.validation_schemas = {}
        self.custom_validators = {}
        
        # Built-in validation types
        self.builtin_validators = {
            'string': self._validate_string,
            'integer': self._validate_integer,
            'float': self._validate_float,
            'boolean': self._validate_boolean,
            'list': self._validate_list,
            'dict': self._validate_dict,
            'enum': self._validate_enum
        }
    
    def validate_value(self, key: str, value, validation_rule: dict) -> dict:
        """Validate a single configuration value."""
        
        try:
            # Get validation type
            validation_type = validation_rule.get('type', 'string')
            
            # Use custom validator if available
            if validation_type in self.custom_validators:
                validator = self.custom_validators[validation_type]
                return validator(key, value, validation_rule)
            
            # Use built-in validator
            if validation_type in self.builtin_validators:
                validator = self.builtin_validators[validation_type]
                return validator(value, validation_rule)
            
            return {
                'valid': False,
                'error': f'Unknown validation type: {validation_type}'
            }
            
        except Exception as e:
            return {
                'valid': False,
                'error': f'Validation error: {str(e)}'
            }
    
    async def validate_full_configuration(self, config: dict) -> dict:
        """Validate entire configuration structure."""
        
        validation_errors = []
        
        try:
            # Validate against schema if available
            if self.validation_schemas:
                schema_errors = await self._validate_against_schema(config)
                validation_errors.extend(schema_errors)
            
            # Validate individual values
            for key, rule in self._get_all_validation_rules().items():
                value = self._get_nested_value(config, key)
                if value is not None:
                    result = self.validate_value(key, value, rule)
                    if not result['valid']:
                        validation_errors.append(f"{key}: {result['error']}")
            
            return {
                'valid': len(validation_errors) == 0,
                'errors': validation_errors
            }
            
        except Exception as e:
            return {
                'valid': False,
                'errors': [f'Configuration validation failed: {str(e)}']
            }
    
    def _validate_string(self, value, rule: dict) -> dict:
        """Validate string value."""
        
        if not isinstance(value, str):
            return {'valid': False, 'error': 'Value must be a string'}
        
        # Check allowed values
        if 'allowed_values' in rule:
            if value not in rule['allowed_values']:
                return {
                    'valid': False,
                    'error': f'Value must be one of: {rule["allowed_values"]}'
                }
        
        # Check length constraints
        if 'min_length' in rule and len(value) < rule['min_length']:
            return {
                'valid': False,
                'error': f'String must be at least {rule["min_length"]} characters'
            }
        
        if 'max_length' in rule and len(value) > rule['max_length']:
            return {
                'valid': False,
                'error': f'String must be at most {rule["max_length"]} characters'
            }
        
        # Check pattern matching
        if 'pattern' in rule:
            import re
            if not re.match(rule['pattern'], value):
                return {
                    'valid': False,
                    'error': f'String must match pattern: {rule["pattern"]}'
                }
        
        return {'valid': True}
    
    def _validate_float(self, value, rule: dict) -> dict:
        """Validate float value."""
        
        if not isinstance(value, (int, float)):
            return {'valid': False, 'error': 'Value must be a number'}
        
        value = float(value)
        
        # Check range constraints
        if 'min_value' in rule and value < rule['min_value']:
            return {
                'valid': False,
                'error': f'Value must be at least {rule["min_value"]}'
            }
        
        if 'max_value' in rule and value > rule['max_value']:
            return {
                'valid': False,
                'error': f'Value must be at most {rule["max_value"]}'
            }
        
        return {'valid': True}
```

### **3. Runtime Manager**

```python
class RuntimeManager:
    """Manage runtime configuration changes and hot-reloading."""
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.hot_reloader = HotReloader()
        self.change_notifier = ChangeNotifier()
        self.rollback_manager = RollbackManager()
        
        # Runtime state
        self.monitoring_active = False
        self.file_watchers = {}
        self.change_queue = asyncio.Queue()
        
        # Performance tracking
        self.runtime_metrics = {
            'hot_reloads': 0,
            'change_notifications': 0,
            'rollbacks': 0,
            'file_watch_events': 0
        }
    
    async def initialize(self):
        """Initialize runtime management components."""
        
        await self.hot_reloader.initialize()
        await self.change_notifier.initialize()
        await self.rollback_manager.initialize()
    
    async def start_monitoring(self):
        """Start runtime configuration monitoring."""
        
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        
        # Start file watching
        await self._start_file_watching()
        
        # Start change processing
        asyncio.create_task(self._process_change_queue())
        
        logging.info("Runtime configuration monitoring started")
    
    async def stop_monitoring(self):
        """Stop runtime configuration monitoring."""
        
        self.monitoring_active = False
        
        # Stop file watchers
        for watcher in self.file_watchers.values():
            await watcher.stop()
        
        self.file_watchers.clear()
        
        logging.info("Runtime configuration monitoring stopped")
    
    async def _start_file_watching(self):
        """Start watching configuration files for changes."""
        
        config_files = [
            'config/leonidas.yaml',
            'config/agents.yaml',
            'config/environment.yaml'
        ]
        
        for config_file in config_files:
            if os.path.exists(config_file):
                watcher = FileWatcher(config_file, self._handle_file_change)
                await watcher.start()
                self.file_watchers[config_file] = watcher
    
    async def _handle_file_change(self, file_path: str):
        """Handle configuration file changes."""
        
        self.runtime_metrics['file_watch_events'] += 1
        
        # Queue change for processing
        await self.change_queue.put({
            'type': 'file_change',
            'file_path': file_path,
            'timestamp': time.time()
        })
    
    async def _process_change_queue(self):
        """Process queued configuration changes."""
        
        while self.monitoring_active:
            try:
                change = await asyncio.wait_for(
                    self.change_queue.get(), timeout=1.0
                )
                
                if change['type'] == 'file_change':
                    await self._process_file_change(change)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logging.error(f"Change queue processing error: {e}")
    
    async def _process_file_change(self, change: dict):
        """Process configuration file change."""
        
        try:
            # Reload configuration from file
            await self.config_manager.reload_configuration('file')
            
            self.runtime_metrics['hot_reloads'] += 1
            
            logging.info(f"Configuration hot-reloaded from {change['file_path']}")
            
        except Exception as e:
            logging.error(f"Hot-reload failed for {change['file_path']}: {e}")
            
            # Attempt rollback on failure
            await self.rollback_manager.rollback_last_change()
```

### **4. Environment Manager**

```python
class EnvironmentManager:
    """Manage environment-specific configuration."""
    
    def __init__(self):
        self.environment_detector = EnvironmentDetector()
        self.profile_manager = ProfileManager()
        self.override_handler = OverrideHandler()
        self.secret_manager = SecretManager()
        
        # Environment state
        self.current_environment = None
        self.active_profile = None
        self.environment_overrides = {}
    
    async def detect_and_configure_environment(self) -> str:
        """Detect current environment and apply configuration."""
        
        # Detect environment
        environment = await self.environment_detector.detect_environment()
        self.current_environment = environment
        
        # Load environment-specific profile
        profile = await self.profile_manager.load_profile(environment)
        self.active_profile = profile
        
        # Apply environment overrides
        overrides = await self.override_handler.get_overrides(environment)
        self.environment_overrides = overrides
        
        # Load secrets for environment
        await self.secret_manager.load_secrets(environment)
        
        return environment
    
    def get_environment_config(self) -> dict:
        """Get complete environment-specific configuration."""
        
        config = {}
        
        # Start with base profile
        if self.active_profile:
            config.update(self.active_profile)
        
        # Apply environment overrides
        if self.environment_overrides:
            config = self._merge_configurations(config, self.environment_overrides)
        
        # Apply secrets
        secrets = self.secret_manager.get_secrets()
        if secrets:
            config = self._merge_configurations(config, secrets)
        
        return config
    
    def _merge_configurations(self, base: dict, override: dict) -> dict:
        """Merge configuration dictionaries with deep merging."""
        
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configurations(result[key], value)
            else:
                result[key] = value
        
        return result
```

## 🔧 **INTEGRATION SPECIFICATIONS**

### **Signal Bus Integration**
```python
# Signal types for configuration management
CONFIGURATION_SIGNALS = {
    'CONFIG_CHANGED': 'config.changed',
    'CONFIG_RELOADED': 'config.reloaded',
    'CONFIG_VALIDATED': 'config.validated',
    'CONFIG_ERROR': 'config.error',
    'ENVIRONMENT_CHANGED': 'config.environment_changed'
}

# Integration with signal bus
async def integrate_with_signal_bus(self, signal_bus: SignalBus):
    """Integrate configuration manager with signal bus."""
    
    # Register configuration change listener
    self.register_change_listener(
        lambda key, old_val, new_val: signal_bus.emit(
            CONFIGURATION_SIGNALS['CONFIG_CHANGED'],
            {'key': key, 'old_value': old_val, 'new_value': new_val}
        )
    )
    
    # Subscribe to configuration requests
    await signal_bus.subscribe(
        'system.config_request',
        self._handle_config_request
    )
```

### **Usage Examples**
```python
# Get singleton instance
config = SystemConfigurationManager()

# Basic configuration access
debug_mode = config.get('system.debug', False)
api_key = config.get('api.gemini.api_key')

# Set configuration values
await config.set('agents.visual_perception.enabled', True)
await config.set('system.log_level', 'DEBUG')

# Batch updates
await config.update_batch({
    'agents.visual_perception.confidence_threshold': 0.9,
    'agents.dialogue_analysis.language': 'pt-BR',
    'memory.visual_memory.retention_days': 60
})

# Register for change notifications
config.register_change_listener(
    lambda key, old, new: print(f"Config changed: {key} = {new}"),
    "agents.*"
)

# Reload configuration
await config.reload_configuration('file')
```

## 📊 **PERFORMANCE REQUIREMENTS**

### **Access Performance**
- **Configuration Read**: < 1ms for cached values
- **Configuration Write**: < 10ms including validation
- **Batch Updates**: < 50ms for 10 simultaneous changes
- **Hot Reload**: < 500ms for complete configuration reload

### **Memory Requirements**
- **Configuration Storage**: < 10MB for complete configuration
- **Change History**: < 5MB for 1000 change records
- **Validation Cache**: < 2MB for validation rules

### **Reliability Requirements**
- **Configuration Persistence**: 99.9% success rate
- **Validation Accuracy**: 100% for critical configuration
- **Rollback Success**: 99% success rate for rollback operations

## 🛡️ **SECURITY & SAFETY**

### **Configuration Security**
```python
class SecretManager:
    """Secure handling of sensitive configuration values."""
    
    def __init__(self):
        self.encryption_key = self._load_encryption_key()
        self.encrypted_keys = set()
    
    def encrypt_value(self, value: str) -> str:
        """Encrypt sensitive configuration value."""
        
        from cryptography.fernet import Fernet
        
        fernet = Fernet(self.encryption_key)
        encrypted_value = fernet.encrypt(value.encode())
        
        return encrypted_value.decode()
    
    def decrypt_value(self, encrypted_value: str) -> str:
        """Decrypt sensitive configuration value."""
        
        from cryptography.fernet import Fernet
        
        fernet = Fernet(self.encryption_key)
        decrypted_value = fernet.decrypt(encrypted_value.encode())
        
        return decrypted_value.decode()
    
    def is_sensitive_key(self, key: str) -> bool:
        """Check if configuration key contains sensitive data."""
        
        sensitive_patterns = [
            'password', 'secret', 'key', 'token', 'credential',
            'api_key', 'private_key', 'auth'
        ]
        
        key_lower = key.lower()
        return any(pattern in key_lower for pattern in sensitive_patterns)
```

## 🧪 **TESTING STRATEGY**

### **Unit Tests**
```python
class TestSystemConfigurationManager(unittest.TestCase):
    
    def setUp(self):
        # Reset singleton for testing
        SystemConfigurationManager._instance = None
        self.config = SystemConfigurationManager()
    
    async def test_singleton_behavior(self):
        """Test singleton pattern implementation."""
        
        config1 = SystemConfigurationManager()
        config2 = SystemConfigurationManager()
        
        self.assertIs(config1, config2)
    
    async def test_configuration_get_set(self):
        """Test basic configuration get/set operations."""
        
        # Test setting and getting values
        await self.config.set('test.value', 'hello')
        result = self.config.get('test.value')
        
        self.assertEqual(result, 'hello')
    
    async def test_configuration_validation(self):
        """Test configuration validation."""
        
        # Test valid value
        result = await self.config.set('system.log_level', 'DEBUG')
        self.assertTrue(result)
        
        # Test invalid value
        with self.assertRaises(ValueError):
            await self.config.set('system.log_level', 'INVALID')
    
    async def test_change_notifications(self):
        """Test configuration change notifications."""
        
        changes_received = []
        
        def change_listener(key, old_val, new_val):
            changes_received.append((key, old_val, new_val))
        
        self.config.register_change_listener(change_listener)
        
        await self.config.set('test.notification', 'value')
        
        self.assertEqual(len(changes_received), 1)
        self.assertEqual(changes_received[0][0], 'test.notification')
```

This System Configuration Manager provides comprehensive, secure, and high-performance configuration management for the Leonidas system, ensuring consistent configuration access and reliable runtime updates across all components.