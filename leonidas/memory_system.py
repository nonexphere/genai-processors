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
"""Sistema de Memória e Contexto Avançado para Leonidas.

Este módulo implementa um sistema completo de memória persistente usando
padrões genai-processors. Inclui processadores para:
- Histórico de sessões em tempo real
- Geração inteligente de resumos
- Carregamento contextual na inicialização
- Memória persistente entre sessões

Arquitetura baseada em streams assíncronos e composição de processadores.
"""

import asyncio
import collections
import functools
import json
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import AsyncIterable, Optional, Any, Dict, List

from absl import logging
import logging as std_logging

# Imports genai-processors
from genai_processors import content_api
from genai_processors import processor
from genai_processors import streams
from genai_processors import cache
from genai_processors.core import genai_model
from google.genai import types as genai_types

# Logger estruturado
logger = std_logging.getLogger(__name__)


class MemoryInputProcessor(processor.Processor):
    """Processa entrada de dados para o sistema de memória.
    
    Este processador enriquece o stream de entrada com metadata de memória,
    incluindo timestamps, session_id e informações de contexto.
    """
    
    def __init__(self, 
                 summary_file: str = "summary.txt",
                 history_dir: str = "history"):
        self.summary_file = Path(summary_file)
        self.history_dir = Path(history_dir)
        self.session_id = self._generate_session_id()
        
        # Garante que diretórios existem
        self.history_dir.mkdir(exist_ok=True)
        
    def _generate_session_id(self) -> str:
        """Gera ID único para a sessão atual."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"leonidas_{timestamp}"
    
    async def call(self, content: AsyncIterable[content_api.ProcessorPart]) -> AsyncIterable[content_api.ProcessorPartTypes]:
        """Processa stream de entrada adicionando contexto de memória."""
        async for part in content:
            # Adiciona metadata de memória
            part.metadata['memory_timestamp'] = time.time()
            part.metadata['session_id'] = self.session_id
            part.metadata['memory_processed'] = True
            
            # Emite parte original com metadata enriquecida
            yield part
            
            # Emite debug info se necessário
            if part.role in ['user', 'assistant']:
                yield processor.debug(f"Memory input processed: {part.role} - {len(part.text or '')} chars")
    
    @functools.cached_property
    def key_prefix(self) -> str:
        return f"{self.__class__.__qualname__}:{self.summary_file}"


class SessionHistoryProcessor(processor.PartProcessor):
    """Processa e armazena histórico da sessão em tempo real.
    
    Este processador mantém um log estruturado de todas as interações
    da sessão atual, persistindo periodicamente em arquivo JSON.
    """
    
    def __init__(self, history_dir: str = "history"):
        self.history_dir = Path(history_dir)
        self.history_dir.mkdir(exist_ok=True)
        
        self.current_session_file = None
        self.session_data = collections.deque(maxlen=10000)
        self.session_start_time = time.time()
        self.last_persist_time = time.time()
        self.persist_interval = 30.0  # Persiste a cada 30 segundos
        
    def match(self, part: content_api.ProcessorPart) -> bool:
        """Processa todas as partes que têm conteúdo conversacional."""
        return (content_api.is_text(part.mimetype) and 
                part.role in ['user', 'assistant', 'system'] and
                part.metadata.get('memory_processed', False))
    
    async def call(self, part: content_api.ProcessorPart) -> AsyncIterable[content_api.ProcessorPartTypes]:
        """Registra interação no histórico e passa adiante."""
        if self.match(part):
            # Registra no histórico da sessão
            await self._log_interaction(part)
            
            # Persiste periodicamente
            current_time = time.time()
            if current_time - self.last_persist_time > self.persist_interval:
                await self._persist_session_data()
                self.last_persist_time = current_time
            
            # Emite status de logging
            yield processor.status(f"Logged {part.role} interaction ({len(self.session_data)} total)")
        
        # Sempre passa a parte adiante
        yield part
    
    async def _log_interaction(self, part: content_api.ProcessorPart):
        """Registra interação no histórico atual."""
        interaction_data = {
            'timestamp': part.metadata.get('memory_timestamp', time.time()),
            'role': part.role,
            'content': part.text or '',
            'metadata': {
                k: v for k, v in part.metadata.items() 
                if k not in ['memory_timestamp', 'session_id']  # Remove metadata interno
            }
        }
        
        self.session_data.append(interaction_data)
        
        logger.info("Session interaction logged", extra={
            'extra_data': {
                'session_id': part.metadata.get('session_id'),
                'role': part.role,
                'content_length': len(part.text or ''),
                'total_interactions': len(self.session_data)
            }
        })
    
    async def _persist_session_data(self):
        """Persiste dados da sessão em arquivo JSON."""
        if not self.session_data:
            return
            
        try:
            # Cria arquivo de sessão se não existe
            if self.current_session_file is None:
                session_id = list(self.session_data)[0].get('metadata', {}).get('session_id', 'unknown')
                if session_id == 'unknown':
                    session_id = f"session_{int(time.time())}"
                    
                self.current_session_file = self.history_dir / f"{session_id}.json"
            
            # Prepara dados para persistência
            session_summary = {
                'session_id': self.current_session_file.stem,
                'start_time': datetime.fromtimestamp(self.session_start_time).isoformat(),
                'last_update': datetime.now().isoformat(),
                'total_interactions': len(self.session_data),
                'interactions': list(self.session_data)
            }
            
            # Escreve arquivo JSON
            with open(self.current_session_file, 'w', encoding='utf-8') as f:
                json.dump(session_summary, f, ensure_ascii=False, indent=2)
                
            logger.info("Session data persisted", extra={
                'extra_data': {
                    'file': str(self.current_session_file),
                    'interactions': len(self.session_data)
                }
            })
            
        except Exception as e:
            logger.error(f"Failed to persist session data: {e}")
    
    async def finalize_session(self) -> Dict[str, Any]:
        """Finaliza sessão e retorna dados completos."""
        await self._persist_session_data()
        
        session_summary = {
            'session_id': self.current_session_file.stem if self.current_session_file else 'unknown',
            'start_time': self.session_start_time,
            'end_time': time.time(),
            'duration_minutes': (time.time() - self.session_start_time) / 60,
            'total_interactions': len(self.session_data),
            'interactions': list(self.session_data)
        }
        
        logger.info("Session finalized", extra={
            'extra_data': {
                'duration_minutes': session_summary['duration_minutes'],
                'total_interactions': session_summary['total_interactions']
            }
        })
        
        return session_summary
    
    @functools.cached_property
    def key_prefix(self) -> str:
        return f"{self.__class__.__qualname__}:{self.history_dir}"


class ContextLoadProcessor(processor.Processor):
    """Carrega contexto inicial do summary.txt na inicialização.
    
    Este processador injeta o conteúdo do summary.txt no início do stream
    para fornecer contexto histórico ao sistema.
    """
    
    def __init__(self, summary_file: str = "summary.txt"):
        self.summary_file = Path(summary_file)
        
    async def call(self, content: AsyncIterable[content_api.ProcessorPart]) -> AsyncIterable[content_api.ProcessorPartTypes]:
        """Carrega contexto inicial e injeta no stream."""
        
        # Carrega summary existente
        summary_content = await self._load_summary_content()
        
        if summary_content:
            # Emite contexto inicial
            yield content_api.ProcessorPart(
                summary_content,
                role='system',
                substream_name='initial_context',
                metadata={
                    'context_type': 'initial_summary',
                    'loaded_at': time.time(),
                    'summary_length': len(summary_content)
                }
            )
            
            yield processor.debug(f"Initial context loaded: {len(summary_content)} characters")
            
        else:
            # Primeira execução - sem contexto
            yield processor.debug("No existing summary found - first execution")
            
            yield content_api.ProcessorPart(
                "",
                role='system',
                substream_name='initial_context',
                metadata={
                    'context_type': 'first_execution',
                    'loaded_at': time.time()
                }
            )
        
        # Processa stream original
        async for part in content:
            yield part
    
    async def _load_summary_content(self) -> Optional[str]:
        """Carrega conteúdo do summary.txt."""
        try:
            if self.summary_file.exists():
                content = self.summary_file.read_text(encoding='utf-8')
                if content.strip():  # Verifica se não está vazio
                    return content
                    
        except Exception as e:
            logger.error(f"Error loading summary: {e}")
            
        return None
    
    @functools.cached_property
    def key_prefix(self) -> str:
        return f"{self.__class__.__qualname__}:{self.summary_file}"


class SummaryGenerationProcessor(processor.Processor):
    """Gera resumos inteligentes usando modelo Gemini.
    
    Este processador analisa o histórico de uma sessão e gera um resumo
    estruturado com insights, decisões e contexto relevante.
    """
    
    def __init__(self, 
                 model: str = "gemini-2.5-flash",
                 api_key: str = None):
        self.model = model
        self.genai_model = genai_model.GenaiModel(
            model_name=model,
            api_key=api_key,
            generate_content_config=genai_types.GenerateContentConfig(
                max_output_tokens=2000,
                temperature=0.3  # Mais determinístico para resumos
            )
        )
        
    async def call(self, content: AsyncIterable[content_api.ProcessorPart]) -> AsyncIterable[content_api.ProcessorPartTypes]:
        """Processa histórico de sessão e gera resumo estruturado."""
        
        # Coleta dados da sessão
        session_parts = []
        async for part in content:
            session_parts.append(part)
            yield part  # Passa adiante
        
        # Gera resumo se há dados suficientes
        conversational_parts = [
            part for part in session_parts 
            if (content_api.is_text(part.mimetype) and 
                part.role in ['user', 'assistant'] and
                len(part.text.strip()) > 10)  # Ignora partes muito pequenas
        ]
        
        if len(conversational_parts) >= 3:  # Mínimo de interações significativas
            summary_prompt = self._create_summary_prompt(conversational_parts)
            
            # Processa com modelo Gemini
            summary_stream = self.genai_model(streams.stream_content([
                content_api.ProcessorPart(
                    summary_prompt,
                    role='user',
                    substream_name='summary_generation'
                )
            ]))
            
            async for summary_part in summary_stream:
                # Emite resumo gerado
                summary_part.metadata['summary_type'] = 'session_summary'
                summary_part.metadata['source_parts_count'] = len(conversational_parts)
                summary_part.metadata['generated_at'] = time.time()
                summary_part.role = 'system'  # Marca como conteúdo do sistema
                yield summary_part
                
                logger.info("Session summary generated", extra={
                    'extra_data': {
                        'source_parts': len(conversational_parts),
                        'summary_length': len(summary_part.text)
                    }
                })
        else:
            yield processor.debug(f"Insufficient data for summary generation: {len(conversational_parts)} parts")
    
    def _create_summary_prompt(self, session_parts: List[content_api.ProcessorPart]) -> str:
        """Cria prompt para geração de resumo."""
        conversation_text = "\n".join([
            f"{part.role}: {part.text}" 
            for part in session_parts 
            if content_api.is_text(part.mimetype)
        ])
        
        return f"""
Analise a seguinte conversa entre um usuário e o Leonidas (assistente de IA colaborativo) e gere um resumo estruturado em português brasileiro.

CONVERSA:
{conversation_text}

Gere um resumo seguindo EXATAMENTE este formato:

# Resumo da Sessão - {datetime.now().strftime('%Y-%m-%d %H:%M')}

## Contexto Geral
[Descreva brevemente o contexto principal da conversa - máximo 3 frases]

## Decisões Importantes
[Liste decisões técnicas ou de projeto tomadas durante a conversa]
- Decisão 1
- Decisão 2

## Tarefas Pendentes  
[Liste tarefas ou ações que ficaram pendentes]
- Tarefa 1
- Tarefa 2

## Preferências do Usuário
[Identifique preferências técnicas ou de trabalho demonstradas]
- Preferência 1
- Preferência 2

## Contexto Técnico
[Descreva detalhes técnicos relevantes: tecnologias, arquiteturas, problemas discutidos]

IMPORTANTE: Responda APENAS com o resumo formatado, sem explicações adicionais.
        """
    
    @functools.cached_property
    def key_prefix(self) -> str:
        return f"{self.__class__.__qualname__}:{self.model}"


class PersistentMemoryProcessor(processor.PartProcessor):
    """Gerencia memória persistente e arquivo summary.txt.
    
    Este processador consolida resumos de sessão com o summary.txt existente,
    mantendo um histórico cumulativo inteligente.
    """
    
    def __init__(self, summary_file: str = "summary.txt"):
        self.summary_file = Path(summary_file)
        self.cache = cache.InMemoryCache(
            ttl_hours=24,
            max_items=100,
            hash_fn=self._summary_hash_fn
        )
        
    def match(self, part: content_api.ProcessorPart) -> bool:
        """Processa partes que são resumos de sessão."""
        return (part.metadata.get('summary_type') == 'session_summary' and
                content_api.is_text(part.mimetype) and
                len(part.text.strip()) > 50)  # Resumos devem ter conteúdo substancial
    
    async def call(self, part: content_api.ProcessorPart) -> AsyncIterable[content_api.ProcessorPartTypes]:
        """Atualiza summary.txt com novo resumo."""
        if self.match(part):
            # Carrega summary existente
            existing_summary = await self._load_existing_summary()
            
            # Consolida com novo resumo
            consolidated_summary = await self._consolidate_summaries(
                existing_summary, part.text
            )
            
            # Persiste summary atualizado
            await self._save_summary(consolidated_summary)
            
            # Emite confirmação
            yield processor.status("Summary.txt updated successfully")
            
            # Emite summary consolidado
            yield content_api.ProcessorPart(
                consolidated_summary,
                role='system',
                metadata={
                    'summary_type': 'consolidated_summary',
                    'updated_at': time.time(),
                    'previous_length': len(existing_summary) if existing_summary else 0,
                    'new_length': len(consolidated_summary)
                }
            )
            
            logger.info("Summary.txt updated", extra={
                'extra_data': {
                    'previous_length': len(existing_summary) if existing_summary else 0,
                    'new_length': len(consolidated_summary)
                }
            })
        else:
            yield part
    
    async def _load_existing_summary(self) -> Optional[str]:
        """Carrega summary.txt existente."""
        try:
            if self.summary_file.exists():
                return self.summary_file.read_text(encoding='utf-8')
        except Exception as e:
            logger.error(f"Error loading existing summary: {e}")
        return None
    
    async def _consolidate_summaries(self, existing: Optional[str], new_summary: str) -> str:
        """Consolida novo resumo com resumo existente."""
        if not existing or not existing.strip():
            # Primeira sessão - usa resumo atual como base
            return self._create_initial_summary(new_summary)
        
        # Consolida resumos existente e novo
        return self._merge_summaries(existing, new_summary)
    
    def _create_initial_summary(self, session_summary: str) -> str:
        """Cria summary.txt inicial baseado na primeira sessão."""
        header = f"""# Leonidas - Resumo de Contexto Acumulado
Última atualização: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Primeira sessão registrada.

"""
        return header + session_summary
    
    def _merge_summaries(self, existing: str, new_summary: str) -> str:
        """Merge inteligente de resumos."""
        # Atualiza header
        lines = existing.split('\n')
        updated_lines = []
        
        for i, line in enumerate(lines):
            if line.startswith('Última atualização:'):
                updated_lines.append(f"Última atualização: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            elif line.startswith('Primeira sessão registrada.'):
                # Remove linha de primeira sessão
                continue
            else:
                updated_lines.append(line)
        
        # Adiciona nova sessão
        updated_lines.append(f"\n---\n\n{new_summary}")
        
        # Comprime se necessário (mantém últimas 5 sessões + contexto geral)
        return self._compress_if_needed('\n'.join(updated_lines))
    
    def _compress_if_needed(self, summary: str) -> str:
        """Comprime summary se exceder tamanho limite."""
        max_size = 10000  # 10KB limite
        
        if len(summary) <= max_size:
            return summary
        
        # Compressão simples: mantém header + últimas 3 sessões
        lines = summary.split('\n')
        header_lines = []
        session_separators = []
        
        for i, line in enumerate(lines):
            if line.strip() == '---':
                session_separators.append(i)
            elif i < 10:  # Primeiras 10 linhas são header
                header_lines.append(line)
        
        if len(session_separators) > 3:
            # Mantém apenas últimas 3 sessões
            keep_from = session_separators[-3]
            compressed_lines = header_lines + ["\n[Sessões anteriores comprimidas]\n"] + lines[keep_from:]
            return '\n'.join(compressed_lines)
        
        return summary
    
    async def _save_summary(self, summary: str):
        """Salva summary.txt atualizado."""
        try:
            self.summary_file.write_text(summary, encoding='utf-8')
        except Exception as e:
            logger.error(f"Error saving summary: {e}")
            raise
    
    def _summary_hash_fn(self, content: content_api.ProcessorContentTypes) -> Optional[str]:
        """Hash function customizada para cache de summaries."""
        # Exclui timestamps para cache consistente
        filtered_content = []
        for part in content_api.ProcessorContent(content).all_parts:
            if 'updated_at' not in part.metadata:
                filtered_content.append(part)
        
        return cache.default_processor_content_hash(filtered_content) if filtered_content else None
    
    @functools.cached_property
    def key_prefix(self) -> str:
        return f"{self.__class__.__qualname__}:{self.summary_file}"
class InitialContextProcessor(processor.PartProcessor):
    """Processa contexto inicial carregado e prepara para decisão de inicialização.
    
    Este processador analisa o summary.txt carregado e decide como o Leonidas
    deve inicializar a nova sessão.
    """
    
    def __init__(self, api_key: str = None):
        self.genai_model = genai_model.GenaiModel(
            model_name="gemini-2.5-flash",
            api_key=api_key,
            generate_content_config=genai_types.GenerateContentConfig(
                max_output_tokens=500,
                temperature=0.2  # Mais determinístico para análise
            )
        )
    
    def match(self, part: content_api.ProcessorPart) -> bool:
        """Processa partes que são contexto inicial."""
        return (part.substream_name == 'initial_context' and
                part.metadata.get('context_type') in ['initial_summary', 'first_execution'])
    
    async def call(self, part: content_api.ProcessorPart) -> AsyncIterable[content_api.ProcessorPartTypes]:
        """Processa contexto inicial usando análise do modelo."""
        if self.match(part):
            if part.metadata.get('context_type') == 'first_execution':
                # Primeira execução - inicialização padrão
                yield content_api.ProcessorPart(
                    json.dumps({
                        "deve_cumprimentar": True,
                        "tipo_inicializacao": "primeira_execucao",
                        "tarefas_pendentes_encontradas": [],
                        "contexto_relevante": "Primeira execução do Leonidas",
                        "acao_sugerida": "Apresentar-se e aguardar instruções"
                    }),
                    role='system',
                    metadata={
                        'analysis_type': 'initial_context_analysis',
                        'source_context_length': 0
                    }
                )
            else:
                # Analisa contexto existente
                analysis_prompt = self._create_context_analysis_prompt(part.text)
                
                # Processa com modelo para análise
                analysis_stream = self.genai_model(streams.stream_content([
                    content_api.ProcessorPart(
                        analysis_prompt,
                        role='user',
                        substream_name='context_analysis'
                    )
                ]))
                
                async for analysis_part in analysis_stream:
                    # Emite análise do contexto
                    analysis_part.metadata['analysis_type'] = 'initial_context_analysis'
                    analysis_part.metadata['source_context_length'] = len(part.text)
                    analysis_part.role = 'system'
                    yield analysis_part
        
        # Sempre passa a parte original adiante
        yield part
    
    def _create_context_analysis_prompt(self, context: str) -> str:
        """Cria prompt para análise do contexto inicial."""
        return f"""
Analise o seguinte resumo de contexto histórico do Leonidas e determine como inicializar a nova sessão.

CONTEXTO HISTÓRICO:
{context}

Com base neste contexto, responda APENAS com um JSON válido seguindo exatamente este formato:

{{"deve_cumprimentar": true, "tipo_inicializacao": "contextual", "tarefas_pendentes_encontradas": ["tarefa1", "tarefa2"], "contexto_relevante": "resumo do que é mais relevante para mencionar", "acao_sugerida": "descrição da ação inicial recomendada"}}

Regras:
- deve_cumprimentar: true se deve falar algo, false para iniciar silencioso
- tipo_inicializacao: "contextual" se há contexto relevante, "silenciosa" se deve aguardar, "pergunta" se deve perguntar algo
- tarefas_pendentes_encontradas: array com tarefas pendentes identificadas
- contexto_relevante: máximo 100 caracteres do que é mais importante
- acao_sugerida: máximo 150 caracteres da ação recomendada

Responda APENAS com o JSON em uma única linha, sem quebras de linha ou explicações.
        """
    
    @functools.cached_property
    def key_prefix(self) -> str:
        return f"{self.__class__.__qualname__}"


class ContextualGreetingProcessor(processor.PartProcessor):
    """Gera um *prompt* de cumprimento contextual baseado na análise.
    
    Este processador cria um prompt para que o LiveProcessor gere uma
    mensagem de inicialização natural baseada na análise do contexto histórico.
    """
    
    def __init__(self, api_key: str = None):
        # Este processador não precisa mais de um modelo, ele apenas gera prompts.
        pass
    
    def match(self, part: content_api.ProcessorPart) -> bool:
        """Processa análises de contexto inicial."""
        return part.metadata.get('analysis_type') == 'initial_context_analysis'
    
    async def call(self, part: content_api.ProcessorPart) -> AsyncIterable[content_api.ProcessorPartTypes]:
        """Gera prompt de cumprimento contextual baseado na análise."""
        if self.match(part):
            try:
                # Parse da análise JSON
                analysis = json.loads(part.text)
                
                if analysis.get('deve_cumprimentar', False):
                    # Gera o PROMPT para o cumprimento
                    greeting_prompt = self._create_greeting_prompt(analysis)
                    
                    # Emite o PROMPT para ser usado pelo LiveProcessor
                    yield content_api.ProcessorPart(
                        greeting_prompt,
                        role='user',
                        substream_name='contextual_greeting_prompt',
                        metadata={
                            'initialization_type': analysis.get('tipo_inicializacao'),
                            'turn_complete': True
                        }
                    )
                    logger.info("Contextual greeting prompt generated")
                
                elif analysis.get('tipo_inicializacao') == 'silenciosa':
                    # Emite indicação de inicialização silenciosa
                    yield content_api.ProcessorPart(
                        "",  # Conteúdo vazio para inicialização silenciosa
                        role='system',
                        substream_name='silent_initialization',
                        metadata={
                            'initialization_type': 'silent',
                            'context_processed': True
                        }
                    )
                    
                    logger.info("Silent initialization configured")
                    
            except json.JSONDecodeError as e:
                # Fallback para inicialização padrão
                yield processor.debug(f"Failed to parse context analysis: {e}, using default initialization")
                
                yield content_api.ProcessorPart(
                    "Apresente-se como Leonidas, seu parceiro de desenvolvimento, e pergunte como posso ajudar hoje.",
                    role='user',
                    substream_name='default_greeting_prompt',
                    metadata={
                        'greeting_type': 'default',
                        'initialization_type': 'fallback',
                        'turn_complete': True
                    }
                )
        
        # Passa parte original adiante
        yield part
    
    def _create_greeting_prompt(self, analysis: dict) -> str:
        """Cria prompt para geração de cumprimento contextual."""
        return f"""
Gere um cumprimento natural e contextual em português brasileiro para iniciar uma sessão do Leonidas.

CONTEXTO DA ANÁLISE:
- Tipo de inicialização: {analysis.get('tipo_inicializacao')}
- Tarefas pendentes: {analysis.get('tarefas_pendentes_encontradas', [])}
- Contexto relevante: {analysis.get('contexto_relevante', '')}
- Ação sugerida: {analysis.get('acao_sugerida', '')}

Gere um cumprimento que:
1. Seja natural e conversacional (não robótico)
2. Mencione brevemente o contexto relevante se houver
3. Sugira continuidade se há tarefas pendentes
4. Seja conciso (máximo 2 frases)
5. Use tom colaborativo, como um parceiro técnico

Exemplos de tom adequado:
- "Oi! Vi que estávamos trabalhando no sistema de autenticação. Quer continuar de onde paramos?"
- "E aí! Lembrei que ficou pendente a documentação da API. Vamos resolver isso?"
- "Olá! Pronto para mais uma sessão produtiva?"

Responda APENAS com o cumprimento, sem explicações adicionais.
        """
    
    @functools.cached_property
    def key_prefix(self) -> str:
        return f"{self.__class__.__qualname__}"


class LeonidasMemorySystem:
    """Sistema completo de memória integrado com genai-processors.
    
    Este é o orquestrador principal que compõe todos os processadores
    de memória em pipelines funcionais.
    """
    
    def __init__(self, 
                 summary_file: str = "summary.txt",
                 history_dir: str = "history",
                 api_key: str = None):
        
        # Processadores individuais
        self.memory_input = MemoryInputProcessor(summary_file, history_dir)
        self.session_history = SessionHistoryProcessor(history_dir)
        self.context_load = ContextLoadProcessor(summary_file)
        self.initial_context = InitialContextProcessor(api_key)
        self.contextual_greeting = ContextualGreetingProcessor(api_key)
        self.summary_generation = SummaryGenerationProcessor(api_key=api_key)
        self.persistent_memory = PersistentMemoryProcessor(summary_file)
        
        # Pipelines compostas usando padrões genai-processors
        self.initialization_pipeline = (
            self.context_load +
            self.initial_context +
            self.contextual_greeting
        )
        
        self.runtime_pipeline = (
            self.memory_input +
            self.session_history
        )
        
        self.finalization_pipeline = (
            self.summary_generation +
            self.persistent_memory
        )
        
        logger.info("Leonidas Memory System initialized", extra={
            'extra_data': {
                'summary_file': summary_file,
                'history_dir': history_dir,
                'has_api_key': api_key is not None
            }
        })
    
    def get_initialization_processor(self) -> processor.Processor:
        """Retorna pipeline de inicialização."""
        return self.initialization_pipeline
    
    def get_runtime_processor(self) -> processor.Processor:
        """Retorna pipeline de runtime."""
        return self.runtime_pipeline
    
    def get_finalization_processor(self) -> processor.Processor:
        """Retorna pipeline de finalização."""
        return self.finalization_pipeline
    
    async def initialize_session(self) -> AsyncIterable[content_api.ProcessorPart]:
        """Inicializa sessão com contexto carregado."""
        # Stream vazio para trigger de inicialização
        empty_stream = streams.stream_content([
            content_api.ProcessorPart(
                "",
                role='system',
                metadata={'trigger': 'session_initialization'}
            )
        ])
        
        async for part in self.initialization_pipeline(empty_stream):
            yield part
    
    async def finalize_session(self, session_data: Optional[List[Dict]] = None) -> AsyncIterable[content_api.ProcessorPart]:
        """Finaliza sessão e processa resumo."""
        if session_data is None:
            # Obtém dados da sessão atual do SessionHistoryProcessor
            session_data = await self.session_history.finalize_session()
            session_interactions = session_data.get('interactions', [])
        else:
            session_interactions = session_data
        
        if not session_interactions:
            yield processor.debug("No session data to process for summary")
            return
        
        # Converte dados da sessão para stream
        session_stream = streams.stream_content([
            content_api.ProcessorPart(
                interaction['content'],
                role=interaction['role'],
                metadata=interaction.get('metadata', {})
            )
            for interaction in session_interactions
            if interaction.get('content', '').strip()  # Ignora interações vazias
        ])
        
        async for part in self.finalization_pipeline(session_stream):
            yield part
    
    async def get_current_context(self) -> Optional[str]:
        """Retorna contexto atual do summary.txt."""
        return await self.context_load._load_summary_content()
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas da sessão atual."""
        return {
            'session_id': self.memory_input.session_id,
            'interactions_logged': len(self.session_history.session_data),
            'session_duration_minutes': (time.time() - self.session_history.session_start_time) / 60,
            'summary_file_exists': self.persistent_memory.summary_file.exists(),
            'history_dir': str(self.session_history.history_dir)
        }
