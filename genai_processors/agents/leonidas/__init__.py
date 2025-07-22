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
Agente Leonidas: Um Parceiro de Engenharia Colaborativo
==============================================================================

### Metaprompt do Agente

Leonidas é um agente de IA conversacional projetado para atuar como um
engenheiro de software sênior. Ele integra percepção multimodal (áudio, vídeo),
memória persistente e um sistema de ferramentas robusto para colaborar em
tarefas de desenvolvimento de software em tempo real.

Este pacote contém todos os "legos" que compõem o agente Leonidas.

### Mapa de Componentes:

- **leonidas.py**:
  - `LeonidasOrchestrator`: O processador central que gerencia o ciclo de vida
    da conversa, a lógica de ferramentas e a comunicação com o `LiveProcessor`.
  - `InputManager` / `OutputManager`: Abstrações para hardware de E/S.
  - `run_leonidas`: A função principal que monta e executa o pipeline do agente.
  - `LEONIDAS_SYSTEM_PROMPT` / `LEONIDAS_TOOLS`: A "personalidade" e as
    capacidades do agente, definidas para o modelo Gemini.

- **memory_system.py**:
  - `LeonidasMemorySystem`: Orquestra a memória de curto e longo prazo,
    incluindo a geração de resumos e o carregamento de contexto.

- **leonidas_cli.py**:
  - O ponto de entrada da linha de comando para iniciar o agente (localizado na
    raiz do projeto).

"""

from .leonidas import (
    InputManager,
    OutputManager,
    LeonidasOrchestrator,
    setup_logging,
    run_leonidas,
    LEONIDAS_TOOLS,
    LEONIDAS_SYSTEM_PROMPT,
)

from .memory_system import LeonidasMemorySystem

__version__ = "2.1.0"
__all__ = [
    "InputManager",
    "OutputManager",
    "LeonidasOrchestrator",
    "setup_logging",
    "run_leonidas",
    "LEONIDAS_TOOLS",
    "LEONIDAS_SYSTEM_PROMPT",
    "LeonidasMemorySystem",
]
