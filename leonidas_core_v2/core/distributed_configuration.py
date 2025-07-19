"""
Distributed Configuration System

Manages configuration across distributed components with synchronization and validation.
"""

import asyncio
import json
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Callable, Set
import threading
import hashlib
import copy


class ConfigurationScope(Enum):
    """Configuration scope levels."""
    GLOBAL = "global"
    COMPONENT = "component"
    MODULE = "module"
    SESSION = "session"


class ConfigurationPriority(Enum):
    """Configuration priority levels."""
    SYSTEM = 1      # System defaults
    GLOBAL = 2      # Global overrides
    COMPONENT = 3   # Component-specific
    MODULE = 4      # Module-specific
    SESSION = 5     # Session-specific
    RUNTIME = 6     # Runtime overrides


@dataclass
class ConfigurationEntry:
    """Single configuration entry."""
    key: str
    value: Any
    scope: ConfigurationScope
    priority: ConfigurationPriority
    timestamp: float
    source: str
    description: str = ""
    validation_schema: Optional[Dict[str, Any]] = None
    encrypted: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "key": self.key,
            "value": self.value,
            "scope": self.scope.value,
            "priority": self.priority.value,
            "timestamp": self.timestamp,
            "source": self.source,
            "description": self.description,
            "validation_schema": self.validation_schema,
            "encrypted": self.encrypted,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConfigurationEntry':
        """Create from dictionary."""
        return cls(
            key=data["key"],
            value=data["value"],
            scope=ConfigurationScope(data["scope"]),
            priority=ConfigurationPriority(data["priority"]),
            timestamp=data["timestamp"],
            source=data["source"],
            description=data.get("description", ""),
            validation_schema=data.get("validation_schema"),
            encrypted=data.get("encrypted", False),
        )


@dataclass
class ConfigurationSnapshot:
    """Snapshot of configuration state."""
    snapshot_id: str
    timestamp: float
    entries: Dict[str, ConfigurationEntry]
    checksum: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "snapshot_id": self.snapshot_id,
            "timestamp": self.timestamp,
            "entries": {k: v.to_dict() for k, v in self.entries.items()},
            "checksum": self.checksum,
        }


class ConfigurationValidator:
    """Validates configuration entries against schemas."""
    
    @staticmethod
    def validate_entry(entry: ConfigurationEntry) -> tuple[bool, Optional[str]]:
        """
        Validate configuration entry.
        
        Args:
            entry: Configuration entry to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not entry.validation_schema:
            return True, None
        
        try:
            schema = entry.validation_schema
            value = entry.value
            
            # Check type
            expected_type = schema.get("type")
            if expected_type:
                if not ConfigurationValidator._check_type(value, expected_type):
                    return False, f"Invalid type for {entry.key}: expected {expected_type}"
            
            # Check range for numeric values
            if isinstance(value, (int, float)):
                min_val = schema.get("minimum")
                max_val = schema.get("maximum")
                
                if min_val is not None and value < min_val:
                    return False, f"Value {value} below minimum {min_val} for {entry.key}"
                
                if max_val is not None and value > max_val:
                    return False, f"Value {value} above maximum {max_val} for {entry.key}"
            
            # Check enum values
            enum_values = schema.get("enum")
            if enum_values and value not in enum_values:
                return False, f"Value {value} not in allowed values {enum_values} for {entry.key}"
            
            # Check string length
            if isinstance(value, str):
                min_length = schema.get("minLength")
                max_length = schema.get("maxLength")
                
                if min_length is not None and len(value) < min_length:
                    return False, f"String too short for {entry.key}: minimum length {min_length}"
                
                if max_length is not None and len(value) > max_length:
                    return False, f"String too long for {entry.key}: maximum length {max_length}"
            
            return True, None
            
        except Exception as e:
            return False, f"Validation error for {entry.key}: {e}"
    
    @staticmethod
    def _check_type(value: Any, expected_type: str) -> bool:
        """Check if value matches expected type."""
        type_mapping = {
            "string": str,
            "number": (int, float),
            "integer": int,
            "boolean": bool,
            "array": list,
            "object": dict,
        }
        
        expected_python_type = type_mapping.get(expected_type)
        if expected_python_type:
            return isinstance(value, expected_python_type)
        
        return True  # Unknown type, assume valid


class DistributedConfiguration:
    """
    Distributed configuration management system.
    
    Provides:
    - Hierarchical configuration with priority levels
    - Cross-component synchronization
    - Configuration validation
    - Change notifications
    - Rollback capabilities
    - Encryption for sensitive values
    """
    
    def __init__(self, 
                 component_id: str,
                 sync_interval: float = 30.0,
                 enable_encryption: bool = True):
        """
        Initialize distributed configuration.
        
        Args:
            component_id: Unique identifier for this component
            sync_interval: Seconds between synchronization checks
            enable_encryption: Enable encryption for sensitive values
        """
        self.component_id = component_id
        self.sync_interval = sync_interval
        self.enable_encryption = enable_encryption
        
        # Configuration storage
        self.entries: Dict[str, ConfigurationEntry] = {}
        self.snapshots: Dict[str, ConfigurationSnapshot] = {}
        
        # Synchronization
        self._sync_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()
        self._lock = threading.RLock()
        
        # Change notifications
        self.change_callbacks: List[Callable[[str, Any, Any], None]] = []
        self.validation_callbacks: List[Callable[[ConfigurationEntry], tuple[bool, Optional[str]]]] = []
        
        # Metrics
        self.metrics = {
            "entries_count": 0,
            "sync_operations": 0,
            "validation_errors": 0,
            "change_notifications": 0,
        }
        
        # Logging
        self.logger = logging.getLogger(f"leonidas.config.{component_id}")
    
    async def start(self) -> None:
        """Start configuration management."""
        self.logger.info(f"Starting distributed configuration for {self.component_id}")
        
        try:
            # Load initial configuration
            await self._load_initial_configuration()
            
            # Start synchronization
            self._sync_task = asyncio.create_task(self._sync_loop())
            
            self.logger.info(f"Distributed configuration started for {self.component_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to start distributed configuration: {e}")
            raise
    
    async def stop(self) -> None:
        """Stop configuration management."""
        self.logger.info(f"Stopping distributed configuration for {self.component_id}")
        
        # Signal shutdown
        self._shutdown_event.set()
        
        # Cancel sync task
        if self._sync_task:
            self._sync_task.cancel()
            try:
                await self._sync_task
            except asyncio.CancelledError:
                pass
        
        # Save final state
        await self._save_configuration()
        
        self.logger.info(f"Distributed configuration stopped for {self.component_id}")
    
    def set(self, 
            key: str, 
            value: Any, 
            scope: ConfigurationScope = ConfigurationScope.COMPONENT,
            priority: ConfigurationPriority = ConfigurationPriority.COMPONENT,
            description: str = "",
            validation_schema: Optional[Dict[str, Any]] = None,
            encrypt: bool = False) -> bool:
        """
        Set configuration value.
        
        Args:
            key: Configuration key
            value: Configuration value
            scope: Configuration scope
            priority: Configuration priority
            description: Description of the configuration
            validation_schema: JSON schema for validation
            encrypt: Whether to encrypt the value
            
        Returns:
            True if set successfully, False otherwise
        """
        try:
            # Create configuration entry
            entry = ConfigurationEntry(
                key=key,
                value=value,
                scope=scope,
                priority=priority,
                timestamp=time.time(),
                source=self.component_id,
                description=description,
                validation_schema=validation_schema,
                encrypted=encrypt and self.enable_encryption,
            )
            
            # Validate entry
            is_valid, error_message = ConfigurationValidator.validate_entry(entry)
            if not is_valid:
                self.logger.error(f"Configuration validation failed for {key}: {error_message}")
                self.metrics["validation_errors"] += 1
                return False
            
            # Apply custom validation callbacks
            for callback in self.validation_callbacks:
                try:
                    is_valid, error_message = callback(entry)
                    if not is_valid:
                        self.logger.error(f"Custom validation failed for {key}: {error_message}")
                        self.metrics["validation_errors"] += 1
                        return False
                except Exception as e:
                    self.logger.error(f"Validation callback error for {key}: {e}")
                    return False
            
            # Encrypt value if needed
            if entry.encrypted:
                entry.value = self._encrypt_value(entry.value)
            
            # Store entry
            with self._lock:
                old_value = None
                if key in self.entries:
                    old_entry = self.entries[key]
                    # Only update if new priority is higher or equal
                    if entry.priority.value < old_entry.priority.value:
                        self.logger.warning(f"Ignoring lower priority update for {key}")
                        return False
                    old_value = old_entry.value
                
                self.entries[key] = entry
                self.metrics["entries_count"] = len(self.entries)
            
            # Notify change callbacks
            self._notify_change(key, old_value, value)
            
            self.logger.debug(f"Configuration set: {key} = {value}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to set configuration {key}: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        try:
            with self._lock:
                if key not in self.entries:
                    return default
                
                entry = self.entries[key]
                value = entry.value
                
                # Decrypt if needed
                if entry.encrypted:
                    value = self._decrypt_value(value)
                
                return value
                
        except Exception as e:
            self.logger.error(f"Failed to get configuration {key}: {e}")
            return default
    
    def get_entry(self, key: str) -> Optional[ConfigurationEntry]:
        """Get full configuration entry."""
        with self._lock:
            entry = self.entries.get(key)
            if entry and entry.encrypted:
                # Return copy with decrypted value
                decrypted_entry = copy.deepcopy(entry)
                decrypted_entry.value = self._decrypt_value(entry.value)
                return decrypted_entry
            return entry
    
    def delete(self, key: str) -> bool:
        """
        Delete configuration entry.
        
        Args:
            key: Configuration key to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            with self._lock:
                if key not in self.entries:
                    return False
                
                old_value = self.entries[key].value
                del self.entries[key]
                self.metrics["entries_count"] = len(self.entries)
            
            # Notify change callbacks
            self._notify_change(key, old_value, None)
            
            self.logger.debug(f"Configuration deleted: {key}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete configuration {key}: {e}")
            return False
    
    def get_all(self, scope: Optional[ConfigurationScope] = None) -> Dict[str, Any]:
        """
        Get all configuration values.
        
        Args:
            scope: Filter by scope (optional)
            
        Returns:
            Dictionary of configuration values
        """
        result = {}
        
        with self._lock:
            for key, entry in self.entries.items():
                if scope is None or entry.scope == scope:
                    value = entry.value
                    if entry.encrypted:
                        value = self._decrypt_value(value)
                    result[key] = value
        
        return result
    
    def create_snapshot(self, snapshot_id: str) -> bool:
        """
        Create configuration snapshot.
        
        Args:
            snapshot_id: Unique identifier for snapshot
            
        Returns:
            True if snapshot created successfully, False otherwise
        """
        try:
            with self._lock:
                entries_copy = copy.deepcopy(self.entries)
                
                # Calculate checksum
                entries_json = json.dumps(
                    {k: v.to_dict() for k, v in entries_copy.items()},
                    sort_keys=True
                )
                checksum = hashlib.sha256(entries_json.encode()).hexdigest()
                
                snapshot = ConfigurationSnapshot(
                    snapshot_id=snapshot_id,
                    timestamp=time.time(),
                    entries=entries_copy,
                    checksum=checksum,
                )
                
                self.snapshots[snapshot_id] = snapshot
            
            self.logger.info(f"Configuration snapshot created: {snapshot_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create snapshot {snapshot_id}: {e}")
            return False
    
    def restore_snapshot(self, snapshot_id: str) -> bool:
        """
        Restore configuration from snapshot.
        
        Args:
            snapshot_id: Snapshot to restore
            
        Returns:
            True if restored successfully, False otherwise
        """
        try:
            with self._lock:
                if snapshot_id not in self.snapshots:
                    self.logger.error(f"Snapshot {snapshot_id} not found")
                    return False
                
                snapshot = self.snapshots[snapshot_id]
                
                # Verify checksum
                entries_json = json.dumps(
                    {k: v.to_dict() for k, v in snapshot.entries.items()},
                    sort_keys=True
                )
                checksum = hashlib.sha256(entries_json.encode()).hexdigest()
                
                if checksum != snapshot.checksum:
                    self.logger.error(f"Snapshot {snapshot_id} checksum mismatch")
                    return False
                
                # Store old entries for rollback
                old_entries = self.entries.copy()
                
                try:
                    # Restore entries
                    self.entries = copy.deepcopy(snapshot.entries)
                    self.metrics["entries_count"] = len(self.entries)
                    
                    # Notify changes
                    for key, entry in self.entries.items():
                        old_value = old_entries.get(key)
                        if old_value:
                            old_value = old_value.value
                        self._notify_change(key, old_value, entry.value)
                    
                    self.logger.info(f"Configuration restored from snapshot: {snapshot_id}")
                    return True
                    
                except Exception as e:
                    # Rollback on error
                    self.entries = old_entries
                    self.metrics["entries_count"] = len(self.entries)
                    raise e
                
        except Exception as e:
            self.logger.error(f"Failed to restore snapshot {snapshot_id}: {e}")
            return False
    
    def add_change_callback(self, callback: Callable[[str, Any, Any], None]) -> None:
        """Add callback for configuration changes."""
        self.change_callbacks.append(callback)
    
    def add_validation_callback(self, callback: Callable[[ConfigurationEntry], tuple[bool, Optional[str]]]) -> None:
        """Add custom validation callback."""
        self.validation_callbacks.append(callback)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get configuration metrics."""
        with self._lock:
            return {
                **self.metrics,
                "snapshots_count": len(self.snapshots),
                "scopes": {
                    scope.value: len([e for e in self.entries.values() if e.scope == scope])
                    for scope in ConfigurationScope
                },
                "priorities": {
                    priority.name: len([e for e in self.entries.values() if e.priority == priority])
                    for priority in ConfigurationPriority
                },
            }
    
    # Abstract methods for persistence (to be implemented by subclasses)
    async def _load_initial_configuration(self) -> None:
        """Load initial configuration from storage."""
        # Default implementation - can be overridden
        pass
    
    async def _save_configuration(self) -> None:
        """Save configuration to storage."""
        # Default implementation - can be overridden
        pass
    
    async def _sync_with_peers(self) -> None:
        """Synchronize configuration with peer components."""
        # Default implementation - can be overridden
        pass
    
    # Private methods
    async def _sync_loop(self) -> None:
        """Configuration synchronization loop."""
        while not self._shutdown_event.is_set():
            try:
                # Synchronize with peers
                await self._sync_with_peers()
                
                # Update metrics
                self.metrics["sync_operations"] += 1
                
                # Wait for next sync
                await asyncio.sleep(self.sync_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Sync loop error: {e}")
                await asyncio.sleep(self.sync_interval)
    
    def _notify_change(self, key: str, old_value: Any, new_value: Any) -> None:
        """Notify change callbacks."""
        if old_value == new_value:
            return
        
        self.metrics["change_notifications"] += 1
        
        for callback in self.change_callbacks:
            try:
                callback(key, old_value, new_value)
            except Exception as e:
                self.logger.error(f"Change callback error for {key}: {e}")
    
    def _encrypt_value(self, value: Any) -> str:
        """Encrypt configuration value."""
        # Simple base64 encoding - in production, use proper encryption
        import base64
        value_json = json.dumps(value)
        return base64.b64encode(value_json.encode()).decode()
    
    def _decrypt_value(self, encrypted_value: str) -> Any:
        """Decrypt configuration value."""
        # Simple base64 decoding - in production, use proper decryption
        import base64
        try:
            value_json = base64.b64decode(encrypted_value.encode()).decode()
            return json.loads(value_json)
        except Exception as e:
            self.logger.error(f"Failed to decrypt value: {e}")
            return encrypted_value