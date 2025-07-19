"""
Stream Processor Base Class

Provides foundation for multi-stream data processing with temporal synchronization.
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Callable, AsyncIterable, Union
import collections
import threading
import uuid


class StreamType(Enum):
    """Types of data streams."""
    AUDIO = "audio"
    VIDEO = "video"
    TEXT = "text"
    SENSOR = "sensor"
    CONTROL = "control"
    METADATA = "metadata"


class StreamQuality(Enum):
    """Stream quality levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    ULTRA = "ultra"


@dataclass
class StreamData:
    """Container for stream data with metadata."""
    stream_id: str
    stream_type: StreamType
    timestamp: float
    sequence_number: int
    data: Any
    metadata: Dict[str, Any] = field(default_factory=dict)
    quality: StreamQuality = StreamQuality.MEDIUM
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "stream_id": self.stream_id,
            "stream_type": self.stream_type.value,
            "timestamp": self.timestamp,
            "sequence_number": self.sequence_number,
            "data": self.data,
            "metadata": self.metadata,
            "quality": self.quality.value,
        }


@dataclass
class StreamInfo:
    """Information about a data stream."""
    stream_id: str
    stream_type: StreamType
    source: str
    format: str
    sample_rate: Optional[float] = None
    resolution: Optional[tuple] = None
    channels: Optional[int] = None
    quality: StreamQuality = StreamQuality.MEDIUM
    active: bool = True
    created_at: float = field(default_factory=time.time)
    last_data_time: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "stream_id": self.stream_id,
            "stream_type": self.stream_type.value,
            "source": self.source,
            "format": self.format,
            "sample_rate": self.sample_rate,
            "resolution": self.resolution,
            "channels": self.channels,
            "quality": self.quality.value,
            "active": self.active,
            "created_at": self.created_at,
            "last_data_time": self.last_data_time,
        }


class StreamBuffer:
    """Thread-safe buffer for stream data with temporal ordering."""
    
    def __init__(self, max_size: int = 1000, max_age_seconds: float = 60.0):
        """
        Initialize stream buffer.
        
        Args:
            max_size: Maximum number of items to store
            max_age_seconds: Maximum age of items before cleanup
        """
        self.max_size = max_size
        self.max_age_seconds = max_age_seconds
        self._buffer = collections.deque(maxlen=max_size)
        self._lock = threading.RLock()
        self._sequence_counter = 0
    
    def add(self, data: StreamData) -> None:
        """Add data to buffer."""
        with self._lock:
            # Set sequence number if not provided
            if data.sequence_number == 0:
                self._sequence_counter += 1
                data.sequence_number = self._sequence_counter
            
            self._buffer.append(data)
            self._cleanup_old_data()
    
    def get_latest(self, count: int = 1) -> List[StreamData]:
        """Get latest N items from buffer."""
        with self._lock:
            if count == 1:
                return [self._buffer[-1]] if self._buffer else []
            else:
                return list(self._buffer)[-count:] if len(self._buffer) >= count else list(self._buffer)
    
    def get_by_time_range(self, start_time: float, end_time: float) -> List[StreamData]:
        """Get items within time range."""
        with self._lock:
            return [
                item for item in self._buffer
                if start_time <= item.timestamp <= end_time
            ]
    
    def get_by_sequence_range(self, start_seq: int, end_seq: int) -> List[StreamData]:
        """Get items within sequence number range."""
        with self._lock:
            return [
                item for item in self._buffer
                if start_seq <= item.sequence_number <= end_seq
            ]
    
    def clear(self) -> None:
        """Clear all data from buffer."""
        with self._lock:
            self._buffer.clear()
    
    def size(self) -> int:
        """Get current buffer size."""
        with self._lock:
            return len(self._buffer)
    
    def _cleanup_old_data(self) -> None:
        """Remove old data from buffer."""
        current_time = time.time()
        cutoff_time = current_time - self.max_age_seconds
        
        # Remove old items from the left
        while self._buffer and self._buffer[0].timestamp < cutoff_time:
            self._buffer.popleft()


class StreamProcessor(ABC):
    """
    Base class for multi-stream data processing.
    
    Provides:
    - Multi-stream input handling
    - Temporal synchronization
    - Quality adaptation
    - Buffer management
    - Performance monitoring
    """
    
    def __init__(self, 
                 processor_id: str,
                 buffer_size: int = 1000,
                 sync_window_ms: float = 100.0,
                 quality_adaptation: bool = True):
        """
        Initialize stream processor.
        
        Args:
            processor_id: Unique identifier for this processor
            buffer_size: Size of stream buffers
            sync_window_ms: Synchronization window in milliseconds
            quality_adaptation: Enable automatic quality adaptation
        """
        self.processor_id = processor_id
        self.buffer_size = buffer_size
        self.sync_window_ms = sync_window_ms
        self.quality_adaptation = quality_adaptation
        
        # Stream management
        self.input_streams: Dict[str, StreamInfo] = {}
        self.output_streams: Dict[str, StreamInfo] = {}
        self.stream_buffers: Dict[str, StreamBuffer] = {}
        
        # Processing state
        self._processing_tasks: List[asyncio.Task] = []
        self._shutdown_event = asyncio.Event()
        self._lock = threading.RLock()
        
        # Performance metrics
        self.metrics = {
            "streams_processed": 0,
            "data_items_processed": 0,
            "processing_time_total": 0.0,
            "sync_errors": 0,
            "quality_adaptations": 0,
            "buffer_overflows": 0,
        }
        
        # Callbacks
        self.data_callbacks: List[Callable[[StreamData], None]] = []
        self.error_callbacks: List[Callable[[Exception], None]] = []
        
        # Logging
        self.logger = logging.getLogger(f"leonidas.stream.{processor_id}")
    
    async def start(self) -> None:
        """Start stream processing."""
        self.logger.info(f"Starting stream processor {self.processor_id}")
        
        try:
            # Initialize processor-specific resources
            await self._initialize()
            
            # Start processing tasks
            self._processing_tasks = [
                asyncio.create_task(self._processing_loop()),
                asyncio.create_task(self._sync_loop()),
                asyncio.create_task(self._quality_adaptation_loop()),
            ]
            
            self.logger.info(f"Stream processor {self.processor_id} started")
            
        except Exception as e:
            self.logger.error(f"Failed to start stream processor {self.processor_id}: {e}")
            raise
    
    async def stop(self) -> None:
        """Stop stream processing."""
        self.logger.info(f"Stopping stream processor {self.processor_id}")
        
        # Signal shutdown
        self._shutdown_event.set()
        
        # Cancel processing tasks
        for task in self._processing_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        if self._processing_tasks:
            await asyncio.gather(*self._processing_tasks, return_exceptions=True)
        
        # Cleanup resources
        await self._cleanup()
        
        self.logger.info(f"Stream processor {self.processor_id} stopped")
    
    def add_input_stream(self, stream_info: StreamInfo) -> bool:
        """
        Add input stream.
        
        Args:
            stream_info: Information about the stream
            
        Returns:
            True if stream added successfully, False otherwise
        """
        try:
            with self._lock:
                if stream_info.stream_id in self.input_streams:
                    self.logger.warning(f"Stream {stream_info.stream_id} already exists")
                    return False
                
                self.input_streams[stream_info.stream_id] = stream_info
                self.stream_buffers[stream_info.stream_id] = StreamBuffer(
                    max_size=self.buffer_size
                )
                
                self.logger.info(f"Added input stream {stream_info.stream_id}")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to add input stream {stream_info.stream_id}: {e}")
            return False
    
    def remove_input_stream(self, stream_id: str) -> bool:
        """
        Remove input stream.
        
        Args:
            stream_id: ID of stream to remove
            
        Returns:
            True if stream removed successfully, False otherwise
        """
        try:
            with self._lock:
                if stream_id not in self.input_streams:
                    self.logger.warning(f"Stream {stream_id} not found")
                    return False
                
                del self.input_streams[stream_id]
                if stream_id in self.stream_buffers:
                    del self.stream_buffers[stream_id]
                
                self.logger.info(f"Removed input stream {stream_id}")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to remove input stream {stream_id}: {e}")
            return False
    
    async def process_data(self, stream_data: StreamData) -> None:
        """
        Process incoming stream data.
        
        Args:
            stream_data: Data to process
        """
        try:
            # Add to buffer
            if stream_data.stream_id in self.stream_buffers:
                self.stream_buffers[stream_data.stream_id].add(stream_data)
                
                # Update stream info
                if stream_data.stream_id in self.input_streams:
                    self.input_streams[stream_data.stream_id].last_data_time = stream_data.timestamp
                
                # Update metrics
                self.metrics["data_items_processed"] += 1
                
                # Notify callbacks
                for callback in self.data_callbacks:
                    try:
                        callback(stream_data)
                    except Exception as e:
                        self.logger.error(f"Data callback error: {e}")
            
        except Exception as e:
            self.logger.error(f"Error processing data for stream {stream_data.stream_id}: {e}")
            for callback in self.error_callbacks:
                try:
                    callback(e)
                except Exception as callback_error:
                    self.logger.error(f"Error callback error: {callback_error}")
    
    def get_synchronized_data(self, timestamp: float, window_ms: float = None) -> Dict[str, StreamData]:
        """
        Get synchronized data from all streams at given timestamp.
        
        Args:
            timestamp: Target timestamp
            window_ms: Synchronization window (uses default if None)
            
        Returns:
            Dictionary mapping stream_id to closest data
        """
        if window_ms is None:
            window_ms = self.sync_window_ms
        
        window_seconds = window_ms / 1000.0
        start_time = timestamp - window_seconds / 2
        end_time = timestamp + window_seconds / 2
        
        synchronized_data = {}
        
        with self._lock:
            for stream_id, buffer in self.stream_buffers.items():
                # Get data within time window
                candidates = buffer.get_by_time_range(start_time, end_time)
                
                if candidates:
                    # Find closest to target timestamp
                    closest = min(candidates, key=lambda x: abs(x.timestamp - timestamp))
                    synchronized_data[stream_id] = closest
        
        return synchronized_data
    
    def get_stream_info(self, stream_id: str) -> Optional[StreamInfo]:
        """Get information about a stream."""
        with self._lock:
            return self.input_streams.get(stream_id) or self.output_streams.get(stream_id)
    
    def get_all_streams(self) -> Dict[str, StreamInfo]:
        """Get information about all streams."""
        with self._lock:
            return {**self.input_streams, **self.output_streams}
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get processing metrics."""
        avg_processing_time = 0.0
        if self.metrics["streams_processed"] > 0:
            avg_processing_time = (
                self.metrics["processing_time_total"] / 
                self.metrics["streams_processed"]
            )
        
        return {
            **self.metrics,
            "average_processing_time": avg_processing_time,
            "active_streams": len(self.input_streams),
            "buffer_sizes": {
                stream_id: buffer.size() 
                for stream_id, buffer in self.stream_buffers.items()
            },
        }
    
    def add_data_callback(self, callback: Callable[[StreamData], None]) -> None:
        """Add callback for processed data."""
        self.data_callbacks.append(callback)
    
    def add_error_callback(self, callback: Callable[[Exception], None]) -> None:
        """Add callback for errors."""
        self.error_callbacks.append(callback)
    
    # Abstract methods to be implemented by subclasses
    @abstractmethod
    async def _initialize(self) -> None:
        """Initialize processor-specific resources."""
        pass
    
    @abstractmethod
    async def _cleanup(self) -> None:
        """Cleanup processor-specific resources."""
        pass
    
    @abstractmethod
    async def _process_streams(self, synchronized_data: Dict[str, StreamData]) -> Optional[StreamData]:
        """
        Process synchronized stream data.
        
        Args:
            synchronized_data: Dictionary of synchronized data from all streams
            
        Returns:
            Processed output data or None
        """
        pass
    
    # Private methods
    async def _processing_loop(self) -> None:
        """Main processing loop."""
        while not self._shutdown_event.is_set():
            try:
                start_time = time.time()
                
                # Get current timestamp for synchronization
                current_time = time.time()
                
                # Get synchronized data
                synchronized_data = self.get_synchronized_data(current_time)
                
                if synchronized_data:
                    # Process data
                    result = await self._process_streams(synchronized_data)
                    
                    if result:
                        # Handle output
                        await self._handle_output(result)
                    
                    # Update metrics
                    processing_time = time.time() - start_time
                    self.metrics["streams_processed"] += 1
                    self.metrics["processing_time_total"] += processing_time
                
                # Small delay to prevent busy waiting
                await asyncio.sleep(0.01)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Processing loop error: {e}")
                await asyncio.sleep(0.1)
    
    async def _sync_loop(self) -> None:
        """Synchronization monitoring loop."""
        while not self._shutdown_event.is_set():
            try:
                # Check for synchronization issues
                await self._check_synchronization()
                await asyncio.sleep(1.0)  # Check every second
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Sync loop error: {e}")
                await asyncio.sleep(1.0)
    
    async def _quality_adaptation_loop(self) -> None:
        """Quality adaptation loop."""
        if not self.quality_adaptation:
            return
        
        while not self._shutdown_event.is_set():
            try:
                # Adapt quality based on performance
                await self._adapt_quality()
                await asyncio.sleep(5.0)  # Adapt every 5 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Quality adaptation error: {e}")
                await asyncio.sleep(5.0)
    
    async def _check_synchronization(self) -> None:
        """Check for synchronization issues."""
        current_time = time.time()
        
        with self._lock:
            for stream_id, stream_info in self.input_streams.items():
                if stream_info.last_data_time:
                    time_since_data = current_time - stream_info.last_data_time
                    
                    # Check for stale streams
                    if time_since_data > 5.0:  # 5 seconds without data
                        self.logger.warning(f"Stream {stream_id} appears stale (no data for {time_since_data:.1f}s)")
                        self.metrics["sync_errors"] += 1
    
    async def _adapt_quality(self) -> None:
        """Adapt stream quality based on performance."""
        # Simple quality adaptation based on buffer sizes
        with self._lock:
            for stream_id, buffer in self.stream_buffers.items():
                buffer_size = buffer.size()
                
                if stream_id in self.input_streams:
                    stream_info = self.input_streams[stream_id]
                    
                    # Reduce quality if buffer is getting full
                    if buffer_size > self.buffer_size * 0.8:
                        if stream_info.quality != StreamQuality.LOW:
                            stream_info.quality = StreamQuality.LOW
                            self.metrics["quality_adaptations"] += 1
                            self.logger.info(f"Reduced quality for stream {stream_id} due to buffer pressure")
                    
                    # Increase quality if buffer is low and performance is good
                    elif buffer_size < self.buffer_size * 0.2:
                        if stream_info.quality == StreamQuality.LOW:
                            stream_info.quality = StreamQuality.MEDIUM
                            self.metrics["quality_adaptations"] += 1
                            self.logger.info(f"Increased quality for stream {stream_id}")
    
    async def _handle_output(self, output_data: StreamData) -> None:
        """Handle processed output data."""
        # Default implementation - can be overridden
        self.logger.debug(f"Processed output: {output_data.stream_id}")
        
        # Notify callbacks
        for callback in self.data_callbacks:
            try:
                callback(output_data)
            except Exception as e:
                self.logger.error(f"Output callback error: {e}")