r"""Live commentator agent based on GenAI Processors.

Agent commentating on the video and audio stream from the default device inputs.
 This Agent can be run from a CLI directly.

## Setup

To install the dependencies for this script, run:

```
pip install google-genai opencv-python pyaudio pillow mss genai-processors
```

Before running this script, ensure the `GOOGLE_API_KEY` environment
variable is set to the api-key you obtained from Google AI Studio.

Important: **Use headphones**. This script uses the system default audio
input and output, which often won't include echo cancellation. So to prevent
the model from interrupting itself it is important that you use headphones.

## Run

To run the script:

```shell
python commentator_cli.py
```

The script takes a video-mode flag `--mode`, this can be "camera", "screen". The
default is "camera". To share your screen run:

```shell
python commentator_cli.py --mode=screen
```

**NOTE**: add the `--config=darwin_arm64` flag to run on mac.

```shell
blaze run --config=darwin_arm64 \
  learning/deepmind/evergreen/agent/realtime/cookbook:live_commentator_oss
```
"""

import argparse
import asyncio
import os
from genai_processors import content_api
from genai_processors.core import audio_io
from genai_processors.core import rate_limit_audio
from genai_processors.core import video
from genai_processors.examples.live import commentator
import pyaudio

# You need to define the API key in the environment variables.
# export GOOGLE_API_KEY=...
API_KEY = os.environ["GOOGLE_API_KEY"]


async def run_commentator(video_mode: str) -> None:
  r"""Runs a live commentator in a CLI environment.

  The commentator is run from a CLI environment. The audio and video input and
  output are connected to the local machine's default input and output devices.


  Args:
    video_mode: The video mode to use for the video. Can be CAMERA or SCREEN.
  """
  pya = pyaudio.PyAudio()
  video_mode_enum = video.VideoMode(video_mode)
  input_processor = video.VideoIn(
      video_mode=video_mode_enum
  ) + audio_io.PyAudioIn(pya)

  async def input_stream():
    """Empty input stream for the live commentary agent."""
    try:
      while True:
        await asyncio.sleep(1)
    finally:
      yield content_api.ProcessorPart("Ending the stream")

  commentator_processor = commentator.create_live_commentator(API_KEY)
  rate_limit_audio_processor = rate_limit_audio.RateLimitAudio(
      commentator.RECEIVE_SAMPLE_RATE
  )
  consume_output = audio_io.PyAudioOut(pya)

  live_commentary_agent = (
      input_processor
      + commentator_processor
      + rate_limit_audio_processor
      + consume_output
  )

  async for _ in live_commentary_agent(input_stream()):
    pass


if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument(
      "--mode",
      type=str,
      default="camera",
      help="pixels to stream from",
      choices=["camera", "screen"],
  )
  args = parser.parse_args()
  asyncio.run(run_commentator(video_mode=args.mode))
