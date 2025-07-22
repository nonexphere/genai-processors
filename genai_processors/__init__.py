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

"""
==============================================================================
Google DeepMind GenAI Processors Library
==============================================================================

### Metaprompt para Desenvolvedores

Bem-vindo ao `genai-processors`, uma biblioteca projetada para construir
sistemas de IA modulares e escaláveis. A filosofia central é tratar cada
capacidade como um "lego" (um `Processor` ou `PartProcessor`) que pode ser
conectado a outros para criar pipelines complexos.

### Mapa da Biblioteca:

- **`processor`**: O núcleo da biblioteca. Define as interfaces `Processor` e
  `PartProcessor` e as funções para combiná-los (`chain`, `parallel`).
- **`content_api`**: Define a estrutura de dados fundamental, `ProcessorPart`,
  que flui entre os processadores.
- **`streams`**: Utilitários para trabalhar com streams assíncronos.
- **`core`**: Contém os "legos" fundamentais e de propósito geral, como E/S de
  áudio/vídeo, manipulação de texto e processamento de PDF.
- **`models`**: Processadores que atuam como clientes para APIs de LLMs (Gemini,
  Ollama, etc.).
- **`agents`**: Composições de alto nível que combinam múltiplos processadores
  para criar agentes complexos, como o Leonidas.
- **`tools`**: (Futuro) Processadores que implementam ferramentas específicas
  que podem ser chamadas por um agente.
- **`factory`**: (Futuro) Processadores projetados para gerar artefatos
  específicos (código, documentos, análises) usando um modelo.
- **`contrib`**: Processadores contribuídos pela comunidade.

"""

__version__ = '1.1.0'

from . import content_api as content_api_
from . import core
from . import models
from . import agents
from . import processor as processor_
from . import streams as streams_

# Aliases
ProcessorPart = content_api_.ProcessorPart
ProcessorContent = content_api_.ProcessorContent
ProcessorPartTypes = content_api_.ProcessorPartTypes
ProcessorContentTypes = content_api_.ProcessorContentTypes
Processor = processor_.Processor
PartProcessor = processor_.PartProcessor
ProcessorFn = processor_.ProcessorFn
PartProcessorWithMatchFn = processor_.PartProcessorWithMatchFn

apply_sync = processor_.apply_sync
apply_async = processor_.apply_async
chain = processor_.chain
parallel = processor_.parallel
parallel_concat = processor_.parallel_concat
create_filter = processor_.create_filter
part_processor_function = processor_.part_processor_function

stream_content = streams_.stream_content
gather_stream = streams_.gather_stream

# Core processors
LiveModelProcessor = core.realtime.LiveModelProcessor
Preamble = core.preamble.Preamble
PyAudioIn = core.audio_io.PyAudioIn
PyAudioOut = core.audio_io.PyAudioOut
SpeechToText = core.speech_to_text.SpeechToText
Suffix = core.preamble.Suffix
TextToSpeech = core.text_to_speech.TextToSpeech
VideoIn = core.video.VideoIn

# Model processors
GenaiModel = models.genai_model.GenaiModel
LiveProcessor = models.live_model.LiveProcessor
OllamaModel = models.ollama_model.OllamaModel
OpenRouterModel = models.openrouter_model.OpenRouterModel
