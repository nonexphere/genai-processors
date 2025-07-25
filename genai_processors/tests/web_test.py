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
import asyncio
from collections.abc import Sequence
import unittest
from absl.testing import absltest
from absl.testing import parameterized
from genai_processors import content_api
from genai_processors import processor
from genai_processors.core import web


class TestFetchRequestExtractor(
    parameterized.TestCase, unittest.IsolatedAsyncioTestCase
):
  """Tests for the FetchRequestExtractor processor."""

  @parameterized.named_parameters(
      dict(
          testcase_name='single_url_with_surrounding_text',
          input_parts=[
              content_api.ProcessorPart(
                  "Go to https://example.com, it's great."
              )
          ],
          expected_parts=[
              content_api.ProcessorPart('Go to '),
              content_api.ProcessorPart.from_dataclass(
                  dataclass=web.FetchRequest(url='https://example.com')
              ),
              content_api.ProcessorPart(" it's great."),
          ],
      ),
      dict(
          testcase_name='multiple_urls_in_one_part',
          input_parts=[
              content_api.ProcessorPart(
                  'See http://a.com and https://b.org today.'
              )
          ],
          expected_parts=[
              content_api.ProcessorPart('See '),
              content_api.ProcessorPart.from_dataclass(
                  dataclass=web.FetchRequest(url='http://a.com')
              ),
              content_api.ProcessorPart(' and '),
              content_api.ProcessorPart.from_dataclass(
                  dataclass=web.FetchRequest(url='https://b.org')
              ),
              content_api.ProcessorPart(' today.'),
          ],
      ),
      dict(
          testcase_name='no_urls',
          input_parts=[content_api.ProcessorPart('This is just plain text.')],
          expected_parts=[
              content_api.ProcessorPart('This is just plain text.')
          ],
      ),
      dict(
          testcase_name='non_text_parts_are_passed_through',
          input_parts=[
              content_api.ProcessorPart('Text before, '),
              content_api.ProcessorPart(b'bytes', mimetype='image/png'),
              content_api.ProcessorPart(' text after.'),
          ],
          expected_parts=[
              content_api.ProcessorPart('Text before, '),
              content_api.ProcessorPart(b'bytes', mimetype='image/png'),
              content_api.ProcessorPart(' text after.'),
          ],
      ),
      dict(
          testcase_name='url_is_entire_part',
          input_parts=[content_api.ProcessorPart('https://example.com')],
          expected_parts=[
              content_api.ProcessorPart.from_dataclass(
                  dataclass=web.FetchRequest(url='https://example.com')
              )
          ],
      ),
      dict(
          testcase_name='url_at_start_of_part',
          input_parts=[
              content_api.ProcessorPart('https://example.com is a site.')
          ],
          expected_parts=[
              content_api.ProcessorPart.from_dataclass(
                  dataclass=web.FetchRequest(url='https://example.com')
              ),
              content_api.ProcessorPart(' is a site.'),
          ],
      ),
      dict(
          testcase_name='url_with_parentheses',
          input_parts=[
              content_api.ProcessorPart(
                  'See https://en.wikipedia.org/wiki/Text_(disambiguation) for'
                  ' details.'
              )
          ],
          expected_parts=[
              content_api.ProcessorPart('See '),
              content_api.ProcessorPart.from_dataclass(
                  dataclass=web.FetchRequest(
                      url='https://en.wikipedia.org/wiki/Text_(disambiguation)'
                  )
              ),
              content_api.ProcessorPart(' for details.'),
          ],
      ),
  )
  async def test_url_extraction(
      self,
      input_parts: Sequence[content_api.ProcessorPart],
      expected_parts: Sequence[content_api.ProcessorPart],
  ):
    extractor = web.FetchRequestExtractor()
    input_stream = processor.stream_content(input_parts)

    results = []
    async for output_part in extractor(input_stream):
      results.append(output_part)

    self.assertLen(results, len(expected_parts))

    for i, (actual, expected) in enumerate(zip(results, expected_parts)):
      with self.subTest(f'part_{i}'):
        self.assertEqual(actual.mimetype, expected.mimetype)
        if content_api.is_dataclass(actual.mimetype, web.FetchRequest):
          self.assertEqual(
              actual.get_dataclass(web.FetchRequest),
              expected.get_dataclass(web.FetchRequest),
          )
        elif content_api.is_text(actual.mimetype):
          self.assertEqual(actual.text, expected.text)
        else:
          self.assertEqual(actual.bytes, expected.bytes)

  async def test_streaming(self):
    extractor = web.FetchRequestExtractor()

    async def one_hello():
      yield content_api.ProcessorPart('Hello', metadata={'turn_complete': True})
      await asyncio.sleep(300)

    async for part in extractor(one_hello()):
      # Test that we got one part despite the input stream not being complete.
      self.assertEqual(part.text, 'Hello')
      break


if __name__ == '__main__':
  absltest.main()
