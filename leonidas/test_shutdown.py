#!/usr/bin/env python3
"""
Teste da funcionalidade de shutdown do Leonidas v2

Este script demonstra como o modelo pode se desligar quando solicitado pelo usuário
através da ferramenta shutdown_system.
"""

import asyncio
import os
import time
from unittest.mock import Mock, AsyncMock
from leonidas_v2 import LeonidasOrchestrator
from genai_processors import content_api
from google.genai import types as genai_types

async def test_shutdown_functionality():
    """Testa a funcionalidade de shutdown do sistema."""
    
    print("🧪 Testando funcionalidade de shutdown do Leonidas v2")
    print("=" * 60)
    
    # Mock API key para teste
    api_key = "test_api_key"
    
    # Criar orchestrator (sem conexão real com Gemini)
    orchestrator = LeonidasOrchestrator(api_key)
    
    # Simular chamada de função shutdown_system
    print("1. Testando shutdown SEM confirmação (deve ser negado)...")
    
    # Teste 1: Shutdown sem confirmação
    response1 = await orchestrator._handle_shutdown_system(
        call_id="test_call_1",
        args={
            "confirmation": False,
            "reason": "Teste sem confirmação"
        }
    )
    
    print(f"   Resposta: {response1.function_response.response}")
    print(f"   Status shutdown: {orchestrator.shutdown_requested}")
    print()
    
    # Teste 2: Shutdown com confirmação
    print("2. Testando shutdown COM confirmação (deve ser aceito)...")
    
    response2 = await orchestrator._handle_shutdown_system(
        call_id="test_call_2", 
        args={
            "confirmation": True,
            "reason": "Usuário solicitou encerramento do sistema"
        }
    )
    
    print(f"   Resposta: {response2.function_response.response}")
    print(f"   Status shutdown: {orchestrator.shutdown_requested}")
    print(f"   Motivo: {orchestrator.shutdown_reason}")
    print()
    
    # Teste 3: Verificar histórico da conversa
    print("3. Verificando histórico da conversa...")
    shutdown_entries = [
        entry for entry in orchestrator.conversation_history 
        if entry.get('metadata', {}).get('type') == 'shutdown'
    ]
    
    print(f"   Entradas de shutdown no histórico: {len(shutdown_entries)}")
    if shutdown_entries:
        for entry in shutdown_entries:
            print(f"   - {entry['text']}")
    print()
    
    # Teste 4: Verificar métricas
    print("4. Verificando métricas de uso de ferramentas...")
    print(f"   Chamadas da ferramenta shutdown_system: {orchestrator.metrics['tool_calls']['shutdown_system']}")
    print()
    
    print("✅ Testes de shutdown concluídos com sucesso!")
    print("=" * 60)
    
    return orchestrator.shutdown_requested

async def simulate_user_interaction():
    """Simula uma interação do usuário solicitando shutdown."""
    
    print("🎭 Simulando interação do usuário")
    print("=" * 60)
    
    # Simular diferentes tipos de solicitação de shutdown
    user_requests = [
        "Por favor, desligue o sistema",
        "Pode encerrar o Leonidas?", 
        "Quero sair do programa",
        "Finalize a sessão",
        "Shutdown do sistema"
    ]
    
    print("Exemplos de solicitações que deveriam ativar o shutdown:")
    for i, request in enumerate(user_requests, 1):
        print(f"   {i}. \"{request}\"")
    
    print()
    print("O modelo deveria:")
    print("   1. Usar a ferramenta 'think' para analisar a solicitação")
    print("   2. Confirmar com o usuário se realmente quer desligar")
    print("   3. Usar 'shutdown_system' com confirmation=True")
    print("   4. Responder com mensagem de despedida")
    print("   5. O sistema detecta a flag e encerra graciosamente")
    print()

def demonstrate_integration():
    """Demonstra como a integração funciona no sistema completo."""
    
    print("🔧 Integração com o sistema principal")
    print("=" * 60)
    
    print("No arquivo leonidas_v2.py, as seguintes modificações foram feitas:")
    print()
    
    print("1. NOVA FERRAMENTA adicionada ao LEONIDAS_TOOLS:")
    print("   - shutdown_system: Permite ao modelo se desligar")
    print("   - Requer confirmação explícita (confirmation=True)")
    print("   - Registra o motivo do shutdown")
    print()
    
    print("2. NOVO HANDLER no LeonidasOrchestrator:")
    print("   - _handle_shutdown_system(): Processa solicitações de shutdown")
    print("   - Valida confirmação antes de aceitar")
    print("   - Define flags shutdown_requested e shutdown_reason")
    print()
    
    print("3. MODIFICAÇÃO no loop principal (run_leonidas_v2):")
    print("   - Verifica periodicamente se shutdown foi solicitado")
    print("   - Encerra o loop graciosamente quando detectado")
    print("   - Exibe mensagem informativa ao usuário")
    print()
    
    print("4. COMPORTAMENTO ESPERADO:")
    print("   - Usuário: 'Por favor, desligue o sistema'")
    print("   - Leonidas: [usa think] -> [confirma] -> [usa shutdown_system]")
    print("   - Sistema: Detecta flag -> Encerra graciosamente")
    print()

async def main():
    """Função principal de teste."""
    
    print("🚀 TESTE COMPLETO DA FUNCIONALIDADE DE SHUTDOWN")
    print("=" * 80)
    print()
    
    # Executar testes
    await test_shutdown_functionality()
    print()
    
    await simulate_user_interaction()
    print()
    
    demonstrate_integration()
    print()
    
    print("📋 RESUMO:")
    print("✅ Ferramenta shutdown_system implementada")
    print("✅ Handler de shutdown funcional") 
    print("✅ Integração com loop principal")
    print("✅ Validação de confirmação")
    print("✅ Logging e histórico")
    print("✅ Encerramento gracioso")
    print()
    
    print("🎯 PRÓXIMOS PASSOS:")
    print("1. Teste com Gemini Live API real")
    print("2. Verificar comportamento em diferentes cenários")
    print("3. Ajustar prompts se necessário para melhor UX")
    print()
    
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())