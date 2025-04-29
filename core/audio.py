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
"""Audio processors."""


import asyncio
import logging
import math
import time
from typing import AsyncIterable, Iterable, Optional
from genai_processors import content_api
from genai_processors import context as context_lib
from genai_processors import processor
from genai_processors import streams
from genai_processors import utils
from google.genai import types as genai_types
import pyaudio

ProcessorPart = content_api.ProcessorPart


# Maximum audio chunk/part duration in seconds.
MAX_AUDIO_PART_SEC = 0.05

# Audio output chunk size in bytes.
AUDIO_OUT_CHUNK_SIZE = 1024


def _audio_duration(audio_data: bytes, sample_rate: int) -> float:
  """Returns the duration of the audio data in seconds."""
  # 2 bytes per sample (16bits)
  return len(audio_data) / (2 * sample_rate)


def split_audio(
    audio_data: bytes,
    sample_rate: int,
    max_duration_sec: float = MAX_AUDIO_PART_SEC,
) -> Iterable[bytes]:
  """Splits audio data into chunks of max_duration_sec."""
  audio_data_length = len(audio_data)
  # 2 bytes per sample (16bits)
  chunk_target_bytes = int(max_duration_sec * sample_rate * 2)
  num_chunks = math.ceil(audio_data_length / chunk_target_bytes)
  for i in range(num_chunks):
    start = i * chunk_target_bytes
    end = min((i + 1) * chunk_target_bytes, audio_data_length)
    if start >= end:
      continue
    yield audio_data[start:end]


# Add accepted audio formats here.
AudioFormats = pyaudio.paInt16 | pyaudio.paInt24


class PyAudioIn(processor.Processor):
  """Receives audio input and inserts it into the input stream.

  The audio input is received from the default input device.

  The audio parts are tagged with a substream name (default "realtime") that can
  be used to distinguish them from other parts.
  """

  def __init__(
      self,
      pya: pyaudio.PyAudio,
      substream_name: str = "realtime",
      audio_format: AudioFormats = pyaudio.paInt16,  # 16-bit PCM.
      channels: int = 1,
      rate: int = 24000,
  ):
    """Initializes the audio input processor.

    Args:
      pya: The pyaudio object to use for capturing audio.
      substream_name: The name of the substream that will contain all the audio
        parts captured from the mic.
      audio_format: The audio format to use for the audio.
      channels: The number of channels in the audio.
      rate: The sample rate of the audio.
    """
    self._pya = pya
    self._format = audio_format
    self._channels = channels
    self._rate = rate
    self._substream_name = substream_name

  async def __call__(
      self, content: AsyncIterable[ProcessorPart]
  ) -> AsyncIterable[ProcessorPart]:
    """Receives audio input from the user and sends it to the model."""
    audio_queue = asyncio.Queue[Optional[ProcessorPart]]()

    async with asyncio.TaskGroup() as tg:
      audio_in_task = tg.create_task(self._get_audio(audio_queue))

      async for part in streams.merge(
          [content, utils.dequeue(audio_queue)], stop_on_first=True
      ):
        yield part
      audio_in_task.cancel()

  async def _get_audio(
      self, output_queue: asyncio.Queue[Optional[ProcessorPart]]
  ):
    """Listens to the audio input device."""
    mic_info = self._pya.get_default_input_device_info()
    self.audio_stream = await asyncio.to_thread(
        self._pya.open,
        format=self._format,
        channels=self._channels,
        rate=self._rate,
        input=True,
        input_device_index=mic_info["index"],
        frames_per_buffer=AUDIO_OUT_CHUNK_SIZE,
    )
    if __debug__:  # pylint: disable=undefined-variable
      kwargs = {"exception_on_overflow": False}
    else:
      kwargs = {}
    try:
      count = 0
      while True:
        data = await asyncio.to_thread(
            self.audio_stream.read, AUDIO_OUT_CHUNK_SIZE, **kwargs
        )
        await output_queue.put(
            ProcessorPart(
                genai_types.Part.from_bytes(
                    data=data,
                    mime_type=f"audio/l16;rate={self._rate}",
                ),
                substream_name=self._substream_name,
                role="USER",
            )
        )
        count += 1
        await asyncio.sleep(0)  # Allow `yield` from output_queue to run
    finally:
      output_queue.put_nowait(None)


class PyAudioOut(processor.Processor):
  """Receives audio output from a live session and talks back to the user.

  Uses pyaudio to play audio back to the user.

  All non audio parts are passed through based on the `passthrough_audio` param
  passed to the constructor.

  Combine this processor with `RateLimitAudio` to receive the audio chunks at
  the time where they need to be played back to the user.
  """

  def __init__(
      self,
      pya: pyaudio.PyAudio,
      audio_format=pyaudio.paInt16,  # 16-bit PCM.
      channels: int = 1,
      rate: int = 24000,
      passthrough_audio: bool = False,
  ):
    self._pya = pya
    self._format = audio_format
    self._channels = channels
    self._rate = rate
    self._passthrough_audio = passthrough_audio

  async def __call__(
      self, content: AsyncIterable[ProcessorPart]
  ) -> AsyncIterable[ProcessorPart]:
    """Receives audio output from a live session."""
    audio_output = asyncio.Queue[Optional[ProcessorPart]]()

    stream = await asyncio.to_thread(
        self._pya.open,
        format=self._format,
        channels=self._channels,
        rate=self._rate,
        output=True,
    )

    async def play_audio():
      while part := await audio_output.get():
        if part.part.inline_data is not None:
          await asyncio.to_thread(stream.write, part.part.inline_data.data)

    async with asyncio.TaskGroup() as tg:
      play_audio_task = tg.create_task(play_audio())

      async for part in content:
        if content_api.is_audio(part.mimetype):
          audio_output.put_nowait(part)
          if self._passthrough_audio:
            yield part
        else:
          yield part
      await audio_output.put(None)
      play_audio_task.cancel()


class RateLimitAudio(processor.Processor):
  """Splits and rate-limits the input audio parts for streaming audio output.

  Gemini API clients are expected to play streaming audio content to the user
  in its natural playback speed. As all audio parts are streamed at once, the
  client needs to stop playing back the audio when the user interrupts it.

  This processor does three things to address that:

    * Parts of potentially long streaming audio content are split into
      sub-parts of no more than 200 milliseconds. (Non-streaming audio is left
      alone, and count as "other parts" for the purposes of this processor.)
    * Parts are yielded from this processor at the rate of their natural
      playing speed, to put a reasonably tight limit on the amount of audio
      buffered beyond the agent's control.
    * Other parts are passed through unchanged. Debug/status parts are
      passed through as soon as possible, overtaking audio if needed.
  """

  def __init__(self, sample_rate: int, delay_other_parts: bool = True):
    """Initializes the rate limiter.

    Args:
      sample_rate: The sample rate of the audio. A typical value is 24000
        (24KHz)
      delay_other_parts: If true, other parts will be delayed until the audio is
        played out. If false, other parts will be passed through as soon as
        possible, overtaking audio if needed.
    """
    self._sample_rate = sample_rate
    self._delay_other_parts = delay_other_parts

  async def __call__(
      self, content: AsyncIterable[ProcessorPart]
  ) -> AsyncIterable[ProcessorPart]:
    """Rate limits audio output."""
    # Most inputs queue here. When full, the fast-tracking of status/debug
    # chunks starts to block, so let's be generous with the queue size.
    audio_queue = asyncio.Queue[Optional[ProcessorPart]](10_000)
    # Delays in outputting from this queue distort the time estimations for
    # audio sub-chunks, so let's bound its size tightly.
    output_queue = asyncio.Queue[Optional[ProcessorPart]](3)

    async def consume_content():
      async for part in content:
        if content_api.is_audio(part.mimetype):
          # Split the audio into small parts so that when we interrupt between
          # them, we don't have to wait to long before interrupting.
          if (
              part.part.inline_data is not None
              and _audio_duration(part.part.inline_data.data, self._sample_rate)
              > 2 * MAX_AUDIO_PART_SEC
          ):
            counter = 0
            for sub_part in split_audio(
                part.part.inline_data.data, self._sample_rate
            ):
              counter += 1
              audio_queue.put_nowait(
                  ProcessorPart(
                      genai_types.Part.from_bytes(
                          data=sub_part,
                          mime_type=part.mimetype,
                      )
                  )
              )
          else:
            audio_queue.put_nowait(part)
        elif part.get_custom_metadata("interrupted"):
          logging.info(
              "%s - Interrupted - flush audio queue", time.perf_counter()
          )
          # Flush the audio queue - stop rate limiting audio asap.
          while not audio_queue.empty():
            audio_queue.get_nowait()
          self._audio_duration = 0.0
        elif (
            not self._delay_other_parts
            or part.substream_name in context_lib.get_reserved_substreams()
        ):
          await output_queue.put(part)
          await asyncio.sleep(0)  # Allow `yield` from output_queue to run
        else:
          await audio_queue.put(part)
      await audio_queue.put(None)

    async def consume_audio():
      start_playing_time = self._perf_counter() - 3600  # 1h back.
      while part := await audio_queue.get():
        if content_api.is_audio(part.mimetype):
          start_playing_time = max(
              self._perf_counter() - 0.05, start_playing_time
          )
          # Remove the 0.05 seconds delay to avoid the audio being cut off
          sleep_sec = max(0, start_playing_time - self._perf_counter())
          if sleep_sec > 1e-3:
            await self._asyncio_sleep(sleep_sec)
          await output_queue.put(part)
          await asyncio.sleep(0)  # Allow `yield` from output_queue to run
          start_playing_time += _audio_duration(
              part.part.inline_data.data, self._sample_rate
          )
        else:
          await output_queue.put(part)
      await output_queue.put(None)

    async with asyncio.TaskGroup() as tg:
      consume_audio_task = tg.create_task(consume_audio())
      consume_content_task = tg.create_task(consume_content())
      while part := await output_queue.get():
        yield part
      consume_content_task.cancel()
      consume_audio_task.cancel()

  # The following wrappers allow unit-tests to mock out walltime.
  def _perf_counter(self):
    return time.perf_counter()

  async def _asyncio_sleep(self, delay: float) -> None:
    await asyncio.sleep(delay)
