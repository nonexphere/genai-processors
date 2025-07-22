# Current Project Setup - Live Configuration

## 🎯 **CONFIGURAÇÃO ATUAL EM PRODUÇÃO**

Este arquivo documenta exatamente como o projeto está configurado **AGORA**, incluindo todas as keys, limitações do Free Tier e estratégias em uso.

---

## 🔑 **GESTÃO DE API KEYS ATUAL**

### **🔵 Google/Gemini Keys**
```yaml
Current Status: "Active - Free Tier"
Key Count: 3
Naming Pattern: 
  - GEMINI_API_KEY_1 (Primary)
  - GEMINI_API_KEY_2 (Secondary) 
  - GEMINI_API_KEY_3 (Backup)

Rotation Strategy: "Round Robin on Rate Limit"
Current Implementation: "Manual in leonidas.py"
Monitoring: "Basic logging"

Free Tier Limits Per Key:
  Live API:
    - 60 requests/minute
    - 1000 audio minutes/day
    - 1 concurrent session
  
  Completion API:
    - 15 requests/minute
    - 1500 requests/day
    - 32K tokens/minute
  
  Flash Lite:
    - 1000 requests/minute
    - 50K requests/day
```

### **🟠 Mistral Keys**
```yaml
Current Status: "Active - Free Tier"
Key Count: 2
Naming Pattern:
  - MISTRAL_API_KEY_1 (Primary)
  - MISTRAL_API_KEY_2 (Backup)

Rotation Strategy: "Manual switching"
Current Implementation: "Not implemented yet"
Usage: "Experimental/Testing only"

Free Tier Limits Per Key:
  All Models:
    - 1000 requests/month
    - 32K tokens/request
    - No concurrent limit specified
```

---

## 🎛️ **CONFIGURAÇÕES ATIVAS NO LEONIDAS**

### **📍 Localização das Configurações**
```python
# File: leonidas/leonidas.py
# Lines: 45-85 (aproximadamente)

CURRENT_LIVE_MODEL = "gemini-live-2.5-flash-preview"
CURRENT_EVENT_MODEL = "gemini-2.5-flash-lite-preview-06-17"
CURRENT_VOICE = "Kore"
CURRENT_LANGUAGE = "pt-BR"
```

### **🎙️ Live API Configuration (Em Uso)**
```python
# Configuração atual no leonidas.py
config = types.LiveConnectConfig(
    response_modalities=["AUDIO"],
    system_instruction=LEONIDAS_SYSTEM_PROMPT,  # ~500 tokens
    speech_config={
        'language_code': 'pt-BR',
        'voice_config': {
            'prebuilt_voice_config': {
                'voice_name': 'Kore'
            }
        }
    },
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
    ),
    generation_config=types.GenerationConfig(
        media_resolution=types.MediaResolution.MEDIA_RESOLUTION_MEDIUM
    ),
    tools=LEONIDAS_TOOLS  # 5 ferramentas definidas
)
```

### **👁️ Event Detection Configuration (Em Uso)**
```python
# Configuração atual para detecção de eventos
event_config = genai_types.GenerateContentConfig(
    system_instruction="Detect events in video feed",
    max_output_tokens=10,
    response_mime_type='text/x.enum',
    response_schema=EventTypes,
    media_resolution=genai_types.MediaResolution.MEDIA_RESOLUTION_LOW
)
```

---

## 📊 **USAGE PATTERNS ATUAIS**

### **📈 Uso Diário Típico - ATUALIZADO JULHO 2025**
```yaml
Leonidas Development Sessions:
  duration_per_session: "30-60 minutes"
  sessions_per_day: "3-5"
  total_daily_audio: "2-4 hours"
  
Live API Usage - MELHORIAS SIGNIFICATIVAS:
  tokens_per_minute: "1,000,000 (vs anterior indefinido)"
  concurrent_sessions: "3 (vs anterior 1)"
  context_window: "1,048,576 tokens (vs anterior 32K)"
  new_capabilities: "PDF support, Code Execution, Affective Dialog"

Event Detection - CAPACIDADES EXPANDIDAS:
  requests_per_minute: "15 (vs anterior 1000 mas contexto 31x maior)"
  requests_per_day: "1000 (vs anterior 50K mas capacidades expandidas)"
  context_window: "1,000,000 tokens (vs anterior 32K)"
  new_capabilities: "Function calling, Code Execution, URL context"

Text Completion - LIMITES MASSIVAMENTE AUMENTADOS:
  gemini_2_5_pro_tpm: "250,000 (vs anterior 32K)"
  gemini_2_5_flash_tpm: "250,000 (vs anterior 1M mas mais estável)"
  gemini_2_5_flash_lite_tpm: "250,000 (novo limite)"
  max_output_tokens: "65,536 (vs anterior 8K)"
```

### **🚦 Rate Limit Encounters - SITUAÇÃO MELHORADA**
```yaml
Frequency: "Drasticamente reduzida devido aos novos limites TPM"
Primary Cause: "TPM limits agora muito mais generosos"
Current Handling: "Manual key switching (menos necessário)"
Downtime: "Significativamente reduzido"

IMPACTO POSITIVO:
  - TPM aumentou 8x-31x dependendo do modelo
  - Contexto expandido permite análises mais complexas
  - Menos interrupções no desenvolvimento
  - Capacidades expandidas (PDF, Code Execution, etc.)

Most Common Limits Hit:
  1. "60 requests/minute on Live API"
  2. "1000 requests/minute on Flash Lite"
  3. "15 requests/minute on Completion API"

Recovery Strategy:
  1. "Switch to next key manually"
  2. "Wait for rate limit reset"
  3. "Continue development"
```

---

## 🔧 **IMPLEMENTAÇÃO ATUAL DE KEY ROTATION**

### **📝 Código Atual (Simplificado)**
```python
# Em leonidas.py - implementação atual
class SimpleKeyManager:
    def __init__(self):
        self.gemini_keys = [
            os.getenv('GEMINI_API_KEY_1'),
            os.getenv('GEMINI_API_KEY_2'), 
            os.getenv('GEMINI_API_KEY_3')
        ]
        self.current_index = 0
    
    def get_current_key(self):
        return self.gemini_keys[self.current_index]
    
    def rotate_key(self):
        self.current_index = (self.current_index + 1) % len(self.gemini_keys)
        print(f"Rotated to key {self.current_index + 1}")
        return self.get_current_key()

# Uso atual - manual quando rate limit
try:
    response = await session.send_realtime_input(audio_data)
except RateLimitError:
    key_manager.rotate_key()
    # Reiniciar sessão com nova key
```

### **🚨 Limitações da Implementação Atual**
- **Manual**: Requer intervenção quando rate limit
- **Sem persistência**: Não lembra qual key estava usando
- **Sem monitoramento**: Não rastreia uso por key
- **Sem prevenção**: Não previne rate limits
- **Sem fallback**: Não tenta outras keys automaticamente

---

## 💾 **ENVIRONMENT VARIABLES ATUAIS**

### **📋 Variáveis Obrigatórias**
```bash
# Google/Gemini Keys
export GEMINI_API_KEY_1="AIza..."  # Primary key
export GEMINI_API_KEY_2="AIza..."  # Secondary key  
export GEMINI_API_KEY_3="AIza..."  # Backup key

# Mistral Keys (experimental)
export MISTRAL_API_KEY_1="..."     # Primary key
export MISTRAL_API_KEY_2="..."     # Backup key

# Project Configuration
export LEONIDAS_ENV="development"
export LEONIDAS_LOG_LEVEL="INFO"
export LEONIDAS_AUDIO_DEVICE="default"
```

### **🔍 Verificação de Keys**
```python
# Script para verificar keys válidas
def verify_keys():
    gemini_keys = [
        os.getenv('GEMINI_API_KEY_1'),
        os.getenv('GEMINI_API_KEY_2'),
        os.getenv('GEMINI_API_KEY_3')
    ]
    
    valid_keys = []
    for i, key in enumerate(gemini_keys, 1):
        if key and len(key) > 20:  # Basic validation
            try:
                # Test key with simple request
                client = genai.Client(api_key=key)
                # Make test call
                valid_keys.append(f"Key {i}: Valid")
            except:
                valid_keys.append(f"Key {i}: Invalid")
        else:
            valid_keys.append(f"Key {i}: Missing")
    
    return valid_keys
```

---

## 📊 **MONITORAMENTO ATUAL**

### **📈 Logs Disponíveis**
```yaml
Location: "logs/"
Format: "JSON structured logs"
Retention: "30 days"

Current Log Files:
  - leonidas-session-YYYY-MM-DD.json
  - performance-metrics-YYYY-MM-DD.json
  - error-log-YYYY-MM-DD.json

Log Content:
  - Session start/end times
  - Model responses and latencies
  - Function calls and results
  - Error messages and stack traces
  - Basic usage statistics
```

### **📊 Métricas Coletadas**
```python
# Métricas atualmente coletadas
current_metrics = {
    "session_duration": "seconds",
    "audio_chunks_sent": "count",
    "audio_chunks_received": "count", 
    "function_calls": "count",
    "interruptions": "count",
    "errors": "count",
    "model_switches": "count"
}

# Métricas NÃO coletadas (mas necessárias)
missing_metrics = {
    "api_key_usage": "per key statistics",
    "rate_limit_hits": "frequency and timing",
    "cost_tracking": "estimated costs",
    "model_performance": "latency by model",
    "usage_patterns": "time-based analysis"
}
```

---

## 🎯 **PROBLEMAS IDENTIFICADOS**

### **🚨 Issues Críticos**
1. **Key Rotation Manual**: Interrompe desenvolvimento
2. **Sem Monitoramento de Quota**: Não sabemos quanto usamos
3. **Sem Prevenção de Rate Limit**: Sempre reagimos, nunca prevenimos
4. **Sem Backup Strategy**: Se todas as keys falharem
5. **Sem Cost Tracking**: Não sabemos quando migrar para paid

### **⚠️ Issues Menores**
1. **Logs não estruturados**: Difícil análise
2. **Sem dashboard**: Visibilidade limitada
3. **Configuração hardcoded**: Difícil ajustar
4. **Sem A/B testing**: Não comparamos modelos
5. **Sem alertas**: Descobrimos problemas tarde

---

## 🔄 **PRÓXIMAS MELHORIAS PLANEJADAS**

### **📅 Curto Prazo (Esta Semana)**
- [ ] **Automatic Key Rotation**: Implementar rotação automática
- [ ] **Usage Monitoring**: Rastrear uso por key
- [ ] **Rate Limit Prevention**: Detectar aproximação do limite
- [ ] **Better Error Handling**: Recuperação automática

### **📅 Médio Prazo (Próximas 2 Semanas)**
- [ ] **Usage Dashboard**: Interface para monitoramento
- [ ] **Cost Tracking**: Estimativa de custos
- [ ] **Performance Benchmarks**: Comparação de modelos
- [ ] **Alert System**: Notificações de problemas

### **📅 Longo Prazo (Próximo Mês)**
- [ ] **Paid Tier Migration**: Estratégia de upgrade
- [ ] **Multi-Provider Load Balancing**: Gemini + Mistral
- [ ] **Advanced Caching**: Reduzir uso de API
- [ ] **Custom Monitoring**: Métricas específicas do projeto

---

## 🛠️ **COMANDOS ÚTEIS**

### **🔍 Verificar Status Atual**
```bash
# Verificar keys configuradas
env | grep -E "(GEMINI|MISTRAL)_API_KEY"

# Verificar logs recentes
ls -la logs/ | head -10

# Verificar uso de disco dos logs
du -sh logs/

# Verificar processo Leonidas ativo
ps aux | grep leonidas
```

### **🚀 Iniciar Leonidas**
```bash
# Desenvolvimento
cd leonidas/
python leonidas_cli.py --mode development --verbose

# Com key específica
GEMINI_API_KEY_1="your_key" python leonidas_cli.py

# Com logging detalhado
python leonidas_cli.py --log-level DEBUG
```

### **📊 Análise de Logs**
```bash
# Contar sessões hoje
grep "session_start" logs/leonidas-session-$(date +%Y-%m-%d).json | wc -l

# Ver últimos erros
tail -20 logs/error-log-$(date +%Y-%m-%d).json

# Análise de performance
grep "ttft" logs/performance-metrics-$(date +%Y-%m-%d).json | tail -10
```

---

## 📞 **CONTATOS E SUPORTE**

### **🆘 Em Caso de Problemas**
1. **Rate Limit**: Aguardar reset ou usar próxima key
2. **Key Inválida**: Verificar environment variables
3. **Modelo Indisponível**: Usar fallback model
4. **Erro de Conexão**: Verificar internet e firewall
5. **Problema Desconhecido**: Verificar logs em `logs/`

### **📚 Documentação de Referência**
- **Leonidas README**: `leonidas/README.md`
- **API Gemini**: [ai.google.dev](https://ai.google.dev)
- **API Mistral**: [docs.mistral.ai](https://docs.mistral.ai)
- **Steering Rules**: `.kiro/steering/`

---

**⚙️ CURRENT SETUP - Retrato fiel da configuração atual**

*Última atualização: 2025-01-22*
*Próxima revisão: Semanal (toda segunda-feira)*