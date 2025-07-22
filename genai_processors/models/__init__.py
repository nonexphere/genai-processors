"""
==============================================================================
Processadores de Modelos: A Interface com a Inteligência
==============================================================================

### Metaprompt para Desenvolvedores

Este módulo contém processadores cuja principal responsabilidade é se comunicar
com APIs de modelos de linguagem (LLMs). Eles abstraem a complexidade da
comunicação de rede, formatação de prompt e parsing de resposta.

Esses processadores são os "motores" que alimentam a inteligência dos agentes
e outros sistemas construídos com esta biblioteca.

### Componentes Expostos:

- **GenaiModel**: Processador para interagir com a API Gemini do Google.
- **LiveProcessor**: Processador para interagir com a API Gemini Live do Google.
- **OllamaModel**: Processador para interagir com modelos locais via Ollama.
- **OpenRouterModel**: Processador para interagir com centenas de modelos via
  API OpenRouter.

"""

from .genai_model import GenaiModel
from .live_model import LiveProcessor
from .ollama_model import OllamaModel
from .openrouter_model import OpenRouterModel


__all__ = [
    "GenaiModel",
    "LiveProcessor",
    "OllamaModel",
    "OpenRouterModel",
]
