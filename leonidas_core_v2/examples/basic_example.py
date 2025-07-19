#!/usr/bin/env python3
"""
Basic Leonidas Core v2.0 Example

Demonstrates the fundamental components and their integration.
"""

import asyncio
import logging
import time
from typing import Dict, Any

from leonidas_core_v2 import (
    ResilientComponent,
    HotSwappableModule,
    StreamProcessor,
    SafetyAwareComponent,
    DistributedConfiguration,
    SITMService,
    PhysicalSimulator,
    VirtualRobot,
    VirtualEnvironment,
)

from leonidas_core_v2.core.hot_swappable_module import ModuleInfo, ModuleCapability, SystemInterface
from leonidas_core_v2.simulation.physical_simulator import RigidBody, CollisionShape, Vector3, ForceCommand
from leonidas_core_v2.simulation.virtual_robot import Joint, JointType, Link, JointLimits, ActuatorType
from leonidas_core_v2.simulation.virtual_environment import EnvironmentConfig, EnvironmentType, EnvironmentObject, ObjectType


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class ExampleModule(HotSwappableModule):
    """Example hot-swappable module."""
    
    def __init__(self):
        module_info = ModuleInfo(
            module_id="example_module",
            name="Example Module",
            version="1.0.0",
            capabilities=[ModuleCapability.TEXT_PROCESSING],
            description="Example module for demonstration",
        )
        super().__init__(module_info)
    
    async def _on_connect(self) -> None:
        """Called when module connects to system."""
        self.logger.info("Example module connected")
    
    async def _on_disconnect(self) -> None:
        """Called when module disconnects from system."""
        self.logger.info("Example module disconnected")
    
    async def _on_activate(self) -> None:
        """Called when module is activated."""
        self.logger.info("Example module activated")
    
    async def _on_suspend(self) -> None:
        """Called when module is suspended."""
        self.logger.info("Example module suspended")
    
    async def _on_configure(self, configuration: Dict[str, Any]) -> None:
        """Called when module configuration is updated."""
        self.logger.info(f"Example module configured: {configuration}")
    
    async def _on_message(self, message: Dict[str, Any]) -> Any:
        """Called to process incoming messages."""
        self.logger.info(f"Example module received message: {message}")
        return {"status": "processed", "message": message}


class ExampleSafetyComponent(SafetyAwareComponent):
    """Example safety-aware component."""
    
    async def _initialize_safety_system(self) -> None:
        """Initialize component-specific safety system."""
        self.logger.info("Safety system initialized")
    
    async def _cleanup_safety_system(self) -> None:
        """Cleanup component-specific safety system."""
        self.logger.info("Safety system cleaned up")
    
    async def _check_constraint(self, constraint, action) -> None:
        """Check if action violates safety constraint."""
        # Simple example - always pass
        return None
    
    async def _execute_emergency_stop(self, reason: str) -> None:
        """Execute component-specific emergency stop procedures."""
        self.logger.critical(f"Emergency stop executed: {reason}")
    
    async def _reset_from_emergency_stop(self) -> None:
        """Reset component from emergency stop state."""
        self.logger.info("Reset from emergency stop")
    
    async def _perform_safety_check(self) -> list:
        """Perform comprehensive safety check."""
        # Simple example - no violations
        return []


async def demonstrate_basic_components():
    """Demonstrate basic Leonidas Core v2.0 components."""
    print("\n=== Leonidas Core v2.0 Basic Components Demo ===\n")
    
    # 1. Distributed Configuration
    print("1. Testing Distributed Configuration...")
    config = DistributedConfiguration("demo_component")
    await config.start()
    
    # Set some configuration values
    config.set("demo_setting", "hello_world", description="Demo setting")
    config.set("numeric_setting", 42, description="Numeric demo setting")
    
    print(f"   Demo setting: {config.get('demo_setting')}")
    print(f"   Numeric setting: {config.get('numeric_setting')}")
    print(f"   Configuration metrics: {config.get_metrics()}")
    
    await config.stop()
    print("   ✓ Configuration system tested\n")
    
    # 2. Safety-Aware Component
    print("2. Testing Safety-Aware Component...")
    safety_component = ExampleSafetyComponent("demo_safety")
    await safety_component.start_safety_monitoring()
    
    # Get safety status
    status = safety_component.get_safety_status()
    print(f"   Safety status: {status['safety_state']['overall_safety_level']}")
    
    await safety_component.stop_safety_monitoring()
    print("   ✓ Safety system tested\n")
    
    # 3. Physical Simulator
    print("3. Testing Physical Simulator...")
    simulator = PhysicalSimulator("demo_simulator")
    await simulator.start()
    
    # Add a simple rigid body
    test_body = RigidBody(
        body_id="test_sphere",
        position=Vector3(0, 0, 5),
        collision_shape=CollisionShape.SPHERE,
        collision_params={"radius": 0.5},
        mass=1.0
    )
    
    success = simulator.add_rigid_body(test_body)
    print(f"   Added rigid body: {success}")
    
    # Apply a force
    force_cmd = ForceCommand(
        body_id="test_sphere",
        force=Vector3(10, 0, 0),
        duration=1.0
    )
    
    success = simulator.apply_force(force_cmd)
    print(f"   Applied force: {success}")
    
    # Let simulation run for a bit
    await asyncio.sleep(2)
    
    # Get body state
    body_state = simulator.get_body_state("test_sphere")
    if body_state:
        print(f"   Body position: {body_state.position.to_list()}")
    
    metrics = simulator.get_simulation_metrics()
    print(f"   Simulation steps: {metrics['steps_executed']}")
    
    await simulator.stop()
    print("   ✓ Physical simulator tested\n")


async def demonstrate_virtual_robot():
    """Demonstrate virtual robot capabilities."""
    print("4. Testing Virtual Robot...")
    
    # Create virtual robot
    robot = VirtualRobot("demo_robot", "Demo Robot")
    
    # Add base link
    base_link = Link(
        link_id="base",
        name="Base Link",
        mass=10.0,
        collision_shape=CollisionShape.BOX,
        collision_params={"width": 0.5, "height": 0.5, "depth": 0.2}
    )
    robot.add_link(base_link)
    
    # Add arm link
    arm_link = Link(
        link_id="arm",
        name="Arm Link",
        mass=2.0,
        collision_shape=CollisionShape.CYLINDER,
        collision_params={"radius": 0.05, "height": 0.5}
    )
    robot.add_link(arm_link)
    
    # Add joint
    joint = Joint(
        joint_id="shoulder",
        joint_type=JointType.REVOLUTE,
        parent_link="base",
        child_link="arm",
        limits=JointLimits(min_position=-3.14, max_position=3.14),
        actuator_type=ActuatorType.SERVO
    )
    robot.add_joint(joint)
    
    # Start robot
    await robot.start()
    
    # Set joint target
    success = robot.set_joint_target("shoulder", 1.57)  # 90 degrees
    print(f"   Set joint target: {success}")
    
    # Let robot move
    await asyncio.sleep(2)
    
    # Get joint state
    joint_state = robot.get_joint_state("shoulder")
    if joint_state:
        print(f"   Joint position: {joint_state['position']:.3f} rad")
        print(f"   Joint target: {joint_state['target']:.3f} rad")
    
    # Get robot status
    status = robot.get_robot_status()
    print(f"   Robot joints: {status['joints_count']}")
    print(f"   Control cycles: {status['metrics']['control_cycles']}")
    
    await robot.stop()
    print("   ✓ Virtual robot tested\n")


async def demonstrate_virtual_environment():
    """Demonstrate virtual environment capabilities."""
    print("5. Testing Virtual Environment...")
    
    # Create environment configuration
    env_config = EnvironmentConfig(
        environment_type=EnvironmentType.OFFICE,
        gravity=Vector3(0, 0, -9.81)
    )
    
    # Create virtual environment
    environment = VirtualEnvironment("demo_environment", env_config)
    await environment.start()
    
    # Add a custom object
    custom_object = EnvironmentObject(
        object_id="demo_box",
        name="Demo Box",
        object_type=ObjectType.DYNAMIC,
        rigid_body=RigidBody(
            body_id="demo_box",
            position=Vector3(1, 1, 2),
            collision_shape=CollisionShape.BOX,
            collision_params={"width": 0.5, "height": 0.5, "depth": 0.5},
            mass=5.0
        )
    )
    
    success = environment.add_object(custom_object)
    print(f"   Added custom object: {success}")
    
    # Get objects in area
    objects_nearby = environment.get_objects_in_area(Vector3(0, 0, 1), 5.0)
    print(f"   Objects in area: {len(objects_nearby)}")
    
    # Get environment status
    status = environment.get_environment_status()
    print(f"   Environment type: {status['config']['environment_type']}")
    print(f"   Total objects: {status['objects_count']}")
    
    await environment.stop()
    print("   ✓ Virtual environment tested\n")


async def demonstrate_sitm_service():
    """Demonstrate SITM service capabilities."""
    print("6. Testing SITM Service...")
    
    # Create SITM service
    sitm = SITMService("demo_sitm", websocket_port=8766)
    await sitm.start()
    
    # Let it run briefly
    await asyncio.sleep(1)
    
    # Get status
    status = sitm.get_sitm_status()
    print(f"   SITM component state: {status['component_status']['state']}")
    print(f"   WebSocket connections: {status['websocket_connections']}")
    
    await sitm.stop()
    print("   ✓ SITM service tested\n")


async def main():
    """Main demonstration function."""
    print("Starting Leonidas Core v2.0 Demonstration...")
    print("=" * 50)
    
    try:
        # Demonstrate basic components
        await demonstrate_basic_components()
        
        # Demonstrate virtual robot
        await demonstrate_virtual_robot()
        
        # Demonstrate virtual environment
        await demonstrate_virtual_environment()
        
        # Demonstrate SITM service
        await demonstrate_sitm_service()
        
        print("=" * 50)
        print("✅ All demonstrations completed successfully!")
        print("\nLeonidas Core v2.0 is ready for development!")
        
    except Exception as e:
        print(f"❌ Demonstration failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())