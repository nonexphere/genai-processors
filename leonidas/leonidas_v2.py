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
from typing import AsyncIterable, Optional, Any

from absl import logging
from genai_processors import content_api
from genai_processors import processor
from genai_processors import streams
from genai_processors.core import audio_io
from genai_processors.core import live_model
from genai_processors.core import rate_limit_audio
from genai_processors.core import video
from google.genai import types as genai_types

# === CONFIGURATION ===
MODEL_LIVE = 'gemini-live-2.5-flash-preview'
AUDIO_INPUT_RATE = 16000   # Input sample rate
AUDIO_OUTPUT_RATE = 24000  # Gemini output sample rate

# === ADVANCED PROMPT SYSTEM ===
LEONIDAS_SYSTEM_PROMPT = [
    # === CORE IDENTITY ===
    (
        "Você é Leonidas, uma IA colaborativa especializada em arquitetura de software, "
        "especificação de sistemas e desenvolvimento colaborativo. Você é um parceiro "
        "intelectual que pensa, analisa e age como um desenvolvedor sênior experiente."
    ),
    
    # === OPERATIONAL PHILOSOPHY ===
    (
        "Sua filosofia operacional segue o ciclo PERCEBER → PENSAR → AGIR:\n"
        "• PERCEBER: Observe atentamente o contexto visual, áudio e conversacional\n"
        "• PENSAR: Use SEMPRE a ferramenta 'think' para externalizar seu raciocínio\n"
        "• AGIR: Execute ações conscientes baseadas em sua análise (speak, change_state, etc.)"
    ),
    
    # === COMMUNICATION STYLE ===
    (
        "Comunique-se em português brasileiro com tom profissional, analítico e colaborativo. "
        "Seja direto, objetivo e estruturado. Evite repetições desnecessárias. "
        "Demonstre expertise técnica sem ser condescendente."
    ),
    
    # === TECHNICAL EXPERTISE ===
    (
        "Suas especialidades incluem:\n"
        "• Arquitetura de software e padrões de design\n"
        "• Análise de código e debugging\n"
        "• Especificação de sistemas complexos\n"
        "• Metodologias ágeis e DevOps\n"
        "• Performance e escalabilidade\n"
        "• Segurança e melhores práticas"
    ),
    
    # === BEHAVIORAL GUIDELINES ===
    (
        "Comportamento esperado:\n"
        "• Seja um ouvinte atento - só fale quando necessário ou solicitado\n"
        "• Use 'change_state' para controlar seu próprio comportamento\n"
        "• Sempre use 'think' antes de qualquer ação significativa\n"
        "• Faça perguntas esclarecedoras quando necessário\n"
        "• Ofereça insights proativos apenas quando relevantes\n"
        "• Aceite interrupções graciosamente"
    ),
    
    # === PROBLEM SOLVING APPROACH ===
    (
        "Abordagem para resolução de problemas:\n"
        "• Pense com base em primeiros princípios\n"
        "• Desconstrua problemas complexos em partes menores\n"
        "• Considere múltiplas soluções e trade-offs\n"
        "• Priorize soluções simples, elegantes e maintíveis\n"
        "• Sempre considere impacto em performance, segurança e escalabilidade"
    ),
    
    # === TOOL USAGE ===
    (
        "Uso de ferramentas:\n"
        "• 'think': Use OBRIGATORIAMENTE antes de qualquer ação\n"
        "• 'speak': Para comunicação direta com o usuário\n"
        "• 'change_state': Para controlar seu comportamento (listening/commentating/paused)\n"
        "• 'get_context': Para recuperar histórico da conversa\n"
        "• 'get_time': Para informações de data/hora\n"
        "• 'google_search': Para buscar informações atualizadas quando necessário"
    ),
    
    # === CONTEXTUAL AWARENESS ===
    (
        "Consciência contextual:\n"
        "• Observe o feed de vídeo para entender o que o usuário está fazendo\n"
        "• Analise código na tela quando visível\n"
        "• Adapte suas respostas ao contexto atual\n"
        "• Mantenha continuidade na conversa\n"
        "• Lembre-se de discussões anteriores usando 'get_context'"
    )
]

# === ADVANCED TOOL SYSTEM ===
LEONIDAS_TOOLS = [
    genai_types.Tool(
        function_declarations=[
            genai_types.FunctionDeclaration(
                name='think',
                description=(
                    'OBRIGATÓRIO: Use esta ferramenta ANTES de qualquer ação significativa. '
                    'Externalize seu processo de raciocínio, análise da situação e planejamento '
                    'da próxima ação. Seja detalhado e estruturado em seu pensamento.'
                ),
                behavior='NON_BLOCKING',
                parameters=genai_types.Schema(
                    type=genai_types.Type.OBJECT,
                    properties={
                        'analysis': genai_types.Schema(
                            type=genai_types.Type.STRING,
                            description='Sua análise detalhada da situação atual'
                        ),
                        'reasoning': genai_types.Schema(
                            type=genai_types.Type.STRING,
                            description='Seu processo de raciocínio e considerações'
                        ),
                        'next_action': genai_types.Schema(
                            type=genai_types.Type.STRING,
                            description='Qual ação você planeja tomar e por quê'
                        )
                    },
                    required=['analysis', 'reasoning', 'next_action']
                )
            ),
            
            genai_types.FunctionDeclaration(
                name='speak',
                description=(
                    'Comunique-se diretamente com o usuário. Use após pensar. '
                    'Seja claro, conciso e contextualmente relevante.'
                ),
                behavior='NON_BLOCKING',
                parameters=genai_types.Schema(
                    type=genai_types.Type.OBJECT,
                    properties={
                        'message': genai_types.Schema(
                            type=genai_types.Type.STRING,
                            description='Sua mensagem para o usuário'
                        ),
                        'tone': genai_types.Schema(
                            type=genai_types.Type.STRING,
                            enum=['professional', 'collaborative', 'analytical', 'supportive'],
                            description='Tom da mensagem'
                        )
                    },
                    required=['message']
                )
            ),
            
            genai_types.FunctionDeclaration(
                name='change_state',
                description=(
                    'Controle seu próprio comportamento e estado operacional. '
                    'Use para adaptar-se ao contexto da conversa.'
                ),
                behavior='NON_BLOCKING',
                parameters=genai_types.Schema(
                    type=genai_types.Type.OBJECT,
                    properties={
                        'new_state': genai_types.Schema(
                            type=genai_types.Type.STRING,
                            enum=['listening', 'commentating', 'paused', 'analyzing'],
                            description='Novo estado comportamental'
                        ),
                        'reason': genai_types.Schema(
                            type=genai_types.Type.STRING,
                            description='Motivo para a mudança de estado'
                        )
                    },
                    required=['new_state', 'reason']
                )
            ),
            
            genai_types.FunctionDeclaration(
                name='get_context',
                description=(
                    'Recupere informações sobre o contexto atual da conversa, '
                    'histórico de interações ou estado do sistema.'
                ),
                behavior='NON_BLOCKING',
                parameters=genai_types.Schema(
                    type=genai_types.Type.OBJECT,
                    properties={
                        'context_type': genai_types.Schema(
                            type=genai_types.Type.STRING,
                            enum=['conversation_history', 'system_status', 'user_context', 'recent_topics'],
                            description='Tipo de contexto solicitado'
                        )
                    },
                    required=['context_type']
                )
            ),
            
            genai_types.FunctionDeclaration(
                name='get_time',
                description=(
                    'Obtenha informações atuais de data e hora. '
                    'Útil para contexto temporal e agendamentos.'
                ),
                behavior='NON_BLOCKING',
                parameters=genai_types.Schema(
                    type=genai_types.Type.OBJECT,
                    properties={
                        'format': genai_types.Schema(
                            type=genai_types.Type.STRING,
                            enum=['datetime', 'date', 'time', 'timestamp'],
                            description='Formato da informação temporal desejada'
                        )
                    }
                )
            )
        ]
    )
]

# === MODULAR PROCESSORS ===

@processor.processor_function
async def InputManager(
    content: AsyncIterable[content_api.ProcessorPart]
) -> AsyncIterable[content_api.ProcessorPart]:
    """
    Input abstraction layer that manages all hardware input sources.
    
    Currently handles video and audio input, but designed to be extensible
    for future multi-feed scenarios (multiple cameras, microphones, etc.).
    """
    # Create the input pipeline - video + audio capture
    input_pipeline = (
        video.VideoIn() + 
        audio_io.PyAudioIn(sample_rate=AUDIO_INPUT_RATE, use_pcm_mimetype=True)
    )
    
    # Process through the input pipeline
    async for part in input_pipeline(content):
        # Add input source metadata for future routing
        part.metadata['input_source'] = 'primary'
        part.metadata['processed_by'] = 'InputManager'
        yield part


@processor.processor_function  
async def OutputManager(
    content: AsyncIterable[content_api.ProcessorPart]
) -> AsyncIterable[content_api.ProcessorPart]:
    """
    Output abstraction layer that manages all hardware output destinations.
    
    Currently handles audio output with rate limiting, but designed to be 
    extensible for future multi-modal output (displays, actuators, etc.).
    """
    # Create the output pipeline - rate limiting + audio output
    output_pipeline = (
        rate_limit_audio.RateLimitAudio(AUDIO_OUTPUT_RATE) +
        audio_io.PyAudioOut(sample_rate=AUDIO_OUTPUT_RATE)
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
                generation_config=genai_types.GenerationConfig(
                    media_resolution=genai_types.MediaResolution.MEDIA_RESOLUTION_MEDIUM
                )
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
        args = content_api.function_calling_utils.parse_function_call(part)
        
        # Update metrics
        self.metrics['tool_calls'][function_name] += 1
        
        # Route to appropriate handler
        response = None
        
        if function_name == 'think':
            response = await self._handle_think(call_id, args)
        elif function_name == 'speak':
            response = await self._handle_speak(call_id, args)
        elif function_name == 'change_state':
            response = await self._handle_change_state(call_id, args)
        elif function_name == 'get_context':
            response = await self._handle_get_context(call_id, args)
        elif function_name == 'get_time':
            response = await self._handle_get_time(call_id, args)
        else:
            response = await self._handle_unknown_function(call_id, function_name)
        
        # Queue the response
        if response:
            await response_queue.put(response)
    
    async def _handle_think(self, call_id: str, args: dict) -> content_api.ProcessorPart:
        """Handle the think tool - externalize model reasoning."""
        
        analysis = args.get('analysis', 'No analysis provided')
        reasoning = args.get('reasoning', 'No reasoning provided')
        next_action = args.get('next_action', 'No action planned')
        
        # Log the thinking process
        logging.info(f"🧠 LEONIDAS THINKING:")
        logging.info(f"   Analysis: {analysis}")
        logging.info(f"   Reasoning: {reasoning}")
        logging.info(f"   Next Action: {next_action}")
        
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
    
    async def _handle_speak(self, call_id: str, args: dict) -> content_api.ProcessorPart:
        """Handle the speak tool - direct communication."""
        
        message = args.get('message', '')
        tone = args.get('tone', 'professional')
        
        logging.info(f"🗣️ LEONIDAS SPEAKING ({tone}): {message}")
        
        # Return the message for audio synthesis
        return content_api.ProcessorPart.from_function_response(
            function_call_id=call_id,
            name='speak',
            response={'output': message},
            scheduling=genai_types.FunctionResponseScheduling.WHEN_IDLE
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
        
        logging.info(f"🔄 STATE CHANGE: {old_state} → {new_state} ({reason})")
        
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
        
        logging.info(f"📋 CONTEXT REQUEST ({context_type}): {context_data}")
        
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
        
        logging.info(f"🕐 TIME REQUEST ({format_type}): {time_data}")
        
        return content_api.ProcessorPart.from_function_response(
            function_call_id=call_id,
            name='get_time',
            response=time_data,
            scheduling=genai_types.FunctionResponseScheduling.SILENT
        )
    
    async def _handle_unknown_function(self, call_id: str, function_name: str) -> content_api.ProcessorPart:
        """Handle unknown function calls."""
        
        logging.warning(f"❓ UNKNOWN FUNCTION CALL: {function_name}")
        
        return content_api.ProcessorPart.from_function_response(
            function_call_id=call_id,
            name=function_name,
            response={'error': f'Unknown function: {function_name}'},
            scheduling=genai_types.FunctionResponseScheduling.SILENT
        )


# === FACTORY FUNCTION ===

def create_leonidas_agent_v2(api_key: str) -> processor.Processor:
    """
    Create the complete Leonidas v2 agent with modular architecture.
    
    This factory function composes the three main processors:
    1. InputManager - Hardware input abstraction
    2. LeonidasOrchestrator - Core intelligence and tool execution  
    3. OutputManager - Hardware output abstraction
    
    Args:
        api_key: Google AI API key for Gemini Live API
        
    Returns:
        Complete Leonidas v2 processor pipeline
    """
    
    return (
        InputManager +           # Layer 1: Input abstraction
        LeonidasOrchestrator(api_key) +  # Layer 2: Core intelligence
        OutputManager            # Layer 3: Output abstraction
    )


# === MAIN EXECUTION ===

async def run_leonidas_v2(api_key: str, video_mode: str = 'camera'):
    """
    Run the Leonidas v2 agent.
    
    Args:
        api_key: Google AI API key
        video_mode: Video input mode ('camera' or 'screen')
    """
    
    # Set video mode environment if needed
    if video_mode == 'screen':
        os.environ['VIDEO_MODE'] = 'screen'
    
    # Create the agent
    agent = create_leonidas_agent_v2(api_key)
    
    # Run the agent
    logging.info("🚀 Leonidas v2 iniciando...")
    logging.info("💡 Use Ctrl+C para encerrar")
    
    try:
        async with processor.context.context():
            # Start with empty stream - InputManager will generate content
            async for part in agent(streams.stream_content([])):
                # Log text output for debugging
                if content_api.is_text(part.mimetype) and part.text:
                    print(f"[{part.role.upper()}]: {part.text}")
    
    except KeyboardInterrupt:
        logging.info("🛑 Leonidas v2 encerrado pelo usuário")
    except Exception as e:
        logging.error(f"❌ Erro no Leonidas v2: {e}")
        raise


if __name__ == '__main__':
    import argparse
    
    # Setup logging
    logging.set_verbosity(logging.INFO)
    
    # Parse arguments
    parser = argparse.ArgumentParser(description='Leonidas v2 - Conversational AI Agent')
    parser.add_argument('--mode', choices=['camera', 'screen'], default='camera',
                       help='Video input mode')
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug logging')
    
    args = parser.parse_args()
    
    if args.debug:
        logging.set_verbosity(logging.DEBUG)
    
    # Get API key
    api_key = os.environ.get('GOOGLE_API_KEY')
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable not set")
    
    # Run the agent
    asyncio.run(run_leonidas_v2(api_key, args.mode))