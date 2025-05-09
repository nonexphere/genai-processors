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
"""Processor which converts a `Topic` to a human-readable string."""

from typing import AsyncIterable

from genai_processors import processor

from .. import interfaces

ProcessorPart = processor.ProcessorPart


class TopicVerbalizer(processor.PartProcessor):
  """Processor which converts `Topic` to a human-readable string.

  Similar to TopicResearcher, TopicVerbalizer is a PartProcessor and it handles
  incoming parts in parallel.

  Moreover, the Genai Processors library is smart enough to combine consecutive
  PartProcessors in a way that avoids the head of the line blocking.

  If the input contains topics A, B, C and TopicResearcher manages to finish
  handling C first, TopicVerbalizer will be able to verbalize it without waiting
  for A and B. The A, B, C order will still be preserved on the output.
  """

  def __init__(
      self,
      config: interfaces.Config | None = None,
  ):
    """Initializes the TopicVerbalizer.

    Args:
      config: The agent configuration.
    """
    self._config = config or interfaces.Config()

  def match(self, part: ProcessorPart) -> bool:
    return part.mimetype == "application/json; type=Topic"

  async def __call__(
      self,
      part: ProcessorPart,
  ) -> AsyncIterable[ProcessorPart]:
    if not self.match(part):
      yield part
      return
    t = part.get_dataclass(interfaces.Topic)
    topic_str = f"## {t.topic}\n*{t.relationship_to_user_content}*"
    if t.research_text:
      topic_str += f"\n\n### Research\n\n{t.research_text}"
    yield ProcessorPart(topic_str)
