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
"""Utilities for fetching documents mentioned in the part stream.

NOTE: THIS MODULE IS UNDER DEVELOPMENT AND IS NOT COMPLETE YET.

Referencing URLs of documents (web pages, images, PDFs) in a prompt is a
convenient way to provide rich context for a model. While registering `http.get`
as a tool is a more flexible and robuust approach, it requires an extra model
call and a round trip for each document loaded. This model offers a more
hardwired but faster alternative.

We split the responsibility for fetching documents and deciding what needs
fetching. A special `FetchRequest` part must be used to explicitly reference the
document to be fetched. `UrlFetch` processor would replace them with the actual
content.

It is very convenient to just mention URL as text in the prompt. However it
becomes easy to trigger the fetch unintentionally and can even be dangerous. So
it should be applied closer to the UI where user journeys are more well defined.
For example parsing URLs directly pasted in-to a chat interface is probably
fine. For extra safety you may want to require the URL be on its own line. We
provide `FetchRequestExtractor` processor for that.

This process can be refined further: e.g. one can use a fast model
(gemini-flash-lite or gemma-nano) to decide whether the URL should be fetched
before passing the prompt to a larger LLM. This way we can reduce latency by
making decisions fast and fetching multiple documents in parallel.
"""

import dataclasses
import re

import dataclasses_json
from genai_processors import content_api
from genai_processors.core import text


@dataclasses_json.dataclass_json
@dataclasses.dataclass(frozen=True)
class FetchRequest(dataclasses_json.DataClassJsonMixin):
  """Dataclass to represent a fetch request for the processor."""

  url: str
  mimetype: str | None = None


def _transform_url_to_fetchrequest(
    part: content_api.ProcessorPart,
) -> content_api.ProcessorPart:
  """Strips punctuation and converts a text part with a URL into a FetchRequest."""
  # Strip trailing comma/period from the URL.
  stripped_url = part.text.rstrip('.,')
  return content_api.ProcessorPart.from_dataclass(
      dataclass=FetchRequest(url=stripped_url),
      metadata=part.metadata,
      substream_name=part.substream_name,
  )


class FetchRequestExtractor(text.MatchProcessor):
  """Extracts URLs from a text stream and yields them as FetchRequest parts.

  This processor is a specialized version of the general-purpose MatchProcessor.
  It finds any string that looks like a URL (e.g. starts with http:// or
  https://) and transforms it into a structured FetchRequest part.

  The matched URL is removed from the text stream, and the surrounding text is
  preserved. The output stream is a mix of text/plain parts and FetchRequest
  parts.
  """

  def __init__(self, *, substream_input: str = '', substream_output: str = ''):
    """Initializes the FetchRequestExtractor processor.

    Args:
      substream_input: (Optional) The input stream to the processor.
      substream_output: (Optional) The output stream of the processor.
    """
    # This pattern is designed to match URLs while avoiding capturing trailing
    # punctuation or undesirable characters.
    # It excludes: whitespace, <, >, ", ', and the zero-width space.
    url_pattern = r'https?://[^\s<>"\'\u200B]+'

    super().__init__(
        pattern=re.compile(url_pattern, re.IGNORECASE),
        word_start='http',
        remove_from_input_stream=True,
        substream_input=substream_input,
        substream_output=substream_output,
        transform=_transform_url_to_fetchrequest,
    )
