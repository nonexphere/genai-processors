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
"""Module to manage a real time conversation with GenAI processors.

A client side hackable alternative to the Gemini Live API: wraps a turn based
non streaming model into a bidirectional streaming API. See LiveModelProcessor
for details.

genai_processors.core.live_model provides server-side bidirectional streaming
API. It is more efficient as it does not require sending the whole conversation
over the network on each turn. But this also makes it rigid. Client-side
implementation provided by this module can be easily adjusted according to the
application needs.
"""

import asyncio
import collections
from collections.abc import AsyncIterable
import enum
import time
import traceback

from genai_processors import content_api
from genai_processors import context
from genai_processors import debug
from genai_processors import mime_types
from genai_processors import processor
from genai_processors import streams
from genai_processors.core import speech_to_text


ProcessorPart = content_api.ProcessorPart
PartProcessor = processor.PartProcessor
Processor = processor.Processor

CONVERSATION_START = '\nThe following is your conversation so far:\n'

# Substream name to output part directly as is without going through the model.
DIRECT_OUTPUT_SUBSTREAM = speech_to_text.TRANSCRIPTION_SUBSTREAM_NAME
# Metadata key that should be set to True if the part that is output directly
# as text (see DIRECT_OUTPUT_TEXT) should also be in the prompt.
DIRECT_OUTPUT_IN_PROMPT = 'is_final'


class _RollingPrompt:
  """Rolling prompt (aka iterator of prompts) for conversation processors.

  A real-time prompt can be seen as an infinite stream of multimodal parts.
  Calling an LLM requires transforming this stream into a finite prompt
  representing the world state at the user's request time.

  This is achieved through this RollingPrompt class, an object storing all
  parts from the real-time stream. This object can be converted into a finite
  sequence of parts at any given time when a model call is required. The process
  works as follows:

  Create a rolling prompt and begin adding parts using `add_part`:

  ```python
  rolling_prompt = _RollingPrompt()
  async for part in realtime_stream:
    rolling_prompt.add_part(part)
  ```

  `realtime_stream` represents an infinite stream. The loop should never block,
  ensuring continuous processing of incoming parts. The rolling prompt will
  constantly receive and add incoming parts, even while the model computes an
  answer. This has implications as explained further.

  As soon as the prompt is created, you can get access to its content via
  `pending()`. This returns a queue for feeding a model early on. This
  approach minimizes Time To First Token (TTFT) by processing parts upon
  arrival. In the example below, input_processor processes input parts eagerly
  before the model call:

  ```python
  model_prompt = rolling_prompt.pending()  # This is an asyncio.Queue

  # Some processors that need to run before calling the model.
  input_processor = speech_to_text + ...
  # Some processors that need to run after calling the model.
  output_processor = text_to_speech + ...
  your_agent = (
    input_processor + genai_model.GenaiModel(...) + output_processor
  )

  # Call agent in a separate asyncio task so that it will start processing
  # all parts concurrently. This task will be cancelled when the user starts
  # talking.
  async def run_agent():
    async for output in your_agent(streams.dequeue(model_prompt)):
    ...
  processor.create_task(run_agent())

  # Eventually, finalize the rolling_prompt, this will trigger the model call.
  rolling_prompt.finalize_pending()
  ```

  This action cuts the prompt and closes the previously used pending prompt.
  Consequently, the concurrently running model call will eventually complete,
  allowing processing of the output parts. These can be sent back to the user
  and added to the prompt, reflecting both user and model turns.

  During the interval between prompt finalization and the first user-received
  output part (potentially several seconds), the real-time stream continues,
  adding new parts to the prompt. Consider image frames from a video stream
  arriving at the stream's FPS rate (1 per second at least), directly adding
  these parts using `add_part` could incorrectly place model turns. For
  example, while the model is computing on previous video frames, new images
  appear and precede the model's answer in the prompt, falsely suggesting the
  model considered the new images during computation.

  To address this, use `add_part_when_model_outputting`. This method ensures
  parts are placed after the model's response, maintaining prompt consistency.
  This method should only be used while the model actively generates output.
  """

  def __init__(
      self,
      duration_prompt_sec: float | None = 600,  # 10 minutes
  ):
    """Initializes the rolling prompt.

    Args:
      duration_prompt_sec: the length of the prompt in terms of the time when
        the parts were added: we consider any part added after now -
        duration_prompt_sec. Set to None to keep all incoming parts. Set to 10
        minutes by default.
    """
    # Current prompt as a queue.
    self._pending = asyncio.Queue[ProcessorPart | None]()
    # Main prompt content used to build the next prompt and the prompt queues.
    self._conversation_history = collections.deque(maxlen=10_000)
    # Time of parts in the conversation history. This deque should be kept in
    # sync with the conversation history.
    self._time_conversation_history_sec = collections.deque(maxlen=10_000)
    # parts sent to the model while the model is outputing.
    self._parts_while_outputting: list[ProcessorPart] = []
    # max time to keep the parts in the prompt
    self._duration_prompt_sec = duration_prompt_sec

  def add_part_when_model_outputting(self, part: ProcessorPart):
    """Adds a part to the prompt once the model is done."""
    self._parts_while_outputting.append(part)

  def model_done(self):
    """Adds all parts that were sent to the model while it was outputing."""
    for part in self._parts_while_outputting:
      self.add_part(part)
    self._parts_while_outputting = []

  def add_part(
      self,
      part: ProcessorPart,
  ) -> None:
    """Adds a part to the current prompt."""
    self._conversation_history.append(part)
    self._time_conversation_history_sec.append(time.perf_counter())
    self._pending.put_nowait(part)

  def pending(self) -> asyncio.Queue[ProcessorPart | None]:
    """Get current pending prompt.

    Note that the returned queue can be empty as it might be consumed by a
    model to generate output. If you need to get a new pending prompt queue to
    check the current content of the prompt, call `new_pending()` instead.

    Returns:
      The current pending prompt as a queue that can be consumed or turned into
      an AsyncIterable using streams.dequeue() to feed a model or another
      processor.
    """
    return self._pending

  def finalize_pending(self) -> None:
    """Close the current pending prompt.

    This must be called eventually to ensure that the pending prompt is finite.
    When called, it adds a None part to the end of the queue to signal the end
    of the prompt. Any model or processor using the pending prompt as input
    would then receive a signal that the prompt is finished and includes all
    input parts.
    """
    self._pending.put_nowait(None)

  def _cut_conversation_history(self):
    """Removes old parts from the conversation history."""
    if not self._conversation_history:
      return
    time_cut_point = time.perf_counter() - self._duration_prompt_sec
    while (
        self._conversation_history
        and self._time_conversation_history_sec[0] < time_cut_point
    ):
      self._conversation_history.popleft()
      self._time_conversation_history_sec.popleft()

  def new_pending(self) -> asyncio.Queue[ProcessorPart | None]:
    """After finalize_pending(), prep the prompt for the next model call.

    This method must be called everytime a model is called with a new prompt.
    It creates a new pending prompt queue that can be fed to a model or a
    processor.

    Returns:
      A new pending prompt queue that can be fed to a model or a processor.
    """
    self._pending = asyncio.Queue[ProcessorPart | None]()
    self._cut_conversation_history()
    for part in self._conversation_history:
      self._pending.put_nowait(part)
    return self._pending


class AudioTriggerMode(enum.StrEnum):
  """Trigger model mode."""

  # Trigger model when user is done talking. This is appropriate for Audio
  # models. Note that the final transcription might not be in the prompt when
  # using this mode as the transcription requires an extra step compared to
  # detecting speech activity.
  END_OF_SPEECH = 'end_of_speech'
  # Trigger model when the final transcription is available. This is appropriate
  # for Text models. It is slower than END_OF_SPEECH as it requires an extra
  # step to get the final transcription.
  FINAL_TRANSCRIPTION = 'final_transcription'


class LiveModelProcessor(Processor):
  """Converts a turn-based model into a real-time aka live processor.

  The `turn_processor` passed in the constructor models a single turn, i.e. a
  GenAI model or a processor that works with a finite input stream aka prompt.

  This live processor takes an infinite input stream. It creates a "rolling"
  (aka sliding) prompt from this infinite input stream by cutting it at given
  times (e.g. when the user is done talking). This prompt is fed to the
  `turn_processor` to generate a response. This response is then added to the
  rolling prompt to contribute to the next prompt and the cycle repeats.

  The live processor can be used with Audio or Text inputs. The turn_based_model
  is triggered for a `part` with `content_api.is_end_of_turn(part)==True` or
  with `part==speech_to_text.EndOfSpeech`.

  While the live processor could take Image inputs as well, we do not recommend
  it as the current implementation does not have any caching of image
  tokenization. This means the image in the rolling prompt will be retokenized
  by the model each time. This is not efficient and will slow down the model
  call. Before we fix it in a future version of the library, you can for now
  develop a work-around by changing how the rolling prompt handles image parts
  (i.e. do not repeat images, only send the latest one).
  """

  def __init__(
      self,
      turn_processor: Processor,
      duration_prompt_sec: float | None = 600,  # 10 minutes
      trigger_model_mode: AudioTriggerMode = AudioTriggerMode.FINAL_TRANSCRIPTION,
  ):
    """Initializes the live model processor.

    Args:
      turn_processor: A processor that models a single turn. This can be a GenAI
        model or a processor that works with a finite input stream.
      duration_prompt_sec: the time in seconds to keep the prompt in the model
        prompt. Set to None to keep the entire prompt. Set to 10 minutes by
        default.
      trigger_model_mode: The mode to trigger the model with audio signals. We
        can trigger a model call by detecting the end of speech or when the
        final transcription is available. The choice of the mode will depend on
        the type of the model. For a `turn_processor` that works with text only,
        we recommend using FINAL_TRANSCRIPTION: this is when the speech to text
        model has finished transcribing the user's speech (note that this adds a
        bit of latency compared to END_OF_SPEECH). For a `turn_processor` that
        works with audio, we recommend using END_OF_SPEECH as it will always
        happen before FINAL_TRANSCRIPTION and will delimit (with
        START_OF_SPEECH) the audio parts where the user talked. If the
        `turn_processor` accepts audio and text inputs, quality can be improved
        by using FINAL_TRANSCRIPTION at the cost of latency.
    """
    self._single_turn_processor = turn_processor
    self.duration_prompt_sec = duration_prompt_sec
    self._trigger_model_mode = trigger_model_mode

  async def _conversation_loop(
      self,
      content: AsyncIterable[ProcessorPart],
      output_queue: asyncio.Queue[ProcessorPart | None],
      rolling_prompt: _RollingPrompt,
  ):
    user_not_talking = asyncio.Event()
    user_not_talking.set()
    conversation_model = _RealTimeConversationModel(
        output_queue=output_queue,
        generation=self._single_turn_processor,
        rolling_prompt=rolling_prompt,
        user_not_talking=user_not_talking,
    )

    async for part in content:
      if context.is_reserved_substream(part.substream_name):
        output_queue.put_nowait(part)
      elif part.substream_name == DIRECT_OUTPUT_SUBSTREAM:
        # part returned to the user as is. It is used in the model prompt only
        # when DIRECT_OUTPUT_IN_PROMPT=True in its metadata.
        part.substream_name = ''
        output_queue.put_nowait(part)
        if part.metadata[DIRECT_OUTPUT_IN_PROMPT]:
          # The final transcription is kept in the prompt as a user input.
          conversation_model.user_input(
              content_api.ProcessorPart(part, substream_name='')
          )
          if self._trigger_model_mode == AudioTriggerMode.FINAL_TRANSCRIPTION:
            # await conversation_model.cancel()
            conversation_model.turn()
      elif mime_types.is_dataclass(part.mimetype, speech_to_text.StartOfSpeech):
        # User starts talking.
        user_not_talking.clear()
        await conversation_model.cancel()
      elif mime_types.is_dataclass(part.mimetype, speech_to_text.EndOfSpeech):
        # User is done talking, a conversation turn is requested.
        user_not_talking.set()
        if self._trigger_model_mode == AudioTriggerMode.END_OF_SPEECH:
          await conversation_model.cancel()
          conversation_model.turn()
      elif content_api.is_end_of_turn(part):
        # A conversation turn is requested outside of audio/speech signals.
        await conversation_model.cancel()
        conversation_model.turn()
      else:
        conversation_model.user_input(part)

    await conversation_model.finish()

    output_queue.put_nowait(None)

  async def call(
      self, content: AsyncIterable[ProcessorPart]
  ) -> AsyncIterable[ProcessorPart]:
    """Generates a conversation with a model."""
    output_queue = asyncio.Queue[ProcessorPart | None]()
    rolling_prompt = _RollingPrompt(
        duration_prompt_sec=self.duration_prompt_sec
    )
    # Create the main conversation loop.
    control_loop_task = processor.create_task(
        self._conversation_loop(
            content,
            output_queue,
            rolling_prompt=rolling_prompt,
        )
    )

    async for part in streams.dequeue(output_queue):
      yield part

    await control_loop_task


class _RealTimeConversationModel:
  """Converts an GenAI processor into a model that can be interrupted."""

  def __init__(
      self,
      output_queue: asyncio.Queue[ProcessorPart | None],
      generation: Processor,
      rolling_prompt: _RollingPrompt,
      user_not_talking: asyncio.Event,
  ):
    self._output_queue = output_queue
    self._prompt = rolling_prompt
    self._user_not_talking = user_not_talking

    self._generation = generation
    # We start enqueuing what is in the prompt into the model to process parts
    # ahead of time whenever possible, we will finalize this call in turn().
    p = debug.TTFTSingleStream('Model Generate', self._generation)
    self._pending_generate_output = asyncio.create_task(
        context.context_cancel_coro(
            self._generate_output(p(streams.dequeue(self._prompt.pending()))),
        )
    )
    self._current_generate_output = None

    # Use an event instead of current_task.done() to allow for cancellation not
    # block the main control loop.
    self._model_done = asyncio.Event()
    self._model_done.set()
    self._pending_turn_task = None

  def user_input(self, part: ProcessorPart):
    """Callback for when the user has a new input."""
    if not self._model_done.is_set():
      self._prompt.add_part_when_model_outputting(part)
    else:
      self._prompt.add_part(part)

  async def cancel(self):
    """Cancels the current model call and pending turn, resets the prompt."""
    if (
        self._current_generate_output is not None
        and not self._model_done.is_set()
    ):
      self._current_generate_output.cancel()
      # Wait for the current generate output to be done. As commented below, the
      # model_done event might not be set if the current generate output is
      # cancelled before entering the try/finally code block. So we stop here
      # whenever generate_output is done or model_done is set.
      done_task = processor.create_task(self._model_done.wait())
      await asyncio.wait(
          (
              done_task,
              self._current_generate_output,
          ),
          return_when=asyncio.FIRST_COMPLETED,
      )
      # current_generate_output can be cancelled before entering the try/finally
      # code block which would not set the model_done event to true nor run the
      # prompt model done clean-up. Ensure we do it here when we know the
      # current generate output is done.
      if not done_task.done() or not done_task.cancelled():
        self._model_done.set()
        self._prompt.model_done()

  async def finish(self):
    """Cancels the current model call and finishes all pending work.

    Finishes the pending generate task which will make a last call to the model.
    This might not appear on the client/UI but will still be computed by the
    model and can be recorded in logs if the processor is wrapped in a logger.
    """
    if (
        self._current_generate_output is not None
        and not self._model_done.is_set()
    ):
      await self.cancel()
    # We still have to finalize the pending request to make sure the model
    # output is processed. This will trigger a new model call whenever the input
    # stream is closed.
    self._prompt.finalize_pending()
    self._model_done.clear()
    if self._pending_generate_output is not None:
      await self._pending_generate_output
      if self._pending_generate_output.exception():
        raise self._pending_generate_output.exception()
      await self._model_done.wait()

  def turn(self):
    """Finalises the pending request and creates a new one."""
    self._model_done.clear()
    # This is a model turn. Finish the current prompt and start a new one.
    self._current_generate_output = self._pending_generate_output
    self._prompt.finalize_pending()
    self._prompt.new_pending()
    # Prepare a new pending task for the next turn. This will do all the
    # pre-processing ahead of time whenever possible.
    p = debug.TTFTSingleStream('Model Generate', self._generation)
    stream_content = p(streams.dequeue(self._prompt.pending()))
    self._pending_generate_output = processor.create_task(
        context.context_cancel_coro(
            self._generate_output(stream_content),
        )
    )

  async def _generate_output(self, content: AsyncIterable[ProcessorPart]):
    """Streams back `content` to the user."""
    try:
      await self._read_model_output(content)
    except Exception as e:
      traceback.print_exception(e)
      raise
    finally:
      self._model_done.set()
      self._prompt.model_done()

  async def _read_model_output(self, content: AsyncIterable[ProcessorPart]):
    """Sends the model output to the user, context buffer, and pending queue."""
    part_to_prompt = []
    try:
      async for part in content:
        self._output_queue.put_nowait(part)
        if (
            content_api.is_text(part.mimetype)
            or content_api.is_image(part.mimetype)
        ) and (part.role.lower() in ['user', 'model']):
          part_to_prompt.append(part)
    finally:
      # We add the prompt whatever has been output. We do this once everything
      # is output to avoid feeding the prompt while it's used to compute the
      # output.
      for c in part_to_prompt:
        self._prompt.add_part(c)
