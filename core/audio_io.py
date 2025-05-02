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
from typing import AsyncIterable, Optional
from genai_processors import content_api
from genai_processors import processor
from genai_processors import streams
from genai_processors import utils
from google.genai import types as genai_types
import pyaudio

ProcessorPart = content_api.ProcessorPart

# Audio output chunk size in bytes.
AUDIO_OUT_CHUNK_SIZE = 1024

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
