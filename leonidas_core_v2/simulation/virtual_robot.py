"""
Virtual Robot

Configurable virtual robot for simulation and testing.
"""

import asyncio
import logging
import time
import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Callable
import threading

from .physical_simulator import Vector3, Quaternion, RigidBody, CollisionShape, ForceCommand


class JointType(Enum):
    """Types of robot joints."""
    REVOLUTE = "revolute"      # Rotational joint
    PRISMATIC = "prismatic"    # Linear joint
    FIXED = "fixed"            # Fixed joint
    SPHERICAL = "spherical"    # Ball joint
    PLANAR = "planar"          # Planar joint


class ActuatorType(Enum):
    """Types of actuators."""
    SERVO = "servo"            # Position controlled
    MOTOR = "motor"            # Velocity controlled
    PNEUMATIC = "pneumatic"    # Pneumatic actuator
    HYDRAULIC = "hydraulic"    # Hydraulic actuator


@dataclass
class JointLimits:
    """Joint limits and constraints."""
    min_position: float = -math.pi
    max_position: float = math.pi
    max_velocity: float = 10.0
    max_acceleration: float = 100.0
    max_torque: float = 100.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "min_position": self.min_position,
            "max_position": self.max_position,
            "max_velocity": self.max_velocity,
            "max_acceleration": self.max_acceleration,
            "max_torque": self.max_torque,
        }


@dataclass
class Joint:
    """Robot joint definition."""
    joint_id: str
    joint_type: JointType
    parent_link: str
    child_link: str
    position: Vector3 = field(default_factory=Vector3)
    orientation: Quaternion = field(default_factory=Quaternion)
    axis: Vector3 = field(default_factory=lambda: Vector3(0, 0, 1))
    limits: JointLimits = field(default_factory=JointLimits)
    actuator_type: ActuatorType = ActuatorType.SERVO
    
    # Current state
    current_position: float = 0.0
    current_velocity: float = 0.0
    current_torque: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "joint_id": self.joint_id,
            "joint_type": self.joint_type.value,
            "parent_link": self.parent_link,
            "child_link": self.child_link,
            "position": self.position.to_list(),
            "orientation": self.orientation.to_list(),
            "axis": self.axis.to_list(),
            "limits": self.limits.to_dict(),
            "actuator_type": self.actuator_type.value,
            "current_position": self.current_position,
            "current_velocity": self.current_velocity,
            "current_torque": self.current_torque,
        }
@dataclass
class Link:
    """Robot link definition."""
    link_id: str
    name: str
    mass: float = 1.0
    inertia: List[float] = field(default_factory=lambda: [1.0, 1.0, 1.0])
    collision_shape: CollisionShape = CollisionShape.BOX
    collision_params: Dict[str, float] = field(default_factory=dict)
    visual_mesh: Optional[str] = None
    
    # Current state
    position: Vector3 = field(default_factory=Vector3)
    orientation: Quaternion = field(default_factory=Quaternion)
    linear_velocity: Vector3 = field(default_factory=Vector3)
    angular_velocity: Vector3 = field(default_factory=Vector3)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "link_id": self.link_id,
            "name": self.name,
            "mass": self.mass,
            "inertia": self.inertia,
            "collision_shape": self.collision_shape.value,
            "collision_params": self.collision_params,
            "visual_mesh": self.visual_mesh,
            "position": self.position.to_list(),
            "orientation": self.orientation.to_list(),
            "linear_velocity": self.linear_velocity.to_list(),
            "angular_velocity": self.angular_velocity.to_list(),
        }


@dataclass
class Sensor:
    """Robot sensor definition."""
    sensor_id: str
    sensor_type: str
    parent_link: str
    position: Vector3 = field(default_factory=Vector3)
    orientation: Quaternion = field(default_factory=Quaternion)
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    # Current readings
    last_reading: Optional[Any] = None
    last_update: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "sensor_id": self.sensor_id,
            "sensor_type": self.sensor_type,
            "parent_link": self.parent_link,
            "position": self.position.to_list(),
            "orientation": self.orientation.to_list(),
            "parameters": self.parameters,
            "last_reading": self.last_reading,
            "last_update": self.last_update,
        }


class VirtualRobot:
    """
    Virtual robot for simulation and testing.
    
    Provides:
    - Configurable robot body schema
    - Forward and inverse kinematics
    - Joint control and monitoring
    - Sensor simulation
    - Safety validation
    """
    
    def __init__(self, 
                 robot_id: str,
                 robot_name: str = "Virtual Robot"):
        """
        Initialize virtual robot.
        
        Args:
            robot_id: Unique identifier for this robot
            robot_name: Human-readable name
        """
        self.robot_id = robot_id
        self.robot_name = robot_name
        
        # Robot structure
        self.links: Dict[str, Link] = {}
        self.joints: Dict[str, Joint] = {}
        self.sensors: Dict[str, Sensor] = {}
        
        # Control state
        self.joint_targets: Dict[str, float] = {}
        self.joint_controllers: Dict[str, 'JointController'] = {}
        
        # Safety
        self.emergency_stop = False
        self.safety_limits_enabled = True
        
        # Threading
        self._control_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()
        self._lock = threading.RLock()
        
        # Callbacks
        self.joint_callbacks: List[Callable[[str, float], None]] = []
        self.sensor_callbacks: List[Callable[[str, Any], None]] = []
        
        # Metrics
        self.robot_metrics = {
            "control_cycles": 0,
            "joint_commands": 0,
            "sensor_readings": 0,
            "safety_violations": 0,
        }
        
        # Logging
        self.logger = logging.getLogger(f"leonidas.robot.{robot_id}")
    
    async def start(self) -> None:
        """Start robot control system."""
        self.logger.info(f"Starting virtual robot {self.robot_id}")
        
        try:
            # Initialize joint controllers
            await self._initialize_controllers()
            
            # Start control loop
            self._control_task = asyncio.create_task(self._control_loop())
            
            self.logger.info(f"Virtual robot {self.robot_id} started")
            
        except Exception as e:
            self.logger.error(f"Failed to start virtual robot: {e}")
            raise
    
    async def stop(self) -> None:
        """Stop robot control system."""
        self.logger.info(f"Stopping virtual robot {self.robot_id}")
        
        # Signal shutdown
        self._shutdown_event.set()
        
        # Cancel control task
        if self._control_task:
            self._control_task.cancel()
            try:
                await self._control_task
            except asyncio.CancelledError:
                pass
        
        # Cleanup controllers
        await self._cleanup_controllers()
        
        self.logger.info(f"Virtual robot {self.robot_id} stopped")
    
    def add_link(self, link: Link) -> bool:
        """Add link to robot."""
        try:
            with self._lock:
                if link.link_id in self.links:
                    self.logger.warning(f"Link {link.link_id} already exists")
                    return False
                
                self.links[link.link_id] = link
                self.logger.debug(f"Added link: {link.link_id}")
                return True
        except Exception as e:
            self.logger.error(f"Failed to add link {link.link_id}: {e}")
            return False
    
    def add_joint(self, joint: Joint) -> bool:
        """Add joint to robot."""
        try:
            with self._lock:
                if joint.joint_id in self.joints:
                    self.logger.warning(f"Joint {joint.joint_id} already exists")
                    return False
                
                # Validate parent and child links exist
                if joint.parent_link not in self.links:
                    self.logger.error(f"Parent link {joint.parent_link} not found")
                    return False
                
                if joint.child_link not in self.links:
                    self.logger.error(f"Child link {joint.child_link} not found")
                    return False
                
                self.joints[joint.joint_id] = joint
                self.joint_targets[joint.joint_id] = joint.current_position
                
                # Create joint controller
                controller = JointController(joint)
                self.joint_controllers[joint.joint_id] = controller
                
                self.logger.debug(f"Added joint: {joint.joint_id}")
                return True
        except Exception as e:
            self.logger.error(f"Failed to add joint {joint.joint_id}: {e}")
            return False
    
    def add_sensor(self, sensor: Sensor) -> bool:
        """Add sensor to robot."""
        try:
            with self._lock:
                if sensor.sensor_id in self.sensors:
                    self.logger.warning(f"Sensor {sensor.sensor_id} already exists")
                    return False
                
                # Validate parent link exists
                if sensor.parent_link not in self.links:
                    self.logger.error(f"Parent link {sensor.parent_link} not found")
                    return False
                
                self.sensors[sensor.sensor_id] = sensor
                self.logger.debug(f"Added sensor: {sensor.sensor_id}")
                return True
        except Exception as e:
            self.logger.error(f"Failed to add sensor {sensor.sensor_id}: {e}")
            return False
    
    def set_joint_target(self, joint_id: str, target: float) -> bool:
        """Set target position for a joint."""
        try:
            with self._lock:
                if joint_id not in self.joints:
                    self.logger.error(f"Joint {joint_id} not found")
                    return False
                
                joint = self.joints[joint_id]
                
                # Validate safety limits
                if self.safety_limits_enabled:
                    if target < joint.limits.min_position or target > joint.limits.max_position:
                        self.logger.error(f"Joint {joint_id} target {target} outside limits")
                        self.robot_metrics["safety_violations"] += 1
                        return False
                
                self.joint_targets[joint_id] = target
                self.robot_metrics["joint_commands"] += 1
                
                self.logger.debug(f"Set joint {joint_id} target: {target}")
                return True
        except Exception as e:
            self.logger.error(f"Failed to set joint target: {e}")
            return False
    
    def get_joint_state(self, joint_id: str) -> Optional[Dict[str, float]]:
        """Get current state of a joint."""
        with self._lock:
            if joint_id not in self.joints:
                return None
            
            joint = self.joints[joint_id]
            return {
                "position": joint.current_position,
                "velocity": joint.current_velocity,
                "torque": joint.current_torque,
                "target": self.joint_targets.get(joint_id, 0.0),
            }
    
    def get_all_joint_states(self) -> Dict[str, Dict[str, float]]:
        """Get states of all joints."""
        with self._lock:
            return {
                joint_id: self.get_joint_state(joint_id)
                for joint_id in self.joints.keys()
            }
    
    def get_sensor_reading(self, sensor_id: str) -> Optional[Any]:
        """Get latest sensor reading."""
        with self._lock:
            if sensor_id not in self.sensors:
                return None
            
            sensor = self.sensors[sensor_id]
            return sensor.last_reading
    
    def trigger_emergency_stop(self, reason: str = "Manual emergency stop") -> None:
        """Trigger emergency stop."""
        self.logger.critical(f"EMERGENCY STOP triggered: {reason}")
        
        with self._lock:
            self.emergency_stop = True
            
            # Stop all joint motion
            for joint_id in self.joints:
                self.joint_targets[joint_id] = self.joints[joint_id].current_position
    
    def reset_emergency_stop(self) -> bool:
        """Reset emergency stop state."""
        try:
            self.logger.info("Resetting emergency stop")
            
            with self._lock:
                self.emergency_stop = False
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to reset emergency stop: {e}")
            return False
    
    def get_robot_status(self) -> Dict[str, Any]:
        """Get comprehensive robot status."""
        with self._lock:
            return {
                "robot_id": self.robot_id,
                "robot_name": self.robot_name,
                "emergency_stop": self.emergency_stop,
                "safety_limits_enabled": self.safety_limits_enabled,
                "links_count": len(self.links),
                "joints_count": len(self.joints),
                "sensors_count": len(self.sensors),
                "metrics": self.robot_metrics.copy(),
                "joint_states": self.get_all_joint_states(),
            }
    
    def add_joint_callback(self, callback: Callable[[str, float], None]) -> None:
        """Add callback for joint state changes."""
        self.joint_callbacks.append(callback)
    
    def add_sensor_callback(self, callback: Callable[[str, Any], None]) -> None:
        """Add callback for sensor readings."""
        self.sensor_callbacks.append(callback)
    
    # Private methods
    async def _initialize_controllers(self) -> None:
        """Initialize joint controllers."""
        for controller in self.joint_controllers.values():
            await controller.initialize()
    
    async def _cleanup_controllers(self) -> None:
        """Cleanup joint controllers."""
        for controller in self.joint_controllers.values():
            await controller.cleanup()
    
    async def _control_loop(self) -> None:
        """Main robot control loop."""
        control_rate = 100  # Hz
        dt = 1.0 / control_rate
        
        while not self._shutdown_event.is_set():
            try:
                start_time = time.time()
                
                # Update joint controllers
                await self._update_joint_controllers(dt)
                
                # Update sensors
                await self._update_sensors()
                
                # Update metrics
                self.robot_metrics["control_cycles"] += 1
                
                # Sleep to maintain control rate
                elapsed = time.time() - start_time
                sleep_time = dt - elapsed
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Control loop error: {e}")
                await asyncio.sleep(dt)
    
    async def _update_joint_controllers(self, dt: float) -> None:
        """Update all joint controllers."""
        with self._lock:
            if self.emergency_stop:
                return
            
            for joint_id, controller in self.joint_controllers.items():
                target = self.joint_targets.get(joint_id, 0.0)
                await controller.update(target, dt)
                
                # Notify callbacks if position changed significantly
                joint = self.joints[joint_id]
                for callback in self.joint_callbacks:
                    try:
                        callback(joint_id, joint.current_position)
                    except Exception as e:
                        self.logger.error(f"Joint callback error: {e}")
    
    async def _update_sensors(self) -> None:
        """Update all sensors."""
        current_time = time.time()
        
        with self._lock:
            for sensor_id, sensor in self.sensors.items():
                # Simple sensor simulation - would be more complex in real implementation
                if sensor.sensor_type == "position":
                    # Return link position
                    if sensor.parent_link in self.links:
                        link = self.links[sensor.parent_link]
                        sensor.last_reading = link.position.to_list()
                        sensor.last_update = current_time
                        self.robot_metrics["sensor_readings"] += 1
                        
                        # Notify callbacks
                        for callback in self.sensor_callbacks:
                            try:
                                callback(sensor_id, sensor.last_reading)
                            except Exception as e:
                                self.logger.error(f"Sensor callback error: {e}")


class JointController:
    """Simple PID controller for joints."""
    
    def __init__(self, joint: Joint):
        self.joint = joint
        self.kp = 10.0  # Proportional gain
        self.ki = 0.1   # Integral gain
        self.kd = 1.0   # Derivative gain
        
        self.integral_error = 0.0
        self.last_error = 0.0
    
    async def initialize(self) -> None:
        """Initialize controller."""
        self.integral_error = 0.0
        self.last_error = 0.0
    
    async def cleanup(self) -> None:
        """Cleanup controller."""
        pass
    
    async def update(self, target: float, dt: float) -> None:
        """Update controller."""
        # Calculate error
        error = target - self.joint.current_position
        
        # PID calculation
        self.integral_error += error * dt
        derivative_error = (error - self.last_error) / dt if dt > 0 else 0.0
        
        # Control output
        control_output = (
            self.kp * error +
            self.ki * self.integral_error +
            self.kd * derivative_error
        )
        
        # Apply limits
        max_torque = self.joint.limits.max_torque
        control_output = max(-max_torque, min(max_torque, control_output))
        
        # Simple integration (would use proper physics in real implementation)
        self.joint.current_torque = control_output
        
        # Update velocity and position
        acceleration = control_output / 1.0  # Assume unit inertia
        self.joint.current_velocity += acceleration * dt
        
        # Apply velocity limits
        max_vel = self.joint.limits.max_velocity
        self.joint.current_velocity = max(-max_vel, min(max_vel, self.joint.current_velocity))
        
        # Update position
        self.joint.current_position += self.joint.current_velocity * dt
        
        # Apply position limits
        min_pos = self.joint.limits.min_position
        max_pos = self.joint.limits.max_position
        self.joint.current_position = max(min_pos, min(max_pos, self.joint.current_position))
        
        # Apply damping
        self.joint.current_velocity *= 0.95
        
        self.last_error = error