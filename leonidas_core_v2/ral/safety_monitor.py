# Copyright 2025 Leonidas Core v2.0
# Licensed under the Apache License, Version 2.0

"""
Safety Monitor - Comprehensive safety monitoring for physical systems
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
import time
import json

from ..core.resilient_component import ResilientComponent


class SafetyLevel(Enum):
    """Safety alert levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class SafetyViolationType(Enum):
    """Types of safety violations"""
    POSITION_LIMIT = "position_limit"
    VELOCITY_LIMIT = "velocity_limit"
    FORCE_LIMIT = "force_limit"
    TEMPERATURE_LIMIT = "temperature_limit"
    CURRENT_LIMIT = "current_limit"
    WORKSPACE_BOUNDARY = "workspace_boundary"
    COLLISION_RISK = "collision_risk"
    COMMUNICATION_LOSS = "communication_loss"
    SENSOR_FAILURE = "sensor_failure"
    ACTUATOR_FAILURE = "actuator_failure"
    CUSTOM = "custom"


@dataclass
class SafetyRule:
    """Safety rule definition"""
    rule_id: str
    name: str
    description: str
    violation_type: SafetyViolationType
    condition: Callable[[Dict[str, Any]], bool]
    severity: SafetyLevel
    auto_response: bool = True
    response_action: Optional[str] = None
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SafetyViolation:
    """Safety violation record"""
    violation_id: str
    rule_id: str
    violation_type: SafetyViolationType
    severity: SafetyLevel
    message: str
    timestamp: float
    device_id: Optional[str] = None
    sensor_data: Dict[str, Any] = field(default_factory=dict)
    resolved: bool = False
    resolution_time: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SafetyZone:
    """Safety zone definition"""
    zone_id: str
    name: str
    boundaries: Dict[str, tuple]  # axis: (min, max)
    safety_level: SafetyLevel
    allowed_devices: Set[str] = field(default_factory=set)
    restricted_operations: List[str] = field(default_factory=list)
    monitoring_frequency: float = 10.0  # Hz


class SafetyMonitor(ResilientComponent):
    """
    Comprehensive safety monitoring system for physical operations
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("safety_monitor")
        
        self.config = config or {}
        
        # Safety rules and violations
        self.safety_rules: Dict[str, SafetyRule] = {}
        self.active_violations: Dict[str, SafetyViolation] = {}
        self.violation_history: List[SafetyViolation] = []
        
        # Safety zones
        self.safety_zones: Dict[str, SafetyZone] = {}
        
        # Monitored devices and sensors
        self.monitored_devices: Dict[str, Dict[str, Any]] = {}
        self.sensor_data: Dict[str, Any] = {}
        
        # Emergency response
        self.emergency_callbacks: List[Callable] = []
        self.emergency_active = False
        
        # Monitoring configuration
        self.monitoring_frequency = self.config.get('monitoring_frequency', 20.0)  # Hz
        self.violation_timeout = self.config.get('violation_timeout', 300.0)  # 5 minutes
        
        # Tasks
        self.monitoring_task: Optional[asyncio.Task] = None
        self.violation_cleanup_task: Optional[asyncio.Task] = None
        
        # Statistics
        self.stats = {
            'total_violations': 0,
            'critical_violations': 0,
            'emergency_stops': 0,
            'rules_checked': 0,
            'monitoring_cycles': 0,
            'last_violation_time': 0
        }
        
        logging.info("Safety monitor initialized")
    
    async def start_monitoring(self) -> bool:
        """Start safety monitoring"""
        try:
            # Load default safety rules
            await self._load_default_safety_rules()
            
            # Start monitoring tasks
            self.monitoring_task = asyncio.create_task(self._monitoring_loop())
            self.violation_cleanup_task = asyncio.create_task(self._violation_cleanup_loop())
            
            logging.info("Safety monitoring started")
            return True
            
        except Exception as e:
            logging.error(f"Failed to start safety monitoring: {e}")
            return False
    
    async def stop_monitoring(self):
        """Stop safety monitoring"""
        try:
            # Cancel tasks
            if self.monitoring_task:
                self.monitoring_task.cancel()
            if self.violation_cleanup_task:
                self.violation_cleanup_task.cancel()
            
            # Wait for tasks to complete
            await asyncio.gather(
                self.monitoring_task, self.violation_cleanup_task,
                return_exceptions=True
            )
            
            logging.info("Safety monitoring stopped")
            
        except Exception as e:
            logging.error(f"Error stopping safety monitoring: {e}")
    
    def add_safety_rule(self, rule: SafetyRule):
        """Add a safety rule"""
        self.safety_rules[rule.rule_id] = rule
        logging.info(f"Safety rule '{rule.name}' added")
    
    def remove_safety_rule(self, rule_id: str) -> bool:
        """Remove a safety rule"""
        if rule_id in self.safety_rules:
            del self.safety_rules[rule_id]
            logging.info(f"Safety rule {rule_id} removed")
            return True
        return False
    
    def enable_rule(self, rule_id: str) -> bool:
        """Enable a safety rule"""
        if rule_id in self.safety_rules:
            self.safety_rules[rule_id].enabled = True
            logging.info(f"Safety rule {rule_id} enabled")
            return True
        return False
    
    def disable_rule(self, rule_id: str) -> bool:
        """Disable a safety rule"""
        if rule_id in self.safety_rules:
            self.safety_rules[rule_id].enabled = False
            logging.info(f"Safety rule {rule_id} disabled")
            return True
        return False
    
    def add_safety_zone(self, zone: SafetyZone):
        """Add a safety zone"""
        self.safety_zones[zone.zone_id] = zone
        logging.info(f"Safety zone '{zone.name}' added")
    
    def register_device(self, device_id: str, device_info: Dict[str, Any]):
        """Register a device for monitoring"""
        self.monitored_devices[device_id] = device_info
        logging.info(f"Device {device_id} registered for safety monitoring")
    
    def unregister_device(self, device_id: str):
        """Unregister a device from monitoring"""
        if device_id in self.monitored_devices:
            del self.monitored_devices[device_id]
            logging.info(f"Device {device_id} unregistered from safety monitoring")
    
    def update_sensor_data(self, sensor_id: str, data: Any):
        """Update sensor data for monitoring"""
        self.sensor_data[sensor_id] = {
            'data': data,
            'timestamp': time.time()
        }
    
    def register_emergency_callback(self, callback: Callable):
        """Register callback for emergency situations"""
        self.emergency_callbacks.append(callback)
    
    async def trigger_emergency_stop(self, reason: str, device_id: Optional[str] = None):
        """Trigger emergency stop"""
        try:
            self.emergency_active = True
            self.stats['emergency_stops'] += 1
            
            # Create emergency violation
            violation = SafetyViolation(
                violation_id=f"emergency_{time.time()}",
                rule_id="emergency_stop",
                violation_type=SafetyViolationType.CUSTOM,
                severity=SafetyLevel.EMERGENCY,
                message=f"Emergency stop triggered: {reason}",
                timestamp=time.time(),
                device_id=device_id
            )
            
            await self._handle_violation(violation)
            
            # Notify emergency callbacks
            for callback in self.emergency_callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(violation)
                    else:
                        callback(violation)
                except Exception as e:
                    logging.error(f"Error in emergency callback: {e}")
            
            logging.critical(f"EMERGENCY STOP: {reason}")
            
        except Exception as e:
            logging.error(f"Error triggering emergency stop: {e}")
    
    async def reset_emergency(self) -> bool:
        """Reset from emergency state"""
        try:
            if not self.emergency_active:
                return True
            
            # Check if it's safe to reset
            if await self._check_emergency_reset_conditions():
                self.emergency_active = False
                
                # Resolve emergency violations
                for violation in self.active_violations.values():
                    if violation.severity == SafetyLevel.EMERGENCY:
                        violation.resolved = True
                        violation.resolution_time = time.time()
                
                logging.info("Emergency state reset")
                return True
            else:
                logging.warning("Emergency reset conditions not met")
                return False
                
        except Exception as e:
            logging.error(f"Error resetting emergency: {e}")
            return False
    
    def get_active_violations(self) -> List[SafetyViolation]:
        """Get all active violations"""
        return list(self.active_violations.values())
    
    def get_violations_by_severity(self, severity: SafetyLevel) -> List[SafetyViolation]:
        """Get violations by severity level"""
        return [v for v in self.active_violations.values() if v.severity == severity]
    
    def get_safety_status(self) -> Dict[str, Any]:
        """Get overall safety status"""
        active_violations = len(self.active_violations)
        critical_violations = len(self.get_violations_by_severity(SafetyLevel.CRITICAL))
        emergency_violations = len(self.get_violations_by_severity(SafetyLevel.EMERGENCY))
        
        if emergency_violations > 0 or self.emergency_active:
            status = "EMERGENCY"
        elif critical_violations > 0:
            status = "CRITICAL"
        elif active_violations > 0:
            status = "WARNING"
        else:
            status = "SAFE"
        
        return {
            'status': status,
            'active_violations': active_violations,
            'critical_violations': critical_violations,
            'emergency_violations': emergency_violations,
            'emergency_active': self.emergency_active,
            'monitored_devices': len(self.monitored_devices),
            'active_rules': len([r for r in self.safety_rules.values() if r.enabled]),
            'last_check': time.time()
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get safety monitoring statistics"""
        return self.stats.copy()
    
    async def _monitoring_loop(self):
        """Main safety monitoring loop"""
        while True:
            try:
                await self._check_all_safety_rules()
                await self._check_safety_zones()
                
                self.stats['monitoring_cycles'] += 1
                
                # Sleep based on monitoring frequency
                await asyncio.sleep(1.0 / self.monitoring_frequency)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"Error in safety monitoring loop: {e}")
                await asyncio.sleep(1.0)
    
    async def _check_all_safety_rules(self):
        """Check all enabled safety rules"""
        for rule in self.safety_rules.values():
            if not rule.enabled:
                continue
            
            try:
                # Prepare context data
                context = {
                    'sensor_data': self.sensor_data,
                    'device_data': self.monitored_devices,
                    'timestamp': time.time(),
                    'emergency_active': self.emergency_active
                }
                
                # Check rule condition
                if rule.condition(context):
                    await self._handle_rule_violation(rule, context)
                
                self.stats['rules_checked'] += 1
                
            except Exception as e:
                logging.error(f"Error checking safety rule {rule.rule_id}: {e}")
    
    async def _check_safety_zones(self):
        """Check safety zone violations"""
        for zone in self.safety_zones.values():
            try:
                # Check devices in this zone
                for device_id, device_info in self.monitored_devices.items():
                    if 'position' in device_info:
                        position = device_info['position']
                        
                        # Check if device is within zone boundaries
                        if not self._is_position_in_zone(position, zone):
                            await self._handle_zone_violation(device_id, zone)
                
            except Exception as e:
                logging.error(f"Error checking safety zone {zone.zone_id}: {e}")
    
    async def _handle_rule_violation(self, rule: SafetyRule, context: Dict[str, Any]):
        """Handle safety rule violation"""
        violation_id = f"{rule.rule_id}_{time.time()}"
        
        # Check if this violation is already active
        existing_violation = None
        for v in self.active_violations.values():
            if v.rule_id == rule.rule_id and not v.resolved:
                existing_violation = v
                break
        
        if existing_violation:
            # Update existing violation timestamp
            existing_violation.timestamp = time.time()
            return
        
        # Create new violation
        violation = SafetyViolation(
            violation_id=violation_id,
            rule_id=rule.rule_id,
            violation_type=rule.violation_type,
            severity=rule.severity,
            message=f"Safety rule violation: {rule.name}",
            timestamp=time.time(),
            sensor_data=context.get('sensor_data', {})
        )
        
        await self._handle_violation(violation)
    
    async def _handle_zone_violation(self, device_id: str, zone: SafetyZone):
        """Handle safety zone violation"""
        violation_id = f"zone_{zone.zone_id}_{device_id}_{time.time()}"
        
        violation = SafetyViolation(
            violation_id=violation_id,
            rule_id=f"zone_{zone.zone_id}",
            violation_type=SafetyViolationType.WORKSPACE_BOUNDARY,
            severity=zone.safety_level,
            message=f"Device {device_id} outside safety zone {zone.name}",
            timestamp=time.time(),
            device_id=device_id
        )
        
        await self._handle_violation(violation)
    
    async def _handle_violation(self, violation: SafetyViolation):
        """Handle a safety violation"""
        try:
            # Add to active violations
            self.active_violations[violation.violation_id] = violation
            self.violation_history.append(violation)
            
            # Update statistics
            self.stats['total_violations'] += 1
            self.stats['last_violation_time'] = violation.timestamp
            
            if violation.severity == SafetyLevel.CRITICAL:
                self.stats['critical_violations'] += 1
            
            # Log violation
            log_level = {
                SafetyLevel.INFO: logging.info,
                SafetyLevel.WARNING: logging.warning,
                SafetyLevel.CRITICAL: logging.error,
                SafetyLevel.EMERGENCY: logging.critical
            }[violation.severity]
            
            log_level(f"SAFETY VIOLATION: {violation.message}")
            
            # Execute automatic response if configured
            if violation.rule_id in self.safety_rules:
                rule = self.safety_rules[violation.rule_id]
                if rule.auto_response and rule.response_action:
                    await self._execute_response_action(rule.response_action, violation)
            
            # Trigger emergency if severity is emergency
            if violation.severity == SafetyLevel.EMERGENCY:
                self.emergency_active = True
            
        except Exception as e:
            logging.error(f"Error handling violation: {e}")
    
    async def _execute_response_action(self, action: str, violation: SafetyViolation):
        """Execute automatic response action"""
        try:
            if action == "emergency_stop":
                await self.trigger_emergency_stop(f"Auto response to {violation.message}")
            elif action == "stop_device":
                if violation.device_id:
                    # This would send stop command to specific device
                    logging.info(f"Stopping device {violation.device_id} due to safety violation")
            elif action == "alert_only":
                # Just log and alert, no automatic action
                pass
            else:
                logging.warning(f"Unknown response action: {action}")
                
        except Exception as e:
            logging.error(f"Error executing response action {action}: {e}")
    
    async def _violation_cleanup_loop(self):
        """Clean up resolved and expired violations"""
        while True:
            try:
                current_time = time.time()
                expired_violations = []
                
                for violation_id, violation in self.active_violations.items():
                    # Check if violation has expired
                    if current_time - violation.timestamp > self.violation_timeout:
                        violation.resolved = True
                        violation.resolution_time = current_time
                        expired_violations.append(violation_id)
                
                # Remove expired violations
                for violation_id in expired_violations:
                    del self.active_violations[violation_id]
                    logging.info(f"Violation {violation_id} expired and removed")
                
                # Limit violation history size
                if len(self.violation_history) > 1000:
                    self.violation_history = self.violation_history[-800:]
                
                await asyncio.sleep(60.0)  # Check every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"Error in violation cleanup: {e}")
                await asyncio.sleep(60.0)
    
    def _is_position_in_zone(self, position: Dict[str, float], zone: SafetyZone) -> bool:
        """Check if position is within safety zone"""
        for axis, value in position.items():
            if axis in zone.boundaries:
                min_val, max_val = zone.boundaries[axis]
                if not (min_val <= value <= max_val):
                    return False
        return True
    
    async def _check_emergency_reset_conditions(self) -> bool:
        """Check if conditions are met for emergency reset"""
        # Check if all emergency violations are resolved
        emergency_violations = self.get_violations_by_severity(SafetyLevel.EMERGENCY)
        if emergency_violations:
            return False
        
        # Check if all devices are in safe state
        for device_id, device_info in self.monitored_devices.items():
            if device_info.get('state') == 'error':
                return False
        
        # Additional safety checks can be added here
        return True
    
    async def _load_default_safety_rules(self):
        """Load default safety rules"""
        # Temperature limit rule
        temp_rule = SafetyRule(
            rule_id="temperature_limit",
            name="Temperature Limit",
            description="Check for overheating",
            violation_type=SafetyViolationType.TEMPERATURE_LIMIT,
            condition=lambda ctx: any(
                sensor.get('data', 0) > 80 
                for sensor in ctx['sensor_data'].values() 
                if 'temperature' in str(sensor)
            ),
            severity=SafetyLevel.CRITICAL,
            auto_response=True,
            response_action="emergency_stop"
        )
        self.add_safety_rule(temp_rule)
        
        # Communication loss rule
        comm_rule = SafetyRule(
            rule_id="communication_loss",
            name="Communication Loss",
            description="Check for device communication loss",
            violation_type=SafetyViolationType.COMMUNICATION_LOSS,
            condition=lambda ctx: any(
                ctx['timestamp'] - sensor.get('timestamp', ctx['timestamp']) > 5.0
                for sensor in ctx['sensor_data'].values()
            ),
            severity=SafetyLevel.WARNING,
            auto_response=False
        )
        self.add_safety_rule(comm_rule)