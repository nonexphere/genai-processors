# Copyright 2025 Leonidas Core v2.0
# Licensed under the Apache License, Version 2.0

"""
Content Renderer - Multi-modal content rendering and display
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import time
import json
import base64

from ..core.resilient_component import ResilientComponent


class ContentType(Enum):
    """Types of content that can be rendered"""
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    HTML = "html"
    MARKDOWN = "markdown"
    PDF = "pdf"
    PRESENTATION = "presentation"
    INTERACTIVE = "interactive"
    CUSTOM = "custom"


class RenderQuality(Enum):
    """Rendering quality levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    ULTRA = "ultra"


@dataclass
class ContentItem:
    """Content item to be rendered"""
    content_id: str
    content_type: ContentType
    data: Any  # Content data (text, bytes, URL, etc.)
    metadata: Dict[str, Any] = field(default_factory=dict)
    display_id: Optional[str] = None  # Target display
    position: tuple = (0, 0)  # (x, y) position
    size: Optional[tuple] = None  # (width, height)
    z_index: int = 0  # Layer order
    duration: Optional[float] = None  # Display duration in seconds
    transition: Optional[str] = None  # Transition effect
    interactive: bool = False
    created_at: float = field(default_factory=time.time)


@dataclass
class RenderContext:
    """Rendering context and parameters"""
    display_id: str
    resolution: tuple
    color_depth: int
    refresh_rate: float
    quality: RenderQuality = RenderQuality.MEDIUM
    anti_aliasing: bool = True
    hardware_acceleration: bool = True
    custom_params: Dict[str, Any] = field(default_factory=dict)


class ContentRenderer(ResilientComponent):
    """
    Multi-modal content renderer supporting various content types
    with hardware-accelerated rendering and multi-display support.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("content_renderer")
        
        self.config = config or {}
        
        # Rendering contexts for each display
        self.render_contexts: Dict[str, RenderContext] = {}
        
        # Content management
        self.active_content: Dict[str, ContentItem] = {}
        self.render_queue: asyncio.Queue = asyncio.Queue(maxsize=1000)
        
        # Rendering engines
        self.text_renderer = TextRenderer()
        self.image_renderer = ImageRenderer()
        self.video_renderer = VideoRenderer()
        self.html_renderer = HTMLRenderer()
        
        # Performance settings
        self.max_concurrent_renders = self.config.get('max_concurrent_renders', 4)
        self.render_timeout = self.config.get('render_timeout', 30.0)
        
        # Tasks
        self.render_workers: List[asyncio.Task] = []
        self.cleanup_task: Optional[asyncio.Task] = None
        
        # Statistics
        self.stats = {
            'items_rendered': 0,
            'render_errors': 0,
            'average_render_time': 0.0,
            'active_renders': 0,
            'cache_hits': 0,
            'cache_misses': 0
        }
        
        # Content cache
        self.content_cache: Dict[str, Any] = {}
        self.cache_max_size = self.config.get('cache_max_size', 100)
        
        logging.info("Content renderer initialized")
    
    async def start(self):
        """Start content renderer"""
        try:
            # Start render workers
            for i in range(self.max_concurrent_renders):
                worker = asyncio.create_task(self._render_worker(f"worker_{i}"))
                self.render_workers.append(worker)
            
            # Start cleanup task
            self.cleanup_task = asyncio.create_task(self._cleanup_loop())
            
            logging.info("Content renderer started")
            
        except Exception as e:
            logging.error(f"Failed to start content renderer: {e}")
            raise
    
    async def stop(self):
        """Stop content renderer"""
        try:
            # Cancel all workers
            for worker in self.render_workers:
                worker.cancel()
            
            if self.cleanup_task:
                self.cleanup_task.cancel()
            
            # Wait for workers to complete
            await asyncio.gather(*self.render_workers, self.cleanup_task, return_exceptions=True)
            
            # Clear active content
            self.active_content.clear()
            
            logging.info("Content renderer stopped")
            
        except Exception as e:
            logging.error(f"Error stopping content renderer: {e}")
    
    def register_display(self, display_id: str, context: RenderContext):
        """Register a display for rendering"""
        self.render_contexts[display_id] = context
        logging.info(f"Display {display_id} registered for rendering")
    
    def unregister_display(self, display_id: str):
        """Unregister a display"""
        if display_id in self.render_contexts:
            del self.render_contexts[display_id]
            
            # Remove content for this display
            content_to_remove = [
                content_id for content_id, content in self.active_content.items()
                if content.display_id == display_id
            ]
            
            for content_id in content_to_remove:
                del self.active_content[content_id]
            
            logging.info(f"Display {display_id} unregistered")
    
    async def render_content(self, content: ContentItem) -> bool:
        """Queue content for rendering"""
        try:
            # Validate content
            if not await self._validate_content(content):
                return False
            
            # Add to render queue
            await self.render_queue.put(content)
            
            logging.debug(f"Content {content.content_id} queued for rendering")
            return True
            
        except asyncio.QueueFull:
            logging.warning("Render queue full, content rejected")
            return False
        except Exception as e:
            logging.error(f"Error queuing content for rendering: {e}")
            return False
    
    async def render_text(self, text: str, display_id: str, **kwargs) -> bool:
        """Render text content"""
        content = ContentItem(
            content_id=f"text_{time.time()}",
            content_type=ContentType.TEXT,
            data=text,
            display_id=display_id,
            **kwargs
        )
        return await self.render_content(content)
    
    async def render_image(self, image_data: Union[bytes, str], display_id: str, **kwargs) -> bool:
        """Render image content"""
        content = ContentItem(
            content_id=f"image_{time.time()}",
            content_type=ContentType.IMAGE,
            data=image_data,
            display_id=display_id,
            **kwargs
        )
        return await self.render_content(content)
    
    async def render_html(self, html: str, display_id: str, **kwargs) -> bool:
        """Render HTML content"""
        content = ContentItem(
            content_id=f"html_{time.time()}",
            content_type=ContentType.HTML,
            data=html,
            display_id=display_id,
            **kwargs
        )
        return await self.render_content(content)
    
    async def clear_display(self, display_id: str):
        """Clear all content from a display"""
        try:
            content_to_remove = [
                content_id for content_id, content in self.active_content.items()
                if content.display_id == display_id
            ]
            
            for content_id in content_to_remove:
                await self.remove_content(content_id)
            
            logging.info(f"Display {display_id} cleared")
            
        except Exception as e:
            logging.error(f"Error clearing display {display_id}: {e}")
    
    async def remove_content(self, content_id: str) -> bool:
        """Remove specific content"""
        try:
            if content_id in self.active_content:
                content = self.active_content[content_id]
                
                # Cleanup content resources
                await self._cleanup_content(content)
                
                # Remove from active content
                del self.active_content[content_id]
                
                logging.debug(f"Content {content_id} removed")
                return True
            
            return False
            
        except Exception as e:
            logging.error(f"Error removing content {content_id}: {e}")
            return False
    
    def get_active_content(self, display_id: Optional[str] = None) -> List[ContentItem]:
        """Get active content, optionally filtered by display"""
        if display_id:
            return [content for content in self.active_content.values() 
                   if content.display_id == display_id]
        else:
            return list(self.active_content.values())
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get rendering statistics"""
        return self.stats.copy()
    
    async def _render_worker(self, worker_id: str):
        """Render worker process"""
        while True:
            try:
                # Get next content to render
                content = await asyncio.wait_for(self.render_queue.get(), timeout=1.0)
                
                # Render content
                await self._render_content_item(content, worker_id)
                
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"Error in render worker {worker_id}: {e}")
                self.stats['render_errors'] += 1
    
    async def _render_content_item(self, content: ContentItem, worker_id: str):
        """Render a single content item"""
        render_start = time.time()
        
        try:
            self.stats['active_renders'] += 1
            
            # Get render context
            if content.display_id not in self.render_contexts:
                logging.error(f"No render context for display {content.display_id}")
                return
            
            context = self.render_contexts[content.display_id]
            
            # Check cache
            cache_key = self._get_cache_key(content)
            if cache_key in self.content_cache:
                rendered_data = self.content_cache[cache_key]
                self.stats['cache_hits'] += 1
            else:
                # Render content based on type
                rendered_data = await self._execute_render(content, context)
                
                # Cache result
                if rendered_data and len(self.content_cache) < self.cache_max_size:
                    self.content_cache[cache_key] = rendered_data
                
                self.stats['cache_misses'] += 1
            
            if rendered_data:
                # Display rendered content
                await self._display_content(content, rendered_data, context)
                
                # Add to active content
                self.active_content[content.content_id] = content
                
                # Schedule removal if duration is set
                if content.duration:
                    asyncio.create_task(self._schedule_content_removal(content))
                
                self.stats['items_rendered'] += 1
                
                # Update average render time
                render_time = time.time() - render_start
                count = self.stats['items_rendered']
                current_avg = self.stats['average_render_time']
                self.stats['average_render_time'] = (current_avg * (count - 1) + render_time) / count
                
                logging.debug(f"Content {content.content_id} rendered by {worker_id}")
            else:
                logging.error(f"Failed to render content {content.content_id}")
                self.stats['render_errors'] += 1
                
        except Exception as e:
            logging.error(f"Error rendering content {content.content_id}: {e}")
            self.stats['render_errors'] += 1
        finally:
            self.stats['active_renders'] -= 1
    
    async def _execute_render(self, content: ContentItem, context: RenderContext) -> Optional[Any]:
        """Execute rendering based on content type"""
        try:
            if content.content_type == ContentType.TEXT:
                return await self.text_renderer.render(content, context)
            elif content.content_type == ContentType.IMAGE:
                return await self.image_renderer.render(content, context)
            elif content.content_type == ContentType.VIDEO:
                return await self.video_renderer.render(content, context)
            elif content.content_type == ContentType.HTML:
                return await self.html_renderer.render(content, context)
            else:
                logging.warning(f"Unsupported content type: {content.content_type}")
                return None
                
        except Exception as e:
            logging.error(f"Error executing render: {e}")
            return None
    
    async def _display_content(self, content: ContentItem, rendered_data: Any, context: RenderContext):
        """Display rendered content on target display"""
        try:
            # This would interface with actual display hardware/software
            logging.debug(f"Displaying content {content.content_id} on {content.display_id}")
            
            # Simulate display operation
            await asyncio.sleep(0.01)
            
        except Exception as e:
            logging.error(f"Error displaying content: {e}")
    
    async def _validate_content(self, content: ContentItem) -> bool:
        """Validate content before rendering"""
        # Check if display is registered
        if content.display_id and content.display_id not in self.render_contexts:
            logging.error(f"Display {content.display_id} not registered")
            return False
        
        # Check content data
        if content.data is None:
            logging.error("Content data is None")
            return False
        
        # Validate position and size
        if content.position and len(content.position) != 2:
            logging.error("Invalid position format")
            return False
        
        if content.size and len(content.size) != 2:
            logging.error("Invalid size format")
            return False
        
        return True
    
    def _get_cache_key(self, content: ContentItem) -> str:
        """Generate cache key for content"""
        data_hash = hash(str(content.data))
        return f"{content.content_type.value}_{data_hash}_{content.size}_{content.metadata.get('style', '')}"
    
    async def _schedule_content_removal(self, content: ContentItem):
        """Schedule content removal after duration"""
        if content.duration:
            await asyncio.sleep(content.duration)
            await self.remove_content(content.content_id)
    
    async def _cleanup_content(self, content: ContentItem):
        """Cleanup content resources"""
        try:
            # Cleanup based on content type
            if content.content_type == ContentType.VIDEO:
                # Stop video playback
                pass
            elif content.content_type == ContentType.AUDIO:
                # Stop audio playback
                pass
            
        except Exception as e:
            logging.error(f"Error cleaning up content: {e}")
    
    async def _cleanup_loop(self):
        """Periodic cleanup of expired content and cache"""
        while True:
            try:
                current_time = time.time()
                
                # Remove expired content
                expired_content = []
                for content_id, content in self.active_content.items():
                    if (content.duration and 
                        current_time - content.created_at > content.duration):
                        expired_content.append(content_id)
                
                for content_id in expired_content:
                    await self.remove_content(content_id)
                
                # Cleanup cache if too large
                if len(self.content_cache) > self.cache_max_size:
                    # Remove oldest entries
                    items_to_remove = len(self.content_cache) - self.cache_max_size + 10
                    cache_keys = list(self.content_cache.keys())
                    for key in cache_keys[:items_to_remove]:
                        del self.content_cache[key]
                
                await asyncio.sleep(60.0)  # Cleanup every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"Error in cleanup loop: {e}")
                await asyncio.sleep(60.0)


# Specialized renderers for different content types
class TextRenderer:
    """Text content renderer"""
    
    async def render(self, content: ContentItem, context: RenderContext) -> Optional[Any]:
        """Render text content"""
        try:
            text = content.data
            style = content.metadata.get('style', {})
            
            # Apply text styling and formatting
            rendered_text = {
                'text': text,
                'font': style.get('font', 'Arial'),
                'size': style.get('size', 12),
                'color': style.get('color', '#000000'),
                'position': content.position,
                'size': content.size
            }
            
            return rendered_text
            
        except Exception as e:
            logging.error(f"Error rendering text: {e}")
            return None


class ImageRenderer:
    """Image content renderer"""
    
    async def render(self, content: ContentItem, context: RenderContext) -> Optional[Any]:
        """Render image content"""
        try:
            image_data = content.data
            
            # Process image based on context quality
            processed_image = {
                'data': image_data,
                'position': content.position,
                'size': content.size,
                'quality': context.quality.value
            }
            
            return processed_image
            
        except Exception as e:
            logging.error(f"Error rendering image: {e}")
            return None


class VideoRenderer:
    """Video content renderer"""
    
    async def render(self, content: ContentItem, context: RenderContext) -> Optional[Any]:
        """Render video content"""
        try:
            video_data = content.data
            
            # Setup video playback
            video_config = {
                'data': video_data,
                'position': content.position,
                'size': content.size,
                'quality': context.quality.value,
                'hardware_acceleration': context.hardware_acceleration
            }
            
            return video_config
            
        except Exception as e:
            logging.error(f"Error rendering video: {e}")
            return None


class HTMLRenderer:
    """HTML content renderer"""
    
    async def render(self, content: ContentItem, context: RenderContext) -> Optional[Any]:
        """Render HTML content"""
        try:
            html_content = content.data
            
            # Process HTML
            rendered_html = {
                'html': html_content,
                'position': content.position,
                'size': content.size,
                'viewport': context.resolution
            }
            
            return rendered_html
            
        except Exception as e:
            logging.error(f"Error rendering HTML: {e}")
            return None