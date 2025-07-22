"""
Safety-Aware Component Base Class

Provides comprehensive safety validation and monitoring for physical system components.
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Callable, Set
import threading
import json


class SafetyLevel(Enum):
    """Safety criticality levels."""
    SAFE = "safe"
    CAUTION = "caution"
    WARNING = "warning"
    DANGER = "danger"
    CRITICAL = "critical"


class SafetyViolationType(Enum):
    """Types of safety violations."""
    COLLISION_RISK = "collision_risk"
    FORCE_LIMIT_EXCEEDED = "force_limit_exceeded"
    SPEED_LIMIT_EXCEEDED = "speed_limit_exceeded"
    WORKSPACE_VIOLATION = "workspace_violation"
    TEMPERATURE_LIMIT = "temperature_limit"
    POWER_LIMIT = "power_limit"
    COMMUNICATION_LOSS = "communication_loss"
    SENSOR_FAILURE = "sensor_failure"
    ACTUATOR_FAILURE = "actuator_failure"
    EMERGENCY_STOP = "emergency_stop"


@dataclass
class SafetyConstraint:
    """Definition of a safety constraint."""
    constraint_id: str
    name: str
    description: str
    safety_level: SafetyLevel
    violation_type: SafetyViolationType
    parameters: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "constraint_id": self.constraint_id,
            "name": self.name,
            "description": self.description,
            "safety_level": self.safety_level.value,
            "violation_type": self.violation_type.value,
            "parameters": self.parameters,
            "enabled": self.enabled,
        }


@dataclass
class SafetyViolation:
    """Record of a safety violation."""
    violation_id: str
    constraint_id: str
    violation_type: SafetyViolationType
    safety_level: SafetyLevel
    timestamp: float
    description: str
    data: Dict[str, Any] = field(default_factory=dict)
    resolved: bool = False
    resolution_time: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "violation_id": self.violation_id,
            "constraint_id": self.constraint_id,
            "violation_type": self.violation_type.value,
            "safety_level": self.safety_level.value,
            "timestamp": self.timestamp,
            "description": self.description,
            "data": self.data,
            "resolved": self.resolved,
            "resolution_time": self.resolution_time,
        }


@dataclass
class SafetyState:
    """Current safety state of the system."""
    overall_safety_level: SafetyLevel = SafetyLevel.SAFE
    active_violations: List[SafetyViolation] = field(default_factory=list)
    emergency_stop_active: bool = False
    last_safety_check: Optional[float] = None
    safety_system_healthy: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "overall_safety_level": self.overall_safety_level.value,
            "active_violations": [v.to_dict() for v in self.active_violations],
            "emergency_stop_active": self.emergency_stop_active,
            "last_safety_check": self.last_safety_check,
            "safety_system_healthy": self.safety_system_healthy,
        }


class SafetyAwareComponent(ABC):
    """
    Base class for safety-aware components in physical systems.
    
    Provides:
    - Safety constraint definition and validation
    - Real-time safety monitoring
    - Emergency stop mechanisms
    - Safety violation tracking and reporting
    - Predictive safety analysis
    """
    
    def __init__(self, 
                 component_id: str,
                 safety_check_interval: float = 0.1,
                 emergency_stop_timeout: float = 1.0,
                 violation_history_size: int = 1000):
        """
        Initialize safety-aware component.
        
        Args:
            component_id: Unique identifier for this component
            safety_check_interval: Seconds between safety checks
            emergency_stop_timeout: Maximum time for emergency stop response
            violation_history_size: Number of violations to keep in history
        """
        self.component_id = component_id
        self.safety_check_interval = safety_check_interval
        self.emergency_stop_timeout = emergency_stop_timeout
        self.violation_history_size = violation_history_size
        
        # Safety state
        self.safety_state = SafetyState()
        self.safety_constraints: Dict[str, SafetyConstraint] = {}
        self.violation_history: List[SafetyViolation] = []
        
        # Emergency stop
        self._emergency_stop_callbacks: List[Callable[[], None]] = []
        self._emergency_stop_event = asyncio.Event()
        
        # Monitoring
        self._safety_monitor_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()
        self._lock = threading.RLock()
        
        # Performance metrics
        self.safety_metrics = {
            "safety_checks_performed": 0,
            "violations_detected": 0,
            "emergency_stops_triggered": 0,
            "average_check_time": 0.0,
            "total_check_time": 0.0,
        }
        
        # Logging
        self.logger = logging.getLogger(f"leonidas.safety.{component_id}")
    
    async def start_safety_monitoring(self) -> None:
        """Start safety monitoring system."""
        self.logger.info(f"Starting safety monitoring for {self.component_id}")
        
        try:
            # Initialize safety system
            await self._initialize_safety_system()
            
            # Start monitoring task
            self._safety_monitor_task = asyncio.create_task(self._safety_monitor_loop())
            
            self.safety_state.safety_system_healthy = True
            self.logger.info(f"Safety monitoring started for {self.component_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to start safety monitoring for {self.component_id}: {e}")
            self.safety_state.safety_system_healthy = False
            raise
    
    async def stop_safety_monitoring(self) -> None:
        """Stop safety monitoring system."""
        self.logger.info(f"Stopping safety monitoring for {self.component_id}")
        
        # Signal shutdown
        self._shutdown_event.set()
        
        # Cancel monitoring task
        if self._safety_monitor_task:
            self._safety_monitor_task.cancel()
            try:
                await self._safety_monitor_task
            except asyncio.CancelledError:
                pass
        
        # Cleanup safety system
        await self._cleanup_safety_system()
        
        self.safety_state.safety_system_healthy = False
        self.logger.info(f"Safety monitoring stopped for {self.component_id}")
    
    def add_safety_constraint(self, constraint: SafetyConstraint) -> bool:
        """
        Add safety constraint.
        
        Args:
            constraint: Safety constraint to add
            
        Returns:
            True if constraint added successfully, False otherwise
        """
        try:
            with self._lock:
                if constraint.constraint_id in self.safety_constraints:
                    self.logger.warning(f"Safety constraint {constraint.constraint_id} already exists")
                    return False
                
                self.safety_constraints[constraint.constraint_id] = constraint
                self.logger.info(f"Added safety constraint {constraint.constraint_id}")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to add safety constraint {constraint.constraint_id}: {e}")
            return False
    
    def remove_safety_constraint(self, constraint_id: str) -> bool:
        """
        Remove safety constraint.
        
        Args:
            constraint_id: ID of constraint to remove
            
        Returns:
            True if constraint removed successfully, False otherwise
        """
        try:
            with self._lock:
                if constraint_id not in self.safety_constraints:
                    self.logger.warning(f"Safety constraint {constraint_id} not found")
                    return False
                
                del self.safety_constraints[constraint_id]
                self.logger.info(f"Removed safety constraint {constraint_id}")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to remove safety constraint {constraint_id}: {e}")
            return False
    
    async def validate_action(self, action: Dict[str, Any]) -> tuple[bool, List[SafetyViolation]]:
        """
        Validate action against safety constraints.
        
        Args:
            action: Action to validate
            
        Returns:
            Tuple of (is_safe, list_of_violations)
        """
        violations = []
        
        try:
            with self._lock:
                for constraint in self.safety_constraints.values():
                    if not constraint.enabled:
                        continue
                    
                    # Check constraint
                    violation = await self._check_constraint(constraint, action)
                    if violation:
                        violations.append(violation)
            
            is_safe = len(violations) == 0
            
            # Log violations
            for violation in violations:
                self.logger.warning(f"Safety violation detected: {violation.description}")
                self._record_violation(violation)
            
            return is_safe, violations
            
        except Exception as e:
            self.logger.error(f"Error validating action: {e}")
            # Fail safe - reject action if validation fails
            return False, []
    
    async def emergency_stop(self, reason: str = "Manual emergency stop") -> None:
        """
        Trigger emergency stop.
        
        Args:
            reason: Reason for emergency stop
        """
        self.logger.critical(f"EMERGENCY STOP triggered for {self.component_id}: {reason}")
        
        with self._lock:
            self.safety_state.emergency_stop_active = True
            self.safety_state.overall_safety_level = SafetyLevel.CRITICAL
            self.safety_metrics["emergency_stops_triggered"] += 1
        
        # Signal emergency stop
        self._emergency_stop_event.set()
        
        # Execute emergency stop callbacks
        for callback in self._emergency_stop_callbacks:
            try:
                callback()
            except Exception as e:
                self.logger.error(f"Emergency stop callback error: {e}")
        
        # Perform component-specific emergency stop
        await self._execute_emergency_stop(reason)
    
    async def reset_emergency_stop(self) -> bool:
        """
        Reset emergency stop state.
        
        Returns:
            True if reset successful, False otherwise
        """
        try:
            self.logger.info(f"Resetting emergency stop for {self.component_id}")
            
            # Perform safety checks before reset
            if not await self._pre_reset_safety_check():
                self.logger.error("Pre-reset safety check failed")
                return False
            
            with self._lock:
                self.safety_state.emergency_stop_active = False
                self.safety_state.overall_safety_level = SafetyLevel.SAFE
            
            # Clear emergency stop event
            self._emergency_stop_event.clear()
            
            # Perform component-specific reset
            await self._reset_from_emergency_stop()
            
            self.logger.info(f"Emergency stop reset for {self.component_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to reset emergency stop for {self.component_id}: {e}")
            return False
    
    def add_emergency_stop_callback(self, callback: Callable[[], None]) -> None:
        """Add callback for emergency stop events."""
        self._emergency_stop_callbacks.append(callback)
    
    def get_safety_status(self) -> Dict[str, Any]:
        """Get current safety status."""
        with self._lock:
            return {
                "component_id": self.component_id,
                "safety_state": self.safety_state.to_dict(),
                "active_constraints": len([c for c in self.safety_constraints.values() if c.enabled]),
                "total_constraints": len(self.safety_constraints),
                "violation_history_count": len(self.violation_history),
                "safety_metrics": self.safety_metrics.copy(),
            }
    
    def get_violation_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent violation history."""
        with self._lock:
            recent_violations = self.violation_history[-limit:] if limit > 0 else self.violation_history
            return [v.to_dict() for v in recent_violations]
    
    # Abstract methods to be implemented by subclasses
    @abstractmethod
    async def _initialize_safety_system(self) -> None:
        """Initialize component-specific safety system."""
        pass
    
    @abstractmethod
    async def _cleanup_safety_system(self) -> None:
        """Cleanup component-specific safety system."""
        pass
    
    @abstractmethod
    async def _check_constraint(self, constraint: SafetyConstraint, action: Dict[str, Any]) -> Optional[SafetyViolation]:
        """
        Check if action violates safety constraint.
        
        Args:
            constraint: Safety constraint to check
            action: Action to validate
            
        Returns:
            SafetyViolation if violated, None otherwise
        """
        pass
    
    @abstractmethod
    async def _execute_emergency_stop(self, reason: str) -> None:
        """Execute component-specific emergency stop procedures."""
        pass
    
    @abstractmethod
    async def _reset_from_emergency_stop(self) -> None:
        """Reset component from emergency stop state."""
        pass
    
    @abstractmethod
    async def _perform_safety_check(self) -> List[SafetyViolation]:
        """
        Perform comprehensive safety check.
        
        Returns:
            List of detected violations
        """
        pass
    
    # Private methods
    async def _safety_monitor_loop(self) -> None:
        """Main safety monitoring loop."""
        while not self._shutdown_event.is_set():
            try:
                start_time = time.time()
                
                # Perform safety check
                violations = await self._perform_safety_check()
                
                # Process violations
                await self._process_violations(violations)
                
                # Update metrics
                check_time = time.time() - start_time
                self.safety_metrics["safety_checks_performed"] += 1
                self.safety_metrics["total_check_time"] += check_time
                self.safety_metrics["average_check_time"] = (
                    self.safety_metrics["total_check_time"] / 
                    self.safety_metrics["safety_checks_performed"]
                )
                
                # Update safety state
                with self._lock:
                    self.safety_state.last_safety_check = time.time()
                
                # Wait for next check
                await asyncio.sleep(self.safety_check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Safety monitor loop error: {e}")
                self.safety_state.safety_system_healthy = False
                await asyncio.sleep(self.safety_check_interval)
    
    async def _process_violations(self, violations: List[SafetyViolation]) -> None:
        """Process detected safety violations."""
        if not violations:
            return
        
        # Update metrics
        self.safety_metrics["violations_detected"] += len(violations)
        
        # Determine overall safety level
        max_level = SafetyLevel.SAFE
        for violation in violations:
            self._record_violation(violation)
            
            if violation.safety_level.value > max_level.value:
                max_level = violation.safety_level
        
        # Update safety state
        with self._lock:
            self.safety_state.overall_safety_level = max_level
            self.safety_state.active_violations = [
                v for v in self.safety_state.active_violations if not v.resolved
            ] + violations
        
        # Trigger emergency stop for critical violations
        critical_violations = [v for v in violations if v.safety_level == SafetyLevel.CRITICAL]
        if critical_violations:
            reasons = [v.description for v in critical_violations]
            await self.emergency_stop(f"Critical safety violations: {'; '.join(reasons)}")
    
    def _record_violation(self, violation: SafetyViolation) -> None:
        """Record safety violation in history."""
        with self._lock:
            self.violation_history.append(violation)
            
            # Limit history size
            if len(self.violation_history) > self.violation_history_size:
                self.violation_history = self.violation_history[-self.violation_history_size//2:]
    
    async def _pre_reset_safety_check(self) -> bool:
        """Perform safety check before resetting emergency stop."""
        try:
            # Check that all critical violations are resolved
            with self._lock:
                active_critical = [
                    v for v in self.safety_state.active_violations 
                    if v.safety_level == SafetyLevel.CRITICAL and not v.resolved
                ]
                
                if active_critical:
                    self.logger.error(f"Cannot reset: {len(active_critical)} critical violations still active")
                    return False
            
            # Perform comprehensive safety check
            violations = await self._perform_safety_check()
            critical_violations = [v for v in violations if v.safety_level == SafetyLevel.CRITICAL]
            
            if critical_violations:
                self.logger.error(f"Cannot reset: {len(critical_violations)} new critical violations detected")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Pre-reset safety check error: {e}")
            return False