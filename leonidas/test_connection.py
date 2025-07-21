#!/usr/bin/env python3
"""
Test script to verify Gemini Live API connectivity.
"""

import asyncio
import os
from google import genai
from google.genai import types as genai_types

async def test_gemini_live_connection():
    """Test basic connection to Gemini Live API."""
    
    print("🔍 Testando conectividade com Gemini Live API...")
    
    # Get API key
    api_key = os.environ.get('GOOGLE_API_KEY')
    if not api_key:
        print("❌ GOOGLE_API_KEY não encontrada!")
        return False
    
    print(f"✅ API Key encontrada: {api_key[:10]}...")
    
    # Create client
    try:
        client = genai.Client(api_key=api_key)
        print("✅ Cliente Gemini criado")
    except Exception as e:
        print(f"❌ Erro ao criar cliente: {e}")
        return False
    
    # Test basic API call first
    try:
        print("🧪 Testando API básica...")
        response = await client.aio.models.generate_content(
            model='gemini-2.0-flash-exp',
            contents='Diga apenas "Olá" em português',
            config=genai_types.GenerateContentConfig(max_output_tokens=10)
        )
        print(f"✅ API básica funcionando: {response.text}")
    except Exception as e:
        print(f"❌ Erro na API básica: {e}")
        return False
    
    # Test Live API connection
    try:
        print("🎙️ Testando Gemini Live API...")
        
        config = genai_types.LiveConnectConfig(
            response_modalities=['AUDIO'],
            system_instruction="Responda apenas 'Olá' em português",
            speech_config={
                'language_code': 'pt-BR',
                'voice_config': {
                    'prebuilt_voice_config': {
                        'voice_name': 'Kore'
                    }
                }
            },
            generation_config=genai_types.GenerationConfig(
                max_output_tokens=10
            )
        )
        
        print("📡 Tentando conectar ao Live API...")
        async with client.aio.live.connect(
            model='gemini-live-2.5-flash-preview',
            config=config
        ) as session:
            print("✅ Conexão Live API estabelecida!")
            
            # Send a simple message
            await session.send_client_content(
                turns=[genai_types.Content(
                    parts=[genai_types.Part(text="Diga olá")]
                )]
            )
            
            # Wait for response
            response_count = 0
            async for response in session.receive():
                response_count += 1
                print(f"📨 Resposta #{response_count} recebida")
                
                if response.text:
                    print(f"💬 Texto: {response.text}")
                
                if response.data:
                    print(f"🔊 Áudio: {len(response.data)} bytes")
                
                # Stop after first meaningful response
                if response_count >= 3:
                    break
            
            print("✅ Teste Live API concluído com sucesso!")
            return True
            
    except Exception as e:
        print(f"❌ Erro no Live API: {e}")
        print(f"   Tipo do erro: {type(e).__name__}")
        
        # Check for specific error types
        if "timeout" in str(e).lower():
            print("💡 Dica: Problema de timeout - verifique sua conexão de internet")
        elif "auth" in str(e).lower() or "key" in str(e).lower():
            print("💡 Dica: Problema de autenticação - verifique sua API key")
        elif "region" in str(e).lower():
            print("💡 Dica: Problema de região - Live API pode não estar disponível na sua região")
        
        return False

async def main():
    """Main test function."""
    
    print("🧪 Teste de Conectividade Gemini Live API")
    print("=" * 50)
    
    success = await test_gemini_live_connection()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Todos os testes passaram!")
        print("✅ Leonidas v2 deve funcionar corretamente")
    else:
        print("❌ Problemas de conectividade detectados")
        print("🔧 Resolva os problemas acima antes de executar o Leonidas v2")
    
    return success

if __name__ == '__main__':
    success = asyncio.run(main())
    exit(0 if success else 1)