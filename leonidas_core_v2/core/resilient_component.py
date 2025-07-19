"""
Resilient Component Base Class

Provides health monitoring, circuit breaker patterns, and automatic recovery
for distributed system components.
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional, Callable, List
import threading


class ComponentState(Enum):
    """Component operational states."""
    INITIALIZING = "initializing"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILING = "failing"
    FAILED = "failed"
    RECOVERING = "recovering"


class CircuitBreakerState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, blocking requests
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class HealthMetrics:
    """Health monitoring metrics."""
    success_count: int = 0
    failure_count: int = 0
    last_success_time: Optional[float] = None
    last_failure_time: Optional[float] = None
    response_times: List[float] = field(default_factory=list)
    error_messages: List[str] = field(default_factory=list)
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        total = self.success_count + self.failure_count
        return self.success_count / total if total > 0 else 1.0
    
    @property
    def average_response_time(self) -> float:
        """Calculate average response time."""
        return sum(self.response_times) / len(self.response_times) if self.response_times else 0.0


class ResilientComponent(ABC):
    """
    Base class for resilient distributed system components.
    
    Provides:
    - Health monitoring and reporting
    - Circuit breaker pattern for fault tolerance
    - Automatic recovery mechanisms
    - Performance metrics collection
    - Graceful degradation capabilities
    """
    
    def __init__(self, 
                 component_id: str,
                 health_check_interval: float = 30.0,
                 failure_threshold: int = 5,
                 recovery_timeout: float = 60.0,
                 circuit_breaker_timeout: float = 30.0):
        """
        Initialize resilient component.
        
        Args:
            component_id: Unique identifier for this component
            health_check_interval: Seconds between health checks
            failure_threshold: Number of failures before circuit opens
            recovery_timeout: Seconds to wait before attempting recovery
            circuit_breaker_timeout: Seconds circuit stays open before half-open
        """
        self.component_id = component_id
        self.health_check_interval = health_check_interval
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.circuit_breaker_timeout = circuit_breaker_timeout
        
        # State management
        self.state = ComponentState.INITIALIZING
        self.circuit_state = CircuitBreakerState.CLOSED
        self.metrics = HealthMetrics()
        
        # Threading and async management
        self._lock = threading.RLock()
        self._health_check_task: Optional[asyncio.Task] = None
        self._recovery_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()
        
        # Callbacks
        self.state_change_callbacks: List[Callable[[ComponentState, ComponentState], None]] = []
        
        # Logging
        self.logger = logging.getLogger(f"leonidas.{component_id}")
    
    async def start(self) -> None:
        """Start the component and begin health monitoring."""
        try:
            self.logger.info(f"Starting component {self.component_id}")
            
            # Initialize component-specific resources
            await self._initialize()
            
            # Start health monitoring
            self._health_check_task = asyncio.create_task(self._health_check_loop())
            
            self._set_state(ComponentState.HEALTHY)
            self.logger.info(f"Component {self.component_id} started successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to start component {self.component_id}: {e}")
            self._set_state(ComponentState.FAILED)
            raise
    
    async def stop(self) -> None:
        """Stop the component gracefully."""
        self.logger.info(f"Stopping component {self.component_id}")
        
        # Signal shutdown
        self._shutdown_event.set()
        
        # Cancel health monitoring
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
        
        # Cancel recovery task
        if self._recovery_task:
            self._recovery_task.cancel()
            try:
                await self._recovery_task
            except asyncio.CancelledError:
                pass
        
        # Cleanup component-specific resources
        await self._cleanup()
        
        self._set_state(ComponentState.FAILED)
        self.logger.info(f"Component {self.component_id} stopped")
    
    async def execute_with_circuit_breaker(self, operation: Callable, *args, **kwargs) -> Any:
        """
        Execute operation with circuit breaker protection.
        
        Args:
            operation: Function to execute
            *args, **kwargs: Arguments for the operation
            
        Returns:
            Operation result
            
        Raises:
            CircuitBreakerOpenError: When circuit is open
        """
        if self.circuit_state == CircuitBreakerState.OPEN:
            # Check if we should transition to half-open
            if (time.time() - self.metrics.last_failure_time) > self.circuit_breaker_timeout:
                self.circuit_state = CircuitBreakerState.HALF_OPEN
                self.logger.info(f"Circuit breaker for {self.component_id} transitioning to half-open")
            else:
                raise CircuitBreakerOpenError(f"Circuit breaker open for {self.component_id}")
        
        start_time = time.time()
        try:
            # Execute operation
            if asyncio.iscoroutinefunction(operation):
                result = await operation(*args, **kwargs)
            else:
                result = operation(*args, **kwargs)
            
            # Record success
            response_time = time.time() - start_time
            self._record_success(response_time)
            
            # Close circuit if it was half-open
            if self.circuit_state == CircuitBreakerState.HALF_OPEN:
                self.circuit_state = CircuitBreakerState.CLOSED
                self.logger.info(f"Circuit breaker for {self.component_id} closed after successful operation")
            
            return result
            
        except Exception as e:
            # Record failure
            self._record_failure(str(e))
            
            # Open circuit if failure threshold exceeded
            if self.metrics.failure_count >= self.failure_threshold:
                self.circuit_state = CircuitBreakerState.OPEN
                self.logger.warning(f"Circuit breaker for {self.component_id} opened due to failures")
            
            raise
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get current health status and metrics."""
        with self._lock:
            return {
                "component_id": self.component_id,
                "state": self.state.value,
                "circuit_state": self.circuit_state.value,
                "success_rate": self.metrics.success_rate,
                "success_count": self.metrics.success_count,
                "failure_count": self.metrics.failure_count,
                "average_response_time": self.metrics.average_response_time,
                "last_success_time": self.metrics.last_success_time,
                "last_failure_time": self.metrics.last_failure_time,
                "recent_errors": self.metrics.error_messages[-5:],  # Last 5 errors
            }
    
    def add_state_change_callback(self, callback: Callable[[ComponentState, ComponentState], None]) -> None:
        """Add callback for state changes."""
        self.state_change_callbacks.append(callback)
    
    # Abstract methods to be implemented by subclasses
    @abstractmethod
    async def _initialize(self) -> None:
        """Initialize component-specific resources."""
        pass
    
    @abstractmethod
    async def _cleanup(self) -> None:
        """Cleanup component-specific resources."""
        pass
    
    @abstractmethod
    async def _health_check(self) -> bool:
        """
        Perform component-specific health check.
        
        Returns:
            True if healthy, False otherwise
        """
        pass
    
    async def _recover(self) -> bool:
        """
        Attempt to recover from failure.
        
        Returns:
            True if recovery successful, False otherwise
        """
        try:
            self.logger.info(f"Attempting recovery for component {self.component_id}")
            self._set_state(ComponentState.RECOVERING)
            
            # Cleanup and reinitialize
            await self._cleanup()
            await self._initialize()
            
            # Test health
            if await self._health_check():
                self._set_state(ComponentState.HEALTHY)
                self.logger.info(f"Recovery successful for component {self.component_id}")
                return True
            else:
                self._set_state(ComponentState.FAILED)
                self.logger.error(f"Recovery failed for component {self.component_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"Recovery error for component {self.component_id}: {e}")
            self._set_state(ComponentState.FAILED)
            return False
    
    async def _health_check_loop(self) -> None:
        """Main health monitoring loop."""
        while not self._shutdown_event.is_set():
            try:
                # Perform health check
                is_healthy = await self._health_check()
                
                if is_healthy:
                    if self.state in [ComponentState.DEGRADED, ComponentState.FAILING]:
                        self._set_state(ComponentState.HEALTHY)
                        self.logger.info(f"Component {self.component_id} recovered to healthy state")
                else:
                    # Handle unhealthy state
                    if self.state == ComponentState.HEALTHY:
                        self._set_state(ComponentState.DEGRADED)
                        self.logger.warning(f"Component {self.component_id} degraded")
                    elif self.state == ComponentState.DEGRADED:
                        self._set_state(ComponentState.FAILING)
                        self.logger.error(f"Component {self.component_id} failing")
                    elif self.state == ComponentState.FAILING:
                        self._set_state(ComponentState.FAILED)
                        self.logger.critical(f"Component {self.component_id} failed")
                        
                        # Attempt recovery
                        if not self._recovery_task or self._recovery_task.done():
                            self._recovery_task = asyncio.create_task(self._attempt_recovery())
                
                # Wait for next check
                await asyncio.sleep(self.health_check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Health check error for {self.component_id}: {e}")
                await asyncio.sleep(self.health_check_interval)
    
    async def _attempt_recovery(self) -> None:
        """Attempt recovery with exponential backoff."""
        attempt = 0
        max_attempts = 3
        
        while attempt < max_attempts and not self._shutdown_event.is_set():
            await asyncio.sleep(self.recovery_timeout * (2 ** attempt))
            
            if await self._recover():
                return
            
            attempt += 1
        
        self.logger.critical(f"All recovery attempts failed for component {self.component_id}")
    
    def _set_state(self, new_state: ComponentState) -> None:
        """Set component state and notify callbacks."""
        with self._lock:
            old_state = self.state
            self.state = new_state
            
            # Notify callbacks
            for callback in self.state_change_callbacks:
                try:
                    callback(old_state, new_state)
                except Exception as e:
                    self.logger.error(f"State change callback error: {e}")
    
    def _record_success(self, response_time: float) -> None:
        """Record successful operation."""
        with self._lock:
            self.metrics.success_count += 1
            self.metrics.last_success_time = time.time()
            self.metrics.response_times.append(response_time)
            
            # Keep only recent response times
            if len(self.metrics.response_times) > 100:
                self.metrics.response_times = self.metrics.response_times[-50:]
    
    def _record_failure(self, error_message: str) -> None:
        """Record failed operation."""
        with self._lock:
            self.metrics.failure_count += 1
            self.metrics.last_failure_time = time.time()
            self.metrics.error_messages.append(error_message)
            
            # Keep only recent errors
            if len(self.metrics.error_messages) > 20:
                self.metrics.error_messages = self.metrics.error_messages[-10:]


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open."""
    pass