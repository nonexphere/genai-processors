# Copyright 2025 DeepMind Technologies Limited. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
"""Video processors."""

import asyncio
import enum
import io
from typing import AsyncIterable, Optional
import cv2
from genai_processors import content_api
from genai_processors import processor
from genai_processors import streams
from genai_processors import utils
import PIL.Image

ProcessorPart = content_api.ProcessorPart


class VideoMode(enum.Enum):
  """Video mode for the VideoIn processor."""

  CAMERA = "camera"
  SCREEN = "screen"


class VideoIn(processor.Processor):
  """Generates image parts from a camera or a computer screen.

  This processor inserts the generated image parts into the input stream.

  The image parts are tagged with a substream name (default "realtime") that can
  be used to distinguish them from other parts.
  """

  def __init__(
      self,
      substream_name: str = "realtime",
      video_mode: VideoMode = VideoMode.CAMERA,
  ):
    """Initializes the processor.

    Args:
      substream_name: The name of the substream to use for the generated images.
      video_mode: The video mode to use for the video. Can be CAMERA or SCREEN.
    """
    self._video_mode = video_mode
    self._substream_name = substream_name

  async def __call__(
      self, content: AsyncIterable[ProcessorPart]
  ) -> AsyncIterable[ProcessorPart]:
    output_queue = asyncio.Queue[Optional[ProcessorPart]]()
    async with asyncio.TaskGroup() as tg:
      if self._video_mode == VideoMode.CAMERA:
        video_task = tg.create_task(self.get_frames(output_queue))
      elif self._video_mode == VideoMode.SCREEN:
        video_task = tg.create_task(self.get_screen(output_queue))
      else:
        raise ValueError(f"Unsupported video mode: {self._video_mode}")
      input_stream = streams.merge(
          [content, utils.dequeue(output_queue)], stop_on_first=True
      )
      async for part in input_stream:
        yield part

      video_task.cancel()

  def _get_single_camera_frame(self, cap) -> Optional[ProcessorPart]:
    """Get a single frame from the camera."""
    # Read the frame queue
    ret, frame = cap.read()
    if not ret:
      return None
    # Fix: Convert BGR to RGB color space
    # OpenCV captures in BGR but PIL expects RGB format
    # This prevents the blue tint in the video feed
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img = PIL.Image.fromarray(frame_rgb)  # Now using RGB frame
    img.thumbnail([1024, 1024])

    image_io = io.BytesIO()
    img.save(image_io, format="jpeg")
    image_io.seek(0)

    mime_type = "image/jpeg"
    image_bytes = image_io.read()
    return ProcessorPart(
        image_bytes,
        mimetype=mime_type,
        substream_name=self._substream_name,
        role="USER",
    )

  async def get_frames(
      self, output_queue: asyncio.Queue[Optional[ProcessorPart]]
  ):
    """Send frames from the camera to the output queue, 1 FPS."""
    # This takes about a second, and will block the whole program
    # causing the audio pipeline to overflow if you don't to_thread it.
    cap = await asyncio.to_thread(
        cv2.VideoCapture, 0
    )  # 0 represents the default camera

    while True:
      frame = await asyncio.to_thread(self._get_single_camera_frame, cap)
      if frame is None:
        print("No frame")
        output_queue.put_nowait(None)
        break

      output_queue.put_nowait(frame)
      await asyncio.sleep(1.0)

    # Release the VideoCapture object
    cap.release()

  def _get_single_screen_frame(self):
    """Get a single frame from the screen."""
    try:
      from mss import mss
    except ImportError:
      raise ImportError("Please install mss package using 'pip install mss'")
    sct = mss.mss()
    monitor = sct.monitors[0]

    i = sct.grab(monitor)

    mime_type = "image/jpeg"
    image_bytes = mss.tools.to_png(i.rgb, i.size)
    img = PIL.Image.open(io.BytesIO(image_bytes))

    image_io = io.BytesIO()
    img.save(image_io, format="jpeg")
    image_io.seek(0)

    image_bytes = image_io.read()
    return ProcessorPart(
        image_bytes,
        mimetype=mime_type,
        substream_name=self._substream_name,
        role="USER",
    )

  async def get_screen(
      self, output_queue: asyncio.Queue[Optional[ProcessorPart]]
  ):
    """Send frames from the screen to the output queue, 1 FPS."""

    while True:
      frame = await asyncio.to_thread(self._get_single_screen_frame)
      if frame is None:
        output_queue.put_nowait(None)
        break

      await asyncio.sleep(1.0)

      output_queue.put_nowait(frame)
