"""
==============================================================================
Processadores de Agentes: Composições de Alto Nível
==============================================================================

### Metaprompt para Desenvolvedores

Este módulo contém implementações de "agentes". Um agente, neste contexto, é
um processador de alto nível que compõe múltiplos processadores menores para
executar uma tarefa complexa e de longa duração, como manter uma conversa
colaborativa.

Os agentes são os principais exemplos de como os "legos" do `genai-processors`
podem ser montados para criar sistemas sofisticados.

### Componentes Expostos:

- **LeonidasOrchestrator**: O cérebro do agente Leonidas, responsável pela
  orquestração da conversa, gerenciamento de estado e execução de ferramentas.

"""

from .leonidas import LeonidasOrchestrator

__all__ = [
    "LeonidasOrchestrator",
]
