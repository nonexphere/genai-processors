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

r"""Live commentator using GenAI Processors.

You can run this example from a CLI directly or from AI Studio.
See commentator_cli.py or commentator_ais.py for usage.

The commentator observes the incoming video/audio feed and produces an audio
commentary on it. While it is the agent who drives the conversation, it is
interactive and can be interruped/corrected by a user.

This example makes a good use of the various ways the Gemini API can receive
content:
 * `system_instruction`: guidelines for the model provided by the agent
   developers. They are hardcoded in this file in the PROMPT_PARTS variable.
 * `session.send_client_content` is used for turn-by-turn scenarios and is
   analogous to what `client.generate_content` does. We use it to provide any
   additional context (non audio and video feeds) to the model. `EventDetector`
   uses this option as it is optimal for its fixed cadence, turn-based
   operation.
 * `session.send_realtime_input` is used for realtime interactive input and has
   built-in voice activation detection (VAD). This allows us to have lower
   latency and makes the model automatically respond to user's utterances. Note
   that
   audio commentary from the model itself needs to be filtered out to avoid VAD
   activating erroneously. We rely on the echo cancellation built into the
   browser for that.
 * **Async function calls**: Gemini API now supports function calls that don't
   block the generation and can even stream their output back to the model. If
   the INTERRUPT scheduling strategy is used, they will interrupt ongoing
   inference and restart it with the latest information available.

The standard Gemini Live API is well suited for the use case where the user
drives the conversation and the model responds when prompted. The live
commentator agent, on the contrary, drives the conversation, keeps commentating
while still reacting to events and to what the user asks.

A naive approach would be to generate one second of commentary every second.
 However, models can produce output much faster than realtime, and forcing
 them to be in a lockstep with the real world will either leave the TPUs
idle or induce a huge overhead on maintaining or recalculating the KV cache.
 Also text-to-speech works better if it can work on longer sentences.

So, we employ a more event-driven approach:

 * Let the model produce long-ish commentary.
 * Slow down the streaming of these comments to real-time using the
   `RateLimitAudio` processor.
 * Rely on Gemini API built-in voice activation detection to notice if the user
   speaks over, corrects, or asks the agent.
 * Run a cheap model to detect whether something notable has happened that the
   agent should interrupt its current speech and generate a new phrase.

The async function calls play the crucial role in driving the interruption
process. We register the `start_commentating` tool which drives the timing when
the model should be making comments. It is the model itself, not a tool, that
produces comments. By using `behaviour="NON_BLOCKING"` the tool is able to
schedule the generation of the next comment without interrupting the current
one.
It also makes the model ingest the latest observations and tells the model
whether
 it should continue its previous comment or react to an interruption.

By representing the agent as an async function we also give the model ability to
 start and stop commentating at will. If the user asks to stop commentating, the
 model will cancel the tool call and turn into a regular voice activated agent.
 When asked to start commentating, the model will invoke `start_commentating`
 tool,
which will awake the event detection loop.
"""

import asyncio
import collections
import dataclasses
import enum
import time
from typing import Any, AsyncIterable, Optional

from absl import logging
from genai_processors import content_api
from genai_processors import processor
from genai_processors import streams
from genai_processors import utils
from genai_processors.core import event_detection
from genai_processors.core import live_model
from genai_processors.core import timestamp
from google.genai import types as genai_types
import numpy as np


# Model to use for the live api processor.
MODEL_LIVE = "models/gemini-2.0-flash-live-001"

# Model to use for the event detection processor.
MODEL_DETECTION = "models/gemini-2.0-flash-lite"

# Number of seconds during which the detection should detect a "no event" before
# stopping the commentator.
NO_DETECTION_SENSITIVITY_SEC = 3

# Audio config
RECEIVE_SAMPLE_RATE = 24000

# User message when the agent detects it should continue commentating.
COMMENT_MSG = (
    "Continue commentating on what you see, do not repeat the same comments."
    " Always address the persons in the camera as 'you' and assume they can"
    " hear you and are in the same room. Remember this is a conversation."
    " Do not cancel the commentating unless the user explicitly asks you to."
)
# User message when the agent detects something special that should interrupt
# the commentating.
INTERRUPT_COMMENT_MSG = (
    "Interrupt the current commentary to comment what you see now. Start your"
    " comment as if you were interrupting yourself. Then commentate on the new"
    " event that just triggered this interruption. Do not cancel the"
    " commentary."
)

# Async function declarations.
TOOLS = [
    genai_types.Tool(
        function_declarations=[
            # start_commentating tool drives the timing when the model should
            # be making comments. It is the model itself, not a tool, that
            # produces comments. By using `behaviour="NON_BLOCKING"` the tool is
            # able to schedule the generation in many ways (controlled by the
            # `scheduling` field in the function response) and to make the model
            # include the latest observations in its prompt before generation.
            genai_types.FunctionDeclaration(
                name="start_commentating",
                description=(
                    "Starts commentating on the video feed. The model should"
                    " continue commentating until the user asks to stop. Caller"
                    " must print() the result for this to work. Do not cancel"
                    " the commentating unless the user asks you to."
                ),
                # TODO(elisseeff): Re-enable once we the Async Fns are launched.
                # behaviour="NON_BLOCKING",
            )
        ]
    )
]

# Prompt for the live api processor.
PROMPT_PARTS = [
    (
        "You are an agent that commentates on a video feed and"
        " interacts with the user in a conversation. Commentate"
        " highlighting the most important things and making it lively"
        " and interesting for the user. Approach the commentating as if"
        " you were on TV commentating and interviewing at the same"
        " time. You can make jokes, explain interesting facts related"
        " to what you see and hear, predict what could happen, judge"
        " some actions or reactions, etc."
    ),
    (
        "You can be interrupted in the middle of a commentary. If this"
        " happens, you should answer the question from the user first."
        " Then you can continue commentating. If the user asks you to"
        " adjust your style or tone, you should do so."
    ),
    (
        "When something changes in the image, video or audio, you"
        " should commentate about it interrupting what you were saying"
        " before. It is important to stay relevant to what is happening"
        " recently and not in the images long before."
    ),
    (
        "Always commentate assuming the persons in the camera hear you"
        " and are in the same room as you. You should always address"
        " the persons in front ofthe camera as 'you'. You should engage"
        " with them."
    ),
]


class EventTypes(enum.StrEnum):
  DETECTION = "yes"
  NO_DETECTION = "no"
  INTERRUPTION = "interruption"


EVENT_DETECTION_PROMPT = (
    "You are an agent that detects events in the video feed. You receive images"
    " from a camera. You must detect whenever a person or a group of people are"
    " facing the camera and are close enough to engage in a conversation. You"
    " must as well detect whenever the camera is pointing at a computer"
    " screen.\n"  # Do not fold
    "Whenever you see a person or a group of people close enough to the camera,"
    f" respond with '{EventTypes.DETECTION}'.\n"  # Do not fold
    f"Whenever you see a computer screen, respond '{EventTypes.DETECTION}'.\n"
    "Whenever you see something special, the user wanting to stop you, interact"
    " with you or whenever you see something new that would change your"
    f" comment, respond with '{EventTypes.INTERRUPTION}'. Do not interrupt if"
    " the user is talking to you, only when something related to the video feed"
    "changes significantly.\n"
    f"In all other cases, respond with '{EventTypes.NO_DETECTION}'.\n"
)


def audio_duration_sec(audio_data: bytes, sample_rate: int) -> float:
  """Returns the duration of the audio data in seconds."""
  # 2 bytes per sample (16bits), 24kHz sample rate
  return len(audio_data) / (2 * sample_rate)


class GenerationType(enum.Enum):
  """Type of the request that triggers a model generation call."""

  # Comment scheduled by the commentator.
  COMMENT = 1
  # Question from the user.
  USER_REQUEST = 2
  # Special event detected during the conversation.
  EVENT_INTERRUPTION = 3


@dataclasses.dataclass
class GenerationRequestInfo:
  """Info on a model Generate call request.

  We have three types of request:

  - USER_REQUEST: user is talking.
  - COMMENT: scheduled comment.
  - EVENT_INTERRUPTION: special event detected during the conversation.

  A generation request is active from the moment we sent a request to the model
  until the model returns the `generation_complete` signal. This means we have
  received all the audio parts we need. When we're after the
  `generation_complete` signal, the request is considered inactive. This is in
  contrast with the server side where the request will stay active until the
  model returns the `turn_complete` or `interrupt` signal.
  """

  # Time when the model call was made.
  generation_start_sec: Optional[float] = None
  # Type of the generation request.
  generation_type: Optional[GenerationType] = None
  # Time when the audio responsestream started. None if no audio stream was
  # received.
  time_audio_start: Optional[float] = None
  # TTFT of the model call. None if no model call was made or if a model call is
  # in progress.
  ttft_sec: Optional[float] = None
  # Time of the audio response stream received so far.
  audio_duration: float = 0.0

  def update(self, media_blob: genai_types.Blob):
    """Updates the generation request with the new media data.

    Args:
      media_blob: The new media data.
    """
    if self.generation_start_sec is not None and self.ttft_sec is None:
      # New comment is starting to be streamed.
      self.time_audio_start = time.perf_counter()
      self.ttft_sec = self.time_audio_start - self.generation_start_sec
    self.audio_duration += audio_duration_sec(
        media_blob.data,
        RECEIVE_SAMPLE_RATE,
    )


class CommentatorState(enum.Enum):
  """Finite set of states that the commentator can be in."""

  # Commentator is not commentating. User can still ask questions but there is
  # no comment request scheduled.
  OFF = 1
  # Commentator is commentating but is not requesting a comment. This state is
  # reached when the commentator receives the first audio part of a comment.
  COMMENTATING = 2
  # User starts talking or, more precisely, the model has detected that the
  # audio-input is a user barging in.
  USER_IS_TALKING = 3
  # The commentator is responding to the user. This state is reached when the
  # commentator receives the first audio part of a user response.
  RESPONDING_TO_USER = 4
  # An event is detected in the video stream. This state is reached when the
  # commentator receives an event interruption. It ends when the model returns
  # the first audio part of the interruption comment. It moves then to
  # COMMENTATING.
  REQUESTING_INTERRUPTION = 5
  # The commentator is requesting a new comment. This state is reached when the
  # commentator sends a comment request to the model. It ends when the model
  # returns the first audio part of the comment. It moves then to COMMENTATING.
  REQUESTING_COMMENT = 6
  # The commentator is requesting a response to the user. This state is
  # reached when the commentator sends a user request to the model. It ends
  # when the model returns the first audio part of the response. It moves then
  # to RESPONDS_TO_USER.
  REQUESTING_USER_RESPONSE = 7
  # The commentator is interrupting from a detection but has not received audio
  # parts yet.
  INTERRUPTED_FROM_DETECTION = 8


class CommentatorAction(enum.Enum):
  """Action that the commentator can take."""

  # Turns on the commentator.
  TURN_ON = 1
  # Turns off the commentator.
  TURN_OFF = 2
  # Starts streaming the media part back to the user. This is the first audio
  # part of a comment, an interruption or a response to a user request.
  STREAM_MEDIA_PART = 3
  # Sends a model call to respond to the user (text based).
  REQUEST_FROM_USER = 4
  # Sends a model call to react to an interruption from the event detection.
  REQUEST_FROM_INTERRUPTION = 5
  # Sends a model call to get the next comment.
  REQUEST_FROM_COMMENTATOR = 6
  # Interrupts the current request (user barging in or event interruption).
  INTERRUPT = 7


@dataclasses.dataclass
class CommentatorStateMachine:
  """(state, action) -> state transitions for the commentator."""

  # State of the commentator.
  state: CommentatorState = CommentatorState.OFF
  # Generation requests currently in progress, aka active.
  generation_request_info: Optional[GenerationRequestInfo] = None
  ttfts: collections.deque[float] = dataclasses.field(
      default_factory=collections.deque
  )
  # Commentator ID, defined by the Async Fn call that triggered the commentator.
  id: Optional[str] = None

  def update(self, action: CommentatorAction, state_arg: Any = None) -> None:
    """Updates the commentator state for the new action."""
    start_state = self.state
    try:
      match action:
        case CommentatorAction.TURN_ON:
          if isinstance(state_arg, str):
            self.id = state_arg
          self.state = CommentatorState.COMMENTATING
          return
        case CommentatorAction.TURN_OFF:
          self.state = CommentatorState.OFF
          self.generation_request_info = None
          self.id = None
          return
        case CommentatorAction.INTERRUPT:
          if (
              self.state != CommentatorState.REQUESTING_INTERRUPTION
              and self.state != CommentatorState.OFF
          ):
            # The user is interrupting, we can drop any comment request.
            self.generation_request = None
            self.start_generation(GenerationType.USER_REQUEST)
            self.state = CommentatorState.USER_IS_TALKING
            return
          # Do not return here, we need to handle the case below when self.state
          # is REQUESTING_INTERRUPTION.
        case _:
          pass

      match self.state:
        case CommentatorState.OFF:
          pass
        case (
            CommentatorState.COMMENTATING | CommentatorState.RESPONDING_TO_USER
        ):
          match action:
            case CommentatorAction.REQUEST_FROM_COMMENTATOR:
              self.state = CommentatorState.REQUESTING_COMMENT
              self.start_generation(GenerationType.COMMENT)
              return
            case CommentatorAction.REQUEST_FROM_USER:
              self.state = CommentatorState.REQUESTING_USER_RESPONSE
              self.start_generation(GenerationType.USER_REQUEST)
              return
            case CommentatorAction.REQUEST_FROM_INTERRUPTION:
              self.state = CommentatorState.REQUESTING_INTERRUPTION
              self.start_generation(GenerationType.EVENT_INTERRUPTION)
              return
            case CommentatorAction.STREAM_MEDIA_PART:
              if isinstance(state_arg, genai_types.Blob):
                self._update_media_blob(state_arg)
              return
            case _:
              pass
        case CommentatorState.USER_IS_TALKING:
          match action:
            case CommentatorAction.STREAM_MEDIA_PART:
              self.state = CommentatorState.RESPONDING_TO_USER
              self.update(action, state_arg)
              return
            case _:
              pass
        case CommentatorState.REQUESTING_COMMENT:
          match action:
            case CommentatorAction.STREAM_MEDIA_PART:
              self.state = CommentatorState.COMMENTATING
              self.update(action, state_arg)
              return
            case CommentatorAction.REQUEST_FROM_INTERRUPTION:
              self.state = CommentatorState.REQUESTING_INTERRUPTION
              self.start_generation(GenerationType.EVENT_INTERRUPTION)
              return
            case _:
              pass
        case CommentatorState.REQUESTING_USER_RESPONSE:
          match action:
            case CommentatorAction.STREAM_MEDIA_PART:
              self.state = CommentatorState.COMMENTATING
              self.update(action, state_arg)
              return
            case _:
              pass
        case CommentatorState.REQUESTING_INTERRUPTION:
          match action:
            case CommentatorAction.INTERRUPT:
              self.state = CommentatorState.INTERRUPTED_FROM_DETECTION
              return
            case _:
              pass
        case CommentatorState.INTERRUPTED_FROM_DETECTION:
          match action:
            case CommentatorAction.STREAM_MEDIA_PART:
              self.state = CommentatorState.COMMENTATING
              self.update(action, state_arg)
              return
            case _:
              pass
    finally:
      logging.debug(
          "%s - Update: %s + %s -> %s",
          time.perf_counter(),
          start_state,
          action,
          self.state,
      )

  def start_generation(self, generation_type: GenerationType):
    logging.debug(
        "%s - Start generation: %s", time.perf_counter(), generation_type
    )
    self.generation_request_info = GenerationRequestInfo(
        generation_start_sec=time.perf_counter(),
        generation_type=generation_type,
    )

  def _update_media_blob(self, media_part: genai_types.Blob):
    """Updates the generation request with the new media data."""
    if not self.generation_request_info:
      logging.debug(
          "%s - No generation request to update.", time.perf_counter()
      )
      return
    if self.generation_request_info.ttft_sec is None:
      self.generation_request_info.update(media_part)
      self.ttfts.append(time.perf_counter())
    else:
      self.generation_request_info.update(media_part)

  def predict_next_ttft(self) -> float:
    """Predict the next TTFT from the history of TTFTs."""
    if not self.ttfts:
      return 0.0
    avg = np.mean(self.ttfts)
    std = np.std(self.ttfts)
    # Subtract the standard deviation to get a lower bound on the next TTFT.
    # Underestimating the TTFT will result in the comment being triggered too
    # late, adding a delay to the conversation but making the comment more
    # aligned (time-wise) with the video stream.
    return max(0.4, avg - std)

  def tentative_trigger_time(self) -> Optional[float]:
    """Returns the tentative time when the commentator will trigger."""
    if (
        self.state != CommentatorState.OFF
        and self.generation_request_info
        and self.generation_request_info.time_audio_start is not None
    ):
      return (
          self.generation_request_info.time_audio_start
          + self.generation_request_info.audio_duration
          - self.predict_next_ttft()
      )


class LiveCommentator(processor.Processor):
  """Processor generating live commentaries on a video and audio stream..

  The audio and video parts to commentate on should have the `realtime`
  substream name. Any other parts will be considered as parts of a user request.
  """

  def __init__(
      self,
      live_api_processor: live_model.LiveProcessor,
      event_detection_processor: Optional[
          event_detection.EventDetection
      ] = None,
  ):
    """Initializes the processor.

    Args:
      live_api_processor: The live API processor to use.
      event_detection_processor: The event detection processor to use. If None,
        the processor will not detect events, the comments will be not be
        interrupted, and the commentator will need to be started manually by the
        user , e.g. by saying "start commentating".
    """
    self._detect_processor = event_detection_processor
    if event_detection_processor is None:
      self._processor = processor.passthrough()
    else:
      self._processor = event_detection_processor
    self._processor = self._processor + live_api_processor
    self._commentator = CommentatorStateMachine()
    # Historic time to first token (TTFT) of the recent requests.
    # We use it request the next comment just before the current one finishes.
    self.ttfts = collections.deque(maxlen=50)

  async def _trigger_comment(
      self,
      at_time: float,
      input_queue: asyncio.Queue[content_api.ProcessorPart],
      will_continue: bool = False,
  ):
    """Triggers a comment from the model."""
    # Resume event detection EVENT_DETECTION_DURATION_SEC before the comment is
    # triggered to have a chance to cancel next comment if no event is detected.
    if self._detect_processor is not None:
      await asyncio.sleep(
          max(
              0,
              # Add 1 second to the delay to make sure we have time to do
              # NO_DETECTION_SENSITIVITY_SEC detections.
              (
                  at_time
                  - (NO_DETECTION_SENSITIVITY_SEC + 1)
                  - time.perf_counter()
              ),
          )
      )
      self._detect_processor.resume_detection(EventTypes.DETECTION)
      self._detect_processor.resume_detection(EventTypes.NO_DETECTION)
    # Wait for the last moment to trigger the comment. This minimizes the
    # delay between any event on the video stream and the comment.
    await asyncio.sleep(max(0, at_time - time.perf_counter()))
    # Check again that we are still in commentating mode. Do not commentate if
    # the user is talking.
    self._commentator.update(CommentatorAction.REQUEST_FROM_COMMENTATOR)
    if self._commentator.state == CommentatorState.REQUESTING_COMMENT:
      input_queue.put_nowait(
          content_api.ProcessorPart.from_function_response(
              function_call_id=self._commentator.id,
              name="start_commentating",
              response={"output": COMMENT_MSG},
              # TODO(elisseeff): uncomment this once the SDK is launched.
              # will_continue=will_continue,
              # scheduling=genai_types.FunctionResponseScheculing.WHEN_IDLE,
          )
      )

  async def __call__(
      self, content: AsyncIterable[content_api.ProcessorPart]
  ) -> AsyncIterable[content_api.ProcessorPart]:
    """Run the main conversation loop."""
    trigger_comment_task = None

    # Input queue for the live api processor - we will inject here what we
    # want to send to the model besides the main content stream.
    input_queue = asyncio.Queue()
    input_stream = streams.merge(
        [content, utils.dequeue(input_queue)], stop_on_first=True
    )

    try:
      async with asyncio.TaskGroup() as tg:
        async for part in self._processor(input_stream):
          # Handle function calls.
          if part.function_call:
            logging.debug(
                "%s - Received tool call: %s",
                time.perf_counter(),
                part,
            )
            fn_id = part.get_custom_metadata("id")
            if part.part.function_call.name == "start_commentating":
              if self._commentator.state != CommentatorState.OFF:
                # We already have a comment in progress, ignore this one and
                # cancel this start_commentating async fn call (done by setting
                # will_continue=False).
                logging.debug(
                    "%s - Ignoring start_commentating: %s",
                    time.perf_counter(),
                    fn_id,
                )
                input_queue.put_nowait(
                    content_api.ProcessorPart.from_function_response(
                        function_call_id=fn_id,
                        name="start_commentating",
                        response={},
                        # TODO(elisseeff): uncomment this once the SDK is launched.
                        # will_continue=False,
                        # scheduling=genai_types.FunctionResponseScheculing.WHEN_IDLE,
                    )
                )
              else:
                self._commentator.update(CommentatorAction.TURN_ON, fn_id)
                self._commentator.update(CommentatorAction.REQUEST_FROM_USER)
            continue

          # Handle start of turn, considered as a user request.
          if part.get_custom_metadata("start_of_user_turn"):
            self._commentator.update(CommentatorAction.REQUEST_FROM_USER)
            continue

          # Handle function cancellation:
          if part.tool_cancellation:
            if part.tool_cancellation == self._commentator.id:
              logging.debug(
                  "%s - Cancelling comment function call: %s",
                  time.perf_counter(),
                  self._commentator.id,
              )
              self._commentator.update(CommentatorAction.TURN_OFF)
              if trigger_comment_task is not None:
                trigger_comment_task.cancel()
            continue

          # Handle when the model is done generating. All audios parts have
          # arrived at this point but they have not been all played back yet.
          if part.get_custom_metadata("generation_complete"):
            logging.debug("%s - generation_complete", time.perf_counter())
            if self._commentator.state != CommentatorState.OFF:
              # Schedule the next commentator turn.
              tentative_trigger_time = (
                  self._commentator.tentative_trigger_time()
              )
              if tentative_trigger_time is not None:
                if self._detect_processor is not None:
                  self._detect_processor.pause_detection(EventTypes.DETECTION)
                  self._detect_processor.pause_detection(
                      EventTypes.NO_DETECTION
                  )
                trigger_comment_task = tg.create_task(
                    self._trigger_comment(
                        tentative_trigger_time,
                        input_queue=input_queue,
                        will_continue=True,
                    )
                )

          # Handle interruption from the user.
          if part.get_custom_metadata("interrupted"):
            logging.debug(
                "%s - Turn interrupted - user %s", time.perf_counter(), part
            )
            self._commentator.update(CommentatorAction.INTERRUPT)
            if trigger_comment_task is not None:
              trigger_comment_task.cancel()
            # An interrupt can also come from an async fn response that cancels
            # the current generation. Check that the last call was a user
            # request. The async fn response case will be handled when we
            # receive the next audio part.
            if self._commentator.state == CommentatorState.USER_IS_TALKING:
              logging.debug("%s - Turn interrupted - user", time.perf_counter())
              yield content_api.ProcessorPart(
                  "", role="MODEL", custom_metadata={"interrupted": True}
              )
            continue

          # Handle interrupt request from the event detection. Do not interrupt
          # yet, wait for the interruption to be confirmed by the model.
          if part.get_custom_metadata("interrupt_request"):
            self._commentator.update(
                CommentatorAction.REQUEST_FROM_INTERRUPTION
            )
            if (
                self._commentator.state
                == CommentatorState.REQUESTING_INTERRUPTION
                and self._commentator.id is not None
            ):
              input_queue.put_nowait(
                  content_api.ProcessorPart.from_function_response(
                      function_call_id=self._commentator.id,
                      name="start_commentating",
                      response={"output": INTERRUPT_COMMENT_MSG},
                      # TODO(elisseeff): uncomment this once the SDK is launched
                      # will_continue=True,
                      # scheduling=genai_types.FunctionResponseScheculing.INTERRUPT,
                  )
              )

          if part.part.inline_data:
            if (
                self._commentator.state
                == CommentatorState.INTERRUPTED_FROM_DETECTION
            ):
              # First audio part after an interruption from the event
              # detection. Interrupt the audio stream currently being played and
              # considers the new audio parts.
              logging.debug(
                  "%s - Yield interrupt from interruption, audio should"
                  " stop now",
                  time.perf_counter(),
              )
              yield content_api.ProcessorPart(
                  "", role="MODEL", custom_metadata={"interrupted": True}
              )
            self._commentator.update(
                CommentatorAction.STREAM_MEDIA_PART, part.part.inline_data
            )

          yield part

        # We're done receiving audio, cancel the trigger comment task if it
        # exists
        if trigger_comment_task is not None:
          trigger_comment_task.cancel()
          await trigger_comment_task
    except Exception as e:
      logging.exception("LiveCommentary got exception:")
      raise e


def create_live_commentator(api_key: str) -> processor.Processor:
  r"""Creates a live commentator.

  A live commentator processor takes audio and video as input and produces
  live commentaries on the audio and video stream. The commentaries are
  interrupted by events detected on the video stream. Input and video streams
  coming from devices should be passed to the processor with the `realtime`
  substream name.

  Args:
    api_key: The API key to use for the model.

  Returns:
    A live commentator processor.
  """
  event_detection_processor = event_detection.EventDetection(
      api_key=api_key,
      model=MODEL_DETECTION,
      config=genai_types.GenerateContentConfig(
          system_instruction=EVENT_DETECTION_PROMPT,
          max_output_tokens=10,
          response_mime_type="text/x.enum",
          response_schema=EventTypes,
      ),
      output_dict={
          EventTypes.DETECTION: [
              content_api.ProcessorPart(
                  "start commentating",
                  role="USER",
                  substream_name="realtime",
                  custom_metadata={"end_of_turn": True},
              )
          ],
          EventTypes.NO_DETECTION: [
              content_api.ProcessorPart(
                  "stop commentating",
                  role="USER",
                  substream_name="realtime",
                  custom_metadata={"end_of_turn": True},
              )
          ],
          EventTypes.INTERRUPTION: [
              content_api.ProcessorPart(
                  "",
                  role="USER",
                  # Setting up a substream name here will ensure this part will
                  # not be sent to the Live API.
                  substream_name="event_detection",
                  custom_metadata={"interrupt_request": True},
              )
          ],
      },
      sensitivity={
          EventTypes.NO_DETECTION: NO_DETECTION_SENSITIVITY_SEC,
      },
      included_in={
          EventTypes.DETECTION: {EventTypes.INTERRUPTION},
      },
  )
  live_api_processor = live_model.LiveProcessor(
      api_key=api_key,
      model_name=MODEL_LIVE,
      realtime_config=genai_types.LiveConnectConfig(
          tools=TOOLS,
          system_instruction=PROMPT_PARTS,
          # output_audio_transcription={},
          realtime_input_config=genai_types.RealtimeInputConfig(
              turn_coverage="TURN_INCLUDES_ALL_INPUT"
          ),
          response_modalities=["AUDIO"],
      ),
      http_options=genai_types.HttpOptions(api_version="v1alpha"),
  )
  return timestamp.add_timestamps() + LiveCommentator(
      live_api_processor=live_api_processor,
      event_detection_processor=event_detection_processor,
  )
