# Leonidas Main Directive - Steering Principal

## 🎯 **DIRETIVA PRINCIPAL DO PROJETO LEONIDAS**

Este é o steering rule principal que direciona todo o desenvolvimento do projeto Leonidas. Todos os outros steering rules são complementares a esta diretiva central.

## 📁 **FOCO PRINCIPAL: PASTA `leonidas/`**

**ATENÇÃO**: O projeto principal está na pasta `leonidas/` e é onde todo o desenvolvimento deve ser focado. Esta pasta contém:

- **`leonidas.py`** - Implementação principal atual
- **`leonidas_v2.py`** - Nova versão em desenvolvimento
- **`leonidas_v2_cli.py`** - Interface CLI da v2
- **`test_v2.py`** - Testes da nova versão
- **`README_v2.md`** - Documentação da v2
- **`TARGET_STATE.md`** - Estado alvo do projeto
- **`REFACTORING_SPEC.md`** - Especificação de refatoração
- **`REFACTORING_COMPLETE.md`** - Status da refatoração

## 🚀 **PRIORIDADES DE DESENVOLVIMENTO**

### **1. Evolução da Versão 2 (PRIORIDADE MÁXIMA)**
- Foco em `leonidas_v2.py` como base principal
- Implementar funcionalidades baseadas nos steering rules de Gemini
- Usar `gemini-live-2.5-flash-preview` como modelo principal
- Integrar padrões de `leonidas-gemini-integration.md`

### **2. Arquitetura Alvo**
```python
# Estrutura base que deve ser seguida
class LeonidasV2:
    def __init__(self):
        self.gemini_client = genai.Client(api_key=api_key)
        self.state_machine = ConversationalStateMachine()
        self.function_manager = AdvancedFunctionManager()
        self.audio_system = GeminiAudioSystem()
        self.context_manager = IntelligentContextManager()
```

### **3. Funcionalidades Core**
- **Conversação em tempo real** com Gemini Live API
- **Análise colaborativa** via function calling
- **Detecção de eventos** visuais
- **Gerenciamento de contexto** inteligente
- **Interface CLI** robusta

## 🔧 **STEERING RULES RELEVANTES (EM ORDEM DE PRIORIDADE)**

### **Tier 1 - Essenciais para Leonidas**
1. `leonidas-gemini-integration.md` - Padrões específicos do projeto
2. `gemini-models-complete-reference.md` - Referência de modelos
3. `gemini-live-api-implementation.md` - Implementação da API Live
4. `gemini-function-scheduling-patterns.md` - Function calling avançado

### **Tier 2 - Importantes para Funcionalidades**
5. `gemini-performance-optimization.md` - Otimização de performance
6. `gemini-state-machine-patterns.md` - Gerenciamento de estado
7. `gemini-context-transcription-management.md` - Contexto e transcrição
8. `gemini-audio-processing-pipeline.md` - Processamento de áudio

### **Tier 3 - Complementares (Usar com Moderação)**
9. `genai-processors-complete-reference.md` - Referência da biblioteca
10. Outros steering rules de genai-processors (apenas quando necessário)

## 📋 **DIRETRIZES DE DESENVOLVIMENTO**

### **Ao Trabalhar no Leonidas:**
1. **SEMPRE** focar na pasta `leonidas/`
2. **SEMPRE** usar `leonidas_v2.py` como base principal
3. **SEMPRE** seguir os padrões de `leonidas-gemini-integration.md`
4. **SEMPRE** implementar em português brasileiro
5. **SEMPRE** usar `gemini-live-2.5-flash-preview` como modelo padrão

### **Padrões de Código:**
```python
# Configuração padrão para Leonidas
LEONIDAS_CONFIG = types.LiveConnectConfig(
    response_modalities=["AUDIO"],
    system_instruction=LEONIDAS_PROMPT_PARTS,
    speech_config={
        'language_code': 'pt-BR',
        'voice_config': {'prebuilt_voice_config': {'voice_name': 'Kore'}}
    },
    tools=LEONIDAS_TOOLS
)
```

### **Funcionalidades Obrigatórias:**
- `start_commentating()` - Análise colaborativa
- `wait_for_user()` - Aguardar usuário
- Event detection com `gemini-2.5-flash-lite-preview-06-17`
- Context management inteligente
- Audio rate limiting natural

## 🚫 **O QUE EVITAR**

### **NÃO Fazer:**
- Não trabalhar na pasta `leonidas_core_v20_archived/` (está arquivada)
- Não usar modelos Gemini obsoletos
- Não implementar funcionalidades genéricas demais
- Não ignorar os padrões específicos do Leonidas
- Não sobrecarregar com todos os steering rules simultaneamente

### **Steering Rules a Usar com Cuidado:**
- GenAI Processors rules (apenas quando necessário)
- Padrões muito genéricos que não se aplicam ao Leonidas
- Implementações que não seguem a arquitetura do projeto

## 🎯 **OBJETIVOS ESPECÍFICOS**

### **Curto Prazo:**
1. Finalizar `leonidas_v2.py` com funcionalidades core
2. Implementar CLI robusta em `leonidas_v2_cli.py`
3. Completar testes em `test_v2.py`
4. Documentar em `README_v2.md`

### **Médio Prazo:**
1. Otimizar performance seguindo steering de otimização
2. Implementar state machine avançada
3. Melhorar context management
4. Adicionar métricas e monitoramento

### **Longo Prazo:**
1. Integração com genai-processors (se necessário)
2. Funcionalidades avançadas de colaboração
3. Deploy em produção
4. Expansão de funcionalidades

## 📖 **COMO USAR ESTE STEERING**

### **Para Desenvolvimento:**
1. Sempre consulte este steering PRIMEIRO
2. Use steering rules específicos conforme necessário
3. Mantenha foco na pasta `leonidas/`
4. Siga os padrões estabelecidos

### **Para Debugging:**
1. Verifique se está seguindo as diretrizes principais
2. Consulte steering rules de performance/debugging
3. Mantenha logs em português brasileiro
4. Use métricas específicas do Leonidas

## 🔄 **EVOLUÇÃO CONTÍNUA**

Este steering rule deve ser atualizado conforme o projeto evolui, mas sempre mantendo:
- Foco na pasta `leonidas/`
- Priorização da versão 2
- Padrões específicos do projeto
- Integração com Gemini Live API
- Desenvolvimento em português brasileiro

---

**LEMBRE-SE**: Este é o steering principal. Todos os outros são complementares e devem ser usados dentro do contexto definido aqui.