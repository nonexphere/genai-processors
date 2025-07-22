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
"""Core processors."""

from . import audio_io
from . import drive
from . import event_detection
from .models import genai_model
from . import github
from . import jinja_template
from . import live_model
from . import ollama_model
from . import pdf
from . import preamble
from . import rate_limit_audio
from . import realtime
from . import speech_to_text
from . import text
from . import text_to_speech
from . import timestamp
from . import video
