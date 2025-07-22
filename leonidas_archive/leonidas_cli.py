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

r"""Interface de Linha de Comando para o agente Leonidas.

Agente colaborativo em tempo real que interage via áudio e vídeo.

## Configuração

Para instalar as dependências para este script, execute:

```
pip install pyaudio genai-processors
```

Antes de executar este script, garanta que a variável de ambiente `GOOGLE_API_KEY`
esteja definida com a chave de API que você obteve do Google AI Studio.

Importante: **Use fones de ouvido**. Este script usa a entrada e saída de áudio
padrão do sistema, que geralmente não inclui cancelamento de eco. Para evitar
que o modelo se interrompa, é importante usar fones de ouvido.

## Executar

Para executar o script:

```shell
python3 ./examples/live/leonidas_cli.py
```

O script usa um argumento `--mode` para vídeo, que pode ser "camera" ou "screen".
O padrão é "camera". Para compartilhar sua tela, execute:

```shell
python3 ./examples/live/leonidas_cli.py --mode=screen
```
"""

import argparse
import asyncio
import os

from absl import logging
from genai_processors.core import audio_io
from genai_processors.core import text
from genai_processors.core import video
import leonidas
import pyaudio

# You need to define the API key in the environment variables.
# export GOOGLE_API_KEY=...
API_KEY = os.environ['GOOGLE_API_KEY']


async def run_leonidas(video_mode: str) -> None:
  r"""Executa o agente Leonidas em um ambiente de linha de comando.

  A entrada e saída de áudio e vídeo são conectadas aos dispositivos
  padrão de entrada e saída da máquina local.

  Args:
    video_mode: O modo de vídeo a ser usado. Pode ser CAMERA ou SCREEN.
  """
  pya = pyaudio.PyAudio()
  video_mode_enum = video.VideoMode(video_mode)
  input_processor = video.VideoIn(
      video_mode=video_mode_enum
  ) + audio_io.PyAudioIn(pya, use_pcm_mimetype=True)

  leonidas_processor = leonidas.create_leonidas_agent(API_KEY)

  consume_output = audio_io.PyAudioOut(pya)

  live_agent = (
      input_processor
      + leonidas_processor
      + consume_output
  )

  print('Leonidas está pronto. Use ctrl+D para sair.')
  async for _ in live_agent(text.terminal_input()):
    pass


if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument(
      '--mode',
      type=str,
      default='camera',
      help='Fonte de pixels para transmitir (camera ou screen).',
      choices=['camera', 'screen'],
  )
  parser.add_argument(
      '--debug',
      type=bool,
      default=False,
      help='Habilitar log de depuração.',
  )
  args = parser.parse_args()
  if args.debug:
    logging.set_verbosity(logging.DEBUG)
  asyncio.run(run_leonidas(video_mode=args.mode))
