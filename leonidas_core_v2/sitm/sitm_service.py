"""
SITM (Stream Ingestion and Transmission Multimodal) Service

Central hub for managing multi-modal data streams with synchronization and distribution.
"""

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Callable, AsyncIterable
import threading
import json
import websockets
import websockets.server
from websockets.exceptions import ConnectionClosed

from ..core.resilient_component import ResilientComponent
from ..core.stream_processor import StreamProcessor, StreamData, StreamInfo, StreamType, StreamQuality


class DeviceType(Enum):
    """Types of devices that can connect to SITM."""
    CAMERA = "camera"
    MICROPHONE = "microphone"
    SENSOR = "sensor"
    DISPLAY = "display"
    SPEAKER = "speaker"
    ACTUATOR = "actuator"
    GENERIC = "generic"


@dataclass
class DeviceInfo:
    """Information about a connected device."""
    device_id: str
    device_type: DeviceType
    name: str
    capabilities: List[str]
    streams: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    connected_at: float = field(default_factory=time.time)
    last_heartbeat: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "device_id": self.device_id,
            "device_type": self.device_type.value,
            "name": self.name,
            "capabilities": self.capabilities,
            "streams": self.streams,
            "metadata": self.metadata,
            "connected_at": self.connected_at,
            "last_heartbeat": self.last_heartbeat,
        }


@dataclass
class SubscriptionInfo:
    """Information about a stream subscription."""
    subscription_id: str
    subscriber_id: str
    stream_id: str
    filters: Dict[str, Any] = field(default_factory=dict)
    quality: StreamQuality = StreamQuality.MEDIUM
    created_at: float = field(default_factory=time.time)
    last_data_sent: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "subscription_id": self.subscription_id,
            "subscriber_id": self.subscriber_id,
            "stream_id": self.stream_id,
            "filters": self.filters,
            "quality": self.quality.value,
            "created_at": self.created_at,
            "last_data_sent": self.last_data_sent,
        }


class DeviceDiscoveryManager:
    """Manages automatic device discovery."""
    
    def __init__(self):
        self.discovered_devices: Dict[str, DeviceInfo] = {}
        self.discovery_callbacks: List[Callable[[DeviceInfo], None]] = []
        self._discovery_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()
        self.logger = logging.getLogger("leonidas.sitm.discovery")
    
    async def start_discovery(self) -> None:
        """Start device discovery."""
        self.logger.info("Starting device discovery")
        self._discovery_task = asyncio.create_task(self._discovery_loop())
    
    async def stop_discovery(self) -> None:
        """Stop device discovery."""
        self.logger.info("Stopping device discovery")
        self._shutdown_event.set()
        
        if self._discovery_task:
            self._discovery_task.cancel()
            try:
                await self._discovery_task
            except asyncio.CancelledError:
                pass
    
    def add_discovery_callback(self, callback: Callable[[DeviceInfo], None]) -> None:
        """Add callback for device discovery events."""
        self.discovery_callbacks.append(callback)
    
    async def _discovery_loop(self) -> None:
        """Main device discovery loop."""
        while not self._shutdown_event.is_set():
            try:
                # Perform discovery (placeholder implementation)
                await self._perform_discovery()
                await asyncio.sleep(10.0)  # Discovery every 10 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Discovery loop error: {e}")
                await asyncio.sleep(10.0)
    
    async def _perform_discovery(self) -> None:
        """Perform actual device discovery."""
        # Placeholder implementation
        # In a real implementation, this would use UPnP, mDNS, network scanning, etc.
        pass


class MultiStreamIngestor(StreamProcessor):
    """Handles ingestion of multiple concurrent streams."""
    
    def __init__(self, processor_id: str = "multi_stream_ingestor"):
        super().__init__(processor_id)
        self.format_converters: Dict[str, Callable[[Any], Any]] = {}
        self.quality_adapters: Dict[StreamQuality, Callable[[Any], Any]] = {}
    
    async def _initialize(self) -> None:
        """Initialize stream ingestor."""
        self.logger.info("Initializing multi-stream ingestor")
        
        # Initialize format converters
        self._setup_format_converters()
        
        # Initialize quality adapters
        self._setup_quality_adapters()
    
    async def _cleanup(self) -> None:
        """Cleanup stream ingestor."""
        self.logger.info("Cleaning up multi-stream ingestor")
    
    async def _process_streams(self, synchronized_data: Dict[str, StreamData]) -> Optional[StreamData]:
        """Process synchronized stream data."""
        if not synchronized_data:
            return None
        
        # Simple pass-through for now
        # In a real implementation, this would perform fusion, normalization, etc.
        return list(synchronized_data.values())[0]
    
    def _setup_format_converters(self) -> None:
        """Setup format conversion functions."""
        # Placeholder implementations
        self.format_converters = {
            "audio/pcm": self._convert_audio_pcm,
            "video/h264": self._convert_video_h264,
            "application/json": self._convert_json,
        }
    
    def _setup_quality_adapters(self) -> None:
        """Setup quality adaptation functions."""
        # Placeholder implementations
        self.quality_adapters = {
            StreamQuality.LOW: self._adapt_quality_low,
            StreamQuality.MEDIUM: self._adapt_quality_medium,
            StreamQuality.HIGH: self._adapt_quality_high,
        }
    
    def _convert_audio_pcm(self, data: Any) -> Any:
        """Convert audio PCM data."""
        return data  # Placeholder
    
    def _convert_video_h264(self, data: Any) -> Any:
        """Convert H.264 video data."""
        return data  # Placeholder
    
    def _convert_json(self, data: Any) -> Any:
        """Convert JSON data."""
        return data  # Placeholder
    
    def _adapt_quality_low(self, data: Any) -> Any:
        """Adapt data for low quality."""
        return data  # Placeholder
    
    def _adapt_quality_medium(self, data: Any) -> Any:
        """Adapt data for medium quality."""
        return data  # Placeholder
    
    def _adapt_quality_high(self, data: Any) -> Any:
        """Adapt data for high quality."""
        return data  # Placeholder


class TemporalSynchronizer:
    """Manages temporal synchronization across streams."""
    
    def __init__(self, reference_clock_source: str = "system"):
        self.reference_clock_source = reference_clock_source
        self.clock_offsets: Dict[str, float] = {}
        self.sync_quality_metrics: Dict[str, float] = {}
        self.logger = logging.getLogger("leonidas.sitm.sync")
    
    def get_synchronized_timestamp(self, source_id: str, original_timestamp: float) -> float:
        """Get synchronized timestamp for a source."""
        offset = self.clock_offsets.get(source_id, 0.0)
        return original_timestamp + offset
    
    def update_clock_offset(self, source_id: str, offset: float) -> None:
        """Update clock offset for a source."""
        self.clock_offsets[source_id] = offset
        self.logger.debug(f"Updated clock offset for {source_id}: {offset:.3f}s")
    
    def calculate_sync_quality(self, source_id: str) -> float:
        """Calculate synchronization quality for a source."""
        # Placeholder implementation
        return self.sync_quality_metrics.get(source_id, 1.0)


class StreamDistributor:
    """Distributes streams to subscribers."""
    
    def __init__(self):
        self.subscriptions: Dict[str, SubscriptionInfo] = {}
        self.subscriber_connections: Dict[str, websockets.WebSocketServerProtocol] = {}
        self.distribution_metrics: Dict[str, Dict[str, Any]] = {}
        self.logger = logging.getLogger("leonidas.sitm.distributor")
    
    def add_subscription(self, subscription: SubscriptionInfo) -> bool:
        """Add stream subscription."""
        try:
            self.subscriptions[subscription.subscription_id] = subscription
            self.logger.info(f"Added subscription {subscription.subscription_id} for stream {subscription.stream_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to add subscription: {e}")
            return False
    
    def remove_subscription(self, subscription_id: str) -> bool:
        """Remove stream subscription."""
        try:
            if subscription_id in self.subscriptions:
                del self.subscriptions[subscription_id]
                self.logger.info(f"Removed subscription {subscription_id}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to remove subscription: {e}")
            return False
    
    async def distribute_data(self, stream_data: StreamData) -> None:
        """Distribute stream data to subscribers."""
        relevant_subscriptions = [
            sub for sub in self.subscriptions.values()
            if sub.stream_id == stream_data.stream_id
        ]
        
        for subscription in relevant_subscriptions:
            try:
                await self._send_to_subscriber(subscription, stream_data)
            except Exception as e:
                self.logger.error(f"Failed to send data to subscriber {subscription.subscriber_id}: {e}")
    
    async def _send_to_subscriber(self, subscription: SubscriptionInfo, stream_data: StreamData) -> None:
        """Send data to a specific subscriber."""
        if subscription.subscriber_id not in self.subscriber_connections:
            return
        
        connection = self.subscriber_connections[subscription.subscriber_id]
        
        try:
            # Apply filters and quality adaptation
            filtered_data = self._apply_filters(stream_data, subscription.filters)
            adapted_data = self._adapt_quality(filtered_data, subscription.quality)
            
            # Send data
            message = {
                "type": "stream_data",
                "subscription_id": subscription.subscription_id,
                "data": adapted_data.to_dict(),
            }
            
            await connection.send(json.dumps(message))
            subscription.last_data_sent = time.time()
            
        except ConnectionClosed:
            # Remove disconnected subscriber
            del self.subscriber_connections[subscription.subscriber_id]
        except Exception as e:
            self.logger.error(f"Error sending to subscriber {subscription.subscriber_id}: {e}")
    
    def _apply_filters(self, stream_data: StreamData, filters: Dict[str, Any]) -> StreamData:
        """Apply filters to stream data."""
        # Placeholder implementation
        return stream_data
    
    def _adapt_quality(self, stream_data: StreamData, quality: StreamQuality) -> StreamData:
        """Adapt stream data quality."""
        # Placeholder implementation
        adapted_data = stream_data
        adapted_data.quality = quality
        return adapted_data


class SITMService(ResilientComponent):
    """
    SITM (Stream Ingestion and Transmission Multimodal) Service.
    
    Central hub for managing multi-modal data streams with:
    - Automatic device discovery
    - Multi-stream ingestion and synchronization
    - Format normalization
    - Stream distribution to subscribers
    - WebSocket API for hot-swappable modules
    """
    
    def __init__(self, 
                 component_id: str = "sitm_service",
                 websocket_host: str = "localhost",
                 websocket_port: int = 8765):
        super().__init__(component_id)
        
        self.websocket_host = websocket_host
        self.websocket_port = websocket_port
        
        # Core components
        self.device_discovery = DeviceDiscoveryManager()
        self.stream_ingestor = MultiStreamIngestor()
        self.temporal_sync = TemporalSynchronizer()
        self.stream_distributor = StreamDistributor()
        
        # State management
        self.connected_devices: Dict[str, DeviceInfo] = {}
        self.active_streams: Dict[str, StreamInfo] = {}
        self.websocket_server: Optional[websockets.WebSocketServer] = None
        
        # WebSocket connections
        self.client_connections: Dict[str, websockets.WebSocketServerProtocol] = {}
        
        # Metrics
        self.sitm_metrics = {
            "devices_connected": 0,
            "streams_active": 0,
            "data_processed": 0,
            "subscriptions_active": 0,
        }
    
    async def _initialize(self) -> None:
        """Initialize SITM service."""
        self.logger.info("Initializing SITM service")
        
        # Initialize components
        await self.stream_ingestor.start()
        await self.device_discovery.start_discovery()
        
        # Setup device discovery callback
        self.device_discovery.add_discovery_callback(self._on_device_discovered)
        
        # Start WebSocket server
        await self._start_websocket_server()
        
        self.logger.info("SITM service initialized")
    
    async def _cleanup(self) -> None:
        """Cleanup SITM service."""
        self.logger.info("Cleaning up SITM service")
        
        # Stop WebSocket server
        if self.websocket_server:
            self.websocket_server.close()
            await self.websocket_server.wait_closed()
        
        # Stop components
        await self.device_discovery.stop_discovery()
        await self.stream_ingestor.stop()
        
        self.logger.info("SITM service cleaned up")
    
    async def _health_check(self) -> bool:
        """Perform SITM service health check."""
        try:
            # Check if WebSocket server is running
            if not self.websocket_server:
                return False
            
            # Check component health
            if not self.stream_ingestor:
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False
    
    async def _start_websocket_server(self) -> None:
        """Start WebSocket server for client connections."""
        self.logger.info(f"Starting WebSocket server on {self.websocket_host}:{self.websocket_port}")
        
        self.websocket_server = await websockets.serve(
            self._handle_websocket_connection,
            self.websocket_host,
            self.websocket_port
        )
        
        self.logger.info("WebSocket server started")
    
    async def _handle_websocket_connection(self, websocket: websockets.WebSocketServerProtocol, path: str) -> None:
        """Handle new WebSocket connection."""
        client_id = str(uuid.uuid4())
        self.client_connections[client_id] = websocket
        self.logger.info(f"New WebSocket connection: {client_id}")
        
        try:
            async for message in websocket:
                await self._handle_websocket_message(client_id, message)
        except ConnectionClosed:
            self.logger.info(f"WebSocket connection closed: {client_id}")
        except Exception as e:
            self.logger.error(f"WebSocket connection error for {client_id}: {e}")
        finally:
            # Cleanup connection
            if client_id in self.client_connections:
                del self.client_connections[client_id]
    
    async def _handle_websocket_message(self, client_id: str, message: str) -> None:
        """Handle WebSocket message from client."""
        try:
            data = json.loads(message)
            message_type = data.get("type")
            
            if message_type == "register_device":
                await self._handle_register_device(client_id, data)
            elif message_type == "stream_data":
                await self._handle_stream_data(client_id, data)
            elif message_type == "subscribe_stream":
                await self._handle_subscribe_stream(client_id, data)
            elif message_type == "unsubscribe_stream":
                await self._handle_unsubscribe_stream(client_id, data)
            elif message_type == "heartbeat":
                await self._handle_heartbeat(client_id, data)
            else:
                self.logger.warning(f"Unknown message type from {client_id}: {message_type}")
                
        except json.JSONDecodeError:
            self.logger.error(f"Invalid JSON from {client_id}: {message}")
        except Exception as e:
            self.logger.error(f"Error handling message from {client_id}: {e}")
    
    async def _handle_register_device(self, client_id: str, data: Dict[str, Any]) -> None:
        """Handle device registration."""
        try:
            device_info = DeviceInfo(
                device_id=data["device_id"],
                device_type=DeviceType(data["device_type"]),
                name=data["name"],
                capabilities=data.get("capabilities", []),
                metadata=data.get("metadata", {}),
            )
            
            self.connected_devices[device_info.device_id] = device_info
            self.sitm_metrics["devices_connected"] = len(self.connected_devices)
            
            # Send confirmation
            response = {
                "type": "device_registered",
                "device_id": device_info.device_id,
                "status": "success",
            }
            
            await self.client_connections[client_id].send(json.dumps(response))
            self.logger.info(f"Device registered: {device_info.device_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to register device: {e}")
            
            # Send error response
            response = {
                "type": "device_registered",
                "status": "error",
                "error": str(e),
            }
            
            await self.client_connections[client_id].send(json.dumps(response))
    
    async def _handle_stream_data(self, client_id: str, data: Dict[str, Any]) -> None:
        """Handle incoming stream data."""
        try:
            stream_data = StreamData(
                stream_id=data["stream_id"],
                stream_type=StreamType(data["stream_type"]),
                timestamp=data["timestamp"],
                sequence_number=data["sequence_number"],
                data=data["data"],
                metadata=data.get("metadata", {}),
                quality=StreamQuality(data.get("quality", "medium")),
            )
            
            # Synchronize timestamp
            sync_timestamp = self.temporal_sync.get_synchronized_timestamp(
                client_id, stream_data.timestamp
            )
            stream_data.timestamp = sync_timestamp
            
            # Process data
            await self.stream_ingestor.process_data(stream_data)
            
            # Distribute to subscribers
            await self.stream_distributor.distribute_data(stream_data)
            
            self.sitm_metrics["data_processed"] += 1
            
        except Exception as e:
            self.logger.error(f"Failed to handle stream data: {e}")
    
    async def _handle_subscribe_stream(self, client_id: str, data: Dict[str, Any]) -> None:
        """Handle stream subscription request."""
        try:
            subscription = SubscriptionInfo(
                subscription_id=str(uuid.uuid4()),
                subscriber_id=client_id,
                stream_id=data["stream_id"],
                filters=data.get("filters", {}),
                quality=StreamQuality(data.get("quality", "medium")),
            )
            
            # Add subscription
            success = self.stream_distributor.add_subscription(subscription)
            
            if success:
                # Register subscriber connection
                self.stream_distributor.subscriber_connections[client_id] = self.client_connections[client_id]
                self.sitm_metrics["subscriptions_active"] = len(self.stream_distributor.subscriptions)
            
            # Send response
            response = {
                "type": "subscription_response",
                "subscription_id": subscription.subscription_id,
                "status": "success" if success else "error",
            }
            
            await self.client_connections[client_id].send(json.dumps(response))
            
        except Exception as e:
            self.logger.error(f"Failed to handle subscription: {e}")
    
    async def _handle_unsubscribe_stream(self, client_id: str, data: Dict[str, Any]) -> None:
        """Handle stream unsubscription request."""
        try:
            subscription_id = data["subscription_id"]
            success = self.stream_distributor.remove_subscription(subscription_id)
            
            if success:
                self.sitm_metrics["subscriptions_active"] = len(self.stream_distributor.subscriptions)
            
            # Send response
            response = {
                "type": "unsubscription_response",
                "subscription_id": subscription_id,
                "status": "success" if success else "error",
            }
            
            await self.client_connections[client_id].send(json.dumps(response))
            
        except Exception as e:
            self.logger.error(f"Failed to handle unsubscription: {e}")
    
    async def _handle_heartbeat(self, client_id: str, data: Dict[str, Any]) -> None:
        """Handle heartbeat from client."""
        device_id = data.get("device_id")
        if device_id and device_id in self.connected_devices:
            self.connected_devices[device_id].last_heartbeat = time.time()
    
    def _on_device_discovered(self, device_info: DeviceInfo) -> None:
        """Handle discovered device."""
        self.logger.info(f"Device discovered: {device_info.device_id}")
        # In a real implementation, this would initiate connection to the device
    
    def get_sitm_status(self) -> Dict[str, Any]:
        """Get SITM service status."""
        return {
            "component_status": self.get_health_status(),
            "sitm_metrics": self.sitm_metrics,
            "connected_devices": len(self.connected_devices),
            "active_streams": len(self.active_streams),
            "websocket_connections": len(self.client_connections),
            "stream_ingestor_metrics": self.stream_ingestor.get_metrics(),
        }