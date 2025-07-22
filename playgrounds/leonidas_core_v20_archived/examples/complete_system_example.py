#!/usr/bin/env python3
# Copyright 2025 Leonidas Core v2.0
# Licensed under the Apache License, Version 2.0

"""
Complete System Example - Demonstrates the full Leonidas Core v2.0 capabilities

This example showcases:
- Multi-modal stream processing (SITM)
- Robot control and safety monitoring (RAL)
- Multi-display media control
- Event-driven architecture
- Physical simulation
- Hot-swappable modules
- Resilient component architecture
"""

import asyncio
import logging
import time
from typing import Dict, Any

# Core components
from leonidas_core_v2 import (
    # Core
    ResilientComponent, HotSwappableModule, StreamProcessor,
    SafetyAwareComponent, DistributedConfiguration,
    # SITM
    SITMService,
    # RAL
    RobotController, DeviceManager, SafetyMonitor,
    CameraSensor, MicrophoneSensor, ServoMotor,
    # Media
    DisplayManager,
    # Simulation
    PhysicalSimulator, VirtualRobot, VirtualEnvironment,
)

# Additional components
from leonidas_core_v2.events import EventBus, Event, EventPriority
from leonidas_core_v2.media import ContentRenderer
from leonidas_core_v2.ral import (
    DeviceInfo, DeviceType, SensorConfiguration, SensorType,
    RobotCapabilities, ActuatorLimits, SafetyRule, SafetyLevel, SafetyViolationType
)
from leonidas_core_v2.media import DisplayInfo, DisplayType, RenderContext, RenderQuality


class LeonidasCoreSystem(ResilientComponent):
    """
    Complete Leonidas Core v2.0 system demonstrating all capabilities
    """
    
    def __init__(self):
        super().__init__("leonidas_core_system")
        
        # Core components
        self.event_bus = EventBus()
        self.config_manager = DistributedConfiguration("system_config")
        
        # SITM Service
        self.sitm_service = SITMService()
        
        # RAL Components
        self.device_manager = DeviceManager()
        self.safety_monitor = SafetyMonitor()
        self.robot_controller = None  # Will be initialized
        
        # Media components
        self.display_manager = DisplayManager()
        self.content_renderer = ContentRenderer()
        
        # Simulation components
        self.physical_simulator = PhysicalSimulator()
        self.virtual_environment = VirtualEnvironment("demo_environment")
        self.virtual_robot = None  # Will be initialized
        
        # System state
        self.is_running = False
        self.components_started = []
        
        logging.info("Leonidas Core v2.0 system initialized")
    
    async def start_system(self):
        """Start the complete system"""
        try:
            logging.info("Starting Leonidas Core v2.0 system...")
            
            # 1. Start core infrastructure
            await self._start_core_infrastructure()
            
            # 2. Initialize and start SITM service
            await self._start_sitm_service()
            
            # 3. Initialize RAL components
            await self._start_ral_components()
            
            # 4.