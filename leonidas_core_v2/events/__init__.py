# Copyright 2025 Leonidas Core v2.0
# Licensed under the Apache License, Version 2.0

"""
Event System

Provides event-driven architecture with pub/sub messaging, event routing,
and real-time event processing capabilities.
"""

from .event_bus import EventBus
from .event_dispatcher import EventDispatcher
from .event_aggregator import EventAggregator

__all__ = [
    "EventBus",
    "EventDispatcher",
    "EventAggregator",
]