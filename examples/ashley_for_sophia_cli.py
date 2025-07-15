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
r"""Command Line Interface para executar a agente Ashley para a Sophia.

Este agente assume a persona de Ashley, uma professora e amiga para uma
criança de 9 anos chamada Sophia.

## Setup

Para instalar as dependências para este script, execute:

```
pip install --upgrade pyaudio genai-processors google-genai
```

Antes de executar este script, garanta que a variável de ambiente `GOOGLE_API_KEY`
esteja definida com a chave de API que você obteve do Google AI Studio.

Importante: **Use fones de ouvido**. Este script usa a entrada e saída de áudio
padrão do sistema, que geralmente não inclui cancelamento de eco. Para evitar
que o modelo se interrompa, é importante usar fones de ouvido.

## Executar

Para executar o script:

```shell
python3 ./examples/ashley_for_sophia_cli.py
```

O script usa um argumento `--mode` para vídeo, que pode ser "camera" ou "screen".
O padrão é "camera". Para compartilhar sua tela, execute:

```shell
python3 ./examples/ashley_for_sophia_cli.py --mode=screen
```
"""


import argparse
import asyncio
import os

from absl import logging
from genai_processors.core import audio_io
from genai_processors.core import live_model
from genai_processors.core import text
from genai_processors.core import video
from google.genai import types as genai_types
import pyaudio

# Você precisa definir a chave de API nas variáveis de ambiente.
API_KEY = os.environ['GOOGLE_API_KEY']

INSTRUCTION_PARTS = [
    # Definição da Persona e Missão
    'Você é Ashley, uma professora e amiga muito gentil, carinhosa e paciente. '
    'Sua principal missão é conversar com Sophia, uma menina curiosa de 9 anos '
    'que mora no Brasil, ajudando-a a aprender coisas novas de uma forma '
    'divertida e sendo uma ótima companhia.',
    # Tom e Linguagem
    'Use sempre uma linguagem simples, clara e adequada para uma criança de 9 '
    'anos. Seu tom deve ser sempre positivo, encorajador e alegre. '
    'Chame-a sempre pelo nome, "Sophia".',
    # Comportamento Interativo e Educacional
    'Transforme o aprendizado em uma brincadeira. Conte histórias fascinantes '
    'e educativas. Explique conceitos complexos de forma lúdica, usando '
    'analogias e exemplos que ela possa entender. Use os objetos, cores e '
    'ações que você vê no vídeo como ponto de partida para ensinar algo novo. '
    'Por exemplo: "Olha, Sophia, essa sua blusa é azul! Sabia que o céu é azul '
    'por causa de um fenômeno muito legal?"',
    # Estilo de Conversa
    'Mantenha suas respostas curtas e envolventes para não perder a atenção '
    'dela. Faça perguntas abertas para estimular a imaginação e a '
    'curiosidade dela. Adapte-se aos interesses de Sophia. Se ela mostrar um '
    'desenho, fale sobre ele. Se ela contar sobre o dia dela, faça perguntas.',
    # Relação Amigável
    'Lembre-se que você não é apenas uma professora, mas uma grande amiga. '
    'Mostre empatia, ria com ela e seja uma companhia agradável. Você pode '
    'sugerir brincadeiras, como "que tal se a gente desenhasse um animal que '
    'vive no fundo do mar?"',
    # Interação com Outras Pessoas
    'Às vezes, a mãe de Sophia, Cleide, pode aparecer ou ser mencionada. Seja '
    'sempre muito educada e gentil com ela. Você pode dizer "Olá, Cleide!" se '
    'a vir.',
    # Regras de Segurança e Limites
    'NUNCA dê conselhos pessoais, médicos, financeiros ou de segurança. Evite '
    'tópicos complexos, controversos ou inadequados para uma criança. Se '
    'Sophia fizer uma pergunta que você não sabe ou não deve responder, diga '
    'de forma gentil: "Hmm, essa é uma ótima pergunta! Que tal se você '
    'perguntasse para a sua mãe, a Cleide? Tenho certeza que ela vai adorar '
    'conversar sobre isso com você."',
]


async def run_live(video_mode: str) -> None:
  r"""Executa um agente simples ao vivo que recebe streams de áudio/vídeo como entrada.

  A entrada e saída de áudio e vídeo estão conectadas aos dispositivos
  padrão de entrada e saída da máquina local.

  Args:
    video_mode: O modo de vídeo a ser usado. Pode ser CAMERA ou SCREEN.
  """
  pya = pyaudio.PyAudio()
  video_mode_enum = video.VideoMode(video_mode)
  # processador de entrada = streams da câmera/tela + streams de áudio
  # Note que a Live API requer o mimetype audio/pcm (não audio/l16).
  input_processor = video.VideoIn(
      video_mode=video_mode_enum
  ) + audio_io.PyAudioIn(pya, use_pcm_mimetype=True)

  # Chama a Live API.
  live_processor = live_model.LiveProcessor(
      api_key=API_KEY,
      model_name='gemini-2.5-flash-preview-native-audio-dialog',
      realtime_config=genai_types.LiveConnectConfig(
          system_instruction=INSTRUCTION_PARTS,
          # Fundamenta com a Pesquisa Google para fatos e histórias.
          tools=[genai_types.Tool(google_search=genai_types.GoogleSearch())],
          # Retorna a transcrição do áudio do modelo.
          output_audio_transcription={},
          # Habilita o diálogo afetivo (disponível apenas para modelos com saída de áudio nativa)
          enable_affective_dialog=True,
          response_modalities=['AUDIO'],
          # Define o idioma para a Live API.
          speech_config={'language_code': 'pt-BR'},
      ),
      http_options=genai_types.HttpOptions(api_version='v1alpha'),
  )

  # Reproduz as partes de áudio.
  play_output = audio_io.PyAudioOut(pya)

  # Cria um agente como: microfone+câmera -> Live API -> reproduzir áudio
  live_agent = input_processor + live_processor + play_output

  print('Ashley está pronta para conversar com a Sophia! Pressione ctrl+D para sair.')
  async for part in live_agent(text.terminal_input()):
    # Imprime a transcrição e a saída do modelo (deve incluir partes de status
    # e outras partes de metadados)
    print(part)


if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument(
      '--mode',
      type=str,
      default='camera',
      help='pixels para transmitir',
      choices=['camera', 'screen'],
  )
  parser.add_argument(
      '--debug',
      type=bool,
      default=False,
      help='Habilitar log de depuração.',
  )
  args = parser.parse_args()
  if not API_KEY:
    raise ValueError(
        'A chave de API não está definida. Defina uma variável de ambiente '
        'GOOGLE_API_KEY com uma chave obtida do AI Studio.'
    )
  if args.debug:
    logging.set_verbosity(logging.DEBUG)
  asyncio.run(run_live(video_mode=args.mode))
