# Copyright 2025 Leonidas Core v2.0
# Licensed under the Apache License, Version 2.0

"""
Sensor Interface - Unified interface for sensor data acquisition
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import time
import numpy as np

from .device_manager import DeviceInterface, DeviceInfo, DeviceType
from ..core.stream_processor import StreamProcessor


class SensorType(Enum):
    """Types of sensors"""
    CAMERA = "camera"
    MICROPHONE = "microphone"
    LIDAR = "lidar"
    IMU = "imu"
    GPS = "gps"
    TEMPERATURE = "temperature"
    PRESSURE = "pressure"
    PROXIMITY = "proximity"
    FORCE = "force"
    CUSTOM = "custom"


@dataclass
class SensorReading:
    """Sensor reading data structure"""
    sensor_id: str
    sensor_type: SensorType
    timestamp: float
    data: Any
    metadata: Dict[str, Any] = field(default_factory=dict)
    quality: float = 1.0  # 0.0 to 1.0
    confidence: float = 1.0  # 0.0 to 1.0


@dataclass
class SensorConfiguration:
    """Sensor configuration parameters"""
    sampling_rate: float = 10.0  # Hz
    resolution: Optional[tuple] = None
    range_min: Optional[float] = None
    range_max: Optional[float] = None
    filters: List[str] = field(default_factory=list)
    calibration: Dict[str, Any] = field(default_factory=dict)
    custom_params: Dict[str, Any] = field(default_factory=dict)


class SensorInterface(DeviceInterface, StreamProcessor):
    """
    Base interface for sensor devices with streaming capabilities
    """
    
    def __init__(self, device_info: DeviceInfo, sensor_type: SensorType):
        DeviceInterface.__init__(self, device_info)
        StreamProcessor.__init__(self, f"sensor_{device_info.device_id}")
        
        self.sensor_type = sensor_type
        self.configuration = SensorConfiguration()
        self.is_streaming = False
        self.data_callbacks: List[Callable] = []
        
        # Data processing
        self.data_buffer = asyncio.Queue(maxsize=1000)
        self.processing_task: Optional[asyncio.Task] = None
        
        # Statistics
        self.stats = {
            'readings_count': 0,
            'errors_count': 0,
            'last_reading_time': 0,
            'average_quality': 0.0,
            'data_rate': 0.0
        }
    
    async def configure_sensor(self, config: SensorConfiguration) -> bool:
        """Configure sensor parameters"""
        try:
            self.configuration = config
            
            # Apply configuration to hardware
            success = await self._apply_hardware_configuration(config)
            
            if success:
                logging.info(f"Sensor {self.device_info.device_id} configured successfully")
            else:
                logging.error(f"Failed to configure sensor {self.device_info.device_id}")
            
            return success
            
        except Exception as e:
            logging.error(f"Error configuring sensor {self.device_info.device_id}: {e}")
            return False
    
    async def start_streaming(self) -> bool:
        """Start sensor data streaming"""
        if self.is_streaming:
            return True
        
        try:
            if not self.is_connected:
                if not await self.connect():
                    return False
            
            # Start hardware streaming
            if not await self._start_hardware_streaming():
                return False
            
            # Start processing task
            self.processing_task = asyncio.create_task(self._data_processing_loop())
            
            self.is_streaming = True
            logging.info(f"Sensor {self.device_info.device_id} streaming started")
            return True
            
        except Exception as e:
            logging.error(f"Error starting sensor streaming: {e}")
            return False
    
    async def stop_streaming(self):
        """Stop sensor data streaming"""
        if not self.is_streaming:
            return
        
        try:
            self.is_streaming = False
            
            # Stop hardware streaming
            await self._stop_hardware_streaming()
            
            # Cancel processing task
            if self.processing_task:
                self.processing_task.cancel()
                await self.processing_task
            
            logging.info(f"Sensor {self.device_info.device_id} streaming stopped")
            
        except Exception as e:
            logging.error(f"Error stopping sensor streaming: {e}")
    
    async def read_single(self) -> Optional[SensorReading]:
        """Read a single sensor value"""
        try:
            if not self.is_connected:
                if not await self.connect():
                    return None
            
            raw_data = await self._read_hardware_data()
            if raw_data is None:
                return None
            
            # Process raw data
            reading = await self._process_raw_data(raw_data)
            
            # Update statistics
            self._update_statistics(reading)
            
            return reading
            
        except Exception as e:
            logging.error(f"Error reading sensor data: {e}")
            self.stats['errors_count'] += 1
            return None
    
    def register_data_callback(self, callback: Callable[[SensorReading], None]):
        """Register callback for sensor data"""
        self.data_callbacks.append(callback)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get sensor statistics"""
        return self.stats.copy()
    
    def get_configuration(self) -> SensorConfiguration:
        """Get current sensor configuration"""
        return self.configuration
    
    async def calibrate(self, calibration_data: Dict[str, Any]) -> bool:
        """Calibrate the sensor"""
        try:
            # Apply calibration
            success = await self._apply_calibration(calibration_data)
            
            if success:
                self.configuration.calibration.update(calibration_data)
                logging.info(f"Sensor {self.device_info.device_id} calibrated successfully")
            
            return success
            
        except Exception as e:
            logging.error(f"Error calibrating sensor: {e}")
            return False
    
    # Abstract methods to be implemented by specific sensor types
    async def _apply_hardware_configuration(self, config: SensorConfiguration) -> bool:
        """Apply configuration to hardware"""
        raise NotImplementedError
    
    async def _start_hardware_streaming(self) -> bool:
        """Start hardware streaming"""
        raise NotImplementedError
    
    async def _stop_hardware_streaming(self):
        """Stop hardware streaming"""
        raise NotImplementedError
    
    async def _read_hardware_data(self) -> Any:
        """Read raw data from hardware"""
        raise NotImplementedError
    
    async def _process_raw_data(self, raw_data: Any) -> SensorReading:
        """Process raw data into sensor reading"""
        raise NotImplementedError
    
    async def _apply_calibration(self, calibration_data: Dict[str, Any]) -> bool:
        """Apply calibration to sensor"""
        return True  # Default implementation
    
    async def _data_processing_loop(self):
        """Main data processing loop for streaming"""
        while self.is_streaming:
            try:
                # Read data with timeout
                raw_data = await asyncio.wait_for(
                    self._read_hardware_data(),
                    timeout=1.0 / self.configuration.sampling_rate
                )
                
                if raw_data is not None:
                    # Process data
                    reading = await self._process_raw_data(raw_data)
                    
                    # Update statistics
                    self._update_statistics(reading)
                    
                    # Queue for stream processing
                    try:
                        self.data_buffer.put_nowait(reading)
                    except asyncio.QueueFull:
                        # Drop oldest reading
                        try:
                            self.data_buffer.get_nowait()
                            self.data_buffer.put_nowait(reading)
                        except asyncio.QueueEmpty:
                            pass
                    
                    # Notify callbacks
                    await self._notify_data_callbacks(reading)
                
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"Error in sensor data processing: {e}")
                self.stats['errors_count'] += 1
                await asyncio.sleep(0.1)
    
    async def _notify_data_callbacks(self, reading: SensorReading):
        """Notify registered callbacks of new data"""
        for callback in self.data_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(reading)
                else:
                    callback(reading)
            except Exception as e:
                logging.error(f"Error in sensor data callback: {e}")
    
    def _update_statistics(self, reading: SensorReading):
        """Update sensor statistics"""
        self.stats['readings_count'] += 1
        self.stats['last_reading_time'] = reading.timestamp
        
        # Update average quality
        count = self.stats['readings_count']
        current_avg = self.stats['average_quality']
        self.stats['average_quality'] = (current_avg * (count - 1) + reading.quality) / count
        
        # Update data rate
        if count > 1:
            time_diff = reading.timestamp - self.stats.get('first_reading_time', reading.timestamp)
            if time_diff > 0:
                self.stats['data_rate'] = count / time_diff
        else:
            self.stats['first_reading_time'] = reading.timestamp


class CameraSensor(SensorInterface):
    """Camera sensor implementation"""
    
    def __init__(self, device_info: DeviceInfo):
        super().__init__(device_info, SensorType.CAMERA)
        self.camera_device = None
    
    async def connect(self) -> bool:
        """Connect to camera"""
        try:
            # This would connect to actual camera hardware
            # For simulation, just mark as connected
            self.is_connected = True
            logging.info(f"Camera {self.device_info.device_id} connected")
            return True
        except Exception as e:
            logging.error(f"Error connecting to camera: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from camera"""
        self.is_connected = False
        if self.camera_device:
            # Release camera resources
            pass
    
    async def _apply_hardware_configuration(self, config: SensorConfiguration) -> bool:
        """Apply camera configuration"""
        # Configure resolution, frame rate, etc.
        return True
    
    async def _start_hardware_streaming(self) -> bool:
        """Start camera streaming"""
        # Start camera capture
        return True
    
    async def _stop_hardware_streaming(self):
        """Stop camera streaming"""
        # Stop camera capture
        pass
    
    async def _read_hardware_data(self) -> Any:
        """Read frame from camera"""
        # This would capture actual frame
        # For simulation, return dummy frame data
        if self.configuration.resolution:
            height, width = self.configuration.resolution
            frame = np.random.randint(0, 255, (height, width, 3), dtype=np.uint8)
        else:
            frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        return frame
    
    async def _process_raw_data(self, raw_data: Any) -> SensorReading:
        """Process camera frame"""
        return SensorReading(
            sensor_id=self.device_info.device_id,
            sensor_type=self.sensor_type,
            timestamp=time.time(),
            data=raw_data,
            metadata={
                'frame_shape': raw_data.shape if hasattr(raw_data, 'shape') else None,
                'data_type': str(type(raw_data))
            },
            quality=0.9,  # Simulated quality
            confidence=0.95
        )


class MicrophoneSensor(SensorInterface):
    """Microphone sensor implementation"""
    
    def __init__(self, device_info: DeviceInfo):
        super().__init__(device_info, SensorType.MICROPHONE)
        self.audio_device = None
    
    async def connect(self) -> bool:
        """Connect to microphone"""
        try:
            self.is_connected = True
            logging.info(f"Microphone {self.device_info.device_id} connected")
            return True
        except Exception as e:
            logging.error(f"Error connecting to microphone: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from microphone"""
        self.is_connected = False
    
    async def _apply_hardware_configuration(self, config: SensorConfiguration) -> bool:
        """Apply microphone configuration"""
        return True
    
    async def _start_hardware_streaming(self) -> bool:
        """Start audio streaming"""
        return True
    
    async def _stop_hardware_streaming(self):
        """Stop audio streaming"""
        pass
    
    async def _read_hardware_data(self) -> Any:
        """Read audio data"""
        # Simulate audio data
        sample_rate = int(self.configuration.sampling_rate * 1000)  # Convert to samples/sec
        duration = 1.0 / self.configuration.sampling_rate  # Duration per reading
        samples = int(sample_rate * duration)
        
        audio_data = np.random.randn(samples).astype(np.float32)
        return audio_data
    
    async def _process_raw_data(self, raw_data: Any) -> SensorReading:
        """Process audio data"""
        return SensorReading(
            sensor_id=self.device_info.device_id,
            sensor_type=self.sensor_type,
            timestamp=time.time(),
            data=raw_data,
            metadata={
                'sample_count': len(raw_data) if hasattr(raw_data, '__len__') else 0,
                'sample_rate': self.configuration.sampling_rate * 1000,
                'data_type': str(type(raw_data))
            },
            quality=0.85,
            confidence=0.9
        )