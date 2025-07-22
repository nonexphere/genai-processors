#!/usr/bin/env python3
"""
Leonidas v2 Demo Script

Este script demonstra como usar o Leonidas v2 programaticamente
e mostra as principais funcionalidades do sistema.
"""

import asyncio
import os
import sys
from genai_processors import content_api, streams
import leonidas

async def demo_basic_usage():
    """Demonstração básica do uso do Leonidas v2."""
    
    print("🚀 Leonidas v2 - Demonstração Básica")
    print("=" * 50)
    
    # Verificar API key
    api_key = os.environ.get('GOOGLE_API_KEY')
    if not api_key:
        print("❌ GOOGLE_API_KEY não encontrada!")
        print("   Configure: export GOOGLE_API_KEY='sua_chave_aqui'")
        return False
    
    print("✅ API Key configurada")
    print("✅ Modelo: gemini-live-2.5-flash-preview")
    print("✅ Arquitetura: Modular (Input → Orchestrator → Output)")
    print("✅ Linguagem: Português Brasileiro")
    print("✅ Sistema de Tools: think, speak, change_state, get_context, get_time")
    
    print("\n🧠 Funcionalidades Principais:")
    print("   • THINK-ACT Cycle: Modelo pensa antes de agir")
    print("   • Auto-gerenciamento de estado")
    print("   • Memória de conversação")
    print("   • Análise contextual")
    print("   • Colaboração inteligente")
    
    print("\n📋 Para usar o Leonidas v2:")
    print("   1. Modo Câmera: python leonidas_cli.py --mode camera")
    print("   2. Modo Tela: python leonidas_cli.py --mode screen")
    print("   3. Debug: python leonidas_cli.py --debug")
    
    return True

def demo_architecture():
    """Demonstração da arquitetura modular."""
    
    print("\n🏗️ Arquitetura Modular")
    print("=" * 30)
    
    # Mostrar componentes
    components = [
        ("InputManager", "Abstração de entrada (câmera, microfone)"),
        ("LeonidasOrchestrator", "Inteligência central + sistema de tools"),
        ("OutputManager", "Abstração de saída (alto-falantes)")
    ]
    
    for name, description in components:
        print(f"   📦 {name}")
        print(f"      {description}")
    
    print("\n🔧 Sistema de Tools:")
    tools = leonidas.LEONIDAS_TOOLS[0].function_declarations
    for tool in tools:
        print(f"   🛠️ {tool.name}: {tool.description[:50]}...")
    
    print(f"\n📝 Sistema de Prompt: {len(leonidas.LEONIDAS_SYSTEM_PROMPT)} seções")
    print("   • Identidade core")
    print("   • Filosofia operacional")
    print("   • Estilo de comunicação")
    print("   • Expertise técnica")
    print("   • Diretrizes comportamentais")

def demo_configuration():
    """Demonstração da configuração."""
    
    print("\n⚙️ Configuração")
    print("=" * 20)
    
    config_items = [
        ("Modelo", leonidas.MODEL_LIVE),
        ("Áudio Entrada", f"{leonidas.AUDIO_INPUT_RATE}Hz"),
        ("Áudio Saída", f"{leonidas.AUDIO_OUTPUT_RATE}Hz"),
        ("Voz", "Kore (profissional, clara)"),
        ("Linguagem", "Português Brasileiro"),
        ("Resolução", "Média (balanceada)")
    ]
    
    for item, value in config_items:
        print(f"   🔹 {item}: {value}")

async def demo_orchestrator():
    """Demonstração do orquestrador (sem API real)."""
    
    print("\n🎭 Orquestrador - Simulação")
    print("=" * 35)
    
    try:
        # Criar orquestrador (falhará sem API key real, mas mostra estrutura)
        orchestrator = leonidas.LeonidasOrchestrator("demo_key")
        
        print(f"   🎯 Estado inicial: {orchestrator.agent_state}")
        print(f"   📊 Métricas: {dict(orchestrator.metrics['tool_calls'])}")
        
        # Simular chamadas de tools
        print("\n   🧪 Testando handlers de tools:")
        
        # Test think
        await orchestrator._handle_think("demo_id", {
            'analysis': 'Análise de demonstração',
            'reasoning': 'Raciocínio de teste',
            'next_action': 'Ação planejada'
        })
        print("   ✅ Think tool funcionando")
        
        # Test state change
        await orchestrator._handle_change_state("demo_id", {
            'new_state': 'analyzing',
            'reason': 'Demonstração de mudança de estado'
        })
        print(f"   ✅ State change: {orchestrator.agent_state}")
        
        # Test context
        context_response = await orchestrator._handle_get_context("demo_id", {
            'context_type': 'system_status'
        })
        print("   ✅ Context retrieval funcionando")
        
        print(f"\n   📈 Estado final: {orchestrator.agent_state}")
        print(f"   📊 Tool calls: {dict(orchestrator.metrics['tool_calls'])}")
        
    except Exception as e:
        print(f"   ⚠️ Simulação limitada (sem API real): {type(e).__name__}")

async def main():
    """Função principal da demonstração."""
    
    # Executar demonstrações
    await demo_basic_usage()
    demo_architecture()
    demo_configuration()
    await demo_orchestrator()
    
    print("\n" + "=" * 60)
    print("🎉 Demonstração Completa!")
    print("=" * 60)
    print("Leonidas v2 está pronto para uso!")
    print("\n🚀 Próximos passos:")
    print("   1. Configure GOOGLE_API_KEY")
    print("   2. Execute: python leonidas_cli.py")
    print("   3. Use fones de ouvido para evitar feedback")
    print("   4. Fale naturalmente - Leonidas pensará antes de responder")
    
    print("\n💡 Dicas:")
    print("   • O agente controla seu próprio comportamento")
    print("   • Observe o console para ver o processo de pensamento")
    print("   • Use --debug para informações detalhadas")
    print("   • Ctrl+C para encerrar graciosamente")

if __name__ == '__main__':
    asyncio.run(main())