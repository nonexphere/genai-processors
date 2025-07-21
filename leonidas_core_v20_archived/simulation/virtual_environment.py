"""
Virtual Environment

Configurable virtual environment for testing robot interactions.
"""

import asyncio
import logging
import time
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Callable
import threading

from .physical_simulator import Vector3, Quaternion, RigidBody, CollisionShape, CollisionInfo


class EnvironmentType(Enum):
    """Types of virtual environments."""
    EMPTY = "empty"                    # Empty space
    OFFICE = "office"                  # Office environment
    WAREHOUSE = "warehouse"            # Warehouse environment
    HOME = "home"                      # Home environment
    LABORATORY = "laboratory"          # Laboratory environment
    OUTDOOR = "outdoor"                # Outdoor environment
    CUSTOM = "custom"                  # Custom environment


class ObjectType(Enum):
    """Types of objects in the environment."""
    STATIC = "static"                  # Static objects (walls, furniture)
    DYNAMIC = "dynamic"                # Dynamic objects (boxes, tools)
    INTERACTIVE = "interactive"        # Interactive objects (buttons, doors)
    HAZARD = "hazard"                  # Hazardous objects (obstacles, dangers)


@dataclass
class EnvironmentObject:
    """Object in the virtual environment."""
    object_id: str
    name: str
    object_type: ObjectType
    rigid_body: RigidBody
    interactive: bool = False
    properties: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "object_id": self.object_id,
            "name": self.name,
            "object_type": self.object_type.value,
            "rigid_body": self.rigid_body.to_dict(),
            "interactive": self.interactive,
            "properties": self.properties,
        }


@dataclass
class EnvironmentConfig:
    """Configuration for virtual environment."""
    environment_type: EnvironmentType
    gravity: Vector3 = field(default_factory=lambda: Vector3(0, 0, -9.81))
    bounds: Tuple[Vector3, Vector3] = field(default_factory=lambda: (Vector3(-10, -10, 0), Vector3(10, 10, 5)))
    lighting: Dict[str, Any] = field(default_factory=dict)
    weather: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "environment_type": self.environment_type.value,
            "gravity": self.gravity.to_list(),
            "bounds": [self.bounds[0].to_list(), self.bounds[1].to_list()],
            "lighting": self.lighting,
            "weather": self.weather,
        }


class VirtualEnvironment:
    """
    Virtual environment for robot testing and simulation.
    
    Provides:
    - Configurable environment types
    - Static and dynamic objects
    - Interactive elements
    - Environmental hazards
    - Scenario scripting
    """
    
    def __init__(self, 
                 environment_id: str,
                 config: EnvironmentConfig):
        """
        Initialize virtual environment.
        
        Args:
            environment_id: Unique identifier for this environment
            config: Environment configuration
        """
        self.environment_id = environment_id
        self.config = config
        
        # Environment objects
        self.objects: Dict[str, EnvironmentObject] = {}
        self.interactive_objects: Dict[str, EnvironmentObject] = {}
        
        # Scenario management
        self.active_scenarios: List['Scenario'] = []
        self.scenario_callbacks: List[Callable[['ScenarioEvent'], None]] = []
        
        # Environment state
        self.is_active = False
        self.simulation_time = 0.0
        
        # Threading
        self._update_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()
        self._lock = threading.RLock()
        
        # Callbacks
        self.object_callbacks: List[Callable[[str, EnvironmentObject], None]] = []
        self.collision_callbacks: List[Callable[[CollisionInfo], None]] = []
        
        # Metrics
        self.environment_metrics = {
            "objects_count": 0,
            "interactions_count": 0,
            "collisions_count": 0,
            "scenarios_executed": 0,
        }
        
        # Logging
        self.logger = logging.getLogger(f"leonidas.environment.{environment_id}")
    
    async def start(self) -> None:
        """Start virtual environment."""
        if self.is_active:
            self.logger.warning("Environment already active")
            return
        
        self.logger.info(f"Starting virtual environment {self.environment_id}")
        
        try:
            # Initialize environment
            await self._initialize_environment()
            
            # Start update loop
            self._update_task = asyncio.create_task(self._update_loop())
            self.is_active = True
            
            self.logger.info(f"Virtual environment {self.environment_id} started")
            
        except Exception as e:
            self.logger.error(f"Failed to start virtual environment: {e}")
            raise
    
    async def stop(self) -> None:
        """Stop virtual environment."""
        if not self.is_active:
            return
        
        self.logger.info(f"Stopping virtual environment {self.environment_id}")
        
        # Signal shutdown
        self._shutdown_event.set()
        self.is_active = False
        
        # Cancel update task
        if self._update_task:
            self._update_task.cancel()
            try:
                await self._update_task
            except asyncio.CancelledError:
                pass
        
        # Cleanup environment
        await self._cleanup_environment()
        
        self.logger.info(f"Virtual environment {self.environment_id} stopped")
    
    def add_object(self, env_object: EnvironmentObject) -> bool:
        """Add object to environment."""
        try:
            with self._lock:
                if env_object.object_id in self.objects:
                    self.logger.warning(f"Object {env_object.object_id} already exists")
                    return False
                
                self.objects[env_object.object_id] = env_object
                
                if env_object.interactive:
                    self.interactive_objects[env_object.object_id] = env_object
                
                self.environment_metrics["objects_count"] = len(self.objects)
                
                self.logger.debug(f"Added object: {env_object.object_id}")
                return True
        except Exception as e:
            self.logger.error(f"Failed to add object {env_object.object_id}: {e}")
            return False
    
    def remove_object(self, object_id: str) -> bool:
        """Remove object from environment."""
        try:
            with self._lock:
                if object_id not in self.objects:
                    self.logger.warning(f"Object {object_id} not found")
                    return False
                
                env_object = self.objects[object_id]
                del self.objects[object_id]
                
                if object_id in self.interactive_objects:
                    del self.interactive_objects[object_id]
                
                self.environment_metrics["objects_count"] = len(self.objects)
                
                self.logger.debug(f"Removed object: {object_id}")
                return True
        except Exception as e:
            self.logger.error(f"Failed to remove object {object_id}: {e}")
            return False
    
    def get_object(self, object_id: str) -> Optional[EnvironmentObject]:
        """Get object by ID."""
        with self._lock:
            return self.objects.get(object_id)
    
    def get_objects_by_type(self, object_type: ObjectType) -> List[EnvironmentObject]:
        """Get all objects of a specific type."""
        with self._lock:
            return [obj for obj in self.objects.values() if obj.object_type == object_type]
    
    def get_objects_in_area(self, center: Vector3, radius: float) -> List[EnvironmentObject]:
        """Get all objects within a spherical area."""
        with self._lock:
            objects_in_area = []
            for obj in self.objects.values():
                distance = (obj.rigid_body.position - center).magnitude()
                if distance <= radius:
                    objects_in_area.append(obj)
            return objects_in_area
    
    def interact_with_object(self, object_id: str, interaction_type: str, parameters: Dict[str, Any] = None) -> bool:
        """Interact with an object in the environment."""
        try:
            with self._lock:
                if object_id not in self.interactive_objects:
                    self.logger.error(f"Object {object_id} is not interactive")
                    return False
                
                env_object = self.interactive_objects[object_id]
                
                # Process interaction based on type
                success = self._process_interaction(env_object, interaction_type, parameters or {})
                
                if success:
                    self.environment_metrics["interactions_count"] += 1
                    
                    # Notify callbacks
                    for callback in self.object_callbacks:
                        try:
                            callback(object_id, env_object)
                        except Exception as e:
                            self.logger.error(f"Object callback error: {e}")
                
                return success
        except Exception as e:
            self.logger.error(f"Failed to interact with object {object_id}: {e}")
            return False
    
    def add_scenario(self, scenario: 'Scenario') -> bool:
        """Add scenario to environment."""
        try:
            with self._lock:
                self.active_scenarios.append(scenario)
                scenario.environment = self
                self.logger.info(f"Added scenario: {scenario.scenario_id}")
                return True
        except Exception as e:
            self.logger.error(f"Failed to add scenario: {e}")
            return False
    
    def remove_scenario(self, scenario_id: str) -> bool:
        """Remove scenario from environment."""
        try:
            with self._lock:
                for i, scenario in enumerate(self.active_scenarios):
                    if scenario.scenario_id == scenario_id:
                        del self.active_scenarios[i]
                        self.logger.info(f"Removed scenario: {scenario_id}")
                        return True
                return False
        except Exception as e:
            self.logger.error(f"Failed to remove scenario {scenario_id}: {e}")
            return False
    
    def get_environment_status(self) -> Dict[str, Any]:
        """Get comprehensive environment status."""
        with self._lock:
            return {
                "environment_id": self.environment_id,
                "config": self.config.to_dict(),
                "is_active": self.is_active,
                "simulation_time": self.simulation_time,
                "objects_count": len(self.objects),
                "interactive_objects_count": len(self.interactive_objects),
                "active_scenarios_count": len(self.active_scenarios),
                "metrics": self.environment_metrics.copy(),
            }
    
    def add_object_callback(self, callback: Callable[[str, EnvironmentObject], None]) -> None:
        """Add callback for object interactions."""
        self.object_callbacks.append(callback)
    
    def add_collision_callback(self, callback: Callable[[CollisionInfo], None]) -> None:
        """Add callback for collisions."""
        self.collision_callbacks.append(callback)
    
    def add_scenario_callback(self, callback: Callable[['ScenarioEvent'], None]) -> None:
        """Add callback for scenario events."""
        self.scenario_callbacks.append(callback)
    
    # Private methods
    async def _initialize_environment(self) -> None:
        """Initialize environment based on type."""
        if self.config.environment_type == EnvironmentType.OFFICE:
            await self._create_office_environment()
        elif self.config.environment_type == EnvironmentType.WAREHOUSE:
            await self._create_warehouse_environment()
        elif self.config.environment_type == EnvironmentType.HOME:
            await self._create_home_environment()
        elif self.config.environment_type == EnvironmentType.LABORATORY:
            await self._create_laboratory_environment()
        elif self.config.environment_type == EnvironmentType.OUTDOOR:
            await self._create_outdoor_environment()
        else:
            # Empty environment - no objects added
            pass
        
        self.logger.debug(f"Initialized {self.config.environment_type.value} environment")
    
    async def _cleanup_environment(self) -> None:
        """Cleanup environment resources."""
        with self._lock:
            self.objects.clear()
            self.interactive_objects.clear()
            self.active_scenarios.clear()
    
    async def _update_loop(self) -> None:
        """Main environment update loop."""
        update_rate = 30  # Hz
        dt = 1.0 / update_rate
        
        while not self._shutdown_event.is_set():
            try:
                start_time = time.time()
                
                # Update simulation time
                self.simulation_time += dt
                
                # Update scenarios
                await self._update_scenarios(dt)
                
                # Update dynamic objects
                await self._update_dynamic_objects(dt)
                
                # Sleep to maintain update rate
                elapsed = time.time() - start_time
                sleep_time = dt - elapsed
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Environment update loop error: {e}")
                await asyncio.sleep(dt)
    
    async def _update_scenarios(self, dt: float) -> None:
        """Update active scenarios."""
        with self._lock:
            for scenario in self.active_scenarios[:]:  # Copy list to avoid modification during iteration
                try:
                    await scenario.update(dt)
                    if scenario.is_completed():
                        self.active_scenarios.remove(scenario)
                        self.environment_metrics["scenarios_executed"] += 1
                except Exception as e:
                    self.logger.error(f"Scenario update error: {e}")
    
    async def _update_dynamic_objects(self, dt: float) -> None:
        """Update dynamic objects in the environment."""
        with self._lock:
            for obj in self.objects.values():
                if obj.object_type == ObjectType.DYNAMIC:
                    # Simple physics update (would be more complex in real implementation)
                    # Apply gravity
                    if not obj.rigid_body.is_static:
                        gravity_force = self.config.gravity * obj.rigid_body.mass
                        acceleration = gravity_force * (1.0 / obj.rigid_body.mass)
                        obj.rigid_body.linear_velocity = obj.rigid_body.linear_velocity + acceleration * dt
                        obj.rigid_body.position = obj.rigid_body.position + obj.rigid_body.linear_velocity * dt
                        
                        # Simple damping
                        obj.rigid_body.linear_velocity = obj.rigid_body.linear_velocity * 0.99
    
    def _process_interaction(self, env_object: EnvironmentObject, interaction_type: str, parameters: Dict[str, Any]) -> bool:
        """Process interaction with an object."""
        # Simple interaction processing - would be more complex in real implementation
        if interaction_type == "activate":
            env_object.properties["activated"] = True
            self.logger.debug(f"Activated object {env_object.object_id}")
            return True
        elif interaction_type == "deactivate":
            env_object.properties["activated"] = False
            self.logger.debug(f"Deactivated object {env_object.object_id}")
            return True
        elif interaction_type == "move":
            if "position" in parameters:
                new_position = Vector3(*parameters["position"])
                env_object.rigid_body.position = new_position
                self.logger.debug(f"Moved object {env_object.object_id} to {new_position.to_list()}")
                return True
        
        self.logger.warning(f"Unknown interaction type: {interaction_type}")
        return False
    
    # Environment creation methods
    async def _create_office_environment(self) -> None:
        """Create office environment with typical furniture and objects."""
        # Add floor
        floor = EnvironmentObject(
            object_id="floor",
            name="Floor",
            object_type=ObjectType.STATIC,
            rigid_body=RigidBody(
                body_id="floor",
                position=Vector3(0, 0, -0.1),
                collision_shape=CollisionShape.BOX,
                collision_params={"width": 20, "height": 20, "depth": 0.2},
                is_static=True
            )
        )
        self.add_object(floor)
        
        # Add desk
        desk = EnvironmentObject(
            object_id="desk",
            name="Office Desk",
            object_type=ObjectType.STATIC,
            rigid_body=RigidBody(
                body_id="desk",
                position=Vector3(2, 0, 0.4),
                collision_shape=CollisionShape.BOX,
                collision_params={"width": 1.5, "height": 0.8, "depth": 0.8},
                is_static=True
            )
        )
        self.add_object(desk)
        
        # Add interactive computer
        computer = EnvironmentObject(
            object_id="computer",
            name="Computer",
            object_type=ObjectType.INTERACTIVE,
            rigid_body=RigidBody(
                body_id="computer",
                position=Vector3(2, 0, 0.9),
                collision_shape=CollisionShape.BOX,
                collision_params={"width": 0.4, "height": 0.3, "depth": 0.2},
                is_static=True
            ),
            interactive=True,
            properties={"powered": False, "screen_on": False}
        )
        self.add_object(computer)
    
    async def _create_warehouse_environment(self) -> None:
        """Create warehouse environment with shelves and boxes."""
        # Add floor
        floor = EnvironmentObject(
            object_id="floor",
            name="Warehouse Floor",
            object_type=ObjectType.STATIC,
            rigid_body=RigidBody(
                body_id="floor",
                position=Vector3(0, 0, -0.1),
                collision_shape=CollisionShape.BOX,
                collision_params={"width": 50, "height": 50, "depth": 0.2},
                is_static=True
            )
        )
        self.add_object(floor)
        
        # Add shelving units
        for i in range(5):
            shelf = EnvironmentObject(
                object_id=f"shelf_{i}",
                name=f"Shelf Unit {i+1}",
                object_type=ObjectType.STATIC,
                rigid_body=RigidBody(
                    body_id=f"shelf_{i}",
                    position=Vector3(i * 4 - 8, 0, 1.0),
                    collision_shape=CollisionShape.BOX,
                    collision_params={"width": 2, "height": 0.5, "depth": 2},
                    is_static=True
                )
            )
            self.add_object(shelf)
        
        # Add dynamic boxes
        for i in range(10):
            box = EnvironmentObject(
                object_id=f"box_{i}",
                name=f"Storage Box {i+1}",
                object_type=ObjectType.DYNAMIC,
                rigid_body=RigidBody(
                    body_id=f"box_{i}",
                    position=Vector3(
                        random.uniform(-8, 8),
                        random.uniform(-8, 8),
                        random.uniform(0.5, 2.0)
                    ),
                    collision_shape=CollisionShape.BOX,
                    collision_params={"width": 0.5, "height": 0.5, "depth": 0.5},
                    mass=10.0
                )
            )
            self.add_object(box)
    
    async def _create_home_environment(self) -> None:
        """Create home environment with furniture and appliances."""
        # Implementation would add typical home objects
        pass
    
    async def _create_laboratory_environment(self) -> None:
        """Create laboratory environment with equipment and instruments."""
        # Implementation would add lab equipment
        pass
    
    async def _create_outdoor_environment(self) -> None:
        """Create outdoor environment with terrain and obstacles."""
        # Implementation would add outdoor elements
        pass


@dataclass
class ScenarioEvent:
    """Event that occurs during a scenario."""
    event_id: str
    event_type: str
    timestamp: float
    data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp,
            "data": self.data,
        }


class Scenario:
    """Base class for environment scenarios."""
    
    def __init__(self, scenario_id: str, name: str):
        self.scenario_id = scenario_id
        self.name = name
        self.environment: Optional[VirtualEnvironment] = None
        self.start_time = 0.0
        self.duration = 0.0
        self.completed = False
        self.events: List[ScenarioEvent] = []
    
    async def start(self) -> None:
        """Start the scenario."""
        self.start_time = time.time()
        await self._on_start()
    
    async def update(self, dt: float) -> None:
        """Update scenario state."""
        self.duration += dt
        await self._on_update(dt)
    
    async def stop(self) -> None:
        """Stop the scenario."""
        self.completed = True
        await self._on_stop()
    
    def is_completed(self) -> bool:
        """Check if scenario is completed."""
        return self.completed
    
    def emit_event(self, event_type: str, data: Dict[str, Any] = None) -> None:
        """Emit a scenario event."""
        event = ScenarioEvent(
            event_id=f"{self.scenario_id}_{len(self.events)}",
            event_type=event_type,
            timestamp=time.time(),
            data=data or {}
        )
        
        self.events.append(event)
        
        # Notify environment callbacks
        if self.environment:
            for callback in self.environment.scenario_callbacks:
                try:
                    callback(event)
                except Exception as e:
                    logging.error(f"Scenario callback error: {e}")
    
    # Abstract methods to be implemented by subclasses
    async def _on_start(self) -> None:
        """Called when scenario starts."""
        pass
    
    async def _on_update(self, dt: float) -> None:
        """Called each update cycle."""
        pass
    
    async def _on_stop(self) -> None:
        """Called when scenario stops."""
        pass