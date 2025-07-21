# Copyright 2025 Leonidas Core v2.0
# Licensed under the Apache License, Version 2.0

"""
Device Manager - Manages connected devices and hardware interfaces
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Type
from dataclasses import dataclass, field
from enum import Enum
import time
import json

from ..core.resilient_component import ResilientComponent


class DeviceType(Enum):
    """Types of devices that can be managed"""
    SENSOR = "sensor"
    ACTUATOR = "actuator"
    CAMERA = "camera"
    MICROPHONE = "microphone"
    SPEAKER = "speaker"
    DISPLAY = "display"
    ROBOT = "robot"
    CUSTOM = "custom"


class DeviceStatus(Enum):
    """Device connection and operational status"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ACTIVE = "active"
    ERROR = "error"
    MAINTENANCE = "maintenance"


@dataclass
class DeviceInfo:
    """Information about a managed device"""
    device_id: str
    device_type: DeviceType
    name: str
    manufacturer: str = ""
    model: str = ""
    version: str = ""
    capabilities: Dict[str, Any] = field(default_factory=dict)
    configuration: Dict[str, Any] = field(default_factory=dict)
    status: DeviceStatus = DeviceStatus.DISCONNECTED
    last_seen: float = field(default_factory=time.time)
    error_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


class DeviceInterface:
    """Base interface for device communication"""
    
    def __init__(self, device_info: DeviceInfo):
        self.device_info = device_info
        self.is_connected = False
    
    async def connect(self) -> bool:
        """Connect to the device"""
        raise NotImplementedError
    
    async def disconnect(self):
        """Disconnect from the device"""
        raise NotImplementedError
    
    async def read_data(self) -> Any:
        """Read data from the device"""
        raise NotImplementedError
    
    async def write_data(self, data: Any) -> bool:
        """Write data to the device"""
        raise NotImplementedError
    
    async def get_status(self) -> Dict[str, Any]:
        """Get device status"""
        raise NotImplementedError
    
    async def configure(self, config: Dict[str, Any]) -> bool:
        """Configure the device"""
        raise NotImplementedError


class DeviceManager(ResilientComponent):
    """
    Manages all connected devices and provides unified interface
    for device discovery, connection, and communication.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("device_manager")
        
        self.config = config or {}
        self.devices: Dict[str, DeviceInfo] = {}
        self.device_interfaces: Dict[str, DeviceInterface] = {}
        self.device_drivers: Dict[DeviceType, Type[DeviceInterface]] = {}
        
        # Discovery and monitoring
        self.discovery_enabled = self.config.get('discovery_enabled', True)
        self.monitoring_interval = self.config.get('monitoring_interval', 5.0)
        self.connection_timeout = self.config.get('connection_timeout', 10.0)
        
        # Tasks
        self.discovery_task: Optional[asyncio.Task] = None
        self.monitoring_task: Optional[asyncio.Task] = None
        
        # Event callbacks
        self.device_callbacks: Dict[str, List[callable]] = {
            'device_connected': [],
            'device_disconnected': [],
            'device_error': [],
            'device_data': []
        }
        
        logging.info("Device manager initialized")
    
    async def start(self):
        """Start device manager services"""
        try:
            # Load device configurations
            await self._load_device_configurations()
            
            # Start discovery and monitoring tasks
            if self.discovery_enabled:
                self.discovery_task = asyncio.create_task(self._discovery_loop())
            
            self.monitoring_task = asyncio.create_task(self._monitoring_loop())
            
            logging.info("Device manager started")
            
        except Exception as e:
            logging.error(f"Failed to start device manager: {e}")
            raise
    
    async def stop(self):
        """Stop device manager and disconnect all devices"""
        try:
            # Cancel tasks
            if self.discovery_task:
                self.discovery_task.cancel()
            if self.monitoring_task:
                self.monitoring_task.cancel()
            
            # Wait for tasks to complete
            await asyncio.gather(
                self.discovery_task, self.monitoring_task,
                return_exceptions=True
            )
            
            # Disconnect all devices
            await self._disconnect_all_devices()
            
            logging.info("Device manager stopped")
            
        except Exception as e:
            logging.error(f"Error stopping device manager: {e}")
    
    def register_device_driver(self, device_type: DeviceType, driver_class: Type[DeviceInterface]):
        """Register a device driver for a specific device type"""
        self.device_drivers[device_type] = driver_class
        logging.info(f"Registered driver for {device_type.value}")
    
    async def add_device(self, device_info: DeviceInfo) -> bool:
        """Add a device to management"""
        try:
            device_id = device_info.device_id
            
            if device_id in self.devices:
                logging.warning(f"Device {device_id} already exists")
                return False
            
            # Create device interface
            if device_info.device_type in self.device_drivers:
                driver_class = self.device_drivers[device_info.device_type]
                interface = driver_class(device_info)
                self.device_interfaces[device_id] = interface
            else:
                logging.warning(f"No driver available for device type {device_info.device_type}")
                return False
            
            # Add to managed devices
            self.devices[device_id] = device_info
            
            # Attempt connection
            if await self._connect_device(device_id):
                await self._notify_device_event('device_connected', device_info)
                logging.info(f"Device {device_id} added and connected")
                return True
            else:
                logging.warning(f"Device {device_id} added but connection failed")
                return False
                
        except Exception as e:
            logging.error(f"Error adding device {device_info.device_id}: {e}")
            return False
    
    async def remove_device(self, device_id: str) -> bool:
        """Remove a device from management"""
        try:
            if device_id not in self.devices:
                logging.warning(f"Device {device_id} not found")
                return False
            
            device_info = self.devices[device_id]
            
            # Disconnect device
            await self._disconnect_device(device_id)
            
            # Remove from management
            del self.devices[device_id]
            if device_id in self.device_interfaces:
                del self.device_interfaces[device_id]
            
            await self._notify_device_event('device_disconnected', device_info)
            logging.info(f"Device {device_id} removed")
            return True
            
        except Exception as e:
            logging.error(f"Error removing device {device_id}: {e}")
            return False
    
    async def connect_device(self, device_id: str) -> bool:
        """Connect to a specific device"""
        return await self._connect_device(device_id)
    
    async def disconnect_device(self, device_id: str) -> bool:
        """Disconnect from a specific device"""
        return await self._disconnect_device(device_id)
    
    async def read_device_data(self, device_id: str) -> Optional[Any]:
        """Read data from a device"""
        try:
            if device_id not in self.device_interfaces:
                logging.error(f"Device {device_id} not found")
                return None
            
            interface = self.device_interfaces[device_id]
            if not interface.is_connected:
                logging.warning(f"Device {device_id} not connected")
                return None
            
            data = await interface.read_data()
            
            # Notify data event
            device_info = self.devices[device_id]
            await self._notify_device_event('device_data', device_info, {'data': data})
            
            return data
            
        except Exception as e:
            logging.error(f"Error reading from device {device_id}: {e}")
            await self._handle_device_error(device_id, str(e))
            return None
    
    async def write_device_data(self, device_id: str, data: Any) -> bool:
        """Write data to a device"""
        try:
            if device_id not in self.device_interfaces:
                logging.error(f"Device {device_id} not found")
                return False
            
            interface = self.device_interfaces[device_id]
            if not interface.is_connected:
                logging.warning(f"Device {device_id} not connected")
                return False
            
            success = await interface.write_data(data)
            return success
            
        except Exception as e:
            logging.error(f"Error writing to device {device_id}: {e}")
            await self._handle_device_error(device_id, str(e))
            return False
    
    async def configure_device(self, device_id: str, config: Dict[str, Any]) -> bool:
        """Configure a device"""
        try:
            if device_id not in self.device_interfaces:
                logging.error(f"Device {device_id} not found")
                return False
            
            interface = self.device_interfaces[device_id]
            success = await interface.configure(config)
            
            if success:
                # Update device configuration
                self.devices[device_id].configuration.update(config)
                logging.info(f"Device {device_id} configured successfully")
            
            return success
            
        except Exception as e:
            logging.error(f"Error configuring device {device_id}: {e}")
            await self._handle_device_error(device_id, str(e))
            return False
    
    def get_device_info(self, device_id: str) -> Optional[DeviceInfo]:
        """Get information about a device"""
        return self.devices.get(device_id)
    
    def get_devices_by_type(self, device_type: DeviceType) -> List[DeviceInfo]:
        """Get all devices of a specific type"""
        return [info for info in self.devices.values() if info.device_type == device_type]
    
    def get_connected_devices(self) -> List[DeviceInfo]:
        """Get all connected devices"""
        return [info for info in self.devices.values() 
                if info.status in [DeviceStatus.CONNECTED, DeviceStatus.ACTIVE]]
    
    def get_all_devices(self) -> Dict[str, DeviceInfo]:
        """Get all managed devices"""
        return self.devices.copy()
    
    def register_callback(self, event_type: str, callback: callable):
        """Register callback for device events"""
        if event_type in self.device_callbacks:
            self.device_callbacks[event_type].append(callback)
        else:
            logging.warning(f"Unknown event type: {event_type}")
    
    async def _discovery_loop(self):
        """Device discovery loop"""
        while True:
            try:
                await self._discover_devices()
                await asyncio.sleep(self.monitoring_interval * 2)  # Discovery less frequent
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"Error in discovery loop: {e}")
                await asyncio.sleep(5.0)
    
    async def _monitoring_loop(self):
        """Device monitoring loop"""
        while True:
            try:
                await self._monitor_devices()
                await asyncio.sleep(self.monitoring_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(1.0)
    
    async def _discover_devices(self):
        """Discover new devices"""
        # This would implement actual device discovery
        # For now, just log that discovery is running
        logging.debug("Running device discovery")
    
    async def _monitor_devices(self):
        """Monitor connected devices"""
        for device_id, device_info in self.devices.items():
            try:
                if device_id in self.device_interfaces:
                    interface = self.device_interfaces[device_id]
                    
                    if interface.is_connected:
                        # Get device status
                        status = await interface.get_status()
                        
                        # Update device info
                        device_info.last_seen = time.time()
                        
                        # Check for errors
                        if 'error' in status and status['error']:
                            await self._handle_device_error(device_id, status['error'])
                    else:
                        # Try to reconnect
                        if device_info.status != DeviceStatus.ERROR:
                            await self._connect_device(device_id)
                            
            except Exception as e:
                logging.error(f"Error monitoring device {device_id}: {e}")
                await self._handle_device_error(device_id, str(e))
    
    async def _connect_device(self, device_id: str) -> bool:
        """Connect to a device"""
        try:
            if device_id not in self.device_interfaces:
                logging.error(f"No interface for device {device_id}")
                return False
            
            device_info = self.devices[device_id]
            interface = self.device_interfaces[device_id]
            
            device_info.status = DeviceStatus.CONNECTING
            
            # Attempt connection with timeout
            connected = await asyncio.wait_for(
                interface.connect(),
                timeout=self.connection_timeout
            )
            
            if connected:
                device_info.status = DeviceStatus.CONNECTED
                device_info.last_seen = time.time()
                device_info.error_count = 0
                logging.info(f"Device {device_id} connected")
                return True
            else:
                device_info.status = DeviceStatus.ERROR
                logging.error(f"Failed to connect to device {device_id}")
                return False
                
        except asyncio.TimeoutError:
            device_info.status = DeviceStatus.ERROR
            logging.error(f"Connection timeout for device {device_id}")
            return False
        except Exception as e:
            device_info.status = DeviceStatus.ERROR
            logging.error(f"Error connecting to device {device_id}: {e}")
            return False
    
    async def _disconnect_device(self, device_id: str) -> bool:
        """Disconnect from a device"""
        try:
            if device_id not in self.device_interfaces:
                return True
            
            device_info = self.devices[device_id]
            interface = self.device_interfaces[device_id]
            
            await interface.disconnect()
            device_info.status = DeviceStatus.DISCONNECTED
            
            logging.info(f"Device {device_id} disconnected")
            return True
            
        except Exception as e:
            logging.error(f"Error disconnecting device {device_id}: {e}")
            return False
    
    async def _disconnect_all_devices(self):
        """Disconnect all devices"""
        for device_id in list(self.devices.keys()):
            await self._disconnect_device(device_id)
    
    async def _handle_device_error(self, device_id: str, error_message: str):
        """Handle device error"""
        if device_id in self.devices:
            device_info = self.devices[device_id]
            device_info.error_count += 1
            device_info.status = DeviceStatus.ERROR
            
            await self._notify_device_event('device_error', device_info, {'error': error_message})
            
            # If too many errors, disconnect device
            if device_info.error_count > 5:
                logging.warning(f"Too many errors for device {device_id}, disconnecting")
                await self._disconnect_device(device_id)
    
    async def _notify_device_event(self, event_type: str, device_info: DeviceInfo, extra_data: Dict[str, Any] = None):
        """Notify callbacks of device events"""
        if event_type in self.device_callbacks:
            event_data = {
                'device_info': device_info,
                'timestamp': time.time()
            }
            if extra_data:
                event_data.update(extra_data)
            
            for callback in self.device_callbacks[event_type]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(event_data)
                    else:
                        callback(event_data)
                except Exception as e:
                    logging.error(f"Error in device callback: {e}")
    
    async def _load_device_configurations(self):
        """Load device configurations from file"""
        config_file = self.config.get('device_config_file', 'devices.json')
        
        try:
            with open(config_file, 'r') as f:
                device_configs = json.load(f)
            
            for device_config in device_configs:
                device_info = DeviceInfo(
                    device_id=device_config['device_id'],
                    device_type=DeviceType(device_config['device_type']),
                    name=device_config['name'],
                    manufacturer=device_config.get('manufacturer', ''),
                    model=device_config.get('model', ''),
                    version=device_config.get('version', ''),
                    capabilities=device_config.get('capabilities', {}),
                    configuration=device_config.get('configuration', {})
                )
                
                await self.add_device(device_info)
                
        except FileNotFoundError:
            logging.info(f"Device configuration file {config_file} not found")
        except Exception as e:
            logging.error(f"Error loading device configurations: {e}")