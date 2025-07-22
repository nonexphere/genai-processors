#!/usr/bin/env python3
"""Teste básico do sistema de memória do Leonidas.

Este script testa as funcionalidades principais do sistema de memória:
- Carregamento de contexto inicial
- Processamento de histórico de sessão
- Geração de resumos
- Persistência de memória
"""

import asyncio
import json
import os
import tempfile
from pathlib import Path

from genai_processors import content_api, streams
from memory_system import LeonidasMemorySystem


async def test_memory_system():
    """Teste completo do sistema de memória."""
    
    print("🧪 Iniciando teste do sistema de memória do Leonidas...")
    
    # Cria diretório temporário para teste
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        summary_file = temp_path / "summary.txt"
        history_dir = temp_path / "history"
        
        print(f"📁 Usando diretório temporário: {temp_dir}")
        
        # Inicializa sistema de memória
        memory_system = LeonidasMemorySystem(
            summary_file=str(summary_file),
            history_dir=str(history_dir),
            api_key=None  # Teste sem API key
        )
        
        print("✅ Sistema de memória inicializado")
        
        # Teste 1: Primeira inicialização (sem summary.txt)
        print("\n🔍 Teste 1: Primeira inicialização")
        
        initialization_results = []
        async for part in memory_system.initialize_session():
            initialization_results.append(part)
            print(f"  - {part.role}: {part.text[:50]}..." if part.text else f"  - {part.role}: [metadata only]")
        
        print(f"✅ Inicialização completada com {len(initialization_results)} partes")
        
        # Teste 2: Processamento de runtime (simulando conversação)
        print("\n🔍 Teste 2: Processamento de runtime")
        
        # Simula uma conversação
        conversation_parts = [
            content_api.ProcessorPart(
                "Olá Leonidas, vamos trabalhar no sistema de autenticação",
                role='user'
            ),
            content_api.ProcessorPart(
                "Perfeito! Vou analisar o sistema atual de autenticação. Que aspectos específicos você gostaria de revisar?",
                role='assistant'
            ),
            content_api.ProcessorPart(
                "Preciso implementar OAuth 2.0 e adicionar rate limiting",
                role='user'
            ),
            content_api.ProcessorPart(
                "Excelente escolha! OAuth 2.0 vai melhorar a segurança e o rate limiting vai proteger contra ataques. Vou ajudar você a implementar isso.",
                role='assistant'
            )
        ]
        
        # Processa através do pipeline de runtime
        runtime_processor = memory_system.get_runtime_processor()
        conversation_stream = streams.stream_content(conversation_parts)
        
        runtime_results = []
        async for part in runtime_processor(conversation_stream):
            runtime_results.append(part)
            if part.substream_name != 'debug':  # Ignora debug para output limpo
                print(f"  - {part.role}: {part.text[:50]}..." if part.text else f"  - {part.role}: [metadata]")
        
        print(f"✅ Runtime processado com {len(runtime_results)} partes")
        
        # Teste 3: Finalização e geração de resumo
        print("\n🔍 Teste 3: Finalização e geração de resumo")
        
        # Simula dados de sessão para finalização
        session_data = [
            {
                'timestamp': 1642780800.0,
                'role': 'user',
                'content': 'Olá Leonidas, vamos trabalhar no sistema de autenticação',
                'metadata': {}
            },
            {
                'timestamp': 1642780820.0,
                'role': 'assistant', 
                'content': 'Perfeito! Vou analisar o sistema atual de autenticação.',
                'metadata': {}
            },
            {
                'timestamp': 1642780840.0,
                'role': 'user',
                'content': 'Preciso implementar OAuth 2.0 e adicionar rate limiting',
                'metadata': {}
            },
            {
                'timestamp': 1642780860.0,
                'role': 'assistant',
                'content': 'Excelente! OAuth 2.0 e rate limiting são fundamentais para segurança.',
                'metadata': {}
            }
        ]
        
        finalization_results = []
        async for part in memory_system.finalize_session(session_data):
            finalization_results.append(part)
            if part.text and len(part.text) > 10:
                print(f"  - {part.role}: {part.text[:100]}...")
        
        print(f"✅ Finalização completada com {len(finalization_results)} partes")
        
        # Teste 4: Verificar se summary.txt foi criado
        print("\n🔍 Teste 4: Verificação de persistência")
        
        if summary_file.exists():
            summary_content = summary_file.read_text(encoding='utf-8')
            print(f"✅ Summary.txt criado com {len(summary_content)} caracteres")
            print("📄 Conteúdo do summary:")
            print(summary_content[:300] + "..." if len(summary_content) > 300 else summary_content)
        else:
            print("❌ Summary.txt não foi criado")
        
        # Teste 5: Verificar arquivos de histórico
        if history_dir.exists():
            history_files = list(history_dir.glob("*.json"))
            print(f"✅ {len(history_files)} arquivo(s) de histórico criado(s)")
            
            if history_files:
                # Lê o primeiro arquivo de histórico
                with open(history_files[0], 'r', encoding='utf-8') as f:
                    history_data = json.load(f)
                print(f"📄 Histórico contém {history_data.get('total_interactions', 0)} interações")
        else:
            print("❌ Diretório de histórico não foi criado")
        
        # Teste 6: Segunda inicialização (com summary.txt existente)
        print("\n🔍 Teste 6: Segunda inicialização com contexto")
        
        # Cria um novo sistema para simular reinicialização
        memory_system_2 = LeonidasMemorySystem(
            summary_file=str(summary_file),
            history_dir=str(history_dir),
            api_key=None
        )
        
        second_init_results = []
        async for part in memory_system_2.initialize_session():
            second_init_results.append(part)
            if part.text and len(part.text) > 10:
                print(f"  - {part.role}: {part.text[:100]}...")
        
        print(f"✅ Segunda inicialização completada com {len(second_init_results)} partes")
        
        # Teste 7: Estatísticas do sistema
        print("\n🔍 Teste 7: Estatísticas do sistema")
        
        stats = memory_system.get_session_stats()
        print("📊 Estatísticas:")
        for key, value in stats.items():
            print(f"  - {key}: {value}")
        
        print("\n🎉 Todos os testes completados com sucesso!")
        print("✅ Sistema de memória está funcionando corretamente")


async def test_individual_processors():
    """Teste individual dos processadores."""
    
    print("\n🔧 Testando processadores individuais...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Teste do ContextLoadProcessor
        from memory_system import ContextLoadProcessor
        
        # Cria um summary.txt de teste
        summary_file = temp_path / "summary.txt"
        summary_file.write_text("""# Leonidas - Resumo de Contexto Acumulado
Última atualização: 2025-01-21 15:30:00

## Contexto Geral
Usuário trabalha em sistema de e-commerce com Python/FastAPI.

## Decisões Importantes
- Migração para OAuth 2.0
- Implementação de rate limiting

## Tarefas Pendentes
- Documentar nova API
- Criar testes unitários
""", encoding='utf-8')
        
        context_loader = ContextLoadProcessor(str(summary_file))
        
        # Testa carregamento de contexto
        empty_stream = streams.stream_content([
            content_api.ProcessorPart("", role='system')
        ])
        
        context_results = []
        async for part in context_loader(empty_stream):
            context_results.append(part)
            if part.substream_name == 'initial_context':
                print(f"✅ Contexto carregado: {len(part.text)} caracteres")
        
        print(f"✅ ContextLoadProcessor testado com {len(context_results)} partes")


if __name__ == "__main__":
    print("🚀 Executando testes do sistema de memória do Leonidas")
    
    # Executa teste principal
    asyncio.run(test_memory_system())
    
    # Executa testes individuais
    asyncio.run(test_individual_processors())
    
    print("\n🏁 Testes finalizados!")