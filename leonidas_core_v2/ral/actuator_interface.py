# Copyright 2025 Leonidas Core v2.0
# Licensed under the Apache License, Version 2.0

"""
Actuator Interface - Unified interface for actuator control
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import time

from .device_manager import DeviceInterface, DeviceInfo
from ..core.safety_aware_component import SafetyAwareComponent


class ActuatorType(Enum):
    """Types of actuators"""
    SERVO_MOTOR = "servo_motor"
    STEPPER_MOTOR = "stepper_motor"
    DC_MOTOR = "dc_motor"
    LINEAR_ACTUATOR = "linear_actuator"
    PNEUMATIC = "pneumatic"
    HYDRAULIC = "hydraulic"
    SPEAKER = "speaker"
    DISPLAY = "display"
    LED = "led"
    RELAY = "relay"
    CUSTOM = "custom"


class ActuatorState(Enum):
    """Actuator operational states"""
    IDLE = "idle"
    MOVING = "moving"
    HOLDING = "holding"
    ERROR = "error"
    EMERGENCY_STOP = "emergency_stop"


@dataclass
class ActuatorCommand:
    """Command for actuator control"""
    command_id: str
    actuator_id: str
    command_type: str
    parameters: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    priority: int = 0  # Higher number = higher priority
    timeout: float = 10.0  # Command timeout in seconds
    safety_checks: bool = True


@dataclass
class ActuatorStatus:
    """Current actuator status"""
    actuator_id: str
    state: ActuatorState
    position: Optional[float] = None
    velocity: Optional[float] = None
    force: Optional[float] = None
    temperature: Optional[float] = None
    current: Optional[float] = None
    voltage: Optional[float] = None
    error_code: Optional[str] = None
    last_command_id: Optional[str] = None
    timestamp: float = field(default_factory=time.time)


@dataclass
class ActuatorLimits:
    """Safety limits for actuator"""
    min_position: Optional[float] = None
    max_position: Optional[float] = None
    max_velocity: Optional[float] = None
    max_acceleration: Optional[float] = None
    max_force: Optional[float] = None
    max_current: Optional[float] = None
    max_temperature: Optional[float] = None


class ActuatorInterface(DeviceInterface, SafetyAwareComponent):
    """
    Base interface for actuator devices with safety monitoring
    """
    
    def __init__(self, device_info: DeviceInfo, actuator_type: ActuatorType):
        DeviceInterface.__init__(self, device_info)
        SafetyAwareComponent.__init__(self)
        
        self.actuator_type = actuator_type
        self.current_status = ActuatorStatus(
            actuator_id=device_info.device_id,
            state=ActuatorState.IDLE
        )
        
        # Safety limits
        self.safety_limits = ActuatorLimits()
        
        # Command processing
        self.command_queue = asyncio.PriorityQueue(maxsize=100)
        self.active_command: Optional[ActuatorCommand] = None
        self.command_history: List[ActuatorCommand] = []
        
        # Status callbacks
        self.status_callbacks: List[Callable] = []
        
        # Control tasks
        self.command_processor_task: Optional[asyncio.Task] = None
        self.status_monitor_task: Optional[asyncio.Task] = None
        
        # Statistics
        self.stats = {
            'commands_executed': 0,
            'commands_failed': 0,
            'total_runtime': 0.0,
            'emergency_stops': 0,
            'last_activity': time.time()
        }
    
    async def start_control(self) -> bool:
        """Start actuator control system"""
        try:
            if not self.is_connected:
                if not await self.connect():
                    return False
            
            # Start control tasks
            self.command_processor_task = asyncio.create_task(self._command_processor())
            self.status_monitor_task = asyncio.create_task(self._status_monitor())
            
            logging.info(f"Actuator {self.device_info.device_id} control started")
            return True
            
        except Exception as e:
            logging.error(f"Error starting actuator control: {e}")
            return False
    
    async def stop_control(self):
        """Stop actuator control system"""
        try:
            # Emergency stop
            await self.emergency_stop()
            
            # Cancel tasks
            if self.command_processor_task:
                self.command_processor_task.cancel()
            if self.status_monitor_task:
                self.status_monitor_task.cancel()
            
            # Wait for tasks to complete
            await asyncio.gather(
                self.command_processor_task, self.status_monitor_task,
                return_exceptions=True
            )
            
            logging.info(f"Actuator {self.device_info.device_id} control stopped")
            
        except Exception as e:
            logging.error(f"Error stopping actuator control: {e}")
    
    async def execute_command(self, command: ActuatorCommand) -> bool:
        """Queue command for execution"""
        try:
            # Validate command
            if not await self._validate_command(command):
                return False
            
            # Add to queue with priority
            priority = -command.priority  # Negative for max-heap behavior
            await self.command_queue.put((priority, time.time(), command))
            
            logging.debug(f"Command {command.command_id} queued for actuator {self.device_info.device_id}")
            return True
            
        except asyncio.QueueFull:
            logging.warning(f"Command queue full for actuator {self.device_info.device_id}")
            return False
        except Exception as e:
            logging.error(f"Error queuing command: {e}")
            return False
    
    async def move_to_position(self, position: float, speed: float = 1.0, timeout: float = 10.0) -> bool:
        """Move actuator to specific position"""
        command = ActuatorCommand(
            command_id=f"move_{time.time()}",
            actuator_id=self.device_info.device_id,
            command_type="move_to_position",
            parameters={
                'position': position,
                'speed': speed
            },
            timeout=timeout
        )
        
        return await self.execute_command(command)
    
    async def set_velocity(self, velocity: float, timeout: float = 5.0) -> bool:
        """Set actuator velocity"""
        command = ActuatorCommand(
            command_id=f"velocity_{time.time()}",
            actuator_id=self.device_info.device_id,
            command_type="set_velocity",
            parameters={
                'velocity': velocity
            },
            timeout=timeout
        )
        
        return await self.execute_command(command)
    
    async def apply_force(self, force: float, duration: float = 1.0) -> bool:
        """Apply force for specified duration"""
        command = ActuatorCommand(
            command_id=f"force_{time.time()}",
            actuator_id=self.device_info.device_id,
            command_type="apply_force",
            parameters={
                'force': force,
                'duration': duration
            },
            timeout=duration + 1.0
        )
        
        return await self.execute_command(command)
    
    async def emergency_stop(self):
        """Emergency stop actuator"""
        try:
            self.current_status.state = ActuatorState.EMERGENCY_STOP
            
            # Clear command queue
            while not self.command_queue.empty():
                try:
                    self.command_queue.get_nowait()
                except asyncio.QueueEmpty:
                    break
            
            # Execute hardware emergency stop
            await self._execute_emergency_stop()
            
            # Update statistics
            self.stats['emergency_stops'] += 1
            
            await self._notify_status_change()
            logging.warning(f"Emergency stop activated for actuator {self.device_info.device_id}")
            
        except Exception as e:
            logging.error(f"Error during emergency stop: {e}")
    
    async def reset_from_emergency(self) -> bool:
        """Reset actuator from emergency stop"""
        try:
            if self.current_status.state != ActuatorState.EMERGENCY_STOP:
                return False
            
            # Perform safety checks
            if await self._perform_safety_checks():
                self.current_status.state = ActuatorState.IDLE
                self.current_status.error_code = None
                await self._notify_status_change()
                
                logging.info(f"Actuator {self.device_info.device_id} reset from emergency stop")
                return True
            else:
                logging.error("Safety checks failed during emergency reset")
                return False
                
        except Exception as e:
            logging.error(f"Error during emergency reset: {e}")
            return False
    
    def set_safety_limits(self, limits: ActuatorLimits):
        """Set safety limits for actuator"""
        self.safety_limits = limits
        logging.info(f"Safety limits updated for actuator {self.device_info.device_id}")
    
    def get_status(self) -> ActuatorStatus:
        """Get current actuator status"""
        return self.current_status
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get actuator statistics"""
        return self.stats.copy()
    
    def register_status_callback(self, callback: Callable):
        """Register callback for status changes"""
        self.status_callbacks.append(callback)
    
    # Abstract methods to be implemented by specific actuator types
    async def _execute_hardware_command(self, command: ActuatorCommand) -> bool:
        """Execute command on hardware"""
        raise NotImplementedError
    
    async def _read_hardware_status(self) -> ActuatorStatus:
        """Read status from hardware"""
        raise NotImplementedError
    
    async def _execute_emergency_stop(self):
        """Execute emergency stop on hardware"""
        raise NotImplementedError
    
    async def _command_processor(self):
        """Process commands from queue"""
        while True:
            try:
                # Get next command
                priority, timestamp, command = await asyncio.wait_for(
                    self.command_queue.get(),
                    timeout=1.0
                )
                
                # Check if actuator is in valid state
                if self.current_status.state == ActuatorState.EMERGENCY_STOP:
                    logging.warning(f"Command rejected - actuator in emergency stop")
                    continue
                
                # Execute command
                await self._execute_command_with_timeout(command)
                
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"Error in command processor: {e}")
                await asyncio.sleep(0.1)
    
    async def _execute_command_with_timeout(self, command: ActuatorCommand):
        """Execute command with timeout and safety checks"""
        try:
            self.active_command = command
            self.current_status.state = ActuatorState.MOVING
            self.current_status.last_command_id = command.command_id
            
            # Perform safety checks if required
            if command.safety_checks and not await self._perform_safety_checks():
                raise Exception("Safety checks failed")
            
            # Execute command with timeout
            success = await asyncio.wait_for(
                self._execute_hardware_command(command),
                timeout=command.timeout
            )
            
            if success:
                self.stats['commands_executed'] += 1
                self.current_status.state = ActuatorState.IDLE
                logging.debug(f"Command {command.command_id} executed successfully")
            else:
                self.stats['commands_failed'] += 1
                self.current_status.state = ActuatorState.ERROR
                self.current_status.error_code = "command_execution_failed"
                logging.error(f"Command {command.command_id} execution failed")
            
            # Add to history
            self.command_history.append(command)
            if len(self.command_history) > 100:
                self.command_history.pop(0)
            
            self.active_command = None
            await self._notify_status_change()
            
        except asyncio.TimeoutError:
            self.stats['commands_failed'] += 1
            self.current_status.state = ActuatorState.ERROR
            self.current_status.error_code = "command_timeout"
            logging.error(f"Command {command.command_id} timed out")
            await self.emergency_stop()
            
        except Exception as e:
            self.stats['commands_failed'] += 1
            self.current_status.state = ActuatorState.ERROR
            self.current_status.error_code = str(e)
            logging.error(f"Command {command.command_id} failed: {e}")
            self.active_command = None
    
    async def _status_monitor(self):
        """Monitor actuator status"""
        while True:
            try:
                # Read hardware status
                hardware_status = await self._read_hardware_status()
                
                # Update current status
                self.current_status.position = hardware_status.position
                self.current_status.velocity = hardware_status.velocity
                self.current_status.force = hardware_status.force
                self.current_status.temperature = hardware_status.temperature
                self.current_status.current = hardware_status.current
                self.current_status.voltage = hardware_status.voltage
                self.current_status.timestamp = time.time()
                
                # Check for safety violations
                if not await self._perform_safety_checks():
                    await self.emergency_stop()
                
                # Update activity time
                self.stats['last_activity'] = time.time()
                
                await asyncio.sleep(0.1)  # 10Hz monitoring
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"Error in status monitor: {e}")
                await asyncio.sleep(1.0)
    
    async def _validate_command(self, command: ActuatorCommand) -> bool:
        """Validate command parameters"""
        try:
            # Check command type
            if command.command_type not in self._get_supported_commands():
                logging.error(f"Unsupported command type: {command.command_type}")
                return False
            
            # Validate parameters based on command type
            if command.command_type == "move_to_position":
                position = command.parameters.get('position')
                if position is None:
                    return False
                
                # Check position limits
                if self.safety_limits.min_position is not None and position < self.safety_limits.min_position:
                    logging.error(f"Position {position} below minimum {self.safety_limits.min_position}")
                    return False
                
                if self.safety_limits.max_position is not None and position > self.safety_limits.max_position:
                    logging.error(f"Position {position} above maximum {self.safety_limits.max_position}")
                    return False
            
            elif command.command_type == "set_velocity":
                velocity = command.parameters.get('velocity')
                if velocity is None:
                    return False
                
                # Check velocity limits
                if self.safety_limits.max_velocity is not None and abs(velocity) > self.safety_limits.max_velocity:
                    logging.error(f"Velocity {velocity} exceeds maximum {self.safety_limits.max_velocity}")
                    return False
            
            elif command.command_type == "apply_force":
                force = command.parameters.get('force')
                if force is None:
                    return False
                
                # Check force limits
                if self.safety_limits.max_force is not None and abs(force) > self.safety_limits.max_force:
                    logging.error(f"Force {force} exceeds maximum {self.safety_limits.max_force}")
                    return False
            
            return True
            
        except Exception as e:
            logging.error(f"Error validating command: {e}")
            return False
    
    async def _perform_safety_checks(self) -> bool:
        """Perform safety checks"""
        try:
            # Check temperature limits
            if (self.safety_limits.max_temperature is not None and 
                self.current_status.temperature is not None and
                self.current_status.temperature > self.safety_limits.max_temperature):
                logging.warning(f"Temperature {self.current_status.temperature} exceeds limit")
                return False
            
            # Check current limits
            if (self.safety_limits.max_current is not None and
                self.current_status.current is not None and
                self.current_status.current > self.safety_limits.max_current):
                logging.warning(f"Current {self.current_status.current} exceeds limit")
                return False
            
            return True
            
        except Exception as e:
            logging.error(f"Error in safety checks: {e}")
            return False
    
    def _get_supported_commands(self) -> List[str]:
        """Get list of supported commands"""
        return ["move_to_position", "set_velocity", "apply_force", "stop"]
    
    async def _notify_status_change(self):
        """Notify callbacks of status changes"""
        for callback in self.status_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(self.current_status)
                else:
                    callback(self.current_status)
            except Exception as e:
                logging.error(f"Error in status callback: {e}")


class ServoMotor(ActuatorInterface):
    """Servo motor implementation"""
    
    def __init__(self, device_info: DeviceInfo):
        super().__init__(device_info, ActuatorType.SERVO_MOTOR)
    
    async def connect(self) -> bool:
        """Connect to servo motor"""
        try:
            self.is_connected = True
            logging.info(f"Servo motor {self.device_info.device_id} connected")
            return True
        except Exception as e:
            logging.error(f"Error connecting to servo motor: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from servo motor"""
        self.is_connected = False
    
    async def _execute_hardware_command(self, command: ActuatorCommand) -> bool:
        """Execute servo motor command"""
        # Simulate command execution
        if command.command_type == "move_to_position":
            position = command.parameters['position']
            speed = command.parameters.get('speed', 1.0)
            
            # Simulate movement time
            movement_time = abs(position - (self.current_status.position or 0)) / speed
            await asyncio.sleep(min(movement_time, 2.0))  # Cap at 2 seconds for simulation
            
            self.current_status.position = position
            
        elif command.command_type == "set_velocity":
            velocity = command.parameters['velocity']
            self.current_status.velocity = velocity
            
        return True
    
    async def _read_hardware_status(self) -> ActuatorStatus:
        """Read servo motor status"""
        # Simulate status reading
        return ActuatorStatus(
            actuator_id=self.device_info.device_id,
            state=self.current_status.state,
            position=self.current_status.position,
            velocity=self.current_status.velocity,
            temperature=25.0 + (time.time() % 10),  # Simulated temperature
            current=1.5,  # Simulated current
            voltage=12.0   # Simulated voltage
        )
    
    async def _execute_emergency_stop(self):
        """Execute servo motor emergency stop"""
        self.current_status.velocity = 0.0
        logging.info(f"Servo motor {self.device_info.device_id} emergency stopped")