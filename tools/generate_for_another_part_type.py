"""Utility that rewrites processors library for a different Part/Chunk type.

The library should define ProcessorPart and ProcessorPartTypes at the top:

  ProcessorPart = content_api.ProcessorPart
  ProcessorPartTypes = content_api.ProcessorPartTypes

and use them instead of from `content_api.`. This allows us to swap the
`content_api` module and Chunk/Part types as needed.

For an example of genrule using this utility see
third_party/py/genai_processors:evergreen_processor_py.
"""

from collections.abc import Sequence

from absl import app
from absl import flags

_SOURCE = flags.DEFINE_string(
    'source',
    None,
    'The source file to transform.',
)

_TARGET = flags.DEFINE_string(
    'target',
    None,
    'Where to write the output.',
)


def main(argv: Sequence[str]) -> None:
  if len(argv) > 1:
    raise app.UsageError('Too many command-line arguments.')

  with open(_SOURCE.value) as source_file:
    source = source_file.read()

  source = source.replace(
      'from genai_processors import content_api',
      'from google3.learning.deepmind.evergreen.model_access.client.python'
      ' import content_api',
  )
  source = source.replace(
      'ProcessorPart = content_api.ProcessorPart',
      'ProcessorPart = content_api.ContentChunk',
  )
  source = source.replace(
      'ProcessorPartTypes = content_api.ProcessorPartTypes',
      'ProcessorPartTypes = content_api.ContentChunkTypes',
  )
  with open(_TARGET.value, 'w') as target_file:
    target_file.write(source)


if __name__ == '__main__':
  app.run(main)
