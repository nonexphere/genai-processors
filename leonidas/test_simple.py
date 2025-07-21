#!/usr/bin/env python3
"""
Simple test to verify the basic Leonidas v2 components work.
"""

import asyncio
import os
import pyaudio
from genai_processors import content_api, streams, processor
import leonidas_v2

async def test_simple_orchestrator():
    """Test just the orchestrator without input/output."""
    
    print("🧪 Testando LeonidasOrchestrator simples...")
    
    api_key = os.environ.get('GOOGLE_API_KEY')
    if not api_key:
        print("❌ GOOGLE_API_KEY não encontrada!")
        return False
    
    try:
        # Create orchestrator
        orchestrator = leonidas_v2.LeonidasOrchestrator(api_key)
        print("✅ Orchestrator criado")
        
        # Create a simple test stream
        async def test_stream():
            yield content_api.ProcessorPart(
                "Olá Leonidas, como você está?",
                role='user'
            )
        
        print("📤 Enviando mensagem de teste...")
        
        response_count = 0
        async with processor.context():
            async for part in orchestrator(test_stream()):
                response_count += 1
                print(f"📨 Resposta #{response_count}: {part.mimetype} - {part.role}")
                
                if content_api.is_text(part.mimetype) and part.text:
                    print(f"💬 Texto: {part.text}")
                
                if part.function_call:
                    print(f"🛠️ Function call: {part.function_call.name}")
                
                # Stop after reasonable number of responses
                if response_count >= 10:
                    break
        
        print(f"✅ Teste concluído com {response_count} respostas")
        return response_count > 0
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_input_manager():
    """Test just the InputManager."""
    
    print("\n🧪 Testando InputManager...")
    
    try:
        pya = pyaudio.PyAudio()
        input_manager = leonidas_v2.InputManager(pya, 'camera')
        print("✅ InputManager criado")
        
        # Test with empty stream
        async def empty_stream():
            return
            yield  # Never reached
        
        part_count = 0
        timeout_seconds = 5
        
        print(f"📹 Testando captura por {timeout_seconds} segundos...")
        
        async with processor.context():
            try:
                async with asyncio.timeout(timeout_seconds):
                    async for part in input_manager(empty_stream()):
                        part_count += 1
                        print(f"📦 Parte #{part_count}: {part.mimetype}")
                        
                        if part_count >= 10:  # Limit for testing
                            break
            except asyncio.TimeoutError:
                print(f"⏰ Timeout após {timeout_seconds} segundos")
        
        pya.terminate()
        print(f"✅ InputManager teste concluído com {part_count} partes")
        return part_count > 0
        
    except Exception as e:
        print(f"❌ Erro no InputManager: {e}")
        return False

async def main():
    """Run simple tests."""
    
    print("🧪 Testes Simples do Leonidas v2")
    print("=" * 40)
    
    # Test orchestrator
    orchestrator_ok = await test_simple_orchestrator()
    
    # Test input manager
    input_ok = await test_input_manager()
    
    print("\n" + "=" * 40)
    print("📊 Resultados:")
    print(f"   Orchestrator: {'✅' if orchestrator_ok else '❌'}")
    print(f"   InputManager: {'✅' if input_ok else '❌'}")
    
    if orchestrator_ok and input_ok:
        print("🎉 Componentes básicos funcionando!")
    else:
        print("🔧 Alguns componentes precisam de ajustes")
    
    return orchestrator_ok and input_ok

if __name__ == '__main__':
    success = asyncio.run(main())
    exit(0 if success else 1)