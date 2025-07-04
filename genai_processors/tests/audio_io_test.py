import time
import unittest
from unittest import mock

from absl.testing import parameterized
from genai_processors import content_api
from genai_processors import streams
from genai_processors.core import audio_io
import pyaudio


class PyAudioInTest(parameterized.TestCase, unittest.IsolatedAsyncioTestCase):
  """Tests for the PyAudioIn processor."""

  def setUp(self):
    super().setUp()
    self.pyaudio_mock = mock.MagicMock()
    self.stream_mock = mock.MagicMock()
    self.input_stream = streams.stream_content(
        [
            content_api.ProcessorPart(
                'hello',
            ),
        ],
        # This delay is added after the text part is returned to ensure the
        # stream ends after the audio part is returned.
        with_delay_sec=0.1,
    )

  async def test_py_audio_in(self):

    def side_effect(chunk_size, exception_on_overflow=False):
      del exception_on_overflow
      del chunk_size
      # Delay it to return the audio bytes after the text part.
      time.sleep(0.05)
      return b'audio_bytes'

    self.stream_mock.read = mock.MagicMock()
    self.stream_mock.read.side_effect = side_effect
    self.pyaudio_mock.open.return_value = self.stream_mock
    with mock.patch.object(
        pyaudio,
        'PyAudio',
        return_value=self.pyaudio_mock,
    ):
      audio_in = audio_io.PyAudioIn(pya=self.pyaudio_mock)
      output = await streams.gather_stream(audio_in(self.input_stream))
      self.assertEqual(
          output,
          [
              content_api.ProcessorPart('hello'),
              content_api.ProcessorPart(
                  content_api.ProcessorPart(
                      b'audio_bytes', mimetype='audio/l16;rate=24000'
                  ),
                  substream_name='realtime',
                  role='USER',
              ),
          ],
      )

  async def test_py_audio_in_with_exception(self):
    self.stream_mock.read = mock.MagicMock()
    self.stream_mock.read.side_effect = IOError('IOError')
    self.pyaudio_mock.open.return_value = self.stream_mock
    with mock.patch.object(
        pyaudio,
        'PyAudio',
        return_value=self.pyaudio_mock,
    ):
      audio_in = audio_io.PyAudioIn(pya=self.pyaudio_mock)
      with self.assertRaises(IOError):
        await streams.gather_stream(audio_in(self.input_stream))


class PyAudioOutTest(parameterized.TestCase, unittest.IsolatedAsyncioTestCase):
  """Tests for the PyAudioOut processor."""

  def setUp(self):
    super().setUp()
    self.pyaudio_mock = mock.MagicMock()
    self.stream_mock = mock.MagicMock()
    self.input_stream = streams.stream_content(
        [
            content_api.ProcessorPart(
                'hello',
            ),
            content_api.ProcessorPart(
                b'audio_bytes',
                mimetype='audio/l16',
            ),
        ],
        # This delay is for testing only.
        with_delay_sec=0.1,
    )

  @parameterized.named_parameters(
      (
          'passthrough_audio',
          True,
          [
              content_api.ProcessorPart('hello'),
              content_api.ProcessorPart(b'audio_bytes', mimetype='audio/l16'),
          ],
      ),
      ('no_passthrough_audio', False, [content_api.ProcessorPart('hello')]),
  )
  async def test_py_audio_out(self, passthrough_audio, expected):

    self.pyaudio_mock.open.return_value = self.stream_mock
    with mock.patch.object(
        pyaudio,
        'PyAudio',
        return_value=self.pyaudio_mock,
    ):
      audio_out = audio_io.PyAudioOut(
          pya=self.pyaudio_mock, passthrough_audio=passthrough_audio
      )
      output = await streams.gather_stream(audio_out(self.input_stream))
      self.stream_mock.write.assert_called_with(b'audio_bytes')
      self.assertEqual(output, expected)

  async def test_py_audio_out_with_exception(self):
    self.stream_mock.write.side_effect = IOError('IOError')
    self.pyaudio_mock.open.return_value = self.stream_mock
    with mock.patch.object(
        pyaudio,
        'PyAudio',
        return_value=self.pyaudio_mock,
    ):
      audio_out = audio_io.PyAudioOut(
          pya=self.pyaudio_mock, passthrough_audio=True
      )
      with self.assertRaises(IOError):
        await streams.gather_stream(audio_out(self.input_stream))


if __name__ == '__main__':
  unittest.main()
