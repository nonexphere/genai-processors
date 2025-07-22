# Model Specifications Management - Complete Reference System

## **SISTEMA COMPLETO DE GERENCIAMENTO DE ESPECIFICAÇÕES DE MODELOS**

Esta steering rule estabelece o padrão definitivo para documentação, organização e manutenção de especificações completas de modelos de IA, com foco em Google (Gemini) e Mistral, cobrindo todos os tipos de modelos e capacidades.

## 📁 **ESTRUTURA SIMPLIFICADA E PRÁTICA**

### **Abordagem Centralizada Recomendada**
```
resource/
├── models/                          # 🏠 ROOT - Especificações de modelos
│   ├── models-master-config.md      # 🎯 ARQUIVO MESTRE - Mapa completo
│   ├── google-gemini-complete.md    # 🔵 Todos os modelos Google/Gemini
│   ├── mistral-complete.md          # 🟠 Todos os modelos Mistral
│   ├── current-setup.md             # ⚙️ Configuração atual do projeto
│   └── free-tier-management.md      # 💳 Gestão de Free Tiers e múltiplas keys
├── apis/                            # 🌐 ROOT - Especificações de APIs
│   ├── gemini-api-complete.md       # 🔵 API Google/Gemini completa
│   └── mistral-api-complete.md      # 🟠 API Mistral completa
```

### **Justificativa da Abordagem Centralizada**
- **Menos fragmentação**: Informações relacionadas ficam juntas
- **Manutenção mais fácil**: Menos arquivos para atualizar
- **Contexto completo**: Visão holística de cada provider
- **Busca mais eficiente**: Menos lugares para procurar informações
- **Melhor para IA**: Contexto completo em um arquivo facilita compreensão

## 📋 **TEMPLATES OBRIGATÓRIOS POR TIPO DE MODELO**

### **🎙️ Template: Real-time/Live Models**
```markdown
# [MODEL_NAME] - Real-time Model Specification

## 📊 **MODEL OVERVIEW**
- **Model ID**: `model-identifier`
- **Provider**: Google/Mistral
- **Type**: Real-time/Live
- **Architecture**: [Half-cascade/Native/End-to-end]
- **Release Date**: YYYY-MM-DD
- **Status**: [Stable/Preview/Experimental/Deprecated]
- **Availability**: [Public/Limited/Private]

## 🎯 **CORE CAPABILITIES**
### **Primary Functions**
- [ ] Real-time bidirectional streaming
- [ ] Voice Activity Detection (VAD)
- [ ] Function calling support
- [ ] Multi-modal input (audio/video/text)
- [ ] Interruption handling
- [ ] Audio transcription (input/output)

### **Supported Modalities**
- **Input**: [Audio/Video/Text/Image]
- **Output**: [Audio/Text/Both]
- **Response Formats**: [Streaming/Turn-based]

### **Language Support**
- **Primary Languages**: [List with codes]
- **Voice Options**: [Available voices with descriptions]
- **Regional Variants**: [Supported regions]

## ⚙️ **TECHNICAL SPECIFICATIONS**

### **Audio Configuration**
```yaml
Input Audio:
  Sample Rate: 16000 Hz
  Format: PCM 16-bit little-endian
  Channels: 1 (mono)
  Encoding: Linear PCM

Output Audio:
  Sample Rate: 24000 Hz
  Format: PCM 16-bit little-endian
  Channels: 1 (mono)
  Encoding: Linear PCM
```

### **Context and Limits**
- **Context Window**: X tokens
- **Session Duration**: X minutes (audio-only), Y minutes (audio+video)
- **Max Input Size**: X MB per request
- **Max Output Tokens**: X tokens per response
- **Concurrent Sessions**: X per API key

### **Performance Characteristics**
- **Typical Latency**: X-Y ms (TTFT)
- **Throughput**: X requests/second
- **Availability**: X% uptime SLA
- **Error Rate**: <X% typical

## 🔧 **CONFIGURATION PATTERNS**

### **Basic Configuration**
```python
config = types.LiveConnectConfig(
    response_modalities=["AUDIO"],
    system_instruction="Your system prompt",
    speech_config={
        'language_code': 'pt-BR',
        'voice_config': {
            'prebuilt_voice_config': {
                'voice_name': 'VoiceName'
            }
        }
    },
    generation_config=types.GenerationConfig(
        media_resolution=types.MediaResolution.MEDIA_RESOLUTION_MEDIUM
    )
)
```

### **Advanced Configuration**
```python
advanced_config = types.LiveConnectConfig(
    response_modalities=["AUDIO"],
    tools=[function_declarations],
    system_instruction=system_prompt,
    output_audio_transcription={},
    realtime_input_config=types.RealtimeInputConfig(
        turn_coverage='TURN_INCLUDES_ALL_INPUT',
        automatic_activity_detection={
            'disabled': False,
            'start_of_speech_sensitivity': types.StartSensitivity.START_SENSITIVITY_MEDIUM,
            'end_of_speech_sensitivity': types.EndSensitivity.END_SENSITIVITY_MEDIUM,
            'prefix_padding_ms': 20,
            'silence_duration_ms': 100
        }
    )
)
```

## 🚦 **RATE LIMITS & QUOTAS**

### **Request Limits**
- **Requests per minute**: X
- **Requests per day**: X
- **Concurrent connections**: X
- **Burst capacity**: X requests

### **Data Limits**
- **Audio input per minute**: X MB
- **Total session data**: X MB
- **Function calls per session**: X
- **Context retention**: X hours

### **Billing & Costs**
- **Input pricing**: $X per 1K tokens
- **Output pricing**: $X per 1K tokens
- **Audio pricing**: $X per minute
- **Function call pricing**: $X per call

## 🛠️ **IMPLEMENTATION EXAMPLES**

### **Basic Usage**
```python
async def basic_live_session():
    client = genai.Client(api_key=api_key)
    
    async with client.aio.live.connect(
        model="model-name",
        config=config
    ) as session:
        # Send audio
        await session.send_realtime_input(
            audio=types.Blob(data=audio_data, mime_type="audio/pcm;rate=16000")
        )
        
        # Receive responses
        async for response in session.receive():
            if response.data:
                # Handle audio output
                play_audio(response.data)
```

### **Advanced Usage with Functions**
```python
async def advanced_live_session():
    # Function declarations
    functions = [
        types.FunctionDeclaration(
            name="function_name",
            description="Function description",
            behavior="NON_BLOCKING"
        )
    ]
    
    config = types.LiveConnectConfig(
        response_modalities=["AUDIO"],
        tools=[types.Tool(function_declarations=functions)]
    )
    
    async with client.aio.live.connect(model="model-name", config=config) as session:
        async for response in session.receive():
            if response.tool_call:
                # Handle function call
                result = await handle_function_call(response.tool_call)
                await session.send_tool_response(
                    function_responses=[
                        types.FunctionResponse(
                            id=response.tool_call.id,
                            name=response.tool_call.name,
                            response=result
                        )
                    ]
                )
```

## 🐛 **ERROR HANDLING & TROUBLESHOOTING**

### **Common Error Codes**
- **400**: Invalid request format
- **401**: Authentication failed
- **403**: Quota exceeded
- **429**: Rate limit exceeded
- **500**: Internal server error

### **Error Handling Patterns**
```python
async def robust_session():
    max_retries = 3
    retry_delay = 1.0
    
    for attempt in range(max_retries):
        try:
            async with client.aio.live.connect(model="model-name", config=config) as session:
                async for response in session.receive():
                    yield response
            break
        except ConnectionError as e:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(retry_delay * (2 ** attempt))
```

## 📈 **PERFORMANCE OPTIMIZATION**

### **Latency Optimization**
- Use `MEDIA_RESOLUTION_LOW` for faster processing
- Limit `max_output_tokens` for quicker responses
- Use appropriate VAD sensitivity settings
- Implement connection pooling

### **Quality Optimization**
- Use `MEDIA_RESOLUTION_HIGH` for better quality
- Adjust VAD sensitivity for natural conversation
- Implement proper audio preprocessing
- Use appropriate voice selection

## 🔄 **MIGRATION & COMPATIBILITY**

### **Version History**
- **v1.0**: Initial release
- **v1.1**: Added function calling
- **v2.0**: Improved audio quality

### **Breaking Changes**
- List of breaking changes between versions
- Migration steps for each version

### **Compatibility Matrix**
- Client library versions
- API version compatibility
- Feature availability by version

## 📚 **ADDITIONAL RESOURCES**

### **Documentation Links**
- [Official API Documentation](link)
- [SDK Reference](link)
- [Best Practices Guide](link)

### **Code Examples**
- [GitHub Repository](link)
- [Sample Applications](link)
- [Integration Examples](link)

### **Community Resources**
- [Developer Forum](link)
- [Stack Overflow Tag](link)
- [Discord Community](link)

---
**Last Updated**: YYYY-MM-DD
**Reviewed By**: [Name]
**Next Review**: YYYY-MM-DD
```

### **💬 Template: Completion Models**
```markdown
# [MODEL_NAME] - Completion Model Specification

## 📊 **MODEL OVERVIEW**
- **Model ID**: `model-identifier`
- **Provider**: Google/Mistral
- **Type**: Text Completion
- **Architecture**: [Transformer/Other]
- **Parameters**: X billion
- **Training Cutoff**: YYYY-MM-DD
- **Release Date**: YYYY-MM-DD
- **Status**: [Stable/Preview/Experimental/Deprecated]

## 🎯 **CORE CAPABILITIES**
### **Primary Functions**
- [ ] Text generation
- [ ] Code completion
- [ ] Question answering
- [ ] Summarization
- [ ] Translation
- [ ] Function calling
- [ ] JSON mode
- [ ] Structured output

### **Supported Input Types**
- **Text**: Plain text, markdown, code
- **Images**: [If multimodal] JPEG, PNG, WebP
- **Documents**: [If supported] PDF, DOCX
- **Code**: [Languages supported]

### **Output Formats**
- **Text**: Plain text, markdown
- **Structured**: JSON, XML
- **Code**: Multiple programming languages
- **Streaming**: Token-by-token streaming

## ⚙️ **TECHNICAL SPECIFICATIONS**

### **Context and Limits**
- **Context Window**: X tokens
- **Max Input Tokens**: X tokens
- **Max Output Tokens**: X tokens
- **Max Images**: X per request (if multimodal)
- **Max File Size**: X MB per file

### **Performance Characteristics**
- **Typical Latency**: X-Y ms (first token)
- **Throughput**: X tokens/second
- **Availability**: X% uptime SLA
- **Error Rate**: <X% typical

### **Model Capabilities Matrix**
| Capability | Support Level | Notes |
|------------|---------------|-------|
| Text Generation | ✅ Full | Native capability |
| Code Generation | ✅ Full | 50+ languages |
| Function Calling | ✅ Full | Parallel calls supported |
| JSON Mode | ✅ Full | Structured output |
| Image Understanding | ⚠️ Limited | If multimodal |
| Audio Processing | ❌ None | Use specialized models |

## 🔧 **CONFIGURATION PATTERNS**

### **Basic Text Generation**
```python
import google.generativeai as genai

genai.configure(api_key=api_key)
model = genai.GenerativeModel('model-name')

response = model.generate_content("Your prompt here")
print(response.text)
```

### **Streaming Generation**
```python
response = model.generate_content(
    "Your prompt here",
    stream=True
)

for chunk in response:
    print(chunk.text, end='')
```

### **Function Calling**
```python
tools = [
    {
        "function_declarations": [
            {
                "name": "function_name",
                "description": "Function description",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "param1": {"type": "string", "description": "Parameter description"}
                    },
                    "required": ["param1"]
                }
            }
        ]
    }
]

model = genai.GenerativeModel('model-name', tools=tools)
response = model.generate_content("Call the function with appropriate parameters")
```

### **JSON Mode**
```python
generation_config = genai.GenerationConfig(
    response_mime_type="application/json",
    response_schema={
        "type": "object",
        "properties": {
            "answer": {"type": "string"},
            "confidence": {"type": "number"}
        }
    }
)

model = genai.GenerativeModel('model-name', generation_config=generation_config)
response = model.generate_content("Generate structured response")
```

## 🚦 **RATE LIMITS & QUOTAS**

### **Request Limits**
- **Requests per minute**: X
- **Requests per day**: X
- **Tokens per minute**: X
- **Concurrent requests**: X

### **Billing & Costs**
- **Input pricing**: $X per 1M tokens
- **Output pricing**: $X per 1M tokens
- **Image pricing**: $X per image (if applicable)
- **Function call pricing**: $X per call

## 🛠️ **IMPLEMENTATION EXAMPLES**

### **Code Completion Example**
```python
def code_completion_example():
    model = genai.GenerativeModel('model-name')
    
    prompt = """
    Complete this Python function:
    
    def fibonacci(n):
        # Complete this function to return the nth Fibonacci number
    """
    
    response = model.generate_content(prompt)
    return response.text
```

### **Multi-modal Example (if supported)**
```python
def multimodal_example():
    model = genai.GenerativeModel('model-name')
    
    # Upload image
    image = genai.upload_file("path/to/image.jpg")
    
    response = model.generate_content([
        "Describe what you see in this image:",
        image
    ])
    
    return response.text
```

## 🐛 **ERROR HANDLING & TROUBLESHOOTING**

### **Common Issues**
- **Token limit exceeded**: Reduce input size or use chunking
- **Rate limit hit**: Implement exponential backoff
- **Invalid function schema**: Validate JSON schema
- **Content filtering**: Review content policy

### **Error Handling Pattern**
```python
import time
from google.generativeai.types import BlockedPromptException, StopCandidateException

def robust_generation(prompt, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt)
            return response.text
        except BlockedPromptException:
            # Content was blocked
            return "Content blocked by safety filters"
        except StopCandidateException:
            # Generation stopped
            return "Generation stopped"
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(2 ** attempt)  # Exponential backoff
```

## 📈 **PERFORMANCE OPTIMIZATION**

### **Prompt Engineering**
- Use clear, specific instructions
- Provide examples for complex tasks
- Structure prompts with clear sections
- Use appropriate temperature settings

### **Efficiency Tips**
- Batch similar requests
- Use streaming for long responses
- Implement caching for repeated queries
- Optimize context window usage

## 🔄 **MIGRATION & COMPATIBILITY**

### **Version History**
- **v1.0**: Initial release
- **v1.5**: Added function calling
- **v2.0**: Improved reasoning capabilities

### **Migration Guide**
```python
# Old API (deprecated)
old_response = old_model.generate_text(prompt)

# New API
new_response = new_model.generate_content(prompt)
text = new_response.text
```

---
**Last Updated**: YYYY-MM-DD
**Reviewed By**: [Name]
**Next Review**: YYYY-MM-DD
```

### **🎯 Template: Specialized Models (TTS, FIM, etc.)**
```markdown
# [MODEL_NAME] - Specialized Model Specification

## 📊 **MODEL OVERVIEW**
- **Model ID**: `model-identifier`
- **Provider**: Google/Mistral
- **Type**: [TTS/FIM/Embedding/Moderation/Other]
- **Specialization**: [Specific use case]
- **Architecture**: [Model architecture details]
- **Release Date**: YYYY-MM-DD
- **Status**: [Stable/Preview/Experimental/Deprecated]

## 🎯 **SPECIALIZED CAPABILITIES**

### **Primary Function**: [e.g., Text-to-Speech]
- **Input Format**: [Text/Code/Other]
- **Output Format**: [Audio/Code/Embeddings/Other]
- **Quality Levels**: [Available quality options]
- **Customization**: [Available customization options]

### **Specific Features**
- [ ] Feature 1
- [ ] Feature 2
- [ ] Feature 3

### **Use Cases**
- **Primary**: [Main use case]
- **Secondary**: [Additional use cases]
- **Not Recommended**: [What not to use it for]

## ⚙️ **TECHNICAL SPECIFICATIONS**

### **Input/Output Specifications**
```yaml
Input:
  Format: [Format details]
  Max Size: X [units]
  Supported Types: [List]

Output:
  Format: [Format details]
  Quality: [Quality specifications]
  Size Range: X-Y [units]
```

### **Performance Characteristics**
- **Processing Time**: X-Y seconds per [unit]
- **Throughput**: X [units] per minute
- **Accuracy**: X% (if applicable)
- **Latency**: X ms typical

## 🔧 **CONFIGURATION & USAGE**

### **Basic Usage**
```python
# Model-specific implementation example
```

### **Advanced Configuration**
```python
# Advanced usage patterns
```

### **Integration Patterns**
```python
# How to integrate with other systems
```

## 🚦 **RATE LIMITS & PRICING**

### **Usage Limits**
- **Requests per minute**: X
- **[Units] per day**: X
- **Concurrent requests**: X

### **Pricing Structure**
- **Base cost**: $X per [unit]
- **Volume discounts**: [Discount structure]
- **Additional features**: [Extra costs]

## 📈 **OPTIMIZATION GUIDELINES**

### **Performance Tips**
- [Specific optimization advice]
- [Best practices for this model type]
- [Common pitfalls to avoid]

### **Quality Optimization**
- [How to improve output quality]
- [Parameter tuning guidelines]
- [Input preprocessing recommendations]

---
**Last Updated**: YYYY-MM-DD
**Reviewed By**: [Name]
**Next Review**: YYYY-MM-DD
```

## 🔍 **PADRÕES DE CLASSIFICAÇÃO E CATEGORIZAÇÃO**

### **📊 Matriz de Classificação de Modelos**

#### **Por Tipo de Funcionalidade**
```yaml
Real-time Models:
  - Live conversation
  - Streaming audio/video
  - Real-time function calling
  - Interruption handling

Completion Models:
  - Text generation
  - Code completion
  - Question answering
  - Summarization

Specialized Models:
  - Text-to-Speech (TTS)
  - Fill-in-Middle (FIM)
  - Embeddings
  - Moderation
  - Image generation
  - Audio transcription

Experimental Models:
  - Research previews
  - Beta features
  - Unstable APIs
```

#### **Por Nível de Estabilidade**
```yaml
Production Ready:
  - Stable API
  - SLA guarantees
  - Full documentation
  - Long-term support

Preview/Beta:
  - Feature complete
  - May have breaking changes
  - Limited SLA
  - Active development

Experimental:
  - Research quality
  - No stability guarantees
  - Frequent changes
  - Limited support
```

#### **Por Capacidades Técnicas**
```yaml
Multimodal:
  - Text + Image
  - Text + Audio
  - Text + Video
  - All modalities

Function Calling:
  - Basic functions
  - Parallel calling
  - Streaming functions
  - Complex workflows

Context Handling:
  - Short context (< 8K)
  - Medium context (8K-32K)
  - Long context (32K-128K)
  - Extended context (> 128K)
```

## 📋 **PROCESSO DE DOCUMENTAÇÃO OBRIGATÓRIO**

### **🔄 Workflow de Criação de Especificações**

#### **Etapa 1: Pesquisa e Coleta**
1. **Documentação Oficial**: Consultar docs oficiais do provider
2. **API Reference**: Analisar endpoints e parâmetros
3. **Release Notes**: Verificar mudanças e novidades
4. **Community Feedback**: Revisar feedback da comunidade
5. **Benchmarks**: Coletar dados de performance

#### **Etapa 2: Estruturação**
1. **Escolher Template**: Selecionar template apropriado
2. **Preencher Seções**: Completar todas as seções obrigatórias
3. **Exemplos Práticos**: Criar exemplos funcionais
4. **Testes de Código**: Validar todos os exemplos
5. **Review Técnico**: Revisão por especialista

#### **Etapa 3: Validação e Publicação**
1. **Teste de Integração**: Testar com aplicações reais
2. **Review de Qualidade**: Verificar completude e precisão
3. **Aprovação Final**: Aprovação por tech lead
4. **Publicação**: Adicionar ao repositório
5. **Notificação**: Comunicar à equipe

### **📊 Checklist de Qualidade Obrigatório**

#### **✅ Completude Técnica**
- [ ] Todas as seções do template preenchidas
- [ ] Especificações técnicas detalhadas
- [ ] Limites e quotas documentados
- [ ] Exemplos de código funcionais
- [ ] Padrões de erro documentados

#### **✅ Precisão e Atualidade**
- [ ] Informações verificadas com fonte oficial
- [ ] Versão do modelo especificada
- [ ] Data de última atualização
- [ ] Links para documentação oficial
- [ ] Status de estabilidade correto

#### **✅ Usabilidade**
- [ ] Exemplos práticos incluídos
- [ ] Casos de uso claramente definidos
- [ ] Padrões de implementação
- [ ] Troubleshooting guide
- [ ] Performance guidelines

#### **✅ Manutenibilidade**
- [ ] Estrutura consistente com template
- [ ] Metadados de revisão incluídos
- [ ] Histórico de versões
- [ ] Responsável pela manutenção definido
- [ ] Cronograma de revisão estabelecido

## 🚦 **SISTEMA DE RATE LIMITS E MONITORAMENTO**

### **📊 Estrutura Padrão de Rate Limits**
```yaml
Rate Limit Categories:
  Requests:
    - per_minute: X
    - per_hour: X
    - per_day: X
    - burst_capacity: X
  
  Tokens:
    - input_per_minute: X
    - output_per_minute: X
    - total_per_day: X
  
  Data:
    - audio_mb_per_minute: X
    - image_count_per_hour: X
    - file_size_limit_mb: X
  
  Concurrent:
    - max_connections: X
    - max_sessions: X
    - max_streams: X

Quota Management:
  - quota_reset_time: "daily/hourly"
  - quota_monitoring: "enabled/disabled"
  - quota_alerts: "threshold_percentage"
  - quota_enforcement: "hard/soft"
```

### **🔍 Monitoramento de Uso**
```python
# Template de monitoramento de rate limits
class ModelUsageMonitor:
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.usage_metrics = {
            'requests_count': 0,
            'tokens_consumed': 0,
            'errors_count': 0,
            'rate_limit_hits': 0
        }
    
    def record_request(self, tokens_used: int):
        self.usage_metrics['requests_count'] += 1
        self.usage_metrics['tokens_consumed'] += tokens_used
    
    def record_rate_limit_hit(self):
        self.usage_metrics['rate_limit_hits'] += 1
    
    def get_usage_report(self) -> dict:
        return {
            'model': self.model_name,
            'metrics': self.usage_metrics,
            'efficiency': self._calculate_efficiency()
        }
```

## 📚 **RECURSOS COMPARTILHADOS OBRIGATÓRIOS**

### **🔗 Authentication Patterns**
```markdown
# Authentication Patterns Reference

## Google/Gemini Authentication
- API Key authentication
- Service Account authentication
- OAuth 2.0 flow
- Environment variable patterns

## Mistral Authentication
- API Key authentication
- Bearer token patterns
- Rate limit headers
- Error response formats
```

### **💰 Pricing Reference**
```markdown
# Pricing Reference - All Models

## Google/Gemini Pricing
| Model | Input (per 1M tokens) | Output (per 1M tokens) | Special |
|-------|----------------------|------------------------|---------|
| gemini-2.5-flash | $0.075 | $0.30 | - |
| gemini-2.5-pro | $1.25 | $5.00 | - |
| gemini-live | $0.075 | $0.30 | +$0.40/min audio |

## Mistral Pricing
| Model | Input (per 1M tokens) | Output (per 1M tokens) | Special |
|-------|----------------------|------------------------|---------|
| mistral-large | $2.00 | $6.00 | - |
| mistral-small | $0.20 | $0.60 | - |
| codestral | $0.20 | $0.60 | - |
```

### **⚠️ Error Codes Reference**
```markdown
# Error Codes Reference - All Providers

## HTTP Status Codes
- 400: Bad Request
- 401: Unauthorized
- 403: Forbidden
- 429: Too Many Requests
- 500: Internal Server Error

## Provider-Specific Errors
### Google/Gemini
- INVALID_ARGUMENT
- PERMISSION_DENIED
- RESOURCE_EXHAUSTED
- INTERNAL

### Mistral
- invalid_request_error
- authentication_error
- rate_limit_error
- api_error
```

## 🔄 **PROCESSO DE MANUTENÇÃO E ATUALIZAÇÃO**

### **📅 Cronograma de Revisão**
```yaml
Revisão Mensal:
  - Verificar novos modelos lançados
  - Atualizar pricing information
  - Revisar rate limits
  - Validar exemplos de código

Revisão Trimestral:
  - Review completo de todas as specs
  - Benchmark de performance
  - Atualização de templates
  - Feedback da comunidade

Revisão Anual:
  - Reestruturação da organização
  - Migração de modelos deprecated
  - Atualização de padrões
  - Planejamento estratégico
```

### **🚨 Triggers de Atualização Imediata**
- Lançamento de novo modelo
- Breaking changes em APIs
- Mudanças significativas em pricing
- Problemas de segurança
- Deprecation notices

### **👥 Responsabilidades**
```yaml
Tech Lead:
  - Aprovação de novas specs
  - Review de mudanças críticas
  - Definição de padrões
  - Planejamento estratégico

Senior Developers:
  - Criação de specs detalhadas
  - Validação técnica
  - Exemplos de código
  - Troubleshooting guides

DevOps/SRE:
  - Monitoramento de rate limits
  - Performance benchmarks
  - Alertas e notificações
  - Automação de processos
```

## 🎯 **MÉTRICAS DE SUCESSO**

### **📊 KPIs de Qualidade da Documentação**
- **Completude**: 100% das seções obrigatórias preenchidas
- **Precisão**: 0 erros em exemplos de código
- **Atualidade**: Máximo 30 dias desde última revisão
- **Usabilidade**: Feedback positivo > 90%
- **Cobertura**: 100% dos modelos em produção documentados

### **⚡ KPIs de Performance**
- **Time to Documentation**: < 5 dias para novos modelos
- **Update Frequency**: Revisão mensal mínima
- **Error Resolution**: < 24h para correção de erros críticos
- **Community Contribution**: > 20% de specs com contribuição externa

---

## 🏆 **CONCLUSÃO E IMPLEMENTAÇÃO**

Esta steering rule estabelece o **padrão definitivo** para documentação de modelos de IA, garantindo:

### **✅ Benefícios Imediatos**
- **Consistência**: Todas as specs seguem o mesmo padrão
- **Completude**: Informações técnicas detalhadas e precisas
- **Usabilidade**: Exemplos práticos e guias de implementação
- **Manutenibilidade**: Processo estruturado de atualização

### **🚀 Próximos Passos**
1. **Implementar estrutura de diretórios**
2. **Criar primeiras specs usando templates**
3. **Estabelecer processo de revisão**
4. **Configurar monitoramento automático**
5. **Treinar equipe nos novos padrões**

### **📞 Lembre-se**
- 📁 **Estrutura obrigatória**: Seguir hierarquia definida
- 📋 **Templates completos**: Usar templates apropriados
- ✅ **Checklist de qualidade**: Validar todas as specs
- 🔄 **Manutenção contínua**: Processo de atualização ativo
- 📊 **Métricas de sucesso**: Monitorar KPIs definidos

---

**🎯 STEERING RULE 01 - Onde especificações técnicas encontram excelência operacional.**