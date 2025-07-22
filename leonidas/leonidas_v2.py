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

"""Leonidas v2 - Modular Conversational AI Agent

A complete refactoring of the Leonidas agent into a modular, fluid conversational
system that thinks, acts, and collaborates like a human partner.

Architecture:
  InputManager → LeonidasOrchestrator → OutputManager
  
The system uses genai-processors for modular composition and gives the Gemini
model full control over its behavior through an advanced tool system.
"""

import asyncio
import collections
import dataclasses
import datetime
import os
import time
from datetime import datetime as dt
from pathlib import Path
from typing import AsyncIterable, Optional, Any

import pyaudio
from absl import logging
import logging as std_logging
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

logger = std_logging.getLogger(__name__) # Adicionado

# === LOGGING CONFIGURATION ===
def setup_logging(debug: bool = False) -> str:
    """
    Configure logging to save to unique files in logs/ directory.
    
    Args:
        debug: Enable debug level logging
        
    Returns:
        Path to the log file created
    """
    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Generate unique log filename with timestamp
    timestamp = dt.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"leonidas_v2_{timestamp}.log"
    log_path = logs_dir / log_filename
    
    # Configure logging level
    log_level = logging.DEBUG if debug else logging.INFO
    
    # Setup file handler
    import json # Adicionado
    
    # Adicionado: Classe JSONFormatter
    class JSONFormatter(std_logging.Formatter):
        def format(self, record):
            log_record = {
                "timestamp": self.formatTime(record, self.datefmt),
                "level": record.levelname,
                "name": record.name,
                "message": record.getMessage(),
            }
            if hasattr(record, 'extra_data'):
                log_record.update(record.extra_data)
            return json.dumps(log_record)

    # Create formatter
    formatter = std_logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Setup file handler
    file_handler = std_logging.FileHandler(log_path, encoding='utf-8')
    file_handler.setLevel(log_level)
    file_handler.setFormatter(JSONFormatter()) # Alterado para usar JSONFormatter
    
    # Setup console handler
    console_handler = std_logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = std_logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Add handlers
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Also configure absl logging
    logging.set_verbosity(log_level)
    
    # Adicionado: Controle de verbosidade de bibliotecas de terceiros
    if debug:
        std_logging.getLogger('websockets.client').setLevel(std_logging.INFO)
        std_logging.getLogger('google_genai').setLevel(std_logging.INFO)
    else:
        std_logging.getLogger('websockets.client').setLevel(std_logging.WARNING)
        std_logging.getLogger('google_genai').setLevel(std_logging.WARNING)

    # Log session start information
    logger.info("=" * 60) # Alterado para logger.info
    logger.info("LEONIDAS V2 SESSION STARTED") # Alterado para logger.info
    logger.info("=" * 60) # Alterado para logger.info
    logger.info(f"Log file: {log_path}") # Alterado para logger.info
    logger.info(f"Timestamp: {dt.now().strftime('%Y-%m-%d %H:%M:%S')}") # Alterado para logger.info
    logger.info(f"Debug mode: {debug}") # Alterado para logger.info
    logger.info(f"Model: {MODEL_LIVE}") # Alterado para logger.info
    logger.info("=" * 60) # Alterado para logger.info
    
    return str(log_path)

# === ADVANCED PROMPT SYSTEM ===
LEONIDAS_SYSTEM_PROMPT = [
    # === 1. PRIME DIRECTIVE ===
    (
        "Sua diretiva principal é maximizar o throughput intelectual e produtivo "
        "da equipe humano-IA. Você é Leonidas, um parceiro de engenharia sênior, "
        "não um assistente. Sua função é pensar junto, analisar criticamente e "
        "acelerar a resolução de problemas complexos de software."
    ),

    # === 2. COGNITIVE ARCHITECTURE: O CICLO P-P-A ===
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
    (
        "Seu comportamento é guiado por estes mandatos:\n"
        "•   **Listen-First Default:** Seu estado padrão é 'listening'. Você não "
        "fala a menos que seja interpelado, interrompido por um insight "
        "crítico seu, ou para executar uma ação planejada.\n"
        "•   **Proatividade Criteriosa:** Intervenções proativas são bem-vindas, "
        "mas devem ser de alto valor (identificar um bug, sugerir uma "
        "melhoria arquitetural significativa). Justifique a interrupção no seu "
        "pensamento.\n"
        "•   **Hierarquia de Contexto:** Priorize a informação na seguinte ordem: "
        "1. Comando direto do usuário. 2. Contexto visual imediato (o que está "
        "na tela). 3. Histórico recente da conversa. 4. Conhecimento geral."
    ),

    # === 5. TOOL PROTOCOL & USAGE (DETALHADO) ===
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
        "chame a ferramenta com `confirmation=true`."
    ),
]

# === ADVANCED TOOL SYSTEM ===
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
            )
        ]
    )
]

# === MODULAR PROCESSORS ===

class InputManager(processor.Processor):
    """
    Input abstraction layer that manages all hardware input sources.
    
    Handles audio input, and optionally video, making it extensible for
    future multi-feed scenarios (multiple cameras, microphones, etc.).
    """
    def __init__(self, pya: pyaudio.PyAudio, video_mode: Optional[str] = None):
        input_processors = [
            audio_io.PyAudioIn(pya, rate=AUDIO_INPUT_RATE, use_pcm_mimetype=True)
        ]
        if video_mode:
            input_processors.append(
                video.VideoIn(video_mode=video.VideoMode(video_mode))
            )
        
        if len(input_processors) > 1:
            # Use parallel_concat for simultaneous audio/video capture
            self.input_pipeline = processor.parallel_concat(input_processors)
        else:
            self.input_pipeline = input_processors[0]

    async def call(
        self, content: AsyncIterable[content_api.ProcessorPart]
    ) -> AsyncIterable[content_api.ProcessorPart]:
        # Process the input stream through the defined pipeline.
        # For source processors, the initial `content` stream keeps them alive.
        async for part in self.input_pipeline(content):
            # Add input source metadata for future routing
            part.metadata['input_source'] = 'primary'
            part.metadata['processed_by'] = 'InputManager'
            yield part


class OutputManager(processor.Processor):
    """
    Output abstraction layer that manages all hardware output destinations.
    
    Currently handles audio output with rate limiting, but designed to be 
    extensible for future multi-modal output (displays, actuators, etc.).
    """
    def __init__(self, pya: pyaudio.PyAudio):
        self._pya = pya

    async def call(
        self, content: AsyncIterable[content_api.ProcessorPart]
    ) -> AsyncIterable[content_api.ProcessorPart]:
        # Create the output pipeline - rate limiting + audio output
        output_pipeline = (
            rate_limit_audio.RateLimitAudio(AUDIO_OUTPUT_RATE) +
            audio_io.PyAudioOut(self._pya, rate=AUDIO_OUTPUT_RATE)
        )
        
        # Process through the output pipeline
        async for part in output_pipeline(content):
            # Add output destination metadata
            part.metadata['output_destination'] = 'primary_audio'
            part.metadata['processed_by'] = 'OutputManager'
            yield part


class LeonidasOrchestrator(processor.Processor):
    """
    The core intelligence of Leonidas v2.
    
    This processor manages the Gemini Live API connection and executes the
    advanced tool system. Unlike the previous monolithic approach, this
    orchestrator is simple and focused - it lets the model control its own
    behavior through tools.
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        
        # Agent state (controlled by the model via change_state tool)
        self.agent_state = 'listening'
        self.state_reason = 'Initial state'
        
        # Conversation memory
        self.conversation_history = collections.deque(maxlen=100)
        self.context_summary = ""
        
        # Performance metrics
        self.metrics = {
            'tool_calls': collections.defaultdict(int),
            'state_changes': [],
            'conversation_turns': 0
        }
        
        # Shutdown control
        self.shutdown_requested = False
        self.shutdown_reason = ""
        
        # Configure the Live API processor
        self.live_processor = live_model.LiveProcessor(
            api_key=api_key,
            model_name=MODEL_LIVE,
            realtime_config=genai_types.LiveConnectConfig(
                tools=LEONIDAS_TOOLS,
                system_instruction=LEONIDAS_SYSTEM_PROMPT,
                output_audio_transcription={},
                realtime_input_config=genai_types.RealtimeInputConfig(
                    turn_coverage='TURN_INCLUDES_ALL_INPUT'
                ),
                response_modalities=['AUDIO'],
                speech_config={
                    'language_code': 'pt-BR',
                    'voice_config': {
                        'prebuilt_voice_config': {
                            'voice_name': 'Kore'
                        }
                    }
                },
                # Use direct fields instead of generation_config (deprecated)
                media_resolution=genai_types.MediaResolution.MEDIA_RESOLUTION_MEDIUM,
                max_output_tokens=500
            ),
            http_options=genai_types.HttpOptions(api_version='v1alpha')
        )
    
    async def call(
        self, 
        content: AsyncIterable[content_api.ProcessorPart]
    ) -> AsyncIterable[content_api.ProcessorPart]:
        """Main orchestration loop."""
        
        # Create input queue for tool responses
        tool_response_queue = asyncio.Queue()
        
        # Merge content stream with tool responses
        merged_input = streams.merge([
            content, 
            streams.dequeue(tool_response_queue)
        ], stop_on_first=True)
        
        # Process through Live API
        async for part in self.live_processor(merged_input):
            
            # Handle conversation history
            if content_api.is_text(part.mimetype) and part.text:
                self._add_to_conversation_history(part)
            
            # Handle function calls
            if part.function_call:
                await self._handle_function_call(part, tool_response_queue)
            
            # Yield all parts
            yield part
    
    def _add_to_conversation_history(self, part: content_api.ProcessorPart):
        """Add part to conversation history."""
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
    ):
        """Handle function calls from the model."""
        
        call_id = part.get_metadata('id')
        function_name = part.function_call.name
        args = part.function_call.args
        
        # Update metrics
        self.metrics['tool_calls'][function_name] += 1
        
        # Route to appropriate handler
        response = None
        
        if function_name == 'think':
            response = await self._handle_think(call_id, args)
        elif function_name == 'change_state':
            response = await self._handle_change_state(call_id, args)
        elif function_name == 'get_context':
            response = await self._handle_get_context(call_id, args)
        elif function_name == 'get_time':
            response = await self._handle_get_time(call_id, args)
        elif function_name == 'shutdown_system':
            response = await self._handle_shutdown_system(call_id, args)
        else:
            response = await self._handle_unknown_function(call_id, function_name)
        
        # Queue the response
        if response:
            await response_queue.put(response)
    
    async def _handle_think(self, call_id: str, args: dict) -> content_api.ProcessorPart:
        """Handle the think tool - externalize model reasoning."""
        
        analysis = args.get('analysis', 'No analysis provided')
        reasoning = args.get('reasoning', 'No reasoning provided')
        next_action = args.get('plan', 'No action planned') # Alterado de 'next_action' para 'plan'
        
        # Log the thinking process as structured data
        log_data = {
            'tool_call': 'think',
            'analysis': analysis,
            'reasoning': reasoning,
            'plan': next_action,
        }
        logger.info("Model is thinking", extra={'extra_data': log_data}) # Alterado para logger.info com extra
        
        # Keep console logs for readability
        print("🧠 LEONIDAS THINKING:")
        print(f"   Analysis: {analysis}")
        print(f"   Reasoning: {reasoning}")
        print(f"   Next Action: {next_action}")
        
        # Store thinking in conversation history
        self.conversation_history.append({
            'timestamp': time.time(),
            'role': 'system',
            'text': f"THINKING - Analysis: {analysis} | Reasoning: {reasoning} | Next: {next_action}",
            'metadata': {'type': 'thinking', 'function': 'think'}
        })
        
        # Return silent response (thinking is internal)
        return content_api.ProcessorPart.from_function_response(
            function_call_id=call_id,
            name='think',
            response={'status': 'thinking_complete'},
            scheduling=genai_types.FunctionResponseScheduling.SILENT
        )
    
    async def _handle_change_state(self, call_id: str, args: dict) -> content_api.ProcessorPart:
        """Handle state changes - model controls its own behavior."""
        
        new_state = args.get('new_state', self.agent_state)
        reason = args.get('reason', 'No reason provided')
        
        old_state = self.agent_state
        self.agent_state = new_state
        self.state_reason = reason
        
        # Record state change
        state_change = {
            'timestamp': time.time(),
            'from_state': old_state,
            'to_state': new_state,
            'reason': reason
        }
        self.metrics['state_changes'].append(state_change)
        
        logger.info(f"STATE CHANGE: {old_state} → {new_state} ({reason})") # Alterado para logger.info
        
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
    
    async def _handle_get_context(self, call_id: str, args: dict) -> content_api.ProcessorPart:
        """Handle context retrieval requests."""
        
        context_type = args.get('context_type', 'conversation_history')
        
        context_data = {}
        
        if context_type == 'conversation_history':
            recent_history = list(self.conversation_history)[-10:]  # Last 10 entries
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
                'current_state': self.agent_state,
                'state_reason': self.state_reason,
                'tool_usage': dict(self.metrics['tool_calls']),
                'uptime': time.time()  # Simplified uptime
            }
        
        elif context_type == 'user_context':
            # Analyze recent user interactions
            user_messages = [
                entry for entry in self.conversation_history 
                if entry['role'].lower() == 'user'
            ][-5:]  # Last 5 user messages
            
            context_data = {
                'recent_user_topics': [msg['text'][:50] + '...' for msg in user_messages],
                'user_interaction_frequency': len(user_messages)
            }
        
        elif context_type == 'recent_topics':
            # Extract topics from recent conversation
            all_text = ' '.join([
                entry['text'] for entry in list(self.conversation_history)[-20:]
                if entry.get('text')
            ])
            context_data = {
                'conversation_summary': all_text[:200] + '...' if len(all_text) > 200 else all_text
            }
        
        logger.info(f"CONTEXT REQUEST ({context_type}): {context_data}") # Alterado para logger.info
        
        return content_api.ProcessorPart.from_function_response(
            function_call_id=call_id,
            name='get_context',
            response=context_data,
            scheduling=genai_types.FunctionResponseScheduling.SILENT
        )
    
    async def _handle_get_time(self, call_id: str, args: dict) -> content_api.ProcessorPart:
        """Handle time/date requests."""
        
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
        
        logger.info(f"TIME REQUEST ({format_type}): {time_data}") # Alterado para logger.info
        
        return content_api.ProcessorPart.from_function_response(
            function_call_id=call_id,
            name='get_time',
            response=time_data,
            scheduling=genai_types.FunctionResponseScheduling.SILENT
        )
    
    async def _handle_shutdown_system(self, call_id: str, args: dict) -> content_api.ProcessorPart:
        """Handle system shutdown requests."""
        
        confirmation = args.get('confirmation', False)
        reason = args.get('reason', 'No reason provided')
        
        if not confirmation:
            logger.warning(f"SHUTDOWN REQUEST DENIED: No confirmation provided") # Alterado para logger.warning
            return content_api.ProcessorPart.from_function_response(
                function_call_id=call_id,
                name='shutdown_system',
                response={
                    'status': 'denied',
                    'message': 'Shutdown requer confirmação explícita'
                },
                scheduling=genai_types.FunctionResponseScheduling.WHEN_IDLE
            )
        
        # Log shutdown request
        logger.info(f"SYSTEM SHUTDOWN REQUESTED: {reason}") # Alterado para logger.info
        
        # Add shutdown to conversation history
        self.conversation_history.append({
            'timestamp': time.time(),
            'role': 'system',
            'text': f"SHUTDOWN INITIATED - Reason: {reason}",
            'metadata': {'type': 'shutdown', 'function': 'shutdown_system'}
        })
        
        # Set shutdown flag (will be checked by main loop)
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
    
    async def _handle_unknown_function(self, call_id: str, function_name: str) -> content_api.ProcessorPart:
        """Handle unknown function calls."""
        
        logger.warning(f"UNKNOWN FUNCTION CALL: {function_name}") # Alterado para logger.warning
        
        return content_api.ProcessorPart.from_function_response(
            function_call_id=call_id,
            name=function_name,
            response={'error': f'Unknown function: {function_name}'},
            scheduling=genai_types.FunctionResponseScheduling.SILENT
        )


# === FACTORY FUNCTION ===

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

async def run_leonidas_v2(api_key: str, video_mode: Optional[str] = None, debug: bool = False):
    """
    Run the Leonidas v2 agent.
    
    Args:
        api_key: Google AI API key
        video_mode: Optional video input mode ('camera' or 'screen').
        debug: Enable debug logging
    """
    
    # Setup logging with automatic file creation
    log_file = setup_logging(debug)
    
    # Set video mode environment if needed
    if video_mode == 'screen':
        os.environ['VIDEO_MODE'] = 'screen'
    
    # Create PyAudio instance
    pya = pyaudio.PyAudio()
    
    try:
        # Create the agent
        agent = create_leonidas_agent_v2(api_key, pya, video_mode)
        
        # Run the agent
        logger.info("Leonidas v2 iniciando...") # Alterado para logger.info
        logger.info(f"Logs sendo salvos em: {log_file}") # Alterado para logger.info
        logger.info("Use Ctrl+C para encerrar") # Alterado para logger.info
        
        logger.info("Criando contexto do processador...") # Alterado para logger.info
        async with processor.context():
            logger.info("Contexto criado, iniciando stream...") # Alterado para logger.info
            
            # Start the input stream directly - let InputManager handle content generation
            if video_mode:
                logger.info("Iniciando captura de áudio e vídeo...") # Alterado para logger.info
            else:
                logger.info("Iniciando captura de áudio...") # Alterado para logger.info
            
            part_count = 0
            try:
                # Use endless_stream() to keep the source processors alive
                async for part in agent(endless_stream()):
                    part_count += 1
                    
                    # Check for shutdown request from the orchestrator
                    if hasattr(agent, '_processors') and len(agent._processors) >= 2:
                        # Get the orchestrator (middle processor in the chain)
                        orchestrator = agent._processors[1]
                        if hasattr(orchestrator, 'shutdown_requested') and orchestrator.shutdown_requested:
                            logger.info(f"SHUTDOWN SOLICITADO PELO MODELO: {orchestrator.shutdown_reason}") # Alterado para logger.info
                            print(f"\n🔴 Sistema sendo desligado: {orchestrator.shutdown_reason}")
                            break
                    
                    # Skip heartbeat logging to avoid spam
                    if not part.metadata.get('heartbeat', False):
                        logger.debug(f"Parte recebida #{part_count}: {part.mimetype} - {part.role}") # Alterado para logger.debug
                    
                    # Log text output for debugging
                    if content_api.is_text(part.mimetype) and part.text and part.text.strip():
                        print(f"[{part.role.upper()}]: {part.text}")
                    
                    # Log other important types
                    elif not part.metadata.get('heartbeat', False) and part_count <= 20:
                        logger.info(f"Parte #{part_count}: {part.mimetype} ({len(part.bytes) if part.bytes else 0} bytes)") # Alterado para logger.info
                        
            except asyncio.CancelledError:
                logger.info("Stream cancelado") # Alterado para logger.info
            
            logger.info(f"Stream finalizado após {part_count} partes") # Alterado para logger.info
    
    except KeyboardInterrupt:
        logger.info("Leonidas v2 encerrado pelo usuário") # Alterado para logger.info
    except Exception as e:
        logger.error(f"Erro no Leonidas v2: {e}") # Alterado para logger.error
        raise
    finally:
        # Cleanup PyAudio
        pya.terminate()
        
        # Log session end
        logger.info("=" * 60) # Alterado para logger.info
        logger.info("LEONIDAS V2 SESSION ENDED") # Alterado para logger.info
        logger.info(f"Log file saved: {log_file}") # Alterado para logger.info
        logger.info("=" * 60) # Alterado para logger.info




if __name__ == '__main__':
    import argparse
    
    # Parse arguments
    parser = argparse.ArgumentParser(description='Leonidas v2 - Conversational AI Agent')
    parser.add_argument('--mode', choices=['camera', 'screen'], default='camera',
                       help='Video input mode')
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug logging')
    
    args = parser.parse_args()
    
    # Get API key
    api_key = os.environ.get('GOOGLE_API_KEY')
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable not set")
    
    # Run the agent with logging setup
    try:
        asyncio.run(run_leonidas_v2(api_key, args.mode, args.debug))
    except Exception as e:
        logging.error(f"Erro no Leonidas v2: {e}")
        raise
