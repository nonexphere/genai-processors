"""
Physical Simulator

Provides physics simulation capabilities for safe development and testing of physical interactions.
"""

import asyncio
import logging
import time
import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Callable
import threading
import numpy as np


class PhysicsEngine(Enum):
    """Available physics engines."""
    SIMPLE = "simple"      # Simple built-in physics
    BULLET = "bullet"      # PyBullet physics engine
    MUJOCO = "mujoco"      # MuJoCo physics engine


class CollisionShape(Enum):
    """Collision shape types."""
    BOX = "box"
    SPHERE = "sphere"
    CYLINDER = "cylinder"
    CAPSULE = "capsule"
    MESH = "mesh"


@dataclass
class Vector3:
    """3D vector representation."""
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    
    def __add__(self, other: 'Vector3') -> 'Vector3':
        return Vector3(self.x + other.x, self.y + other.y, self.z + other.z)
    
    def __sub__(self, other: 'Vector3') -> 'Vector3':
        return Vector3(self.x - other.x, self.y - other.y, self.z - other.z)
    
    def __mul__(self, scalar: float) -> 'Vector3':
        return Vector3(self.x * scalar, self.y * scalar, self.z * scalar)
    
    def magnitude(self) -> float:
        return math.sqrt(self.x**2 + self.y**2 + self.z**2)
    
    def normalize(self) -> 'Vector3':
        mag = self.magnitude()
        if mag > 0:
            return Vector3(self.x / mag, self.y / mag, self.z / mag)
        return Vector3()
    
    def to_list(self) -> List[float]:
        return [self.x, self.y, self.z]


@dataclass
class Quaternion:
    """Quaternion representation for rotations."""
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    w: float = 1.0
    
    def to_list(self) -> List[float]:
        return [self.x, self.y, self.z, self.w]
    
    @classmethod
    def from_euler(cls, roll: float, pitch: float, yaw: float) -> 'Quaternion':
        """Create quaternion from Euler angles (in radians)."""
        cr = math.cos(roll * 0.5)
        sr = math.sin(roll * 0.5)
        cp = math.cos(pitch * 0.5)
        sp = math.sin(pitch * 0.5)
        cy = math.cos(yaw * 0.5)
        sy = math.sin(yaw * 0.5)
        
        return cls(
            x=sr * cp * cy - cr * sp * sy,
            y=cr * sp * cy + sr * cp * sy,
            z=cr * cp * sy - sr * sp * cy,
            w=cr * cp * cy + sr * sp * sy
        )


@dataclass
class RigidBody:
    """Rigid body in physics simulation."""
    body_id: str
    position: Vector3 = field(default_factory=Vector3)
    orientation: Quaternion = field(default_factory=Quaternion)
    linear_velocity: Vector3 = field(default_factory=Vector3)
    angular_velocity: Vector3 = field(default_factory=Vector3)
    mass: float = 1.0
    collision_shape: CollisionShape = CollisionShape.BOX
    collision_params: Dict[str, float] = field(default_factory=dict)
    is_static: bool = False
    friction: float = 0.5
    restitution: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "body_id": self.body_id,
            "position": self.position.to_list(),
            "orientation": self.orientation.to_list(),
            "linear_velocity": self.linear_velocity.to_list(),
            "angular_velocity": self.angular_velocity.to_list(),
            "mass": self.mass,
            "collision_shape": self.collision_shape.value,
            "collision_params": self.collision_params,
            "is_static": self.is_static,
            "friction": self.friction,
            "restitution": self.restitution,
        }


@dataclass
class CollisionInfo:
    """Information about a collision."""
    body_a_id: str
    body_b_id: str
    contact_point: Vector3
    contact_normal: Vector3
    penetration_depth: float
    impulse_magnitude: float
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "body_a_id": self.body_a_id,
            "body_b_id": self.body_b_id,
            "contact_point": self.contact_point.to_list(),
            "contact_normal": self.contact_normal.to_list(),
            "penetration_depth": self.penetration_depth,
            "impulse_magnitude": self.impulse_magnitude,
            "timestamp": self.timestamp,
        }


@dataclass
class ForceCommand:
    """Command to apply force to a rigid body."""
    body_id: str
    force: Vector3
    position: Optional[Vector3] = None  # Local position for torque
    duration: float = 0.0  # 0 = single timestep
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "body_id": self.body_id,
            "force": self.force.to_list(),
            "position": self.position.to_list() if self.position else None,
            "duration": self.duration,
        }


class SimplePhysicsEngine:
    """Simple built-in physics engine for basic simulation."""
    
    def __init__(self, gravity: Vector3 = Vector3(0, 0, -9.81)):
        self.gravity = gravity
        self.bodies: Dict[str, RigidBody] = {}
        self.active_forces: List[ForceCommand] = []
        self.collision_callbacks: List[Callable[[CollisionInfo], None]] = []
        self.timestep = 1.0 / 60.0  # 60 FPS
        
    def add_body(self, body: RigidBody) -> bool:
        """Add rigid body to simulation."""
        if body.body_id in self.bodies:
            return False
        
        self.bodies[body.body_id] = body
        return True
    
    def remove_body(self, body_id: str) -> bool:
        """Remove rigid body from simulation."""
        if body_id not in self.bodies:
            return False
        
        del self.bodies[body_id]
        return True
    
    def apply_force(self, force_command: ForceCommand) -> None:
        """Apply force to a rigid body."""
        self.active_forces.append(force_command)
    
    def step(self, dt: float = None) -> List[CollisionInfo]:
        """Step the physics simulation."""
        if dt is None:
            dt = self.timestep
        
        collisions = []
        
        # Apply forces and integrate
        for body in self.bodies.values():
            if body.is_static:
                continue
            
            # Apply gravity
            gravity_force = self.gravity * body.mass
            
            # Apply active forces
            total_force = gravity_force
            for force_cmd in self.active_forces:
                if force_cmd.body_id == body.body_id:
                    total_force = total_force + force_cmd.force
            
            # Simple Euler integration
            acceleration = total_force * (1.0 / body.mass)
            body.linear_velocity = body.linear_velocity + acceleration * dt
            body.position = body.position + body.linear_velocity * dt
            
            # Simple damping
            body.linear_velocity = body.linear_velocity * 0.99
            body.angular_velocity = body.angular_velocity * 0.99
        
        # Clear single-timestep forces
        self.active_forces = [f for f in self.active_forces if f.duration > 0]
        
        # Update force durations
        for force in self.active_forces:
            force.duration -= dt
        
        # Remove expired forces
        self.active_forces = [f for f in self.active_forces if f.duration > 0]
        
        # Simple collision detection
        collisions = self._detect_collisions()
        
        # Notify collision callbacks
        for collision in collisions:
            for callback in self.collision_callbacks:
                try:
                    callback(collision)
                except Exception as e:
                    logging.error(f"Collision callback error: {e}")
        
        return collisions
    
    def _detect_collisions(self) -> List[CollisionInfo]:
        """Simple collision detection."""
        collisions = []
        body_list = list(self.bodies.values())
        
        for i in range(len(body_list)):
            for j in range(i + 1, len(body_list)):
                body_a = body_list[i]
                body_b = body_list[j]
                
                # Simple sphere-sphere collision detection
                if (body_a.collision_shape == CollisionShape.SPHERE and 
                    body_b.collision_shape == CollisionShape.SPHERE):
                    
                    radius_a = body_a.collision_params.get("radius", 0.5)
                    radius_b = body_b.collision_params.get("radius", 0.5)
                    
                    distance_vec = body_b.position - body_a.position
                    distance = distance_vec.magnitude()
                    
                    if distance < (radius_a + radius_b):
                        # Collision detected
                        contact_normal = distance_vec.normalize()
                        penetration = (radius_a + radius_b) - distance
                        contact_point = body_a.position + contact_normal * radius_a
                        
                        collision = CollisionInfo(
                            body_a_id=body_a.body_id,
                            body_b_id=body_b.body_id,
                            contact_point=contact_point,
                            contact_normal=contact_normal,
                            penetration_depth=penetration,
                            impulse_magnitude=0.0,  # Simplified
                        )
                        
                        collisions.append(collision)
                        
                        # Simple collision response
                        if not body_a.is_static and not body_b.is_static:
                            # Separate bodies
                            separation = contact_normal * (penetration * 0.5)
                            body_a.position = body_a.position - separation
                            body_b.position = body_b.position + separation
        
        return collisions
    
    def add_collision_callback(self, callback: Callable[[CollisionInfo], None]) -> None:
        """Add collision callback."""
        self.collision_callbacks.append(callback)


class PhysicalSimulator:
    """
    Physical simulator for safe development and testing.
    
    Provides:
    - Physics simulation with multiple engine backends
    - Collision detection and response
    - Force and torque application
    - Safety validation for physical commands
    - Visualization and debugging tools
    """
    
    def __init__(self, 
                 simulator_id: str = "physical_simulator",
                 physics_engine: PhysicsEngine = PhysicsEngine.SIMPLE,
                 timestep: float = 1.0/60.0,
                 enable_visualization: bool = False):
        """
        Initialize physical simulator.
        
        Args:
            simulator_id: Unique identifier for this simulator
            physics_engine: Physics engine to use
            timestep: Simulation timestep in seconds
            enable_visualization: Enable visualization (if available)
        """
        self.simulator_id = simulator_id
        self.physics_engine_type = physics_engine
        self.timestep = timestep
        self.enable_visualization = enable_visualization
        
        # Physics engine
        self.physics_engine = self._create_physics_engine()
        
        # Simulation state
        self.is_running = False
        self.simulation_time = 0.0
        self.step_count = 0
        
        # Threading
        self._simulation_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()
        self._lock = threading.RLock()
        
        # Callbacks
        self.step_callbacks: List[Callable[[float], None]] = []
        self.collision_callbacks: List[Callable[[CollisionInfo], None]] = []
        
        # Metrics
        self.simulation_metrics = {
            "steps_executed": 0,
            "collisions_detected": 0,
            "bodies_simulated": 0,
            "average_step_time": 0.0,
            "total_step_time": 0.0,
        }
        
        # Logging
        self.logger = logging.getLogger(f"leonidas.simulation.{simulator_id}")
    
    async def start(self) -> None:
        """Start physics simulation."""
        if self.is_running:
            self.logger.warning("Simulator already running")
            return
        
        self.logger.info(f"Starting physics simulator {self.simulator_id}")
        
        try:
            # Initialize physics engine
            await self._initialize_physics_engine()
            
            # Start simulation loop
            self._simulation_task = asyncio.create_task(self._simulation_loop())
            self.is_running = True
            
            self.logger.info(f"Physics simulator {self.simulator_id} started")
            
        except Exception as e:
            self.logger.error(f"Failed to start physics simulator: {e}")
            raise
    
    async def stop(self) -> None:
        """Stop physics simulation."""
        if not self.is_running:
            return
        
        self.logger.info(f"Stopping physics simulator {self.simulator_id}")
        
        # Signal shutdown
        self._shutdown_event.set()
        self.is_running = False
        
        # Cancel simulation task
        if self._simulation_task:
            self._simulation_task.cancel()
            try:
                await self._simulation_task
            except asyncio.CancelledError:
                pass
        
        # Cleanup physics engine
        await self._cleanup_physics_engine()
        
        self.logger.info(f"Physics simulator {self.simulator_id} stopped")
    
    def add_rigid_body(self, body: RigidBody) -> bool:
        """
        Add rigid body to simulation.
        
        Args:
            body: Rigid body to add
            
        Returns:
            True if added successfully, False otherwise
        """
        try:
            with self._lock:
                success = self.physics_engine.add_body(body)
                if success:
                    self.simulation_metrics["bodies_simulated"] = len(self.physics_engine.bodies)
                    self.logger.debug(f"Added rigid body: {body.body_id}")
                return success
        except Exception as e:
            self.logger.error(f"Failed to add rigid body {body.body_id}: {e}")
            return False
    
    def remove_rigid_body(self, body_id: str) -> bool:
        """
        Remove rigid body from simulation.
        
        Args:
            body_id: ID of body to remove
            
        Returns:
            True if removed successfully, False otherwise
        """
        try:
            with self._lock:
                success = self.physics_engine.remove_body(body_id)
                if success:
                    self.simulation_metrics["bodies_simulated"] = len(self.physics_engine.bodies)
                    self.logger.debug(f"Removed rigid body: {body_id}")
                return success
        except Exception as e:
            self.logger.error(f"Failed to remove rigid body {body_id}: {e}")
            return False
    
    def apply_force(self, force_command: ForceCommand) -> bool:
        """
        Apply force to a rigid body.
        
        Args:
            force_command: Force command to apply
            
        Returns:
            True if applied successfully, False otherwise
        """
        try:
            with self._lock:
                # Validate force command
                if not self._validate_force_command(force_command):
                    return False
                
                self.physics_engine.apply_force(force_command)
                self.logger.debug(f"Applied force to body {force_command.body_id}")
                return True
        except Exception as e:
            self.logger.error(f"Failed to apply force: {e}")
            return False
    
    def get_body_state(self, body_id: str) -> Optional[RigidBody]:
        """
        Get current state of a rigid body.
        
        Args:
            body_id: ID of body to query
            
        Returns:
            RigidBody state or None if not found
        """
        with self._lock:
            return self.physics_engine.bodies.get(body_id)
    
    def get_all_bodies(self) -> Dict[str, RigidBody]:
        """Get all rigid bodies in simulation."""
        with self._lock:
            return self.physics_engine.bodies.copy()
    
    def add_step_callback(self, callback: Callable[[float], None]) -> None:
        """Add callback for simulation steps."""
        self.step_callbacks.append(callback)
    
    def add_collision_callback(self, callback: Callable[[CollisionInfo], None]) -> None:
        """Add callback for collisions."""
        self.collision_callbacks.append(callback)
        self.physics_engine.add_collision_callback(callback)
    
    def get_simulation_metrics(self) -> Dict[str, Any]:
        """Get simulation performance metrics."""
        with self._lock:
            avg_step_time = 0.0
            if self.simulation_metrics["steps_executed"] > 0:
                avg_step_time = (
                    self.simulation_metrics["total_step_time"] / 
                    self.simulation_metrics["steps_executed"]
                )
            
            return {
                **self.simulation_metrics,
                "average_step_time": avg_step_time,
                "simulation_time": self.simulation_time,
                "step_count": self.step_count,
                "is_running": self.is_running,
                "physics_engine": self.physics_engine_type.value,
            }
    
    def reset_simulation(self) -> None:
        """Reset simulation to initial state."""
        with self._lock:
            # Clear all bodies
            self.physics_engine.bodies.clear()
            
            # Reset simulation state
            self.simulation_time = 0.0
            self.step_count = 0
            
            # Reset metrics
            self.simulation_metrics = {
                "steps_executed": 0,
                "collisions_detected": 0,
                "bodies_simulated": 0,
                "average_step_time": 0.0,
                "total_step_time": 0.0,
            }
            
            self.logger.info("Simulation reset")
    
    # Private methods
    def _create_physics_engine(self):
        """Create physics engine based on configuration."""
        if self.physics_engine_type == PhysicsEngine.SIMPLE:
            return SimplePhysicsEngine()
        elif self.physics_engine_type == PhysicsEngine.BULLET:
            # Would create PyBullet engine
            raise NotImplementedError("PyBullet engine not implemented yet")
        elif self.physics_engine_type == PhysicsEngine.MUJOCO:
            # Would create MuJoCo engine
            raise NotImplementedError("MuJoCo engine not implemented yet")
        else:
            raise ValueError(f"Unknown physics engine: {self.physics_engine_type}")
    
    async def _initialize_physics_engine(self) -> None:
        """Initialize physics engine."""
        # Setup collision callbacks
        self.physics_engine.add_collision_callback(self._on_collision)
        
        self.logger.debug("Physics engine initialized")
    
    async def _cleanup_physics_engine(self) -> None:
        """Cleanup physics engine."""
        self.logger.debug("Physics engine cleaned up")
    
    async def _simulation_loop(self) -> None:
        """Main simulation loop."""
        last_time = time.time()
        
        while not self._shutdown_event.is_set():
            try:
                current_time = time.time()
                dt = current_time - last_time
                
                # Limit timestep to prevent instability
                dt = min(dt, self.timestep * 2)
                
                # Step physics
                step_start = time.time()
                collisions = self.physics_engine.step(dt)
                step_time = time.time() - step_start
                
                # Update simulation state
                with self._lock:
                    self.simulation_time += dt
                    self.step_count += 1
                    
                    # Update metrics
                    self.simulation_metrics["steps_executed"] += 1
                    self.simulation_metrics["collisions_detected"] += len(collisions)
                    self.simulation_metrics["total_step_time"] += step_time
                
                # Notify step callbacks
                for callback in self.step_callbacks:
                    try:
                        callback(dt)
                    except Exception as e:
                        self.logger.error(f"Step callback error: {e}")
                
                # Sleep to maintain target framerate
                sleep_time = self.timestep - (time.time() - current_time)
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
                
                last_time = current_time
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Simulation loop error: {e}")
                await asyncio.sleep(self.timestep)
    
    def _validate_force_command(self, force_command: ForceCommand) -> bool:
        """Validate force command for safety."""
        # Check if body exists
        if force_command.body_id not in self.physics_engine.bodies:
            self.logger.error(f"Body {force_command.body_id} not found")
            return False
        
        # Check force magnitude (safety limit)
        force_magnitude = force_command.force.magnitude()
        max_force = 1000.0  # Newton
        
        if force_magnitude > max_force:
            self.logger.error(f"Force magnitude {force_magnitude} exceeds safety limit {max_force}")
            return False
        
        return True
    
    def _on_collision(self, collision: CollisionInfo) -> None:
        """Handle collision events."""
        self.logger.debug(f"Collision detected: {collision.body_a_id} <-> {collision.body_b_id}")
        
        # Notify collision callbacks
        for callback in self.collision_callbacks:
            try:
                callback(collision)
            except Exception as e:
                self.logger.error(f"Collision callback error: {e}")