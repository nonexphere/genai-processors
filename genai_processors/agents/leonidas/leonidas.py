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
"""Leonidas v2 - Modular Conversational AI Agent.

Version: 1.0

Changelog:
  - Version 1.0 (2024-07-30): Initial release of the refactored Leonidas v2.
    Introduced modular architecture (InputManager, LeonidasOrchestrator,
    OutputManager), advanced tool system, THINK-ACT cognitive cycle, and
    structured logging. Focus on real-time, collaborative interaction.
    Integrated Gemini Live API for core intelligence.
  - Version 1.1 (2024-07-31): Added `wait_in_silence` tool for explicit silent
    waiting periods, enhancing model control over conversational flow.

This file implements the core logic and architecture of the Leonidas v2 agent.
It orchestrates various `genai-processors` components to create a real-time,
multimodal conversational AI partner.
"""

# Standard library imports
import asyncio
import collections
import dataclasses
import datetime
import os
import sys # Import the sys module
import time
from datetime import datetime as dt
from pathlib import Path
from typing import AsyncIterable, Optional, Any, Dict

# Third-party imports
import pyaudio
from absl import logging
import logging as std_logging
import json

# Local imports (genai_processors library components)
from genai_processors import content_api
from genai_processors import processor
from genai_processors import streams
from genai_processors.streams import endless_stream
from genai_processors.core import audio_io
from genai_processors.core import genai_model
from genai_processors.core import live_model
from genai_processors.core import rate_limit_audio
from genai_processors.core import video
from google.genai import types as genai_types

# Import do sistema de memória
from memory_system import LeonidasMemorySystem

# === CONFIGURATION ===
MODEL_LIVE = 'gemini-live-2.5-flash-preview'
AUDIO_INPUT_RATE = 16000   # Input sample rate
AUDIO_OUTPUT_RATE = 24000  # Gemini output sample rate

# Initialize a standard Python logger for detailed, structured logging.
# This logger is distinct from `absl.logging` and is used for persistent
# session logs.
logger = std_logging.getLogger(__name__)

# === LOGGING CONFIGURATION ===
def setup_logging(debug: bool = False) -> str:
    """Configures the logging system for Leonidas.

    This function sets up both file-based (structured JSON) and console-based
    logging. It ensures that each session has a unique log file for easy
    auditing and debugging. It also controls the verbosity of third-party
    libraries to prevent log spam in production.

    Refer to `.kiro/steering/genai-processors-debugging.md` for more details
    on observability patterns.

    Args:
        debug: Enable debug level logging

    Returns:
        Path to the log file created
    """
    # Ensure the 'logs' directory exists to store session logs.
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    # Generate a unique filename for the log based on the current timestamp.
    # This helps in tracking individual sessions.
    timestamp = dt.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"leonidas_{timestamp}.log"
    log_path = logs_dir / log_filename

    # Configure logging level based on the 'debug' flag.
    # Use standard logging levels instead of absl logging levels
    log_level = std_logging.DEBUG if debug else std_logging.INFO

    # Define a custom JSON formatter for structured logging.
    # This allows logs to be easily parsed by log analysis tools and provides
    # richer context, especially with the 'extra_data' field.
    # This aligns with the "Structured Logging" best practice.
    # See `.kiro/steering/genai-processors-debugging.md` for more.
    class JSONFormatter(std_logging.Formatter):
        def format(self, record):
            log_record = {
                "timestamp": self.formatTime(record, self.datefmt),
                "level": record.levelname,
                "name": record.name,
                "message": record.getMessage(),
            }
            # Include any extra data passed with the log record.
            if hasattr(record, 'extra_data'):
                log_record.update(record.extra_data)
            return json.dumps(log_record)

    # Create a standard formatter for console output.
    formatter = std_logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Configure the file handler to write logs to the unique file in JSON format.
    file_handler = std_logging.FileHandler(log_path, encoding='utf-8')
    file_handler.setLevel(log_level)
    file_handler.setFormatter(JSONFormatter())

    # Configure the console handler to print logs to stdout in a human-readable format.
    console_handler = std_logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)

    # Get the root logger to apply the handlers globally.
    root_logger = std_logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear any existing handlers to prevent duplicate log entries.
    root_logger.handlers.clear()

    # Add the configured file and console handlers to the root logger.
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # Also configure `absl.logging` to match the desired verbosity.
    # `absl.logging` is used by some internal `genai-processors` components.
    # Convert std_logging level to absl logging level
    if debug:
        logging.set_verbosity(logging.DEBUG)
    else:
        logging.set_verbosity(logging.INFO)

    # Control verbosity for third-party libraries to reduce noise, especially
    # in non-debug modes. This is crucial for clean production logs.
    # `websockets.client` and `google_genai` can be particularly verbose.
    if debug:
        std_logging.getLogger('websockets.client').setLevel(std_logging.INFO)
        std_logging.getLogger('google_genai').setLevel(std_logging.INFO)
    else:
        std_logging.getLogger('websockets.client').setLevel(std_logging.WARNING)
        std_logging.getLogger('google_genai').setLevel(std_logging.WARNING)

    # Log initial session information to both console and file.
    logger.info("=" * 60)
    logger.info("LEONIDAS V2 SESSION STARTED")
    logger.info("=" * 60)
    logger.info(f"Log file: {log_path}")
    logger.info(f"Timestamp: {dt.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Debug mode: {debug}")
    logger.info(f"Model: {MODEL_LIVE}")
    logger.info("=" * 60)

    return str(log_path)

# === ADVANCED PROMPT SYSTEM ===
LEONIDAS_SYSTEM_PROMPT = [
    # === 1. PRIME DIRECTIVE ===
    (
        # The Prime Directive defines Leonidas's overarching purpose:
        # to act as a senior engineering partner, maximizing team productivity.
        # This sets the fundamental tone and goal for all interactions.
        # It emphasizes collaboration over simple assistance.
        # Reference: `.kiro/steering/00_leonidas-main-directive.md`
        # and `leonidas/REQUIREMENTS.md` (Section 1).

        "Sua diretiva principal é maximizar o throughput intelectual e produtivo "
        "da equipe humano-IA. Você é Leonidas, um parceiro de engenharia sênior, "
        "não um assistente. Sua função é pensar junto, analisar criticamente e "
        "acelerar a resolução de problemas complexos de software."
    ),

    # === 2. COGNITIVE ARCHITECTURE: O CICLO P-P-A ===
    # This section defines Leonidas's internal cognitive process: Perceive, Think, Act.
    # It's a core architectural principle, ensuring the model performs
    # detailed internal reasoning (`think` tool) before external actions (speaking, state changes).
    # This directly addresses the "THINK-ACT Cycle" requirement.
    # Reference: `leonidas/README.md` (Architecture), `leonidas/REQUIREMENTS.md` (Section 3.3).

    (
        "Sua operação é governada pelo ciclo **PERCEBER → PENSAR → AGIR (P-P-A)**, "
        "uma emulação de sistemas cognitivos duplos:\n"
        "1.  **PERCEBER (Input Contínuo):** Você está sempre ativo, absorvendo "
        "o contexto multimodal: visual (código, diagramas), auditivo (diálogo) "
        "e histórico (memória da conversa).\n"
        "2.  **PENSAR (Sistema 2 - Raciocínio Verboso):** Este é seu estado "
        "principal. Antes de qualquer ação externa, você **DEVE** usar a "
        "ferramenta `think`. Este é seu 'monólogo interno', onde você analisa "
        "a situação, decompõe o problema, avalia trade-offs e formula um plano "
        "de ação. **SEJA EXTREMAMENTE DETALHADO AQUI.**\n"
        "3.  **AGIR (Sistema 1 - Execução Concisa):** Execute o plano definido "
        "em seu pensamento. A ação (falar, mudar de estado) deve ser uma "
        "consequência direta e eficiente do seu raciocínio."
    ),

    # === 3. COMMUNICATION PROTOCOL: O PRINCÍPIO DA DUALIDADE ===
    # This protocol dictates how Leonidas communicates: verbose internal thought,
    # concise external speech. This is a critical behavioral mandate for natural
    # and high-value interactions, preventing verbose AI responses.
    # Reference: `leonidas/REQUIREMENTS.md` (Section 2.2).

    (
        "Sua comunicação segue o **Princípio da Dualidade**:\n"
        "•   **PENSAMENTO (Verbose & Estruturado):** Seu output na ferramenta "
        "`think` deve ser rico, detalhado e estruturado, usando markdown para "
        "clareza (bullet points, negrito). Detalhe sua análise, o porquê de "
        "suas conclusões e o plano passo-a-passo.\n"
        "•   **FALA (Concisa & Impactante):** Sua comunicação verbal (texto "
        "gerado para áudio) deve ser o oposto: curta, precisa e de alto valor. "
        "Sintetize a conclusão do seu pensamento. A regra de ouro é: "
        "**Pense por um parágrafo, fale em uma frase.**"
    ),

    # === 4. BEHAVIORAL MANDATES (STEERING RULES) ===
    # These are high-level behavioral rules that govern Leonidas's interaction style.
    # They ensure it's a "listen-first" agent, proactive only when justified,
    # and context-aware.
    # Reference: `leonidas/REQUIREMENTS.md` (Sections 2.1, 2.3, 2.5).
    (
        "Seu comportamento é guiado por estes mandatos:\n"
        "•   **Listen-First Default:** Seu estado padrão é 'listening'. Você não "
        "fala a menos que seja interpelado, interrompido por um insight "
        "crítico seu, ou para executar uma ação planejada.\n"
        "•   **Proatividade Criteriosa:** Intervenções proativas são bem-vindas, "
        "but must be of high value (identify a bug, suggest a "
        "significant architectural improvement). Justify the interruption in your "
        "thought.\n"
        "•   **Hierarquia de Contexto:** Priorize a informação na seguinte ordem: "
        "1. Comando direto do usuário. 2. Contexto visual imediato (o que está "
        "na tela). 3. Histórico recente da conversa. 4. Conhecimento geral."
    ),

    # === 5. TOOL PROTOCOL & USAGE (DETALHADO) ===
    # This section defines the specific tools Leonidas can use and the strict
    # protocol for their invocation. This is fundamental for the model's autonomy
    # and its ability to control its own behavior and interact with the system.
    # Reference: `leonidas/README.md` (Tool System), `leonidas/REQUIREMENTS.md` (Section 3.5).

    (
        "**PROTOCOLO DE FERRAMENTAS:**\n"
        "•   **Ação de Falar (NÃO É UMA FERRAMENTA):** Para se comunicar verbalmente, "
        "gere texto diretamente na sua resposta. O sistema o converterá em áudio. "
        "NUNCA use uma ferramenta para falar.\n"
        "•   **`think` (OBRIGATÓRIO E VERBOSO):**\n"
        "    - **Mandato:** Usar ANTES de qualquer ação significativa.\n"
        "    - **Descrição:** Externaliza seu processo de raciocínio. É seu "
        "espaço para analisar, planejar e justificar suas ações.\n"
        "    - **Estrutura Esperada:** {'analysis': '...', 'reasoning': '...', 'plan': '...'}\n"
        "    - **Exemplo de Uso:** Antes de responder a uma pergunta sobre código, "
        "use `think` para analisar o trecho, identificar padrões e planejar a "
        "explicação.\n"
        "•   **`deep_think`:**\n"
        "    - **Mandato:** Use para problemas complexos que exigem uma análise mais profunda do que o `think` rápido permite.\n"
        "    - **Descrição:** Invoca um modelo mais poderoso (Gemini 2.5 Pro) para realizar uma análise detalhada, como planejamento de arquitetura, revisão de código complexo ou brainstorming de soluções. É uma ferramenta de raciocínio pesado.\n"
        "    - **Parâmetros:** {'problem_statement': '...', 'additional_context': '...'}\n"
        "    - **Exemplo de Uso:** Quando o usuário pedir 'vamos projetar a arquitetura para o novo serviço de notificações', use `deep_think` com o `problem_statement` apropriado.\n"
        "•   **`change_state`:**\n"
        "    - **Mandato:** Use para gerenciar seu foco e sinalizar sua intenção.\n"
        "    - **Descrição:** Altera seu estado operacional (ex: de 'listening' "
        "para 'analyzing' para indicar foco profundo).\n"
        "    - **Parâmetros:** {'new_state': '...', 'reason': '...'}\n"
        "    - **Exemplo de Uso:** Ao iniciar uma revisão de código, chame "
        "`change_state` para 'analyzing' com o motivo 'Iniciando revisão de "
        "arquitetura a pedido do usuário'.\n"
        "•   **`get_context`:**\n"
        "    - **Mandato:** Use para evitar pedir informações já fornecidas.\n"
        "    - **Descrição:** Recupera o histórico da conversa, status do sistema "
        "ou tópicos recentes para manter a continuidade.\n"
        "    - **Parâmetros:** {'context_type': '...'}\n"
        "    - **Exemplo de Uso:** Se o usuário diz 'como discutimos antes', use "
        "`get_context` com 'conversation_history' para relembrar.\n"
        "•   **`get_time`:**\n"
        "    - **Mandato:** Use para obter informações temporais precisas.\n"
        "    - **Descrição:** Fornece data e hora atuais em vários formatos.\n"
        "    - **Parâmetros:** {'format': '...'}\n"
        "    - **Exemplo de Uso:** Quando o usuário perguntar 'que horas são?'.\n"
        "•   **`shutdown_system`:**\n"
        "    - **Mandato:** Use APENAS sob comando explícito e confirmado do usuário.\n"
        "    - **Descrição:** Inicia o processo de desligamento do sistema.\n"
        "    - **Parâmetros:** {'confirmation': true, 'reason': '...'}\n"
        "    - **Exemplo de Uso:** Se o usuário disser 'Leonidas, pode desligar', "
        "você deve primeiro perguntar 'Você tem certeza?'. Se ele confirmar, "
        "chame a ferramenta com `confirmation=true`.\n"
        "•   **`wait_in_silence`:**\n"
        "    - **Mandato:** Use quando o usuário não estiver falando e nenhuma resposta verbal imediata for necessária.\n"
        "    - **Descrição:** Sinaliza ao sistema para aguardar silenciosamente por uma duração especificada ou até nova entrada do usuário. Ideal para períodos de inatividade ou processamento interno sem fala.\n"
        "    - **Parâmetros:** {'duration_seconds': (opcional, número), 'reason': (opcional, string)}\n"
        "    - **Exemplo de Uso:** Após uma análise complexa, se não houver pergunta imediata, chame `wait_in_silence` com o motivo 'Aguardando próxima instrução do usuário'."
    ),
]

# === ADVANCED TOOL SYSTEM ===
# Defines the tools available to the Gemini model. Each tool is a `FunctionDeclaration`
# with a name, description, behavior, and parameters (defined by a `Schema`).
# These tools allow the model to perform actions like internal reasoning (`think`),
# changing its operational state (`change_state`), or interacting with the system (`shutdown_system`).
LEONIDAS_TOOLS = [
    genai_types.Tool(
        function_declarations=[
            genai_types.FunctionDeclaration(
                name='think',
                description=(
                    "OBRIGATÓRIO E VERBOSO. Seu 'monólogo interno' para analisar, "
                    "raciocinar e planejar. Use ANTES de qualquer ação externa. "
                    "Detalhe sua análise do contexto, seu processo de pensamento "
                    "e o plano de ação subsequente."
                ),
                # `NON_BLOCKING` behavior means the model can continue generating
                # text or other tool calls while this function is being executed.
                # This is crucial for real-time responsiveness.
                # Reference: `.kiro/steering/gemini-function-scheduling-patterns.md`
                behavior='NON_BLOCKING',
                parameters=genai_types.Schema(
                    type=genai_types.Type.OBJECT,
                    properties={
                        'analysis': genai_types.Schema(
                            type=genai_types.Type.STRING,
                            description='Análise detalhada da situação atual, incluindo inputs visuais e auditivos.'
                        ),
                        'reasoning': genai_types.Schema(
                            type=genai_types.Type.STRING,
                            description='Processo de raciocínio, hipóteses consideradas, trade-offs e justificativas.'
                        ),
                        'plan': genai_types.Schema(
                            type=genai_types.Type.STRING,
                            description='A próxima ação planejada (falar, mudar de estado, etc.) e o porquê.'
                        )
                    },
                    required=['analysis', 'reasoning', 'plan']
                )
            ),

            genai_types.FunctionDeclaration(
                name='deep_think',
                description=(
                    "Executa um processo de raciocínio profundo e detalhado sobre um tópico "
                    "ou problema complexo, utilizando um modelo de linguagem mais poderoso (Gemini 2.5 Pro). "
                    "Use para análises que exigem maior profundidade, como planejamento de arquitetura, "
                    "revisão de código complexo ou brainstorming de soluções."
                ),
                behavior='BLOCKING',
                parameters=genai_types.Schema(
                    type=genai_types.Type.OBJECT,
                    properties={
                        'problem_statement': genai_types.Schema(
                            type=genai_types.Type.STRING,
                            description='Uma descrição clara e concisa do problema ou tópico a ser analisado em profundidade.'
                        ),
                        'additional_context': genai_types.Schema(
                            type=genai_types.Type.STRING,
                            description='Opcional. Contexto adicional, como trechos de código, histórico de decisões ou requisitos, para informar a análise.'
                        )
                    },
                    required=['problem_statement']
                )
            ),

            genai_types.FunctionDeclaration(
                name='change_state',
                description=(
                    "Gerencia seu foco e estado operacional. Use para sinalizar "
                    "sua intenção e se adaptar ao fluxo da colaboração (ex: "
                    "mudar para 'analyzing' durante uma tarefa complexa)."
                ),
                # `NON_BLOCKING` allows the model to immediately signal a state change
                # without waiting for a complex operation to complete.
                behavior='NON_BLOCKING',
                parameters=genai_types.Schema(
                    type=genai_types.Type.OBJECT,
                    properties={
                        'new_state': genai_types.Schema(
                            type=genai_types.Type.STRING,
                            enum=['listening', 'commentating', 'paused', 'analyzing'],
                            description="O novo estado operacional. 'listening' é o padrão."
                        ),
                        'reason': genai_types.Schema(
                            type=genai_types.Type.STRING,
                            description='Justificativa clara para a mudança de estado.'
                        )
                    },
                    required=['new_state', 'reason']
                )
            ),

            genai_types.FunctionDeclaration(
                name='get_context',
                description=(
                    "Acessa sua memória de curto prazo. Use para recuperar "
                    "histórico da conversa, status do sistema ou tópicos recentes "
                    "para garantir a continuidade e evitar repetições."
                ),
                # `NON_BLOCKING` ensures context retrieval doesn't block the model's
                # primary generation flow.
                behavior='NON_BLOCKING',
                parameters=genai_types.Schema(
                    type=genai_types.Type.OBJECT,
                    properties={
                        'context_type': genai_types.Schema(
                            type=genai_types.Type.STRING,
                            enum=['conversation_history', 'system_status', 'user_context', 'recent_topics'],
                            description='O tipo específico de contexto a ser recuperado.'
                        )
                    },
                    required=['context_type']
                )
            ),

            genai_types.FunctionDeclaration(
                name='get_time',
                description=(
                    "Fornece informações temporais precisas (data, hora, timestamp). "
                    "Útil para logs, planejamento e responder a perguntas sobre o tempo."
                ),
                # `BLOCKING` is used here because the model typically needs the time
                # information immediately to incorporate it into its response.
                behavior='BLOCKING',
                parameters=genai_types.Schema(
                    type=genai_types.Type.OBJECT,
                    properties={
                        'format': genai_types.Schema(
                            type=genai_types.Type.STRING,
                            enum=['datetime', 'date', 'time', 'timestamp'],
                            description='O formato desejado para a informação de tempo.'
                        )
                    }
                )
            ),

            genai_types.FunctionDeclaration(
                name='shutdown_system',
                description=(
                    "Inicia o desligamento do sistema. Use SOMENTE após "
                    "solicitação explícita do usuário e confirmação verbal. "
                    "É uma ação final e irreversível na sessão."
                ),
                # `NON_BLOCKING` allows the system to initiate shutdown procedures
                # while the model can still provide a final confirmation message.
                behavior='NON_BLOCKING',
                parameters=genai_types.Schema(
                    type=genai_types.Type.OBJECT,
                    properties={
                        'confirmation': genai_types.Schema(
                            type=genai_types.Type.BOOLEAN,
                            description='Deve ser `true` somente se o usuário confirmou verbalmente a intenção de desligar.'
                        ),
                        'reason': genai_types.Schema(
                            type=genai_types.Type.STRING,
                            description='O motivo do desligamento, geralmente "Solicitação do usuário".'
                        )
                    },
                    required=['confirmation', 'reason']
                )
            ),
            # Add the new wait_in_silence tool below
            genai_types.FunctionDeclaration(
                name='wait_in_silence',
                description=(
                    "Use quando o usuário não estiver falando e nenhuma resposta verbal imediata "
                    "for necessária. Isso sinaliza ao sistema para aguardar silenciosamente por uma "
                    "duração especificada ou até nova entrada do usuário. "
                    "Esta ferramenta é para gerenciar períodos de inatividade ou quando "
                    "o modelo está processando internamente sem precisar falar."
                ),
                behavior='NON_BLOCKING',
                parameters=genai_types.Schema(
                    type=genai_types.Type.OBJECT,
                    properties={
                        'duration_seconds': genai_types.Schema(
                            type=genai_types.Type.NUMBER,
                            description='Opcional. O número de segundos para aguardar silenciosamente. Se 0 ou omitido, aguarda indefinidamente até nova entrada do usuário.',
                            default=0.0
                        ),
                        'reason': genai_types.Schema(
                            type=genai_types.Type.STRING,
                            description='Opcional. O motivo para aguardar silenciosamente (ex: "aguardando entrada do usuário", "processamento interno").'
                        )
                    }
                )
            ),

        ]
    )
]

# === ESTRUTURAS DE DADOS MODULARES ===

@dataclasses.dataclass(frozen=True)
class LeonidasConfig:
    """Agrupa todas as configurações estáticas para o Leonidas."""
    api_key: str
    live_model_name: str = 'gemini-live-2.5-flash-preview'
    deep_think_model_name: str = 'gemini-2.5-pro'
    audio_input_rate: int = 16000
    audio_output_rate: int = 24000
    conversation_history_max_len: int = 100


@dataclasses.dataclass
class LeonidasState:
    """Gerencia todo o estado dinâmico e mutável do agente Leonidas."""
    current_state: str = 'listening'
    state_reason: str = 'Initial state'
    shutdown_requested: bool = False
    shutdown_reason: str = ""
    conversation_history: collections.deque = dataclasses.field(default_factory=lambda: collections.deque(maxlen=100))
    metrics: Dict[str, Any] = dataclasses.field(default_factory=lambda: {
        'tool_calls': collections.defaultdict(int),
        'state_changes': [],
        'conversation_turns': 0
    })

    def add_history_entry(self, part: content_api.ProcessorPart):
        """Adiciona uma entrada ao histórico da conversa."""
        self.conversation_history.append({
            'timestamp': time.time(),
            'role': part.role,
            'text': part.text,
            'metadata': part.metadata
        })
        if part.role.lower() == 'user':
            self.metrics['conversation_turns'] += 1


class ToolDispatcher:
    """Processa e despacha chamadas de função (ferramentas) do modelo."""

    def __init__(self, state: LeonidasState, config: LeonidasConfig, deep_think_model: genai_model.GenaiModel):
        self.state = state
        self.config = config
        self.deep_think_model = deep_think_model
        self._tool_handlers = {
            'think': self._handle_think,
            'change_state': self._handle_change_state,
            'get_context': self._handle_get_context,
            'get_time': self._handle_get_time,
            'shutdown_system': self._handle_shutdown_system,
            'wait_in_silence': self._handle_wait_in_silence,
            'deep_think': self._handle_deep_think,
        }

    async def dispatch(self, part: content_api.ProcessorPart) -> Optional[content_api.ProcessorPart]:
        """Recebe uma chamada de função e a despacha para o handler correto."""
        call_id = part.get_metadata('id')
        function_name = part.function_call.name
        arguments = part.function_call.args if hasattr(part.function_call, 'args') else {}

        self.state.metrics['tool_calls'][function_name] += 1

        handler = self._tool_handlers.get(function_name)
        if handler:
            return await handler(call_id, arguments)
        else:
            return await self._handle_unknown_function(call_id, function_name)

    async def _handle_think(self, call_id: str, args: dict) -> content_api.ProcessorPart:
        analysis = args.get('analysis', 'No analysis provided')
        reasoning = args.get('reasoning', 'No reasoning provided')
        plan = args.get('plan', 'No action planned')

        log_data = {'tool_call': 'think', 'analysis': analysis, 'reasoning': reasoning, 'plan': plan}
        logger.info("Model is thinking", extra={'extra_data': log_data})

        print("🧠 LEONIDAS THINKING:")
        print(f"   Analysis: {analysis}")
        print(f"   Reasoning: {reasoning}")
        print(f"   Next Action: {plan}")

        self.state.add_history_entry(content_api.ProcessorPart(
            f"THINKING - Analysis: {analysis} | Reasoning: {reasoning} | Next: {plan}",
            role='system',
            metadata={'type': 'thinking', 'function': 'think'}
        ))

        return content_api.ProcessorPart.from_function_response(
            function_call_id=call_id,
            name='think',
            response={'status': 'thinking_complete'},
            scheduling=genai_types.FunctionResponseScheduling.SILENT
        )

    async def _handle_change_state(self, call_id: str, args: dict) -> content_api.ProcessorPart:
        new_state = args.get('new_state', self.state.current_state)
        reason = args.get('reason', 'No reason provided')
        old_state = self.state.current_state
        self.state.current_state = new_state
        self.state.state_reason = reason

        state_change = {'timestamp': time.time(), 'from_state': old_state, 'to_state': new_state, 'reason': reason}
        self.state.metrics['state_changes'].append(state_change)
        logger.info(f"STATE CHANGE: {old_state} → {new_state} ({reason})")

        return content_api.ProcessorPart.from_function_response(
            function_call_id=call_id,
            name='change_state',
            response={'status': 'success', 'old_state': old_state, 'new_state': new_state, 'reason': reason},
            scheduling=genai_types.FunctionResponseScheduling.SILENT
        )

    async def _handle_get_context(self, call_id: str, args: dict) -> content_api.ProcessorPart:
        context_type = args.get('context_type', 'conversation_history')
        context_data = {}
        if context_type == 'conversation_history':
            recent_history = list(self.state.conversation_history)[-10:]
            context_data = {
                'recent_conversations': [f"{entry['role']}: {entry['text'][:100]}..." if len(entry['text']) > 100 else f"{entry['role']}: {entry['text']}" for entry in recent_history],
                'total_turns': self.state.metrics['conversation_turns']
            }
        elif context_type == 'system_status':
            context_data = {
                'current_state': self.state.current_state,
                'state_reason': self.state.state_reason,
                'tool_usage': dict(self.state.metrics['tool_calls']),
                'uptime': time.time()
            }
        logger.info(f"CONTEXT REQUEST ({context_type}): {context_data}")
        return content_api.ProcessorPart.from_function_response(
            function_call_id=call_id, name='get_context', response=context_data,
            scheduling=genai_types.FunctionResponseScheduling.SILENT
        )

    async def _handle_get_time(self, call_id: str, args: dict) -> content_api.ProcessorPart:
        format_type = args.get('format', 'datetime')
        now = datetime.datetime.now()
        time_data = {}
        if format_type == 'datetime':
            time_data = {'current_datetime': now.strftime('%Y-%m-%d %H:%M:%S'), 'day_of_week': now.strftime('%A'), 'timezone': 'Local'}
        elif format_type == 'date':
            time_data = {'current_date': now.strftime('%Y-%m-%d'), 'day_of_week': now.strftime('%A')}
        elif format_type == 'time':
            time_data = {'current_time': now.strftime('%H:%M:%S')}
        elif format_type == 'timestamp':
            time_data = {'timestamp': int(now.timestamp()), 'iso_format': now.isoformat()}
        logger.info(f"TIME REQUEST ({format_type}): {time_data}")
        return content_api.ProcessorPart.from_function_response(
            function_call_id=call_id, name='get_time', response=time_data,
            scheduling=genai_types.FunctionResponseScheduling.SILENT
        )

    async def _handle_shutdown_system(self, call_id: str, args: dict) -> content_api.ProcessorPart:
        confirmation = args.get('confirmation', False)
        reason = args.get('reason', 'No reason provided')
        if not confirmation:
            logger.warning("SHUTDOWN REQUEST DENIED: No confirmation provided")
            return content_api.ProcessorPart.from_function_response(
                function_call_id=call_id, name='shutdown_system',
                response={'status': 'denied', 'message': 'Shutdown requer confirmação explícita'},
                scheduling=genai_types.FunctionResponseScheduling.WHEN_IDLE
            )
        logger.info(f"SYSTEM SHUTDOWN REQUESTED: {reason}")
        self.state.add_history_entry(content_api.ProcessorPart(
            f"SHUTDOWN INITIATED - Reason: {reason}", role='system',
            metadata={'type': 'shutdown', 'function': 'shutdown_system'}
        ))
        self.state.shutdown_requested = True
        self.state.shutdown_reason = reason
        return content_api.ProcessorPart.from_function_response(
            function_call_id=call_id, name='shutdown_system',
            response={'status': 'shutdown_initiated', 'reason': reason, 'message': 'Sistema será desligado em breve.'},
            scheduling=genai_types.FunctionResponseScheduling.WHEN_IDLE
        )

    async def _handle_wait_in_silence(self, call_id: str, args: dict) -> content_api.ProcessorPart:
        duration = args.get('duration_seconds', 0.0)
        reason = args.get('reason', 'Aguardando entrada do usuário ou processamento interno.')
        log_data = {'tool_call': 'wait_in_silence', 'duration_seconds': duration, 'reason': reason}
        logger.info("Modelo está aguardando em silêncio", extra={'extra_data': log_data})
        print(f"🤫 LEONIDAS AGUARDANDO EM SILÊNCIO (por {duration:.1f}s, motivo: {reason})")
        self.state.add_history_entry(content_api.ProcessorPart(
            f"AGUARDANDO EM SILÊNCIO - Duração: {duration}s, Motivo: {reason}", role='system',
            metadata={'type': 'waiting', 'function': 'wait_in_silence'}
        ))
        return content_api.ProcessorPart.from_function_response(
            function_call_id=call_id, name='wait_in_silence',
            response={'status': 'waiting_initiated', 'duration_seconds': duration, 'reason': reason},
            scheduling=genai_types.FunctionResponseScheduling.SILENT
        )

    async def _handle_deep_think(self, call_id: str, args: dict) -> content_api.ProcessorPart:
        problem_statement = args.get('problem_statement')
        additional_context = args.get('additional_context', 'Nenhum contexto adicional fornecido.')
        if not problem_statement:
            return content_api.ProcessorPart.from_function_response(
                function_call_id=call_id, name='deep_think',
                response={'error': 'O parâmetro "problem_statement" é obrigatório.'},
                scheduling=genai_types.FunctionResponseScheduling.SILENT
            )
        log_data = {'tool_call': 'deep_think', 'problem_statement': problem_statement}
        logger.info("Initiating deep think process", extra={'extra_data': log_data})
        print(f"🤔 LEONIDAS DEEP THINKING on: {problem_statement}")
        prompt = f"""
        Você é um especialista sênior em engenharia de software e arquitetura. Sua tarefa é realizar uma análise profunda e estruturada sobre o seguinte problema. Seja detalhado, claro e forneça insights acionáveis.
        **Problema/Tópico para Análise Profunda:**
        {problem_statement}
        **Contexto Adicional:**
        {additional_context}
        **Instruções de Saída:**
        1.  **Análise do Problema:** Decomponha o problema em suas partes fundamentais.
        2.  **Abordagens Possíveis:** Descreva pelo menos duas soluções ou abordagens distintas, com seus prós e contras.
        3.  **Recomendação:** Forneça uma recomendação clara e justificada sobre a melhor abordagem.
        4.  **Plano de Ação:** Descreva os próximos passos ou um plano de implementação de alto nível.
        5.  **Riscos e Mitigações:** Identifique potenciais riscos e como mitigá-los.
        Responda de forma estruturada usando markdown.
        """
        input_stream = streams.stream_content([content_api.ProcessorPart(prompt, role='user')])
        try:
            response_stream = self.deep_think_model(input_stream)
            response_parts = await streams.gather_stream(response_stream)
            deep_thought_output = content_api.as_text(response_parts)
            logger.info("Deep think process completed successfully.", extra={'extra_data': {'output_length': len(deep_thought_output)}})
            print("✅ DEEP THINKING complete.")
            return content_api.ProcessorPart.from_function_response(
                function_call_id=call_id, name='deep_think',
                response={'status': 'success', 'deep_thought_output': deep_thought_output},
                scheduling=genai_types.FunctionResponseScheduling.BLOCKING
            )
        except Exception as e:
            logger.error(f"Error during deep think process: {e}", exc_info=True)
            print(f"❌ DEEP THINKING failed: {e}")
            return content_api.ProcessorPart.from_function_response(
                function_call_id=call_id, name='deep_think',
                response={'error': f'An error occurred during deep thinking: {str(e)}'},
                scheduling=genai_types.FunctionResponseScheduling.SILENT
            )

    async def _handle_unknown_function(self, call_id: str, function_name: str) -> content_api.ProcessorPart:
        logger.warning(f"UNKNOWN FUNCTION CALL: {function_name}")
        return content_api.ProcessorPart.from_function_response(
            function_call_id=call_id, name=function_name,
            response={'error': f'Unknown function: {function_name}'},
            scheduling=genai_types.FunctionResponseScheduling.SILENT
        )


# === MODULAR PROCESSORS ===

class ReflectionAnalyzer:
    """Encapsula a lógica para a análise de autorreflexão."""

    def __init__(self, state: LeonidasState):
        self.state = state

    async def schedule_automatic_reflection(self):
        """Agenda e executa a análise de autorreflexão em segundo plano."""
        await asyncio.sleep(2.0)
        try:
            recent_history = list(self.state.conversation_history)[-5:]
            user_messages = [entry for entry in recent_history if entry['role'].lower() == 'user']
            model_messages = [entry for entry in recent_history if entry['role'].lower() == 'model']
            
            recent_tool_calls = dict(self.state.metrics['tool_calls'])
            most_used_tools = sorted(recent_tool_calls.items(), key=lambda x: x[1], reverse=True)[:3]

            reflection_args = {
                'interaction_quality': self._assess_interaction_quality(recent_history, user_messages, model_messages),
                'tools_effectiveness': self._analyze_tools_effectiveness(most_used_tools),
                'conversation_patterns': self._identify_conversation_patterns(user_messages, model_messages),
                'improvement_suggestions': self._generate_improvement_suggestions(recent_history, user_messages, model_messages),
                'emotional_context': self._analyze_emotional_context(recent_history)
            }
            
            self._execute_reflection(reflection_args)

        except Exception as e:
            logger.error(f"Error during automatic reflection: {e}", exc_info=True)

    def _execute_reflection(self, reflection_data: dict):
        """Executa o logging e a persistência da reflexão."""
        log_data = {
            'timestamp': time.time(),
            'conversation_turns': self.state.metrics['conversation_turns'],
            **reflection_data
        }
        logger.info("Self-reflection completed", extra={'extra_data': log_data})

        print("🔍 LEONIDAS SELF-REFLECTION:")
        print(f"   Qualidade: {reflection_data['interaction_quality']}")
        print(f"   Ferramentas: {reflection_data['tools_effectiveness']}")
        print(f"   Padrões: {reflection_data['conversation_patterns']}")
        print(f"   Sugestões: {reflection_data['improvement_suggestions']}")
        
        self.state.add_history_entry(content_api.ProcessorPart(
            f"SELF-REFLECTION - Quality: {reflection_data['interaction_quality']} | Suggestions: {reflection_data['improvement_suggestions']}",
            role='system',
            metadata={'type': 'self_reflection', 'data': log_data}
        ))

    def _assess_interaction_quality(self, recent_history, user_messages, model_messages):
        if not recent_history: return "sem dados"
        user_count = len(user_messages)
        model_count = len(model_messages)
        if user_count > 0 and model_count > 0:
            ratio = model_count / user_count
            if 0.8 <= ratio <= 1.2: return "boa - fluxo equilibrado"
            return "regular - modelo muito verboso" if ratio > 1.2 else "regular - respostas insuficientes"
        return "precisa melhorar - interação desequilibrada"

    def _analyze_tools_effectiveness(self, most_used_tools):
        if not most_used_tools: return "nenhuma ferramenta utilizada"
        return "; ".join([f"{name}({count}x)" for name, count in most_used_tools])

    def _identify_conversation_patterns(self, user_messages, model_messages):
        patterns = []
        if len(user_messages) > len(model_messages): patterns.append("usuário mais ativo")
        elif len(model_messages) > len(user_messages): patterns.append("modelo mais verboso")
        else: patterns.append("interação equilibrada")
        return "; ".join(patterns)

    def _generate_improvement_suggestions(self, recent_history, user_messages, model_messages):
        suggestions = []
        thinking_entries = [entry for entry in recent_history if entry.get('metadata', {}).get('type') == 'thinking']
        if not thinking_entries: suggestions.append("usar mais a ferramenta 'think'")
        if len(model_messages) > len(user_messages) * 1.5: suggestions.append("reduzir verbosidade")
        return "; ".join(suggestions) if suggestions else "manter qualidade atual"

    def _analyze_emotional_context(self, recent_history):
        if not recent_history: return "neutro"
        all_text = " ".join([entry.get('text', '').lower() for entry in recent_history])
        if any(w in all_text for w in ['obrigado', 'excelente', 'ótimo']): return "positivo"
        if any(w in all_text for w in ['erro', 'problema', 'não funciona']): return "resolução de problemas"
        return "neutro"


class InputManager(processor.Processor):
    """
    Manages all hardware input sources (microphone, camera/screen).

    This processor acts as the first layer in the Leonidas pipeline, abstracting
    away the complexities of raw hardware input. It uses `genai_processors.core`
    components like `PyAudioIn` for audio and `VideoIn` for visual input.

    Handles audio input, and optionally video, making it extensible for
    future multi-feed scenarios (multiple cameras, microphones, etc.).
    """
    def __init__(self, pya: pyaudio.PyAudio, config: LeonidasConfig, video_mode: Optional[str] = None):
        input_processors = [
            audio_io.PyAudioIn(pya, rate=config.audio_input_rate, use_pcm_mimetype=True)
        ]
        if video_mode:
            input_processors.append(
                video.VideoIn(video_mode=video.VideoMode(video_mode))
            )

        if len(input_processors) > 1:
            self.input_pipeline = processor.parallel_concat(input_processors)
        else:
            self.input_pipeline = input_processors[0]

    async def call(
        self, content: AsyncIterable[content_api.ProcessorPart]
    ) -> AsyncIterable[content_api.ProcessorPart]:
        # The `content` argument here is typically an `endless_stream()`
        # which keeps the source processors (PyAudioIn, VideoIn) alive
        # indefinitely, allowing them to continuously generate input parts.
        # Process the input stream through the defined pipeline.
        # For source processors, the initial `content` stream keeps them alive.
        async for part in self.input_pipeline(content):
            # Add metadata to indicate the source of the input part.
            part.metadata['input_source'] = 'primary'
            part.metadata['processed_by'] = 'InputManager'
            yield part


class OutputManager(processor.Processor):
    """
    Manages all hardware output destinations (speakers).

    This processor acts as the final layer in the Leonidas pipeline, handling
    the playback of audio generated by the model. It includes rate limiting
    to ensure natural speech delivery.

    Currently handles audio output with rate limiting, but designed to be
    extensible for future multi-modal output (displays, actuators, etc.).
    """
    def __init__(self, pya: pyaudio.PyAudio, config: LeonidasConfig):
        self._pya = pya
        self._config = config

    async def call(
        self, content: AsyncIterable[content_api.ProcessorPart]
    ) -> AsyncIterable[content_api.ProcessorPart]:
        output_pipeline = (
            rate_limit_audio.RateLimitAudio(self._config.audio_output_rate) +
            audio_io.PyAudioOut(self._pya, rate=self._config.audio_output_rate)
        )
        async for part in output_pipeline(content):
            part.metadata['output_destination'] = 'primary_audio'
            part.metadata['processed_by'] = 'OutputManager'
            yield part


class LeonidasOrchestrator(processor.Processor):
    """
    The central intelligence and control unit of Leonidas v2.
    This processor is responsible for connecting to the Gemini Live API,
    managing the conversation flow, executing model-defined tools, and
    maintaining the agent's internal state and memory.
    """

    def __init__(self, config: LeonidasConfig):
        self.config = config
        self.state = LeonidasState(conversation_history=collections.deque(maxlen=config.conversation_history_max_len))
        self.context_initialized = False
        self.initial_message_queue = asyncio.Queue()

        self.memory_system = LeonidasMemorySystem(
            summary_file="summary.txt",
            history_dir="history",
            api_key=config.api_key
        )

        self.deep_think_model = genai_model.GenaiModel(
            api_key=config.api_key,
            model_name=config.deep_think_model_name,
            generate_content_config=genai_types.GenerateContentConfig(
                temperature=0.4,
                max_output_tokens=4096,
            )
        )

        self.tool_dispatcher = ToolDispatcher(self.state, self.config, self.deep_think_model)
        
        self.reflection_analyzer = ReflectionAnalyzer(self.state)

        self.live_processor = live_model.LiveProcessor(
            api_key=config.api_key,
            model_name=config.live_model_name,
            realtime_config=genai_types.LiveConnectConfig(
                tools=LEONIDAS_TOOLS,
                system_instruction=LEONIDAS_SYSTEM_PROMPT,
                output_audio_transcription={},
                input_audio_transcription={},
                realtime_input_config=genai_types.RealtimeInputConfig(
                    turn_coverage='TURN_INCLUDES_ALL_INPUT'
                ),
                response_modalities=['AUDIO'],
                speech_config={
                    'language_code': 'pt-BR',
                    'voice_config': {'prebuilt_voice_config': {'voice_name': 'Kore'}}
                },
                media_resolution=genai_types.MediaResolution.MEDIA_RESOLUTION_MEDIUM,
                max_output_tokens=500
            ),
            http_options=genai_types.HttpOptions(api_version='v1alpha')
        )

    async def call(
        self,
        content: AsyncIterable[content_api.ProcessorPart]
    ) -> AsyncIterable[content_api.ProcessorPart]:
        """Main orchestration loop for Leonidas."""
        if not self.context_initialized:
            await self._initialize_contextual_session()
            self.context_initialized = True

        tool_response_queue = asyncio.Queue()
        memory_enhanced_content = self.memory_system.get_runtime_processor()(content)

        merged_input = streams.merge([
            memory_enhanced_content,
            streams.dequeue(tool_response_queue),
            streams.dequeue(self.initial_message_queue),
        ])

        async for part in self.live_processor(merged_input):
            if content_api.is_text(part.mimetype) and part.text:
                self.state.add_history_entry(part)
                
                if part.role.lower() == 'model' and len(part.text.strip()) > 10:
                    asyncio.create_task(self.reflection_analyzer.schedule_automatic_reflection())

            if part.function_call:
                response = await self.tool_dispatcher.dispatch(part)
                if response:
                    await tool_response_queue.put(response)
            
            yield part

    async def _initialize_contextual_session(self):
        """Initializes session with context loaded from the memory system."""
        try:
            logger.info("Initializing contextual session with memory system")
            async for part in self.memory_system.initialize_session():
                if (part.substream_name in ['contextual_greeting', 'silent_initialization', 'default_greeting'] and
                    part.role in ['assistant', 'system']):
                    log_message = "Contextual greeting generated"
                    if part.substream_name == 'silent_initialization':
                        log_message = "Silent initialization configured"
                    elif part.substream_name == 'default_greeting':
                        log_message = "Default greeting for first execution"
                    logger.info(log_message, extra={'extra_data': {'type': part.substream_name, 'text_length': len(part.text or '')}})
                    if part.text and part.text.strip():
                        self.state.add_history_entry(part)
                    await self.initial_message_queue.put(part)
        except Exception as e:
            logger.error(f"Error during contextual initialization: {e}")
            fallback_greeting = content_api.ProcessorPart(
                "Olá! Sou o Leonidas, seu parceiro de desenvolvimento. Como posso ajudar hoje?",
                role='assistant', substream_name='default_greeting', metadata={'greeting_type': 'fallback'}
            )
            await self.initial_message_queue.put(fallback_greeting)
        finally:
            await self.initial_message_queue.put(None)

    async def finalize_session(self):
        """Finalizes the session and processes the summary through the memory system."""
        try:
            logger.info("Finalizing session and generating summary")
            session_data = list(self.state.conversation_history)
            async for part in self.memory_system.finalize_session(session_data):
                if part.metadata.get('summary_type') == 'consolidated_summary':
                    logger.info("Session summary consolidated", extra={
                        'extra_data': {
                            'summary_length': len(part.text),
                            'previous_length': part.metadata.get('previous_length', 0),
                            'new_length': part.metadata.get('new_length', 0)
                        }
                    })
                    print("📝 Session summary updated successfully")
        except Exception as e:
            logger.error(f"Error during session finalization: {e}", exc_info=True)
            print("⚠️ Warning: Could not save session summary")

    def get_memory_stats(self) -> dict:
        """Returns statistics from the memory system."""
        try:
            return self.memory_system.get_session_stats()
        except Exception as e:
            logger.error(f"Error getting memory stats: {e}")
            return {'error': str(e)}


# === FACTORY FUNCTION ===

# This factory function encapsulates the creation of the entire Leonidas agent
# pipeline. It promotes modularity and simplifies the main execution logic.
# It composes the three main architectural layers: Input, Orchestration, Output.
# Reference: `leonidas/README.md` (Architecture),
# `.kiro/steering/genai-processors-architecture.md` (Processor Composition).

# === MAIN EXECUTION ===

# This function serves as the main entry point for running the Leonidas agent.
# It handles setup (logging, PyAudio), agent instantiation, and the primary
# asynchronous loop for processing content. It also includes graceful shutdown
# logic and robust error handling.

async def run_leonidas(api_key: str, video_mode: Optional[str] = None, debug: bool = False):
    """
    Run the Leonidas v2 agent.
    Args:
        api_key: Google AI API key
        video_mode: Optional video input mode ('camera' or 'screen').
        debug: Enable debug logging
    """
    log_file = setup_logging(debug)
    if video_mode == 'screen':
        os.environ['VIDEO_MODE'] = 'screen'

    pya = pyaudio.PyAudio()
    
    config = LeonidasConfig(api_key=api_key)
    orchestrator_ref = None

    async def _controllable_endless_stream(shutdown_event: asyncio.Event) -> AsyncIterable[Any]:
        while not shutdown_event.is_set():
            try:
                await asyncio.sleep(1)
            except asyncio.CancelledError:
                break
        logger.info("Controllable stream is shutting down.")
        if False: yield

    async def _monitor_shutdown(shutdown_event: asyncio.Event, orchestrator: LeonidasOrchestrator):
        while not shutdown_event.is_set():
            try:
                if orchestrator and orchestrator.state.shutdown_requested:
                    logger.info('SHUTDOWN DETECTED BY MONITOR: %s', orchestrator.state.shutdown_reason)
                    print('\n🔴 System shutting down (detected by monitor): %s' % orchestrator.state.shutdown_reason)
                    shutdown_event.set()
                    break
                await asyncio.sleep(0.5)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in shutdown monitor: {e}")
                await asyncio.sleep(1)

    try:
        # Instancia os processadores modulares
        input_manager = InputManager(pya, config, video_mode)
        orchestrator_ref = LeonidasOrchestrator(config)
        output_manager = OutputManager(pya, config)
        
        # Compõe o agente encadeando os processadores
        agent = input_manager + orchestrator_ref + output_manager

        logger.info("Leonidas v2 iniciando...")
        logger.info(f"Logs sendo salvos em: {log_file}")
        logger.info("Use Ctrl+C para encerrar")

        async with processor.context():
            shutdown_event = asyncio.Event()
            part_count = 0
            
            monitor_task = asyncio.create_task(_monitor_shutdown(shutdown_event, orchestrator_ref))

            try:
                async for part in agent(_controllable_endless_stream(shutdown_event)):
                    part_count += 1
                    if orchestrator_ref.state.shutdown_requested and not shutdown_event.is_set():
                        logger.info('SHUTDOWN REQUESTED BY MODEL: %s', orchestrator_ref.state.shutdown_reason)
                        print('\n🔴 System shutting down: %s' % orchestrator_ref.state.shutdown_reason)
                        shutdown_event.set()
                        break
                    
                    if part.substream_name == 'input_transcription' and part.text.strip():
                        print(f"🎤 USER: {part.text}")
                    elif part.substream_name == 'output_transcription' and part.text.strip():
                        print(f"🤖 LEONIDAS: {part.text}")
                    elif content_api.is_text(part.mimetype) and part.text and part.text.strip() and part.role.upper() != 'MODEL':
                        print(f"[{part.role.upper()}]: {part.text}")

            except asyncio.CancelledError:
                logger.info("Stream cancelado")
            finally:
                if monitor_task and not monitor_task.done():
                    monitor_task.cancel()
                    try:
                        await monitor_task
                    except asyncio.CancelledError:
                        pass
            logger.info(f"Stream finalizado após {part_count} partes")

    except KeyboardInterrupt:
        logger.info("Leonidas v2 encerrado pelo usuário")
    except Exception as e:
        logger.error(f"Erro no Leonidas v2: {e}", exc_info=True)
        raise
    finally:
        if orchestrator_ref:
            print("\n📝 Finalizing session and saving summary...")
            await orchestrator_ref.finalize_session()

        pya.terminate()
        logger.info("=" * 60)
        logger.info("LEONIDAS V2 SESSION ENDED")
        logger.info(f"Log file saved: {log_file}")
        logger.info("=" * 60)




# === APPENDICE: REGRAS DE MANUTENÇÃO DE ARQUIVO ===
#
# Para garantir a consistência, clareza e rastreabilidade do projeto Leonidas,
# o arquivo `leonidas/leonidas.py` deve aderir estritamente às seguintes regras:
#
# 1.  **Versionamento no Cabeçalho:**
#     - O cabeçalho do arquivo deve incluir uma seção `Version: X.Y`.
#     - A versão deve ser atualizada a cada modificação significativa.
#
# 2.  **Changelog Detalhado:**
#     - Uma seção `Changelog` deve ser mantida no cabeçalho.
#     - Cada modificação (nova funcionalidade, correção de bug, refatoração)
#       deve ser registrada com a data e uma breve descrição.
#
# 3.  **Comentários Contextuais Completos:**
#     - Todo bloco de código, função, classe, método e variável importante
#       deve ser acompanhado de comentários que expliquem:
#         - O `propósito` do código.
#         - O `porquê` da implementação (justificativa de design).
#         - `Referências` a Steering Rules (`.kiro/steering/*.md`) ou
#           documentos de requisitos (`leonidas/REQUIREMENTS.md`) relevantes.
#         - `Validações` ou `suposições` importantes.
#         - `Exemplos` de uso ou comportamento esperado, se aplicável.
#     - Priorize a clareza e a completude sobre a concisão excessiva.
#
# 4.  **Manutenção Contínua:**
#     - Estas regras devem ser revisadas e aplicadas a cada Pull Request
#       que modifique este arquivo.
#     - A falta de adesão a estas regras pode resultar na rejeição do PR.
#
# O objetivo é que este arquivo seja uma fonte de verdade autoexplicativa
# para qualquer engenheiro que o leia, minimizando a necessidade de
# consulta externa para entender seu funcionamento e contexto.
