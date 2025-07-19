# Copyright 2025 Leonidas Core v2.0
# Licensed under the Apache License, Version 2.0

"""
Leonidas Core v2.0 - Universal AI Platform

A comprehensive AI platform that transforms Leonidas from a software collaborator
into a universal AI core capable of physical world interaction, multi-modal
data processing, and distributed system management.

Key Features:
- Multi-modal stream ingestion and synchronization (SITM)
- Hot-swappable module architecture
- Physical world interaction capabilities (RAL)
- Multi-display media control
- Distributed system resilience
"""

__version__ = "2.0.0"
__author__ = "Leonidas Core Team"

# Core components
from .core.resilient_component import ResilientComponent
from .core.hot_swappable_module import HotSwappableModule
from .core.stream_processor import StreamProcessor
from .core.safety_aware_component import SafetyAwareComponent
from .core.distributed_configuration import DistributedConfiguration

# SITM Service
from .sitm.sitm_service import SITMService

# Robot Abstraction Layer (RAL)
from .ral.robot_controller import RobotController
from .ral.device_manager import DeviceManager
from .ral.sensor_interface import SensorInterface, CameraSensor, MicrophoneSensor
from .ral.actuator_interface import ActuatorInterface, ServoMotor
from .ral.safety_monitor import SafetyMonitor

# Media Control
from .media.display_manager import DisplayManager

# Physical simulation
from .simulation.physical_simulator import PhysicalSimulator
from .simulation.virtual_robot import VirtualRobot
from .simulation.virtual_environment import VirtualEnvironment

__all__ = [
    # Core
    "ResilientComponent",
    "HotSwappableModule", 
    "StreamProcessor",
    "SafetyAwareComponent",
    "DistributedConfiguration",
    # SITM
    "SITMService",
    # RAL
    "RobotController",
    "DeviceManager",
    "SensorInterface",
    "CameraSensor", 
    "MicrophoneSensor",
    "ActuatorInterface",
    "ServoMotor",
    "SafetyMonitor",
    # Media
    "DisplayManager",
    # Simulation
    "PhysicalSimulator",
    "VirtualRobot",
    "VirtualEnvironment",
]