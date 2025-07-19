# Copyright 2025 Leonidas Core v2.0
# Licensed under the Apache License, Version 2.0

"""
Robot Controller - Main interface for robot control and coordination
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import time

from ..core.resilient_component import ResilientComponent
from ..core.safety_aware_component import SafetyAwareComponent


class RobotState(Enum):
    """Robot operational states"""
    OFFLINE = "offline"
    INITIALIZING = "initializing"
    IDLE = "idle"
    ACTIVE = "active"
    EMERGENCY_STOP = "emergency_stop"
    MAINTENANCE = "maintenance"
    ERROR = "error"


@dataclass
class RobotCapabilities:
    """Robot capabilities and specifications"""
    max_speed: float = 1.0  # m/s
    max_acceleration: float = 2.0  # m/s²
    payload_capacity: float = 5.0  # kg
    reach_radius: float = 1.0  # meters
    degrees_of_freedom: int = 6
    supported_tools: List[str] = field(default_factory=list)
    sensor_types: List[str] = field(default_factory=list)
    safety_features: List[str] = field(default_factory=list)


@dataclass
class RobotStatus:
    """Current robot status"""
    state: RobotState
    position: Dict[str, float] = field(default_factory=dict)
    velocity: Dict[str, float] = field(default_factory=dict)
    joint_angles: List[float] = field(default_factory=list)
    tool_status: Dict[str, Any] = field(default_factory=dict)
    sensor_readings: Dict[str, Any] = field(default_factory=dict)
    error_messages: List[str] = field(default_factory=list)
    last_update: float = field(default_factory=time.time)


class RobotController(ResilientComponent, SafetyAwareComponent):
    """
    Main robot controller providing high-level robot control interface
    with safety monitoring and resilient operation.
    """
    
    def __init__(self, 
                 robot_id: str,
                 capabilities: RobotCapabilities,
                 config: Optional[Dict[str, Any]] = None):
        super().__init__(f"robot_controller_{robot_id}")
        
        self.robot_id = robot_id
        self.capabilities = capabilities
        self.config = config or {}
        
        # Robot state
        self.status = RobotStatus(state=RobotState.OFFLINE)
        self.command_queue = asyncio.Queue(maxsize=100)
        self.status_callbacks: List[Callable] = []
        
        # Control parameters
        self.control_frequency = self.config.get('control_frequency', 100)  # Hz
        self.safety_check_interval = self.config.get('safety_check_interval', 0.1)  # seconds
        
        # Tasks
        self.control_task: Optional[asyncio.Task] = None
        self.monitoring_task: Optional[asyncio.Task] = None
        
        # Safety limits
        self.safety_limits = {
            'max_velocity': capabilities.max_speed,
            'max_acceleration': capabilities.max_acceleration,
            'workspace_bounds': self.config.get('workspace_bounds', {}),
            'joint_limits': self.config.get('joint_limits', {}),
        }
        
        logging.info(f"Robot controller initialized for {robot_id}")
    
    async def initialize(self) -> bool:
        """Initialize robot controller and establish connections"""
        try:
            self.status.state = RobotState.INITIALIZING
            await self._notify_status_change()
            
            # Initialize hardware connections
            await self._initialize_hardware()
            
            # Start control and monitoring tasks
            self.control_task = asyncio.create_task(self._control_loop())
            self.monitoring_task = asyncio.create_task(self._monitoring_loop())
            
            # Perform initial safety checks
            if await self._perform_safety_checks():
                self.status.state = RobotState.IDLE
                await self._notify_status_change()
                logging.info(f"Robot {self.robot_id} initialized successfully")
                return True
            else:
                self.status.state = RobotState.ERROR
                self.status.error_messages.append("Initial safety checks failed")
                await self._notify_status_change()
                return False
                
        except Exception as e:
            self.status.state = RobotState.ERROR
            self.status.error_messages.append(f"Initialization failed: {str(e)}")
            await self._notify_status_change()
            logging.error(f"Robot initialization failed: {e}")
            return False
    
    async def shutdown(self):
        """Safely shutdown robot controller"""
        try:
            logging.info(f"Shutting down robot {self.robot_id}")
            
            # Stop all movement
            await self.emergency_stop()
            
            # Cancel tasks
            if self.control_task:
                self.control_task.cancel()
            if self.monitoring_task:
                self.monitoring_task.cancel()
            
            # Wait for tasks to complete
            await asyncio.gather(
                self.control_task, self.monitoring_task, 
                return_exceptions=True
            )
            
            # Shutdown hardware connections
            await self._shutdown_hardware()
            
            self.status.state = RobotState.OFFLINE
            await self._notify_status_change()
            
        except Exception as e:
            logging.error(f"Error during robot shutdown: {e}")
    
    async def move_to_position(self, 
                             target_position: Dict[str, float],
                             speed: float = 0.5,
                             precision: float = 0.01) -> bool:
        """Move robot to target position"""
        if not await self._validate_safety_conditions():
            return False
        
        command = {
            'type': 'move_to_position',
            'target_position': target_position,
            'speed': min(speed, self.capabilities.max_speed),
            'precision': precision,
            'timestamp': time.time()
        }
        
        try:
            await self.command_queue.put(command)
            return True
        except asyncio.QueueFull:
            logging.warning("Command queue full, move command rejected")
            return False
    
    async def move_joints(self, 
                         joint_angles: List[float],
                         speed: float = 0.5) -> bool:
        """Move robot joints to specified angles"""
        if not await self._validate_safety_conditions():
            return False
        
        if len(joint_angles) != self.capabilities.degrees_of_freedom:
            logging.error(f"Invalid joint angles count: expected {self.capabilities.degrees_of_freedom}, got {len(joint_angles)}")
            return False
        
        command = {
            'type': 'move_joints',
            'joint_angles': joint_angles,
            'speed': min(speed, self.capabilities.max_speed),
            'timestamp': time.time()
        }
        
        try:
            await self.command_queue.put(command)
            return True
        except asyncio.QueueFull:
            logging.warning("Command queue full, joint move command rejected")
            return False
    
    async def activate_tool(self, tool_name: str, parameters: Dict[str, Any] = None) -> bool:
        """Activate specified tool with parameters"""
        if tool_name not in self.capabilities.supported_tools:
            logging.error(f"Tool {tool_name} not supported")
            return False
        
        if not await self._validate_safety_conditions():
            return False
        
        command = {
            'type': 'activate_tool',
            'tool_name': tool_name,
            'parameters': parameters or {},
            'timestamp': time.time()
        }
        
        try:
            await self.command_queue.put(command)
            return True
        except asyncio.QueueFull:
            logging.warning("Command queue full, tool activation rejected")
            return False
    
    async def emergency_stop(self):
        """Immediately stop all robot movement"""
        self.status.state = RobotState.EMERGENCY_STOP
        
        # Clear command queue
        while not self.command_queue.empty():
            try:
                self.command_queue.get_nowait()
            except asyncio.QueueEmpty:
                break
        
        # Send emergency stop command
        await self._execute_emergency_stop()
        await self._notify_status_change()
        
        logging.warning(f"Emergency stop activated for robot {self.robot_id}")
    
    async def reset_from_emergency(self) -> bool:
        """Reset robot from emergency stop state"""
        if self.status.state != RobotState.EMERGENCY_STOP:
            return False
        
        try:
            # Perform safety checks
            if await self._perform_safety_checks():
                self.status.state = RobotState.IDLE
                self.status.error_messages.clear()
                await self._notify_status_change()
                logging.info(f"Robot {self.robot_id} reset from emergency stop")
                return True
            else:
                logging.error("Safety checks failed during emergency reset")
                return False
        except Exception as e:
            logging.error(f"Error during emergency reset: {e}")
            return False
    
    def register_status_callback(self, callback: Callable):
        """Register callback for status changes"""
        self.status_callbacks.append(callback)
    
    def get_status(self) -> RobotStatus:
        """Get current robot status"""
        return self.status
    
    def get_capabilities(self) -> RobotCapabilities:
        """Get robot capabilities"""
        return self.capabilities
    
    async def _control_loop(self):
        """Main control loop processing commands"""
        while True:
            try:
                # Get next command with timeout
                command = await asyncio.wait_for(
                    self.command_queue.get(), 
                    timeout=1.0
                )
                
                # Execute command if robot is in active state
                if self.status.state in [RobotState.IDLE, RobotState.ACTIVE]:
                    await self._execute_command(command)
                else:
                    logging.warning(f"Command rejected - robot state: {self.status.state}")
                
            except asyncio.TimeoutError:
                # No commands to process
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"Error in control loop: {e}")
                await asyncio.sleep(0.1)
    
    async def _monitoring_loop(self):
        """Monitoring loop for status updates and safety checks"""
        while True:
            try:
                # Update robot status
                await self._update_status()
                
                # Perform periodic safety checks
                if not await self._perform_safety_checks():
                    await self.emergency_stop()
                
                await asyncio.sleep(self.safety_check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(1.0)
    
    async def _execute_command(self, command: Dict[str, Any]):
        """Execute robot command"""
        command_type = command['type']
        
        try:
            self.status.state = RobotState.ACTIVE
            
            if command_type == 'move_to_position':
                await self._execute_position_move(command)
            elif command_type == 'move_joints':
                await self._execute_joint_move(command)
            elif command_type == 'activate_tool':
                await self._execute_tool_activation(command)
            else:
                logging.warning(f"Unknown command type: {command_type}")
            
            self.status.state = RobotState.IDLE
            
        except Exception as e:
            self.status.state = RobotState.ERROR
            self.status.error_messages.append(f"Command execution failed: {str(e)}")
            logging.error(f"Command execution error: {e}")
    
    async def _execute_position_move(self, command: Dict[str, Any]):
        """Execute position movement command"""
        # This would interface with actual robot hardware
        # For now, simulate the movement
        target = command['target_position']
        speed = command['speed']
        
        logging.info(f"Moving to position {target} at speed {speed}")
        
        # Simulate movement time
        await asyncio.sleep(1.0)
        
        # Update position
        self.status.position.update(target)
        self.status.last_update = time.time()
    
    async def _execute_joint_move(self, command: Dict[str, Any]):
        """Execute joint movement command"""
        joint_angles = command['joint_angles']
        speed = command['speed']
        
        logging.info(f"Moving joints to {joint_angles} at speed {speed}")
        
        # Simulate movement time
        await asyncio.sleep(1.0)
        
        # Update joint angles
        self.status.joint_angles = joint_angles.copy()
        self.status.last_update = time.time()
    
    async def _execute_tool_activation(self, command: Dict[str, Any]):
        """Execute tool activation command"""
        tool_name = command['tool_name']
        parameters = command['parameters']
        
        logging.info(f"Activating tool {tool_name} with parameters {parameters}")
        
        # Simulate tool activation
        await asyncio.sleep(0.5)
        
        # Update tool status
        self.status.tool_status[tool_name] = {
            'active': True,
            'parameters': parameters,
            'activation_time': time.time()
        }
        self.status.last_update = time.time()
    
    async def _initialize_hardware(self):
        """Initialize hardware connections"""
        # This would establish connections to actual robot hardware
        logging.info("Initializing hardware connections")
        await asyncio.sleep(0.5)  # Simulate initialization time
    
    async def _shutdown_hardware(self):
        """Shutdown hardware connections"""
        logging.info("Shutting down hardware connections")
        await asyncio.sleep(0.2)  # Simulate shutdown time
    
    async def _update_status(self):
        """Update robot status from hardware"""
        # This would read actual sensor data and robot state
        self.status.last_update = time.time()
        
        # Simulate sensor readings
        self.status.sensor_readings.update({
            'temperature': 25.0 + (time.time() % 10),
            'voltage': 24.0,
            'current': 2.5
        })
    
    async def _perform_safety_checks(self) -> bool:
        """Perform comprehensive safety checks"""
        try:
            # Check workspace bounds
            if not self._check_workspace_bounds():
                return False
            
            # Check joint limits
            if not self._check_joint_limits():
                return False
            
            # Check sensor readings
            if not self._check_sensor_safety():
                return False
            
            return True
            
        except Exception as e:
            logging.error(f"Safety check error: {e}")
            return False
    
    def _check_workspace_bounds(self) -> bool:
        """Check if robot is within safe workspace bounds"""
        bounds = self.safety_limits.get('workspace_bounds', {})
        if not bounds:
            return True
        
        for axis, value in self.status.position.items():
            if axis in bounds:
                min_val, max_val = bounds[axis]
                if not (min_val <= value <= max_val):
                    logging.warning(f"Position {axis}={value} outside bounds [{min_val}, {max_val}]")
                    return False
        
        return True
    
    def _check_joint_limits(self) -> bool:
        """Check if joint angles are within safe limits"""
        limits = self.safety_limits.get('joint_limits', {})
        if not limits or not self.status.joint_angles:
            return True
        
        for i, angle in enumerate(self.status.joint_angles):
            if i in limits:
                min_angle, max_angle = limits[i]
                if not (min_angle <= angle <= max_angle):
                    logging.warning(f"Joint {i} angle {angle} outside limits [{min_angle}, {max_angle}]")
                    return False
        
        return True
    
    def _check_sensor_safety(self) -> bool:
        """Check sensor readings for safety violations"""
        readings = self.status.sensor_readings
        
        # Check temperature
        if 'temperature' in readings:
            temp = readings['temperature']
            if temp > 80.0:  # Temperature limit
                logging.warning(f"High temperature detected: {temp}°C")
                return False
        
        # Check voltage
        if 'voltage' in readings:
            voltage = readings['voltage']
            if voltage < 20.0 or voltage > 28.0:  # Voltage range
                logging.warning(f"Voltage out of range: {voltage}V")
                return False
        
        return True
    
    async def _execute_emergency_stop(self):
        """Execute emergency stop procedure"""
        # This would send emergency stop commands to hardware
        logging.info("Executing emergency stop")
        
        # Clear velocities
        self.status.velocity.clear()
        
        # Deactivate all tools
        for tool_name in self.status.tool_status:
            self.status.tool_status[tool_name]['active'] = False
    
    async def _validate_safety_conditions(self) -> bool:
        """Validate current safety conditions before command execution"""
        if self.status.state == RobotState.EMERGENCY_STOP:
            logging.warning("Command rejected - robot in emergency stop")
            return False
        
        if self.status.state == RobotState.ERROR:
            logging.warning("Command rejected - robot in error state")
            return False
        
        return await self._perform_safety_checks()
    
    async def _notify_status_change(self):
        """Notify registered callbacks of status changes"""
        for callback in self.status_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(self.status)
                else:
                    callback(self.status)
            except Exception as e:
                logging.error(f"Error in status callback: {e}")