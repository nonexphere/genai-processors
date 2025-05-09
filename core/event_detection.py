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
r"""Event detection processor.

This processor detects events from the images it receives in its input stream:

 * All input is propagated to the output.
 * Last `max_images` encountered in the input are used to detect event.
 Non-image content is ignored.
 * If an event is detected corresponding ProcessorParts are injected in-to the
 output.
 * Event detection is asynchronous so events may not necessarily be injected
 after the ProcessorPart on which it has been observed.


It keeps making calls to the model passed in the constructor to detect events
in the images. When the model is generating a response, the processor keeps
collecting up to `max_images` coming up in the input stream and sends them all
together to the model in the next call. `max_images` is a parameter that
controls the number of images to keep in the input stream and should be tuned
based on the image frequency in the input stream and the latency of the model
to generate a response. With a FPS of 1, a `max_images` of 5 is a reasonable
value.

The event detection can be paused and resumed for a given event name.

The set of events should be defined by an Enum class. The model response will
be a string that matches one of the values of the Enum.


```py
import enum

# Only use the enum.auto() function to define the values of the enum. Or ensure
# all the string values are lower case.
class EventName(enum.StrEnum):
  SUNNY = enum.auto()
  RAINING = enum.auto()
  RAINING_WITH_MEATBALLS = enum.auto()
```

The config passed to the constructor should contain the response schema for
the event detection model.

```python
config = {
    system_instruction=(
        "Determine the weather conditions under which these images have been"
        f" taken. Respond with '{EventName.SUNNY}' if the sun is shining, "
        f"'{EventName.RAINING}' if it is raining and"
        f"'{EventName.RAINING_WITH_MEATBALLS}' if the rain contains \meatballs."
        " You can classify any edible objects as meatballs.",
    "response_mime_type": "text/x.enum",
    "response_schema": EventName
    ...
}
```

Each event is associated to an output that the processor will generate when the
event is detected. The output should be a `ProcessorPart` and is defined by the
user. It is specified in the constructor via the `output_dict` argument.

```python
output_dict = {
    EventName.EVENT_1: ProcessorPart(
        text="event_1 is detected",
        role="USER",
        end_of_turn=True,
    ),
    EventName.EVENT_2: ProcessorPart(
        text="event_2 is detected",
        role="USER",
        end_of_turn=True,
    ),
}
```

Lastly, the sensitivity dictionary passed to the constructor is used to
define the number of detections in a row that should happen before the event
detection processor sends a detection output. The keys of this dictionary should
be the event names and the values should be the number of detection in a row.

This is helpful in noisy situations where you want to have confirmation of a
detection before you generate an output for the event detection.
"""

import asyncio
import collections
import dataclasses
import time
from typing import AsyncIterable, Optional
from absl import logging
from genai_processors import content_api
from genai_processors import processor
from genai_processors.core import timestamp
from google import genai
from google.genai import types as genai_types

ProcessorPart = content_api.ProcessorPart


def print_exception(tag: str, e: Exception):
  if isinstance(e, ExceptionGroup):
    for e in e.exceptions:
      print_exception(tag, e)
  else:
    print(f"Exception in {tag}: {e}")
    raise e


@dataclasses.dataclass
class EventState:
  """State of an single event detection."""

  # True if the event detection is paused. The detection should not output
  # anything when the event is detected but paused.
  paused: bool = False
  # The time in seconds when the event was last detected. The reference time is
  # not specified. To be used to compute duration, not absolute time.
  detection_time_sec: float = 0
  # True if the event is detected.
  event_detected: bool = False
  # Number of detection in a row that should happen before the event detection
  # processor sends a detection output.
  sensitivity: int = 1
  # When events represent transitions between states (e.g. activities: still,
  # moving, running, ...) some of them can be more specific states included in
  # others (e.g. running is included in moving). If we are already in a more
  # specific state we don't want to to transition to a less specific one. This
  # set represents the events that are more generic than the current event and
  # should be ignored when we're already in this state.
  included_in: set[str] = dataclasses.field(default_factory=set)
  # Output to return when the event is detected.
  output: content_api.ProcessorContent = dataclasses.field(
      default_factory=content_api.ProcessorContent
  )


class EventDetection(processor.Processor):
  """Event detection processor."""

  def __init__(
      self,
      api_key: str,
      model: str,
      config: genai_types.GenerateContentConfig,
      output_dict: dict[str, content_api.ProcessorContentTypes],
      sensitivity: Optional[dict[str, int]] = None,
      included_in: Optional[dict[str, set[str]]] = None,
      max_images: int = 5,
  ):
    """Initializes the event detection processor.

    Args:
      api_key: The API key to use for the event detection model.
      model: The model to use for the event detection.
      config: The configuration to use for the event detection model. This
        configuration should contain the response schema for the event detection
        model.
      output_dict: A dictionary of event names to the output to return when the
        event is detected. All event names should be in the keys of this dict.
      sensitivity: A dictionary of event names to the number of detection in a
        row that should happen before the event detection processor sends a
        detection output.
      included_in: A dictionary of event names to the set of events that are
        more specific than the key, e.g. {"running": {"moving"}}.
      max_images: The maximum number of images to keep in the input stream.
    """
    self._client = genai.Client(api_key=api_key)
    self._model = model
    self._config = config

    if not config.response_schema:
      raise ValueError("Response schema is required for event detection.")

    self._event_states: dict[str, EventState] = {}
    for event_name, output in output_dict.items():
      self._event_states[event_name.lower()] = EventState(
          output=content_api.ProcessorContent(output)
      )
      # All events are included in themselves.
      self._event_states[event_name.lower()].included_in = set(
          [event_name.lower()]
      )
    if sensitivity:
      for event_name, sensitivity_value in sensitivity.items():
        self._event_states[event_name.lower()].sensitivity = sensitivity_value

    if included_in:
      for event_name, included_set in included_in.items():
        self._event_states[event_name.lower()].included_in.update(included_set)
    self._event_counter = collections.defaultdict(int)
    self._last_event_detected = ""

    # deque of (image, timestamp) tuples.
    self._images = collections.deque[tuple[ProcessorPart, float]](
        maxlen=max_images
    )

  def pause_detection(self, event_name: str):
    """Pause event detection for `event_name`.

    Args:
      event_name: The name of the event to pause. This should be one of the keys
        in the `output_dict` passed to the constructor.
    """
    event_state = self._event_states[event_name.lower()]
    event_state.paused = True
    event_state.event_detected = False
    self._event_counter[event_name.lower()] = 0
    self._last_event_detected = ""

  def resume_detection(self, event_name: str) -> None:
    """Resumes event detection for `event_name`."""
    self._event_states[event_name.lower()].paused = False

  def event_state(self, event_name: str) -> EventState:
    return self._event_states[event_name.lower()]

  def _update_counter(self, event_name: str) -> None:
    """Updates the counter for `event_name`."""
    if self._event_states.get(event_name.lower()) is None:
      raise ValueError(
          f"Event name {event_name} is not in the event states. Please check"
          " the `output_dict` passed to the constructor."
      )
    if self._event_states[event_name.lower()].paused:
      # Do not update the counter if the event is paused.
      return
    for k in self._event_states:
      if k == event_name.lower():
        self._event_counter[k] += 1
      else:
        self._event_counter[k] = 0

  async def detect_event(
      self,
      output_queue: asyncio.Queue[ProcessorPart],
  ):
    """Detects an event in the image."""
    images_with_timestamp = []
    start_time = None
    for image, t in self._images:
      if start_time is None:
        start_time = t
      images_with_timestamp.append(image)
      images_with_timestamp.append(
          content_api.ProcessorPart(timestamp.to_timestamp(t - start_time))
      )
    response = await self._client.aio.models.generate_content(
        model=self._model,
        config=self._config,
        contents=images_with_timestamp,
    )
    logging.debug(
        "%s - Event detection response: %s / %s",
        time.perf_counter(),
        response.text,
        self._last_event_detected,
    )
    if not response.text:
      logging.debug(
          "%s - No text response from the event detection model",
          time.perf_counter(),
      )
      return

    # Only interrupt if the event is detected(commentating on) and not already
    # interrupted.
    event_name = response.text.lower()
    self._update_counter(event_name)
    if event_name in self._event_states:
      event_state = self._event_states[event_name]
      if (
          not event_state.paused
          and self._event_counter[event_name] >= event_state.sensitivity
      ):
        if self._last_event_detected not in event_state.included_in:
          logging.debug(
              "%s - New event detection: %s", time.perf_counter(), response.text
          )
          event_state.event_detected = True
          event_state.detection_time_sec = time.perf_counter()
          for part in event_state.output:
            output_queue.put_nowait(part)
        self._last_event_detected = event_name

  async def __call__(
      self, content: AsyncIterable[ProcessorPart]
  ) -> AsyncIterable[ProcessorPart]:
    """Run the event detection processor."""
    output_queue = asyncio.Queue()

    async with asyncio.TaskGroup() as tg:

      async def consume_content():
        image_detection_task = None
        async for part in content:
          output_queue.put_nowait(part)
          if content_api.is_image(part.mimetype):
            self._images.append((part.part, time.perf_counter()))
            if image_detection_task is None or image_detection_task.done():
              # Only run one image detection task at a time when the previous
              # one is done. Use a single image to minimize detection latency.
              image_detection_task = tg.create_task(
                  self.detect_event(output_queue)
              )
        output_queue.put_nowait(None)
        if image_detection_task is not None:
          try:
            image_detection_task.cancel()
            await image_detection_task
          except asyncio.CancelledError:
            pass

      consume_content_task = tg.create_task(consume_content())

      while chunk := await output_queue.get():
        yield chunk

      await consume_content_task
