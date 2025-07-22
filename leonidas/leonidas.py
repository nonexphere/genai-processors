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
import datetime
import os
import sys # Import the sys module
import time
from datetime import datetime as dt
from pathlib import Path
from typing import AsyncIterable, Optional, Any

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
from genai_processors.core import live_model
from genai_processors.core import rate_limit_audio
from genai_processors.core import video
from google.genai import types as genai_types

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
    log_level = logging.DEBUG if debug else logging.INFO

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
    logging.set_verbosity(log_level)

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

# === MODULAR PROCESSORS ===

class InputManager(processor.Processor):
    """
    Manages all hardware input sources (microphone, camera/screen).

    This processor acts as the first layer in the Leonidas pipeline, abstracting
    away the complexities of raw hardware input. It uses `genai_processors.core`
    components like `PyAudioIn` for audio and `VideoIn` for visual input.

    Handles audio input, and optionally video, making it extensible for
    future multi-feed scenarios (multiple cameras, microphones, etc.).
    """
    def __init__(self, pya: pyaudio.PyAudio, video_mode: Optional[str] = None):
        input_processors = [
            # PyAudioIn captures audio from the default microphone.
            # `use_pcm_mimetype=True` ensures compatibility with Gemini Live API.
            audio_io.PyAudioIn(pya, rate=AUDIO_INPUT_RATE, use_pcm_mimetype=True)
        ]
        if video_mode:
            # VideoIn captures frames from camera or screen.
            # This is added to the input pipeline only if `video_mode` is specified.
            input_processors.append(
                video.VideoIn(video_mode=video.VideoMode(video_mode))
            )

        # If both audio and video are enabled, `parallel_concat` ensures
        # both streams are processed concurrently and merged into a single
        # input stream for the next stage.
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
    def __init__(self, pya: pyaudio.PyAudio):
        self._pya = pya

    async def call(
        self, content: AsyncIterable[content_api.ProcessorPart]
    ) -> AsyncIterable[content_api.ProcessorPart]:
        # `RateLimitAudio` ensures that audio chunks are played at a natural
        # speed, preventing rapid playback or buffering issues.
        # `PyAudioOut` sends the audio data to the default speaker.
        # Create the output pipeline - rate limiting + audio output
        output_pipeline = (
            rate_limit_audio.RateLimitAudio(AUDIO_OUTPUT_RATE) +
            audio_io.PyAudioOut(self._pya, rate=AUDIO_OUTPUT_RATE)
        )

        # Process through the output pipeline
        async for part in output_pipeline(content):
            # Add metadata to indicate the destination of the output part.
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

    def __init__(self, api_key: str):
        # Google AI API key for authentication with Gemini Live API.
        self.api_key = api_key

        # Agent's current operational state, controlled by the model
        # using the `change_state` tool. This allows the model to
        # manage its own behavior (e.g., listening, analyzing).
        self.agent_state = 'listening'
        self.state_reason = 'Initial state'

        # Stores a rolling window of conversation history for context.
        # `collections.deque` is used for efficient appends and pops from both ends.
        # `maxlen` prevents unbounded memory growth.
        self.conversation_history = collections.deque(maxlen=100)
        self.context_summary = "" # Placeholder for future context summarization

        # Collects various performance and operational metrics,
        # such as tool usage counts and state transition history.
        self.metrics = {
            'tool_calls': collections.defaultdict(int),
            'state_changes': [],
            'conversation_turns': 0
        }

        # Flags to signal a system shutdown, initiated by the model
        # via the `shutdown_system` tool.
        self.shutdown_requested = False
        self.shutdown_reason = ""

        # Configure the Live API processor. This is the core component that
        # interacts with Google's Gemini Live API for real-time conversational AI.
        self.live_processor = live_model.LiveProcessor(
            api_key=api_key,
            model_name=MODEL_LIVE,
            # `realtime_config` defines the behavior of the Gemini Live API session.
            # This configuration is critical for real-time performance, tool availability,
            # and speech characteristics.
            # Reference: `.kiro/steering/gemini-models-complete-reference.md`
            realtime_config=genai_types.LiveConnectConfig(
                # `tools` declares the functions the model can call.
                tools=LEONIDAS_TOOLS,
                # `system_instruction` provides the model with its persona,
                # directives, and tool usage protocols.
                system_instruction=LEONIDAS_SYSTEM_PROMPT,
                # `output_audio_transcription` enables transcription of the model's
                # spoken output, useful for logging and debugging.
                output_audio_transcription={},
                # `realtime_input_config` defines how real-time inputs (audio/video)
                # are handled, including turn coverage for conversation turns.
                realtime_input_config=genai_types.RealtimeInputConfig(
                    turn_coverage='TURN_INCLUDES_ALL_INPUT'
                ),
                # `response_modalities` specifies the types of output the model should
                # generate (e.g., AUDIO, TEXT).
                response_modalities=['AUDIO'],
                # `speech_config` defines the language and voice for Text-to-Speech.
                # 'Kore' is selected for its professional and clear tone in Portuguese.
                speech_config={
                    'language_code': 'pt-BR',
                    'voice_config': {
                        'prebuilt_voice_config': {
                            'voice_name': 'Kore'
                        }
                    }
                },
                # `media_resolution` balances quality and latency for visual inputs.
                media_resolution=genai_types.MediaResolution.MEDIA_RESOLUTION_MEDIUM,
                # `max_output_tokens` limits the length of model responses,
                # crucial for maintaining conversational flow and controlling costs.
                max_output_tokens=500
            ),
            # `http_options` can specify API version or other HTTP client settings.
            http_options=genai_types.HttpOptions(api_version='v1alpha')
        )

    async def call(
        self,
        content: AsyncIterable[content_api.ProcessorPart]
    ) -> AsyncIterable[content_api.ProcessorPart]:
        """Main orchestration loop for Leonidas.

        This method processes the incoming stream of multimodal content,
        sends it to the Gemini Live API, and handles the model's responses,
        including text, audio, and tool calls.
        """

        # A queue to inject responses from tool calls back into the main
        # processing stream. This allows tool outputs to be treated as
        # new inputs for the model.
        tool_response_queue = asyncio.Queue()

        # Merge the primary content stream (from InputManager) with the
        # stream of tool responses. This ensures that tool responses are processed
        # by the Live API as part of the ongoing conversation.
        merged_input = streams.merge([
            content,
            streams.dequeue(tool_response_queue)
        ], stop_on_first=True)

        # The `live_processor` handles the actual communication with the
        # Gemini Live API, managing the WebSocket connection and streaming
        # of inputs and outputs.
        async for part in self.live_processor(merged_input):

            # If the part is text, add it to the conversation history.
            # This is used for context management and future `get_context` calls.
            if content_api.is_text(part.mimetype) and part.text:
                self._add_to_conversation_history(part)

            # If the part is a function call from the model, handle it
            # by executing the corresponding Python function and queuing
            # its response back to the model. This is the core of the
            # model's self-control and tool usage.
            if part.function_call:
                await self._handle_function_call(part, tool_response_queue)

            # Yield all parts (text, audio, etc.) to the next processor in the pipeline (OutputManager).
            yield part

    def _add_to_conversation_history(self, part: content_api.ProcessorPart):
        """Add part to conversation history.

        This method stores relevant parts (user input, model output) in a
        `collections.deque` to maintain a rolling window of the conversation.
        It also updates the total conversation turn count.
        """
        self.conversation_history.append({
            'timestamp': time.time(),
            'role': part.role,
            'text': part.text,
            'metadata': part.metadata
        })

        if part.role.lower() == 'user':
            self.metrics['conversation_turns'] += 1

    async def _handle_function_call(
        self,
        part: content_api.ProcessorPart,
        response_queue: asyncio.Queue
    ): # type: ignore
        """Handles function calls made by the Gemini model.

        This method extracts the function name and arguments from the
        `ProcessorPart`, updates internal metrics, and dispatches the call
        to the appropriate handler function (e.g., `_handle_think`,
        `_handle_shutdown_system`). The result is then queued back to the model.
        """

        call_id = part.get_metadata('id')
        function_name = part.function_call.name
        arguments = part.function_call.args if hasattr(part.function_call, 'args') else {}

        # Update metrics for tool calls.
        self.metrics['tool_calls'][function_name] += 1

        # Route to appropriate handler
        response = None
        # Each `_handle_X` method corresponds to a tool declared in `LEONIDAS_TOOLS`.
        # They execute the logic associated with the tool and return a
        # `ProcessorPart` containing the function response, which is then
        # sent back to the model.
        # Reference: `.kiro/steering/gemini-function-scheduling-patterns.md`

        if function_name == 'think':
            response = await self._handle_think(call_id, arguments)
        elif function_name == 'change_state':
            response = await self._handle_change_state(call_id, arguments)
        elif function_name == 'get_context':
            response = await self._handle_get_context(call_id, arguments)
        elif function_name == 'get_time':
            response = await self._handle_get_time(call_id, arguments)
        elif function_name == 'shutdown_system':
            response = await self._handle_shutdown_system(call_id, arguments)
        elif function_name == 'wait_in_silence':
            response = await self._handle_wait_in_silence(call_id, arguments)
        else:
            response = await self._handle_unknown_function(call_id, function_name)

        # Queue the response back to the model.
        if response:
            await response_queue.put(response)

    async def _handle_think(self, call_id: str, args: dict) -> content_api.ProcessorPart:
        """Handles the `think` tool call.

        This tool is mandatory for the model to externalize its reasoning
        process. The analysis, reasoning, and plan are logged internally
        (structured JSON log) and printed to the console for transparency.
        The response to the model is `SILENT` as thinking is an internal process.
        """

        analysis = args.get('analysis', 'No analysis provided')
        reasoning = args.get('reasoning', 'No reasoning provided')
        next_action = args.get('plan', 'No action planned') # Alterado de 'next_action' para 'plan'

        # Prepare structured log data for the thinking process.
        log_data = {
            'tool_call': 'think',
            'analysis': analysis,
            'reasoning': reasoning,
            'plan': next_action,
        }
        # Log the thinking process with structured data for later analysis.
        logger.info("Model is thinking", extra={'extra_data': log_data})

        # Keep console logs for readability, showing the model's internal thought process.
        print("🧠 LEONIDAS THINKING:")
        print(f"   Analysis: {analysis}")
        print(f"   Reasoning: {reasoning}")
        print(f"   Next Action: {next_action}")

        # Store thinking in conversation history.
        # This allows the model to refer back to its own thought process
        # in subsequent turns via `get_context`.
        self.conversation_history.append({
            'timestamp': time.time(),
            'role': 'system',
            'text': f"THINKING - Analysis: {analysis} | Reasoning: {reasoning} | Next: {next_action}",
            'metadata': {'type': 'thinking', 'function': 'think'}
        })

        # Return a silent function response to the model.
        # `SILENT` scheduling means the model does not expect a verbal response
        # from the system for this tool call, as it's an internal action.
        return content_api.ProcessorPart.from_function_response(
            function_call_id=call_id,
            name='think',
            response={'status': 'thinking_complete'},
            scheduling=genai_types.FunctionResponseScheduling.SILENT
        )

    async def _handle_change_state(self, call_id: str, args: dict) -> content_api.ProcessorPart: # type: ignore
        """Handles the `change_state` tool call.

        This tool allows the model to control its own operational state
        (e.g., 'listening', 'analyzing'). This is a key aspect of the
        model's self-management and adaptability.
        """

        new_state = args.get('new_state', self.agent_state)
        reason = args.get('reason', 'No reason provided')

        old_state = self.agent_state
        self.agent_state = new_state
        self.state_reason = reason

        # Record state change for metrics and history.
        state_change = {
            'timestamp': time.time(),
            'from_state': old_state,
            'to_state': new_state,
            'reason': reason
        }
        self.metrics['state_changes'].append(state_change)
        # Log the state change for debugging and auditing.
        logger.info(f"STATE CHANGE: {old_state} → {new_state} ({reason})")

        return content_api.ProcessorPart.from_function_response(
            function_call_id=call_id,
            name='change_state',
            response={
                'status': 'success',
                'old_state': old_state,
                'new_state': new_state,
                'reason': reason
            },
            scheduling=genai_types.FunctionResponseScheduling.SILENT
        )

    async def _handle_get_context(self, call_id: str, args: dict) -> content_api.ProcessorPart: # type: ignore
        """Handles the `get_context` tool call.

        This tool allows the model to retrieve various types of contextual
        information, such as conversation history or system status, to inform
        its responses and maintain continuity.
        """

        context_type = args.get('context_type', 'conversation_history')

        context_data = {}

        if context_type == 'conversation_history':
            recent_history = list(self.conversation_history)[-10:]  # Last 10 entries
            # Summarize recent conversation entries to fit within token limits
            # and provide a concise overview to the model.
            context_data = {
                'recent_conversations': [
                    f"{entry['role']}: {entry['text'][:100]}..."
                    if len(entry['text']) > 100 else f"{entry['role']}: {entry['text']}"
                    for entry in recent_history
                ],
                'total_turns': self.metrics['conversation_turns']
            }

        elif context_type == 'system_status':
            context_data = {
                # Provide current operational state and tool usage statistics.
                # This helps the model understand its own environment.
                'current_state': self.agent_state,
                'state_reason': self.state_reason,
                'tool_usage': dict(self.metrics['tool_calls']),
                'uptime': time.time()  # Simplified uptime
            }

        elif context_type == 'user_context':
            # Extract recent user messages to infer user's current focus or
            # interaction patterns.
            user_messages = [
                entry for entry in self.conversation_history
                if entry['role'].lower() == 'user'
            ][-5:]  # Last 5 user messages

            context_data = {
                'recent_user_topics': [msg['text'][:50] + '...' for msg in user_messages],
                'user_interaction_frequency': len(user_messages)
            }

        elif context_type == 'recent_topics':
            # A simple summarization of recent text content to extract
            # overarching themes. In a more advanced system, this would use an LLM.
            all_text = ' '.join([
                entry['text'] for entry in list(self.conversation_history)[-20:]
                if entry.get('text')
            ])
            context_data = {
                'conversation_summary': all_text[:200] + '...' if len(all_text) > 200 else all_text
            }
        # Log the context request and the data provided to the model.
        logger.info(f"CONTEXT REQUEST ({context_type}): {context_data}")

        return content_api.ProcessorPart.from_function_response(
            function_call_id=call_id,
            name='get_context',
            response=context_data,
            scheduling=genai_types.FunctionResponseScheduling.SILENT
        )

    async def _handle_get_time(self, call_id: str, args: dict) -> content_api.ProcessorPart: # type: ignore
        """Handles the `get_time` tool call.

        Provides the current date and time in various formats as requested by the model.
        """

        format_type = args.get('format', 'datetime')
        now = datetime.datetime.now()

        time_data = {}

        if format_type == 'datetime':
            time_data = {
                'current_datetime': now.strftime('%Y-%m-%d %H:%M:%S'),
                'day_of_week': now.strftime('%A'),
                'timezone': 'Local'
            }
        elif format_type == 'date':
            time_data = {
                'current_date': now.strftime('%Y-%m-%d'),
                'day_of_week': now.strftime('%A')
            }
        elif format_type == 'time':
            time_data = {
                'current_time': now.strftime('%H:%M:%S')
            }
        elif format_type == 'timestamp':
            time_data = {
                'timestamp': int(now.timestamp()),
                'iso_format': now.isoformat()
            }
        # Log the time request and the data returned.
        logger.info(f"TIME REQUEST ({format_type}): {time_data}")

        return content_api.ProcessorPart.from_function_response(
            function_call_id=call_id,
            name='get_time',
            response=time_data,
            scheduling=genai_types.FunctionResponseScheduling.SILENT
        )

    async def _handle_shutdown_system(self, call_id: str, args: dict) -> content_api.ProcessorPart: # type: ignore
        """Handles the `shutdown_system` tool call.

        This critical tool allows the model to initiate a graceful shutdown
        of the Leonidas system, but only after explicit user confirmation.
        """

        confirmation = args.get('confirmation', False)
        reason = args.get('reason', 'No reason provided')

        # If the model calls `shutdown_system` without `confirmation=true`,
        # it's denied, and a warning is logged. This enforces the safety
        # mechanism for critical operations.
        if not confirmation:
            logger.warning(f"SHUTDOWN REQUEST DENIED: No confirmation provided")
            return content_api.ProcessorPart.from_function_response(
                function_call_id=call_id,
                name='shutdown_system',
                response={
                    'status': 'denied',
                    'message': 'Shutdown requer confirmação explícita'
                },
                scheduling=genai_types.FunctionResponseScheduling.WHEN_IDLE
            )

        # Log the successful shutdown request.
        logger.info(f"SYSTEM SHUTDOWN REQUESTED: {reason}")

        # Add shutdown event to conversation history for auditing.
        self.conversation_history.append({
            'timestamp': time.time(),
            'role': 'system',
            'text': f"SHUTDOWN INITIATED - Reason: {reason}",
            'metadata': {'type': 'shutdown', 'function': 'shutdown_system'}
        })

        # Set the internal flag that signals the main execution loop
        # to initiate the system shutdown.
        self.shutdown_requested = True
        self.shutdown_reason = reason

        return content_api.ProcessorPart.from_function_response(
            function_call_id=call_id,
            name='shutdown_system',
            response={
                'status': 'shutdown_initiated',
                'reason': reason,
                'message': 'Sistema será desligado em breve. Obrigado por usar o Leonidas!'
            },
            scheduling=genai_types.FunctionResponseScheduling.WHEN_IDLE
        )

    async def _handle_wait_in_silence(self, call_id: str, args: dict) -> content_api.ProcessorPart:
        """Handles the `wait_in_silence` tool call.

        This tool allows the model to signal that it should wait silently,
        without generating any verbal output, for a specified duration or
        until new user input is detected.
        """
        duration = args.get('duration_seconds', 0.0)
        reason = args.get('reason', 'Aguardando entrada do usuário ou processamento interno.')

        log_data = {
            'tool_call': 'wait_in_silence',
            'duration_seconds': duration,
            'reason': reason,
        }
        logger.info("Modelo está aguardando em silêncio", extra={'extra_data': log_data})
        print(f"🤫 LEONIDAS AGUARDANDO EM SILÊNCIO (por {duration:.1f}s, motivo: {reason})")

        # Store waiting event in conversation history.
        self.conversation_history.append({
            'timestamp': time.time(),
            'role': 'system',
            'text': f"AGUARDANDO EM SILÊNCIO - Duração: {duration}s, Motivo: {reason}",
            'metadata': {'type': 'waiting', 'function': 'wait_in_silence'}
        })

        # Return a silent function response to the model.
        # `SILENT` scheduling means the model does not expect a verbal response
        # from the system for this tool call, as it's an internal action.
        return content_api.ProcessorPart.from_function_response(
            function_call_id=call_id,
            name='wait_in_silence',
            response={'status': 'waiting_initiated', 'duration_seconds': duration, 'reason': reason},
            scheduling=genai_types.FunctionResponseScheduling.SILENT
        )

    async def _handle_unknown_function(self, call_id: str, function_name: str) -> content_api.ProcessorPart: # type: ignore
        """Handles calls to functions not explicitly defined in `LEONIDAS_TOOLS`.

        This serves as a fallback for unexpected model behavior or
        unimplemented tools, logging a warning for debugging.
        """

        logger.warning(f"UNKNOWN FUNCTION CALL: {function_name}")

        return content_api.ProcessorPart.from_function_response(
            function_call_id=call_id,
            name=function_name,
            response={'error': f'Unknown function: {function_name}'},
            scheduling=genai_types.FunctionResponseScheduling.SILENT
        )


# === FACTORY FUNCTION ===

# This factory function encapsulates the creation of the entire Leonidas agent
# pipeline. It promotes modularity and simplifies the main execution logic.
# It composes the three main architectural layers: Input, Orchestration, Output.
# Reference: `leonidas/README.md` (Architecture),
# `.kiro/steering/genai-processors-architecture.md` (Processor Composition).

def create_leonidas_agent_v2(api_key: str, pya: pyaudio.PyAudio = None, video_mode: Optional[str] = None) -> processor.Processor:
    """
    Create the complete Leonidas v2 agent with modular architecture.

    This factory function composes the three main processors:
    1. InputManager - Hardware input abstraction
    2. LeonidasOrchestrator - Core intelligence and tool execution
    3. OutputManager - Hardware output abstraction

    Args:
        api_key: Google AI API key for Gemini Live API
        pya: PyAudio instance for audio I/O
        video_mode: Optional video input mode ('camera' or 'screen'). If None,
          video is disabled.

    Returns:
        Complete Leonidas v2 processor pipeline
    """

    return (
        InputManager(pya, video_mode) +      # Layer 1: Input abstraction
        LeonidasOrchestrator(api_key) +      # Layer 2: Core intelligence
        OutputManager(pya)                   # Layer 3: Output abstraction
    )


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

    # Setup logging for the session, creating a unique log file.
    # This is the first step to ensure all subsequent operations are logged.
    log_file = setup_logging(debug)

    # Set an environment variable for video mode if screen capture is requested.
    # This might be used by underlying video capture libraries.
    if video_mode == 'screen':
        os.environ['VIDEO_MODE'] = 'screen'

    # Initialize PyAudio, which is required for microphone input and speaker output.
    pya = pyaudio.PyAudio()

    try:
        # Create the full Leonidas agent pipeline using the factory function.
        agent = create_leonidas_agent_v2(api_key, pya, video_mode)

        # Log startup messages to inform the user.
        logger.info("Leonidas v2 iniciando...")
        logger.info(f"Logs sendo salvos em: {log_file}")
        logger.info("Use Ctrl+C para encerrar")

        logger.info("Criando contexto do processador...")
        # `processor.context()` creates an `asyncio.TaskGroup` that manages
        # all background tasks spawned by processors within this context.
        # This ensures proper cancellation and error propagation across the pipeline.
        # Reference: `.kiro/steering/genai-processors-architecture.md` (Context and Task Management).
        async with processor.context():
            logger.info("Contexto criado, iniciando stream...")

            # The `agent` (which starts with `InputManager`) is called with
            # `endless_stream()`. This is a special stream that never ends,
            # keeping the input source processors (microphone, camera) alive
            # and continuously generating input parts.
            # Reference: `genai_processors/streams.py` (endless_stream).
            if video_mode:
                logger.info("Iniciando captura de áudio e vídeo...")
            else:
                logger.info("Iniciando captura de áudio...")

            part_count = 0
            try:
                async for part in agent(endless_stream()):
                    part_count += 1

                    # Check if the `shutdown_system` tool was called by the model.
                    # This involves inspecting the internal structure of the chained
                    # processor to access the `LeonidasOrchestrator` instance.
                    # This is a direct implementation of the "Encerramento Gracioso"
                    # requirement from `leonidas/REQUIREMENTS.md` (Section 4.2).
                    # Note: Accessing `_processors` directly is for internal control
                    # and relies on the known pipeline structure.
                    if hasattr(agent, '_processors') and len(agent._processors) >= 2:
                        # Get the orchestrator (middle processor in the chain)
                        orchestrator = agent._processors[1]
                        if hasattr(orchestrator, 'shutdown_requested') and orchestrator.shutdown_requested:
                            logger.info(f"SHUTDOWN SOLICITADO PELO MODELO: {orchestrator.shutdown_reason}")
                            print(f"\n🔴 Sistema sendo desligado: {orchestrator.shutdown_reason}")
                            break

                    # Skip logging for heartbeat parts (e.g., from video stream)
                    # to avoid excessive log spam, especially in debug mode.
                    if not part.metadata.get('heartbeat', False):
                        logger.debug(f"Parte recebida #{part_count}: {part.mimetype} - {part.role}")

                    # Print text output from the model to the console for immediate feedback.
                    if content_api.is_text(part.mimetype) and part.text and part.text.strip():
                        print(f"[{part.role.upper()}]: {part.text}")

                    # Log other important part types (non-heartbeat, first 20 parts)
                    # for initial debugging and understanding stream flow.
                    elif not part.metadata.get('heartbeat', False) and part_count <= 20:
                        logger.info(f"Parte #{part_count}: {part.mimetype} ({len(part.bytes) if part.bytes else 0} bytes)")

            except asyncio.CancelledError:
                # This exception is typically raised when the `TaskGroup` is cancelled,
                # for example, during a graceful shutdown.
                logger.info("Stream cancelado")

            logger.info(f"Stream finalizado após {part_count} partes")

    except KeyboardInterrupt:
        # Handle Ctrl+C for graceful user-initiated shutdown.
        logger.info("Leonidas v2 encerrado pelo usuário")
    except Exception as e:
        # Catch any unexpected exceptions and log them.
        logger.error(f"Erro no Leonidas v2: {e}")
        raise
    finally:
        # Ensure PyAudio resources are always released.
        pya.terminate()

        # Log session end.
        logger.info("=" * 60)
        logger.info("LEONIDAS V2 SESSION ENDED")
        logger.info(f"Log file saved: {log_file}")
        logger.info("=" * 60)


if __name__ == '__main__':
    # This block ensures that `main()` is called only when the script is
    # executed directly, not when imported as a module.
    # It parses command-line arguments and initiates the agent's execution.

    import argparse

    # Parse arguments
    parser = argparse.ArgumentParser(
        description='Leonidas v2 - Modular Conversational AI Agent',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                            # Run in audio-only mode
  %(prog)s --video-mode camera        # Use camera input
  %(prog)s --video-mode screen        # Use screen capture
  %(prog)s --video-mode camera --debug # Enable debug logging

Requirements:
  - Set GOOGLE_API_KEY environment variable
  - Install: pip install genai-processors pyaudio
  - Use headphones to prevent audio feedback
        """
    )

    parser.add_argument(
        '--video-mode',
        type=str,
        choices=['camera', 'screen'],
        default=None,
        help='Enable video input mode: camera for webcam, screen for screen capture. Disabled by default.'
    )

    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging for troubleshooting'
    )

    parser.add_argument(
        '--api-key',
        type=str,
        help='Google AI API key (overrides GOOGLE_API_KEY env var)'
    )

    args = parser.parse_args()

    # Configure logging
    if args.debug:
        logging.set_verbosity(logging.DEBUG)
        print("Debug logging enabled")
    else:
        logging.set_verbosity(logging.INFO)

    # Get API key
    api_key = args.api_key or os.environ.get('GOOGLE_API_KEY')
    if not api_key:
        print("Error: Google AI API key not found!")
        print("   Set GOOGLE_API_KEY environment variable or use --api-key")
        print("   Get your key at: https://aistudio.google.com/app/apikey")
        sys.exit(1)

    # Display startup information
    print("=" * 60)
    print("Leonidas v2 - Conversational AI Agent")
    print("=" * 60)
    print(f"Video Mode: {args.video_mode if args.video_mode else 'Disabled'}")
    print(f"Audio: Enabled (use headphones recommended)")
    print(f"Model: gemini-live-2.5-flash-preview")
    print(f"Language: Portuguese Brazilian")
    print(f"Architecture: Modular (InputManager → Orchestrator → OutputManager)")
    print("=" * 60)
    print("Tips:")
    print("   • Speak naturally - Leonidas will think before responding")
    print("   • The agent can change its own behavior based on context")
    print("   • Use Ctrl+C to exit gracefully")
    print("   • Check console for thinking process and state changes")
    print("=" * 60)

    try:
        # Run the agent
        print("Starting Leonidas v2...")
        asyncio.run(run_leonidas(api_key, args.video_mode, args.debug))

    except KeyboardInterrupt:
        print("\nLeonidas v2 shutdown requested by user")
        print("   Session ended gracefully")

    except ImportError as e:
        print(f"Import Error: {e}")
        print("   Install required packages: pip install genai-processors pyaudio")
        sys.exit(1)

    except Exception as e:
        print(f"Unexpected Error: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        else:
            print("   Use --debug flag for detailed error information")
        sys.exit(1)


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
