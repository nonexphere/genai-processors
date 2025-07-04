import enum
import http
import json
import unittest
from unittest import mock

from absl.testing import parameterized
from genai_processors import content_api
from genai_processors import processor
from genai_processors.core import ollama_model
import httpx


class OkEnum(enum.StrEnum):
  OK = 'OK'
  OKAY = 'okay'


class GithubProcessorTest(parameterized.TestCase):

  def test_inference(self):
    def request_handler(request: httpx.Request):
      self.assertEqual(str(request.url), 'http://127.0.0.1:11434/api/chat')
      self.assertEqual(
          json.loads(request.content.decode('utf-8')),
          {
              'model': 'gemma3',
              'messages': [
                  {
                      'role': 'system',
                      'content': 'You are an OK agent: you respond with OK.',
                  },
                  {'role': 'user', 'images': ['UE5HRw0KGgo=']},
                  {'role': 'user', 'content': 'is this image okay?'},
              ],
              'tools': None,
              'format': {
                  'type': 'string',
                  'title': 'OkEnum',
                  'enum': ['OK', 'okay'],
              },
              'options': {},
              'keep_alive': None,
          },
      )

      response = (
          '{"message": {"content": "O", "role": "model"}}\n'
          '{"message": {"content": "K", "role": "model"}}\n'
      )
      return httpx.Response(
          http.HTTPStatus.OK, content=response.encode('utf-8')
      )

    mock_client = httpx.AsyncClient(
        transport=httpx.MockTransport(request_handler)
    )

    with mock.patch.object(httpx, 'AsyncClient', return_value=mock_client):
      model = ollama_model.OllamaModel(
          model_name='gemma3',
          generate_content_config=ollama_model.GenerateContentConfig(
              system_instruction='You are an OK agent: you respond with OK.',
              response_schema=OkEnum,
              response_mime_type='text/x.enum',
          ),
      )
      output = processor.apply_sync(
          model,
          [
              content_api.ProcessorPart(
                  b'PNG\x47\x0D\x0A\x1A\x0A', mimetype='image/png'
              ),
              'is this image okay?',
          ],
      )

    self.assertEqual(content_api.as_text(output), 'OK')


if __name__ == '__main__':
  unittest.main()
