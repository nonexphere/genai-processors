"""
Hot-Swappable Module Interface

Enables dynamic connection and disconnection of modules without system restart.
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Callable, Set
import json
import uuid


class ModuleState(Enum):
    """Module connection states."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DISCONNECTING = "disconnecting"
    ERROR = "error"


class ModuleCapability(Enum):
    """Standard module capabilities."""
    AUDIO_PROCESSING = "audio_processing"
    VIDEO_PROCESSING = "video_processing"
    TEXT_PROCESSING = "text_processing"
    SENSOR_DATA = "sensor_data"
    ACTUATOR_CONTROL = "actuator_control"
    DECISION_MAKING = "decision_making"
    MEMORY_STORAGE = "memory_storage"
    COMMUNICATION = "communication"


@dataclass
class ModuleInfo:
    """Module information and metadata."""
    module_id: str
    name: str
    version: str
    capabilities: List[ModuleCapability]
    description: str
    author: str = ""
    dependencies: List[str] = field(default_factory=list)
    configuration_schema: Dict[str, Any] = field(default_factory=dict)
    resource_requirements: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "module_id": self.module_id,
            "name": self.name,
            "version": self.version,
            "capabilities": [cap.value for cap in self.capabilities],
            "description": self.description,
            "author": self.author,
            "dependencies": self.dependencies,
            "configuration_schema": self.configuration_schema,
            "resource_requirements": self.resource_requirements,
        }


@dataclass
class ConnectionInfo:
    """Connection information for a module."""
    connection_id: str
    module_info: ModuleInfo
    connected_at: float
    last_heartbeat: float
    configuration: Dict[str, Any] = field(default_factory=dict)
    subscriptions: Set[str] = field(default_factory=set)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)


class HotSwappableModule(ABC):
    """
    Base interface for hot-swappable modules.
    
    Modules implementing this interface can be dynamically connected to and
    disconnected from the Leonidas Core system without requiring restart.
    """
    
    def __init__(self, module_info: ModuleInfo):
        """
        Initialize hot-swappable module.
        
        Args:
            module_info: Module metadata and capabilities
        """
        self.module_info = module_info
        self.connection_id = str(uuid.uuid4())
        self.state = ModuleState.DISCONNECTED
        self.configuration: Dict[str, Any] = {}
        self.subscriptions: Set[str] = set()
        
        # Connection management
        self._connection_callbacks: List[Callable[[ModuleState], None]] = []
        self._message_handlers: Dict[str, Callable[[Dict[str, Any]], Any]] = {}
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()
        
        # Performance tracking
        self.performance_metrics = {
            "messages_processed": 0,
            "processing_time_total": 0.0,
            "last_activity": time.time(),
            "errors": 0,
        }
        
        # Logging
        self.logger = logging.getLogger(f"leonidas.module.{module_info.module_id}")
    
    async def connect(self, system_interface: 'SystemInterface') -> bool:
        """
        Connect module to the system.
        
        Args:
            system_interface: Interface to communicate with the core system
            
        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.logger.info(f"Connecting module {self.module_info.module_id}")
            self._set_state(ModuleState.CONNECTING)
            
            # Store system interface
            self.system_interface = system_interface
            
            # Perform module-specific initialization
            await self._on_connect()
            
            # Start heartbeat
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            
            self._set_state(ModuleState.CONNECTED)
            self.logger.info(f"Module {self.module_info.module_id} connected successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect module {self.module_info.module_id}: {e}")
            self._set_state(ModuleState.ERROR)
            return False
    
    async def disconnect(self) -> None:
        """Disconnect module from the system."""
        self.logger.info(f"Disconnecting module {self.module_info.module_id}")
        self._set_state(ModuleState.DISCONNECTING)
        
        # Signal shutdown
        self._shutdown_event.set()
        
        # Stop heartbeat
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
        
        # Perform module-specific cleanup
        await self._on_disconnect()
        
        self._set_state(ModuleState.DISCONNECTED)
        self.logger.info(f"Module {self.module_info.module_id} disconnected")
    
    async def activate(self) -> bool:
        """
        Activate module for processing.
        
        Returns:
            True if activation successful, False otherwise
        """
        if self.state != ModuleState.CONNECTED:
            self.logger.warning(f"Cannot activate module {self.module_info.module_id} in state {self.state}")
            return False
        
        try:
            await self._on_activate()
            self._set_state(ModuleState.ACTIVE)
            self.logger.info(f"Module {self.module_info.module_id} activated")
            return True
        except Exception as e:
            self.logger.error(f"Failed to activate module {self.module_info.module_id}: {e}")
            return False
    
    async def suspend(self) -> bool:
        """
        Suspend module processing.
        
        Returns:
            True if suspension successful, False otherwise
        """
        if self.state != ModuleState.ACTIVE:
            self.logger.warning(f"Cannot suspend module {self.module_info.module_id} in state {self.state}")
            return False
        
        try:
            await self._on_suspend()
            self._set_state(ModuleState.SUSPENDED)
            self.logger.info(f"Module {self.module_info.module_id} suspended")
            return True
        except Exception as e:
            self.logger.error(f"Failed to suspend module {self.module_info.module_id}: {e}")
            return False
    
    async def configure(self, configuration: Dict[str, Any]) -> bool:
        """
        Update module configuration.
        
        Args:
            configuration: New configuration parameters
            
        Returns:
            True if configuration successful, False otherwise
        """
        try:
            # Validate configuration against schema
            if not self._validate_configuration(configuration):
                return False
            
            old_config = self.configuration.copy()
            self.configuration.update(configuration)
            
            # Apply configuration
            await self._on_configure(configuration)
            
            self.logger.info(f"Module {self.module_info.module_id} configured successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to configure module {self.module_info.module_id}: {e}")
            # Rollback configuration
            self.configuration = old_config
            return False
    
    async def subscribe(self, stream_name: str) -> bool:
        """
        Subscribe to a data stream.
        
        Args:
            stream_name: Name of the stream to subscribe to
            
        Returns:
            True if subscription successful, False otherwise
        """
        try:
            if hasattr(self, 'system_interface'):
                success = await self.system_interface.subscribe_stream(self.connection_id, stream_name)
                if success:
                    self.subscriptions.add(stream_name)
                    self.logger.info(f"Module {self.module_info.module_id} subscribed to {stream_name}")
                return success
            return False
        except Exception as e:
            self.logger.error(f"Failed to subscribe to {stream_name}: {e}")
            return False
    
    async def unsubscribe(self, stream_name: str) -> bool:
        """
        Unsubscribe from a data stream.
        
        Args:
            stream_name: Name of the stream to unsubscribe from
            
        Returns:
            True if unsubscription successful, False otherwise
        """
        try:
            if hasattr(self, 'system_interface'):
                success = await self.system_interface.unsubscribe_stream(self.connection_id, stream_name)
                if success:
                    self.subscriptions.discard(stream_name)
                    self.logger.info(f"Module {self.module_info.module_id} unsubscribed from {stream_name}")
                return success
            return False
        except Exception as e:
            self.logger.error(f"Failed to unsubscribe from {stream_name}: {e}")
            return False
    
    async def process_message(self, message: Dict[str, Any]) -> Any:
        """
        Process incoming message from the system.
        
        Args:
            message: Message to process
            
        Returns:
            Processing result
        """
        start_time = time.time()
        
        try:
            message_type = message.get("type", "unknown")
            
            # Update performance metrics
            self.performance_metrics["messages_processed"] += 1
            self.performance_metrics["last_activity"] = start_time
            
            # Route to appropriate handler
            if message_type in self._message_handlers:
                result = await self._message_handlers[message_type](message)
            else:
                result = await self._on_message(message)
            
            # Update processing time
            processing_time = time.time() - start_time
            self.performance_metrics["processing_time_total"] += processing_time
            
            return result
            
        except Exception as e:
            self.performance_metrics["errors"] += 1
            self.logger.error(f"Error processing message in {self.module_info.module_id}: {e}")
            raise
    
    def register_message_handler(self, message_type: str, handler: Callable[[Dict[str, Any]], Any]) -> None:
        """Register handler for specific message type."""
        self._message_handlers[message_type] = handler
    
    def add_connection_callback(self, callback: Callable[[ModuleState], None]) -> None:
        """Add callback for state changes."""
        self._connection_callbacks.append(callback)
    
    def get_status(self) -> Dict[str, Any]:
        """Get current module status and metrics."""
        avg_processing_time = 0.0
        if self.performance_metrics["messages_processed"] > 0:
            avg_processing_time = (
                self.performance_metrics["processing_time_total"] / 
                self.performance_metrics["messages_processed"]
            )
        
        return {
            "connection_id": self.connection_id,
            "module_info": self.module_info.to_dict(),
            "state": self.state.value,
            "configuration": self.configuration,
            "subscriptions": list(self.subscriptions),
            "performance_metrics": {
                **self.performance_metrics,
                "average_processing_time": avg_processing_time,
            },
        }
    
    # Abstract methods to be implemented by subclasses
    @abstractmethod
    async def _on_connect(self) -> None:
        """Called when module connects to system."""
        pass
    
    @abstractmethod
    async def _on_disconnect(self) -> None:
        """Called when module disconnects from system."""
        pass
    
    @abstractmethod
    async def _on_activate(self) -> None:
        """Called when module is activated."""
        pass
    
    @abstractmethod
    async def _on_suspend(self) -> None:
        """Called when module is suspended."""
        pass
    
    @abstractmethod
    async def _on_configure(self, configuration: Dict[str, Any]) -> None:
        """Called when module configuration is updated."""
        pass
    
    @abstractmethod
    async def _on_message(self, message: Dict[str, Any]) -> Any:
        """Called to process incoming messages."""
        pass
    
    # Private methods
    async def _heartbeat_loop(self) -> None:
        """Send periodic heartbeat to system."""
        while not self._shutdown_event.is_set():
            try:
                if hasattr(self, 'system_interface'):
                    await self.system_interface.send_heartbeat(self.connection_id)
                await asyncio.sleep(30)  # Heartbeat every 30 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Heartbeat error for {self.module_info.module_id}: {e}")
    
    def _set_state(self, new_state: ModuleState) -> None:
        """Set module state and notify callbacks."""
        old_state = self.state
        self.state = new_state
        
        # Notify callbacks
        for callback in self._connection_callbacks:
            try:
                callback(new_state)
            except Exception as e:
                self.logger.error(f"Connection callback error: {e}")
    
    def _validate_configuration(self, configuration: Dict[str, Any]) -> bool:
        """
        Validate configuration against schema.
        
        Args:
            configuration: Configuration to validate
            
        Returns:
            True if valid, False otherwise
        """
        # Basic validation - can be extended with JSON schema validation
        schema = self.module_info.configuration_schema
        
        if not schema:
            return True  # No schema means any configuration is valid
        
        # Check required fields
        required_fields = schema.get("required", [])
        for field in required_fields:
            if field not in configuration:
                self.logger.error(f"Missing required configuration field: {field}")
                return False
        
        # Check field types
        properties = schema.get("properties", {})
        for field, value in configuration.items():
            if field in properties:
                expected_type = properties[field].get("type")
                if expected_type and not self._check_type(value, expected_type):
                    self.logger.error(f"Invalid type for field {field}: expected {expected_type}")
                    return False
        
        return True
    
    def _check_type(self, value: Any, expected_type: str) -> bool:
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


class SystemInterface(ABC):
    """Interface for modules to communicate with the core system."""
    
    @abstractmethod
    async def subscribe_stream(self, connection_id: str, stream_name: str) -> bool:
        """Subscribe to a data stream."""
        pass
    
    @abstractmethod
    async def unsubscribe_stream(self, connection_id: str, stream_name: str) -> bool:
        """Unsubscribe from a data stream."""
        pass
    
    @abstractmethod
    async def send_heartbeat(self, connection_id: str) -> None:
        """Send heartbeat to system."""
        pass
    
    @abstractmethod
    async def send_message(self, message: Dict[str, Any]) -> None:
        """Send message to system."""
        pass