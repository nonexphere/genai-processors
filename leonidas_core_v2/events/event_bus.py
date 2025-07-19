# Copyright 2025 Leonidas Core v2.0
# Licensed under the Apache License, Version 2.0

"""
Event Bus - Central event distribution system
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
import time
import json
import uuid

from ..core.resilient_component import ResilientComponent


class EventPriority(Enum):
    """Event priority levels"""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


@dataclass
class Event:
    """Event data structure"""
    event_id: str
    event_type: str
    source: str
    data: Any
    timestamp: float = field(default_factory=time.time)
    priority: EventPriority = EventPriority.NORMAL
    metadata: Dict[str, Any] = field(default_factory=dict)
    correlation_id: Optional[str] = None
    reply_to: Optional[str] = None
    ttl: Optional[float] = None  # Time to live in seconds


@dataclass
class EventSubscription:
    """Event subscription information"""
    subscription_id: str
    subscriber_id: str
    event_pattern: str  # Event type pattern (supports wildcards)
    callback: Callable
    priority_filter: Optional[EventPriority] = None
    metadata_filter: Optional[Dict[str, Any]] = None
    created_at: float = field(default_factory=time.time)
    active: bool = True


class EventBus(ResilientComponent):
    """
    Central event bus providing pub/sub messaging with pattern matching,
    priority handling, and reliable delivery.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("event_bus")
        
        self.config = config or {}
        
        # Event storage and queues
        self.event_queue = asyncio.PriorityQueue(maxsize=10000)
        self.subscriptions: Dict[str, EventSubscription] = {}
        self.subscribers: Dict[str, Set[str]] = {}  # subscriber_id -> subscription_ids
        
        # Event routing
        self.event_patterns: Dict[str, Set[str]] = {}  # pattern -> subscription_ids
        
        # Event persistence
        self.event_history: List[Event] = []
        self.max_history_size = self.config.get('max_history_size', 1000)
        
        # Processing configuration
        self.max_concurrent_handlers = self.config.get('max_concurrent_handlers', 10)
        self.event_timeout = self.config.get('event_timeout', 30.0)
        self.retry_attempts = self.config.get('retry_attempts', 3)
        
        # Tasks
        self.event_processor_task: Optional[asyncio.Task] = None
        self.cleanup_task: Optional[asyncio.Task] = None
        self.handler_semaphore = asyncio.Semaphore(self.max_concurrent_handlers)
        
        # Statistics
        self.stats = {
            'events_published': 0,
            'events_delivered': 0,
            'events_failed': 0,
            'active_subscriptions': 0,
            'average_delivery_time': 0.0,
            'queue_size': 0
        }
        
        logging.info("Event bus initialized")
    
    async def start(self):
        """Start event bus"""
        try:
            # Start event processor
            self.event_processor_task = asyncio.create_task(self._event_processor())
            
            # Start cleanup task
            self.cleanup_task = asyncio.create_task(self._cleanup_loop())
            
            logging.info("Event bus started")
            
        except Exception as e:
            logging.error(f"Failed to start event bus: {e}")
            raise
    
    async def stop(self):
        """Stop event bus"""
        try:
            # Cancel tasks
            if self.event_processor_task:
                self.event_processor_task.cancel()
            if self.cleanup_task:
                self.cleanup_task.cancel()
            
            # Wait for tasks to complete
            await asyncio.gather(
                self.event_processor_task, self.cleanup_task,
                return_exceptions=True
            )
            
            logging.info("Event bus stopped")
            
        except Exception as e:
            logging.error(f"Error stopping event bus: {e}")
    
    async def publish(self, event: Event) -> bool:
        """Publish an event to the bus"""
        try:
            # Validate event
            if not self._validate_event(event):
                return False
            
            # Set event ID if not provided
            if not event.event_id:
                event.event_id = str(uuid.uuid4())
            
            # Add to queue with priority
            priority = -event.priority.value  # Negative for max-heap behavior
            await self.event_queue.put((priority, event.timestamp, event))
            
            # Update statistics
            self.stats['events_published'] += 1
            self.stats['queue_size'] = self.event_queue.qsize()
            
            # Add to history
            self.event_history.append(event)
            if len(self.event_history) > self.max_history_size:
                self.event_history.pop(0)
            
            logging.debug(f"Event {event.event_id} published: {event.event_type}")
            return True
            
        except asyncio.QueueFull:
            logging.warning("Event queue full, event rejected")
            return False
        except Exception as e:
            logging.error(f"Error publishing event: {e}")
            return False
    
    async def publish_simple(self, 
                           event_type: str, 
                           source: str, 
                           data: Any,
                           priority: EventPriority = EventPriority.NORMAL,
                           **kwargs) -> bool:
        """Publish a simple event"""
        event = Event(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            source=source,
            data=data,
            priority=priority,
            **kwargs
        )
        return await self.publish(event)
    
    def subscribe(self, 
                  subscriber_id: str,
                  event_pattern: str,
                  callback: Callable,
                  priority_filter: Optional[EventPriority] = None,
                  metadata_filter: Optional[Dict[str, Any]] = None) -> str:
        """Subscribe to events matching a pattern"""
        try:
            subscription_id = str(uuid.uuid4())
            
            subscription = EventSubscription(
                subscription_id=subscription_id,
                subscriber_id=subscriber_id,
                event_pattern=event_pattern,
                callback=callback,
                priority_filter=priority_filter,
                metadata_filter=metadata_filter
            )
            
            # Store subscription
            self.subscriptions[subscription_id] = subscription
            
            # Update subscriber mapping
            if subscriber_id not in self.subscribers:
                self.subscribers[subscriber_id] = set()
            self.subscribers[subscriber_id].add(subscription_id)
            
            # Update pattern mapping
            if event_pattern not in self.event_patterns:
                self.event_patterns[event_pattern] = set()
            self.event_patterns[event_pattern].add(subscription_id)
            
            # Update statistics
            self.stats['active_subscriptions'] += 1
            
            logging.info(f"Subscription {subscription_id} created for {subscriber_id}: {event_pattern}")
            return subscription_id
            
        except Exception as e:
            logging.error(f"Error creating subscription: {e}")
            return ""
    
    def unsubscribe(self, subscription_id: str) -> bool:
        """Unsubscribe from events"""
        try:
            if subscription_id not in self.subscriptions:
                logging.warning(f"Subscription {subscription_id} not found")
                return False
            
            subscription = self.subscriptions[subscription_id]
            
            # Remove from pattern mapping
            pattern = subscription.event_pattern
            if pattern in self.event_patterns:
                self.event_patterns[pattern].discard(subscription_id)
                if not self.event_patterns[pattern]:
                    del self.event_patterns[pattern]
            
            # Remove from subscriber mapping
            subscriber_id = subscription.subscriber_id
            if subscriber_id in self.subscribers:
                self.subscribers[subscriber_id].discard(subscription_id)
                if not self.subscribers[subscriber_id]:
                    del self.subscribers[subscriber_id]
            
            # Remove subscription
            del self.subscriptions[subscription_id]
            
            # Update statistics
            self.stats['active_subscriptions'] -= 1
            
            logging.info(f"Subscription {subscription_id} removed")
            return True
            
        except Exception as e:
            logging.error(f"Error removing subscription: {e}")
            return False
    
    def unsubscribe_all(self, subscriber_id: str) -> int:
        """Unsubscribe all subscriptions for a subscriber"""
        try:
            if subscriber_id not in self.subscribers:
                return 0
            
            subscription_ids = list(self.subscribers[subscriber_id])
            removed_count = 0
            
            for subscription_id in subscription_ids:
                if self.unsubscribe(subscription_id):
                    removed_count += 1
            
            logging.info(f"Removed {removed_count} subscriptions for {subscriber_id}")
            return removed_count
            
        except Exception as e:
            logging.error(f"Error removing subscriptions for {subscriber_id}: {e}")
            return 0
    
    def get_subscriptions(self, subscriber_id: Optional[str] = None) -> List[EventSubscription]:
        """Get subscriptions, optionally filtered by subscriber"""
        if subscriber_id:
            if subscriber_id in self.subscribers:
                subscription_ids = self.subscribers[subscriber_id]
                return [self.subscriptions[sid] for sid in subscription_ids 
                       if sid in self.subscriptions]
            else:
                return []
        else:
            return list(self.subscriptions.values())
    
    def get_event_history(self, 
                         event_type: Optional[str] = None,
                         source: Optional[str] = None,
                         limit: int = 100) -> List[Event]:
        """Get event history with optional filtering"""
        events = self.event_history
        
        # Apply filters
        if event_type:
            events = [e for e in events if self._match_pattern(e.event_type, event_type)]
        
        if source:
            events = [e for e in events if e.source == source]
        
        # Return most recent events
        return events[-limit:] if limit > 0 else events
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get event bus statistics"""
        self.stats['queue_size'] = self.event_queue.qsize()
        return self.stats.copy()
    
    async def _event_processor(self):
        """Main event processing loop"""
        while True:
            try:
                # Get next event
                priority, timestamp, event = await asyncio.wait_for(
                    self.event_queue.get(),
                    timeout=1.0
                )
                
                # Check TTL
                if event.ttl and time.time() - event.timestamp > event.ttl:
                    logging.debug(f"Event {event.event_id} expired")
                    continue
                
                # Process event
                await self._process_event(event)
                
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"Error in event processor: {e}")
                await asyncio.sleep(0.1)
    
    async def _process_event(self, event: Event):
        """Process a single event"""
        try:
            # Find matching subscriptions
            matching_subscriptions = self._find_matching_subscriptions(event)
            
            if not matching_subscriptions:
                logging.debug(f"No subscribers for event {event.event_type}")
                return
            
            # Deliver to all matching subscribers
            delivery_tasks = []
            for subscription in matching_subscriptions:
                task = asyncio.create_task(
                    self._deliver_event(event, subscription)
                )
                delivery_tasks.append(task)
            
            # Wait for all deliveries
            results = await asyncio.gather(*delivery_tasks, return_exceptions=True)
            
            # Count successful deliveries
            successful_deliveries = sum(1 for result in results if result is True)
            failed_deliveries = len(results) - successful_deliveries
            
            self.stats['events_delivered'] += successful_deliveries
            self.stats['events_failed'] += failed_deliveries
            
            if failed_deliveries > 0:
                logging.warning(f"Event {event.event_id}: {failed_deliveries} delivery failures")
            
        except Exception as e:
            logging.error(f"Error processing event {event.event_id}: {e}")
            self.stats['events_failed'] += 1
    
    async def _deliver_event(self, event: Event, subscription: EventSubscription) -> bool:
        """Deliver event to a specific subscription"""
        if not subscription.active:
            return False
        
        async with self.handler_semaphore:
            delivery_start = time.time()
            
            try:
                # Execute callback with timeout
                if asyncio.iscoroutinefunction(subscription.callback):
                    await asyncio.wait_for(
                        subscription.callback(event),
                        timeout=self.event_timeout
                    )
                else:
                    # Run sync callback in thread pool
                    loop = asyncio.get_event_loop()
                    await asyncio.wait_for(
                        loop.run_in_executor(None, subscription.callback, event),
                        timeout=self.event_timeout
                    )
                
                # Update delivery time statistics
                delivery_time = time.time() - delivery_start
                count = self.stats['events_delivered'] + 1
                current_avg = self.stats['average_delivery_time']
                self.stats['average_delivery_time'] = (
                    (current_avg * (count - 1) + delivery_time) / count
                )
                
                return True
                
            except asyncio.TimeoutError:
                logging.warning(f"Event delivery timeout for subscription {subscription.subscription_id}")
                return False
            except Exception as e:
                logging.error(f"Error delivering event to {subscription.subscriber_id}: {e}")
                return False
    
    def _find_matching_subscriptions(self, event: Event) -> List[EventSubscription]:
        """Find subscriptions that match the event"""
        matching_subscriptions = []
        
        for pattern, subscription_ids in self.event_patterns.items():
            if self._match_pattern(event.event_type, pattern):
                for subscription_id in subscription_ids:
                    if subscription_id in self.subscriptions:
                        subscription = self.subscriptions[subscription_id]
                        
                        if self._match_subscription_filters(event, subscription):
                            matching_subscriptions.append(subscription)
        
        return matching_subscriptions
    
    def _match_pattern(self, event_type: str, pattern: str) -> bool:
        """Check if event type matches pattern (supports wildcards)"""
        if pattern == "*":
            return True
        
        if "*" not in pattern:
            return event_type == pattern
        
        # Simple wildcard matching
        pattern_parts = pattern.split("*")
        
        if len(pattern_parts) == 2:
            prefix, suffix = pattern_parts
            return event_type.startswith(prefix) and event_type.endswith(suffix)
        
        # More complex wildcard patterns can be implemented here
        return event_type == pattern
    
    def _match_subscription_filters(self, event: Event, subscription: EventSubscription) -> bool:
        """Check if event matches subscription filters"""
        # Check priority filter
        if (subscription.priority_filter is not None and 
            event.priority != subscription.priority_filter):
            return False
        
        # Check metadata filter
        if subscription.metadata_filter:
            for key, value in subscription.metadata_filter.items():
                if key not in event.metadata or event.metadata[key] != value:
                    return False
        
        return True
    
    def _validate_event(self, event: Event) -> bool:
        """Validate event before publishing"""
        if not event.event_type:
            logging.error("Event type is required")
            return False
        
        if not event.source:
            logging.error("Event source is required")
            return False
        
        return True
    
    async def _cleanup_loop(self):
        """Periodic cleanup of expired events and inactive subscriptions"""
        while True:
            try:
                current_time = time.time()
                
                # Remove inactive subscriptions
                inactive_subscriptions = [
                    sub_id for sub_id, sub in self.subscriptions.items()
                    if not sub.active
                ]
                
                for sub_id in inactive_subscriptions:
                    self.unsubscribe(sub_id)
                
                # Limit event history size
                if len(self.event_history) > self.max_history_size:
                    self.event_history = self.event_history[-self.max_history_size:]
                
                await asyncio.sleep(300.0)  # Cleanup every 5 minutes
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"Error in cleanup loop: {e}")
                await asyncio.sleep(300.0)