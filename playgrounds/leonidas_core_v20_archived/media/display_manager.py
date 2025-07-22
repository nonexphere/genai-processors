# Copyright 2025 Leonidas Core v2.0
# Licensed under the Apache License, Version 2.0

"""
Display Manager - Multi-display management and control
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import time

from ..core.resilient_component import ResilientComponent


class DisplayType(Enum):
    """Types of displays"""
    PRIMARY = "primary"
    SECONDARY = "secondary"
    PROJECTION = "projection"
    TOUCH = "touch"
    VR_HEADSET = "vr_headset"
    AR_DISPLAY = "ar_display"
    LED_MATRIX = "led_matrix"
    CUSTOM = "custom"


class DisplayOrientation(Enum):
    """Display orientations"""
    LANDSCAPE = "landscape"
    PORTRAIT = "portrait"
    LANDSCAPE_FLIPPED = "landscape_flipped"
    PORTRAIT_FLIPPED = "portrait_flipped"


@dataclass
class DisplayInfo:
    """Information about a display"""
    display_id: str
    name: str
    display_type: DisplayType
    resolution: Tuple[int, int]  # (width, height)
    position: Tuple[int, int] = (0, 0)  # (x, y) position in virtual desktop
    orientation: DisplayOrientation = DisplayOrientation.LANDSCAPE
    refresh_rate: float = 60.0  # Hz
    color_depth: int = 24  # bits
    is_primary: bool = False
    is_touch_enabled: bool = False
    is_active: bool = True
    brightness: float = 1.0  # 0.0 to 1.0
    contrast: float = 1.0
    gamma: float = 1.0
    capabilities: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DisplayLayout:
    """Layout configuration for multiple displays"""
    layout_id: str
    name: str
    displays: Dict[str, DisplayInfo]
    virtual_resolution: Tuple[int, int]
    primary_display_id: str
    layout_type: str = "extended"  # extended, mirrored, single
    created_at: float = field(default_factory=time.time)


class DisplayManager(ResilientComponent):
    """
    Manages multiple displays and provides unified interface for
    display configuration, content routing, and layout management.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("display_manager")
        
        self.config = config or {}
        self.displays: Dict[str, DisplayInfo] = {}
        self.layouts: Dict[str, DisplayLayout] = {}
        self.current_layout: Optional[DisplayLayout] = None
        
        # Display monitoring
        self.monitoring_enabled = self.config.get('monitoring_enabled', True)
        self.monitoring_interval = self.config.get('monitoring_interval', 5.0)
        
        # Tasks
        self.monitoring_task: Optional[asyncio.Task] = None
        
        # Event callbacks
        self.display_callbacks: Dict[str, List[callable]] = {
            'display_connected': [],
            'display_disconnected': [],
            'display_changed': [],
            'layout_changed': []
        }
        
        logging.info("Display manager initialized")
    
    async def start(self):
        """Start display manager"""
        try:
            # Discover connected displays
            await self._discover_displays()
            
            # Create default layout
            await self._create_default_layout()
            
            # Start monitoring if enabled
            if self.monitoring_enabled:
                self.monitoring_task = asyncio.create_task(self._monitoring_loop())
            
            logging.info("Display manager started")
            
        except Exception as e:
            logging.error(f"Failed to start display manager: {e}")
            raise
    
    async def stop(self):
        """Stop display manager"""
        try:
            # Cancel monitoring task
            if self.monitoring_task:
                self.monitoring_task.cancel()
                await self.monitoring_task
            
            logging.info("Display manager stopped")
            
        except Exception as e:
            logging.error(f"Error stopping display manager: {e}")
    
    async def add_display(self, display_info: DisplayInfo) -> bool:
        """Add a display to management"""
        try:
            display_id = display_info.display_id
            
            if display_id in self.displays:
                logging.warning(f"Display {display_id} already exists")
                return False
            
            # Validate display configuration
            if not await self._validate_display_config(display_info):
                return False
            
            # Add display
            self.displays[display_id] = display_info
            
            # Initialize display
            if await self._initialize_display(display_info):
                await self._notify_display_event('display_connected', display_info)
                logging.info(f"Display {display_id} added successfully")
                return True
            else:
                # Remove if initialization failed
                del self.displays[display_id]
                logging.error(f"Failed to initialize display {display_id}")
                return False
                
        except Exception as e:
            logging.error(f"Error adding display {display_info.display_id}: {e}")
            return False
    
    async def remove_display(self, display_id: str) -> bool:
        """Remove a display from management"""
        try:
            if display_id not in self.displays:
                logging.warning(f"Display {display_id} not found")
                return False
            
            display_info = self.displays[display_id]
            
            # Cleanup display
            await self._cleanup_display(display_info)
            
            # Remove from management
            del self.displays[display_id]
            
            # Update layouts that use this display
            await self._update_layouts_after_display_removal(display_id)
            
            await self._notify_display_event('display_disconnected', display_info)
            logging.info(f"Display {display_id} removed")
            return True
            
        except Exception as e:
            logging.error(f"Error removing display {display_id}: {e}")
            return False
    
    async def configure_display(self, display_id: str, config: Dict[str, Any]) -> bool:
        """Configure display settings"""
        try:
            if display_id not in self.displays:
                logging.error(f"Display {display_id} not found")
                return False
            
            display_info = self.displays[display_id]
            
            # Update display configuration
            if 'brightness' in config:
                display_info.brightness = max(0.0, min(1.0, config['brightness']))
            
            if 'contrast' in config:
                display_info.contrast = max(0.0, min(2.0, config['contrast']))
            
            if 'gamma' in config:
                display_info.gamma = max(0.1, min(3.0, config['gamma']))
            
            if 'orientation' in config:
                display_info.orientation = DisplayOrientation(config['orientation'])
            
            if 'position' in config:
                display_info.position = tuple(config['position'])
            
            # Apply configuration to hardware
            success = await self._apply_display_configuration(display_info, config)
            
            if success:
                await self._notify_display_event('display_changed', display_info)
                logging.info(f"Display {display_id} configured successfully")
            
            return success
            
        except Exception as e:
            logging.error(f"Error configuring display {display_id}: {e}")
            return False
    
    async def create_layout(self, layout: DisplayLayout) -> bool:
        """Create a new display layout"""
        try:
            # Validate layout
            if not await self._validate_layout(layout):
                return False
            
            # Store layout
            self.layouts[layout.layout_id] = layout
            
            logging.info(f"Display layout '{layout.name}' created")
            return True
            
        except Exception as e:
            logging.error(f"Error creating layout: {e}")
            return False
    
    async def apply_layout(self, layout_id: str) -> bool:
        """Apply a display layout"""
        try:
            if layout_id not in self.layouts:
                logging.error(f"Layout {layout_id} not found")
                return False
            
            layout = self.layouts[layout_id]
            
            # Apply layout configuration
            success = await self._apply_layout_configuration(layout)
            
            if success:
                self.current_layout = layout
                await self._notify_display_event('layout_changed', layout)
                logging.info(f"Layout '{layout.name}' applied successfully")
            
            return success
            
        except Exception as e:
            logging.error(f"Error applying layout {layout_id}: {e}")
            return False
    
    async def set_primary_display(self, display_id: str) -> bool:
        """Set primary display"""
        try:
            if display_id not in self.displays:
                logging.error(f"Display {display_id} not found")
                return False
            
            # Clear current primary
            for display in self.displays.values():
                display.is_primary = False
            
            # Set new primary
            self.displays[display_id].is_primary = True
            
            # Apply primary display configuration
            success = await self._set_hardware_primary_display(display_id)
            
            if success:
                logging.info(f"Display {display_id} set as primary")
            
            return success
            
        except Exception as e:
            logging.error(f"Error setting primary display: {e}")
            return False
    
    async def enable_display(self, display_id: str) -> bool:
        """Enable a display"""
        return await self._set_display_state(display_id, True)
    
    async def disable_display(self, display_id: str) -> bool:
        """Disable a display"""
        return await self._set_display_state(display_id, False)
    
    def get_display_info(self, display_id: str) -> Optional[DisplayInfo]:
        """Get information about a display"""
        return self.displays.get(display_id)
    
    def get_all_displays(self) -> Dict[str, DisplayInfo]:
        """Get all displays"""
        return self.displays.copy()
    
    def get_active_displays(self) -> Dict[str, DisplayInfo]:
        """Get all active displays"""
        return {id: info for id, info in self.displays.items() if info.is_active}
    
    def get_primary_display(self) -> Optional[DisplayInfo]:
        """Get primary display"""
        for display in self.displays.values():
            if display.is_primary:
                return display
        return None
    
    def get_current_layout(self) -> Optional[DisplayLayout]:
        """Get current display layout"""
        return self.current_layout
    
    def get_all_layouts(self) -> Dict[str, DisplayLayout]:
        """Get all display layouts"""
        return self.layouts.copy()
    
    def register_callback(self, event_type: str, callback: callable):
        """Register callback for display events"""
        if event_type in self.display_callbacks:
            self.display_callbacks[event_type].append(callback)
        else:
            logging.warning(f"Unknown event type: {event_type}")
    
    async def _discover_displays(self):
        """Discover connected displays"""
        try:
            # This would interface with actual display detection APIs
            # For simulation, create a default display
            default_display = DisplayInfo(
                display_id="display_0",
                name="Primary Display",
                display_type=DisplayType.PRIMARY,
                resolution=(1920, 1080),
                position=(0, 0),
                is_primary=True,
                capabilities=["color", "brightness_control", "contrast_control"]
            )
            
            await self.add_display(default_display)
            
        except Exception as e:
            logging.error(f"Error discovering displays: {e}")
    
    async def _create_default_layout(self):
        """Create default display layout"""
        if not self.displays:
            return
        
        # Create layout with all current displays
        default_layout = DisplayLayout(
            layout_id="default",
            name="Default Layout",
            displays=self.displays.copy(),
            virtual_resolution=self._calculate_virtual_resolution(),
            primary_display_id=next(
                (id for id, info in self.displays.items() if info.is_primary),
                list(self.displays.keys())[0]
            )
        )
        
        await self.create_layout(default_layout)
        await self.apply_layout("default")
    
    async def _monitoring_loop(self):
        """Monitor display status"""
        while True:
            try:
                await self._check_display_status()
                await asyncio.sleep(self.monitoring_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"Error in display monitoring: {e}")
                await asyncio.sleep(5.0)
    
    async def _check_display_status(self):
        """Check status of all displays"""
        for display_id, display_info in self.displays.items():
            try:
                # Check if display is still connected
                is_connected = await self._check_display_connection(display_id)
                
                if not is_connected and display_info.is_active:
                    display_info.is_active = False
                    await self._notify_display_event('display_disconnected', display_info)
                    logging.warning(f"Display {display_id} disconnected")
                elif is_connected and not display_info.is_active:
                    display_info.is_active = True
                    await self._notify_display_event('display_connected', display_info)
                    logging.info(f"Display {display_id} reconnected")
                    
            except Exception as e:
                logging.error(f"Error checking display {display_id}: {e}")
    
    async def _validate_display_config(self, display_info: DisplayInfo) -> bool:
        """Validate display configuration"""
        # Check resolution
        if display_info.resolution[0] <= 0 or display_info.resolution[1] <= 0:
            logging.error("Invalid display resolution")
            return False
        
        # Check brightness range
        if not (0.0 <= display_info.brightness <= 1.0):
            logging.error("Invalid brightness value")
            return False
        
        return True
    
    async def _validate_layout(self, layout: DisplayLayout) -> bool:
        """Validate display layout"""
        # Check if all displays in layout exist
        for display_id in layout.displays:
            if display_id not in self.displays:
                logging.error(f"Display {display_id} in layout not found")
                return False
        
        # Check primary display
        if layout.primary_display_id not in layout.displays:
            logging.error("Primary display not in layout")
            return False
        
        return True
    
    async def _initialize_display(self, display_info: DisplayInfo) -> bool:
        """Initialize display hardware"""
        try:
            # This would initialize actual display hardware
            logging.info(f"Initializing display {display_info.display_id}")
            await asyncio.sleep(0.1)  # Simulate initialization time
            return True
        except Exception as e:
            logging.error(f"Error initializing display: {e}")
            return False
    
    async def _cleanup_display(self, display_info: DisplayInfo):
        """Cleanup display resources"""
        try:
            logging.info(f"Cleaning up display {display_info.display_id}")
            await asyncio.sleep(0.1)  # Simulate cleanup time
        except Exception as e:
            logging.error(f"Error cleaning up display: {e}")
    
    async def _apply_display_configuration(self, display_info: DisplayInfo, config: Dict[str, Any]) -> bool:
        """Apply configuration to display hardware"""
        try:
            # This would apply actual hardware configuration
            logging.info(f"Applying configuration to display {display_info.display_id}")
            return True
        except Exception as e:
            logging.error(f"Error applying display configuration: {e}")
            return False
    
    async def _apply_layout_configuration(self, layout: DisplayLayout) -> bool:
        """Apply layout configuration to displays"""
        try:
            # Configure each display in the layout
            for display_id, display_info in layout.displays.items():
                if display_id in self.displays:
                    # Update display configuration
                    self.displays[display_id] = display_info
                    
                    # Apply hardware configuration
                    await self._apply_display_configuration(display_info, {})
            
            return True
        except Exception as e:
            logging.error(f"Error applying layout configuration: {e}")
            return False
    
    async def _set_hardware_primary_display(self, display_id: str) -> bool:
        """Set primary display in hardware"""
        try:
            # This would set the primary display in the OS/hardware
            logging.info(f"Setting hardware primary display to {display_id}")
            return True
        except Exception as e:
            logging.error(f"Error setting hardware primary display: {e}")
            return False
    
    async def _set_display_state(self, display_id: str, enabled: bool) -> bool:
        """Enable or disable a display"""
        try:
            if display_id not in self.displays:
                logging.error(f"Display {display_id} not found")
                return False
            
            display_info = self.displays[display_id]
            display_info.is_active = enabled
            
            # Apply hardware state change
            success = await self._apply_hardware_display_state(display_id, enabled)
            
            if success:
                state = "enabled" if enabled else "disabled"
                logging.info(f"Display {display_id} {state}")
                await self._notify_display_event('display_changed', display_info)
            
            return success
            
        except Exception as e:
            logging.error(f"Error setting display state: {e}")
            return False
    
    async def _apply_hardware_display_state(self, display_id: str, enabled: bool) -> bool:
        """Apply display state to hardware"""
        try:
            # This would enable/disable the display in hardware
            return True
        except Exception as e:
            logging.error(f"Error applying hardware display state: {e}")
            return False
    
    async def _check_display_connection(self, display_id: str) -> bool:
        """Check if display is connected"""
        # This would check actual hardware connection
        # For simulation, always return True
        return True
    
    def _calculate_virtual_resolution(self) -> Tuple[int, int]:
        """Calculate virtual desktop resolution"""
        if not self.displays:
            return (1920, 1080)
        
        max_x = max(info.position[0] + info.resolution[0] for info in self.displays.values())
        max_y = max(info.position[1] + info.resolution[1] for info in self.displays.values())
        
        return (max_x, max_y)
    
    async def _update_layouts_after_display_removal(self, display_id: str):
        """Update layouts after display removal"""
        layouts_to_update = []
        
        for layout_id, layout in self.layouts.items():
            if display_id in layout.displays:
                layouts_to_update.append(layout_id)
        
        for layout_id in layouts_to_update:
            layout = self.layouts[layout_id]
            
            # Remove display from layout
            if display_id in layout.displays:
                del layout.displays[display_id]
            
            # Update primary display if needed
            if layout.primary_display_id == display_id:
                if layout.displays:
                    layout.primary_display_id = next(iter(layout.displays.keys()))
                else:
                    # Remove empty layout
                    del self.layouts[layout_id]
                    continue
            
            # Recalculate virtual resolution
            layout.virtual_resolution = self._calculate_virtual_resolution()
    
    async def _notify_display_event(self, event_type: str, data: Any):
        """Notify callbacks of display events"""
        if event_type in self.display_callbacks:
            event_data = {
                'event_type': event_type,
                'data': data,
                'timestamp': time.time()
            }
            
            for callback in self.display_callbacks[event_type]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(event_data)
                    else:
                        callback(event_data)
                except Exception as e:
                    logging.error(f"Error in display callback: {e}")