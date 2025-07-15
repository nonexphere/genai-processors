# Documento de Design do Projeto (PDR): Leonidas v1.0

**Autor:** Arquiteto-Chefe de IA
**Data:** 24 de Maio de 2024
**Status:** Proposto

## 1. Visão Geral e Objetivos

O projeto Leonidas visa criar uma interface de IA multimodal (voz e visão) que atue como um colaborador de desenvolvimento de software. Diferente de assistentes reativos, Leonidas deve possuir uma capacidade de "pensamento" secundária que lhe permita analisar o contexto da tarefa, aprender com as interações e intervir proativamente com insights e correções relevantes.

**Objetivos Principais:**
- **Estabilidade:** Criar uma arquitetura robusta que permita desenvolvimento incremental.
- **Inteligência Contextual:** O agente deve entender o que está sendo trabalhado, não apenas responder a comandos isolados.
- **Comportamento Humano:** O agente deve ser primariamente um ouvinte, falando apenas quando necessário ou quando tiver uma contribuição valiosa.
- **Memória:** O agente deve ser capaz de armazenar e recuperar informações de interações passadas.

## 2. Arquitetura Proposta: Sistema Duplo

A arquitetura se baseia em um modelo de processamento duplo para emular o pensamento rápido/reativo e o lento/deliberativo.

- **Sistema 1 (O Falante):** `LeonidasAgent`. Lida com a interface em tempo real. É otimizado para baixa latência na conversação.
- **Sistema 2 (O Pensador):** `CognitiveAnalyzer`. Opera em paralelo, analisando a interação completa (usuário e Sistema 1) para gerar insights de alta qualidade.

## 3. Detalhamento dos Componentes

### 3.1. `VisualPerception` (Processador de Percepção Visual)
- **Responsabilidade:** Converter o fluxo de vídeo em um fluxo de descrições textuais de baixo nível sobre o estado visual do ambiente (ex: "arquivo X aberto", "terminal visível").
- **Tecnologia:** `genai_processors.core.event_detection` reconfigurado.
- **Fluxo de Dados:** `VideoIn` -> `VisualPerception` -> `LeonidasAgent` (como contexto) e `CognitiveAnalyzer` (como contexto).

### 3.2. `LeonidasAgent` (Sistema 1)
- **Responsabilidade:** Gerenciar a conversação em tempo real com o usuário.
- **Tecnologia:** `genai_processors.core.live_model` (`LiveProcessor`).
- **Fluxo de Dados:**
    - **Entrada:** Áudio do usuário, contexto do `VisualPerception`, sinais de interrupção do `CognitiveAnalyzer`.
    - **Saída:** Áudio de resposta para o usuário, transcrição da sua própria resposta para o `CognitiveAnalyzer`.
- **Comportamento Chave:** Não inicia a fala proativamente. Apenas responde ao usuário ou a uma interrupção do Sistema 2.

### 3.3. `CognitiveAnalyzer` (Sistema 2)
- **Responsabilidade:** Analisar o diálogo completo e o contexto para gerar insights ou correções.
- **Tecnologia:** Novo `processor.Processor` contendo um `genai_model.GenaiModel` (e.g., Gemini Flash).
- **Fluxo de Dados:**
    - **Entrada:** Transcrição do usuário, transcrição do `LeonidasAgent`, contexto do `VisualPerception`, dados da `MemoryStore`.
    - **Saída:** Um sinal de interrupção (`interrupt_request`) contendo o texto do insight, direcionado ao `LeonidasAgent`.

### 3.4. `MemoryStore` (Camada de Memória)
- **Responsabilidade:** Persistir e recuperar dados de interações passadas.
- **Tecnologia:** (A ser definida) Inicialmente pode ser um arquivo de log estruturado (JSONL), evoluindo para um banco de dados vetorial.
- **Fluxo de Dados:** O `CognitiveAnalyzer` lê e escreve nesta camada.

## 4. Plano de Implementação Incremental

Para evitar instabilidade, o desenvolvimento seguirá as seguintes fases:

1.  **Fase 0: Estabilização.** Reverter as alterações recentes para uma base funcional do "Live Commentator" renomeado para Leonidas.
2.  **Fase 1: Desacoplamento da Percepção.** Modificar o `EventDetection` para se tornar o `VisualPerception` passivo. O agente se tornará reativo, não proativo.
3.  **Fase 2: Integração do Contexto Visual.** Fazer o `LeonidasAgent` consumir e utilizar o contexto textual do `VisualPerception` em seus prompts.
4.  **Fase 3: Introdução do Sistema 2 (Passivo).** Adicionar o `CognitiveAnalyzer` à pipeline, mas com uma implementação "passthrough" (sem lógica) para validar a estrutura de `streams.split` e `streams.merge`.
5.  **Fase 4: Ativação do Sistema 2 (Ativo).** Implementar a lógica de análise e interrupção no `CognitiveAnalyzer`.
6.  **Fase 5: Implementação da Memória.** Conectar o `CognitiveAnalyzer` a uma `MemoryStore` inicial.
