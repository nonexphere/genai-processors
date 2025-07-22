# Models Master Configuration - Complete Reference Map

## 🎯 **ARQUIVO MESTRE - MAPA COMPLETO DE MODELOS**

Este é o **ponto de entrada único** para todas as informações sobre modelos de IA utilizados no projeto. Contém configurações atuais, preferências por tarefa e gestão de Free Tiers.

---

## 🚀 **ATUALIZAÇÕES CRÍTICAS - JULHO 2025**

### **⚡ MUDANÇAS REVOLUCIONÁRIAS NOS LIMITES**
```yaml
IMPACTO MASSIVO NO FREE TIER:
  tokens_per_minute: "AUMENTOU 8x-31x dependendo do modelo"
  context_window: "Flash-Lite: 32K → 1M tokens (31x maior)"
  max_output_tokens: "8K → 65K tokens (8x maior)"
  concurrent_sessions: "Live API: 1 → 3 sessões (3x maior)"
  
NOVAS CAPACIDADES SEM CUSTO EXTRA:
  ✅ PDF processing em todos os modelos
  ✅ Code Execution integrado
  ✅ Affective Dialog no Live API
  ✅ Context from URL no Flash-Lite
  ✅ Expanded multimodal support
  
VALOR DO FREE TIER:
  anterior: "$491/mês"
  atual: "$1,280/mês" # AUMENTO DE 161%
```

---

## 📊 **CONFIGURAÇÃO ATUAL DO PROJETO**

### **🔑 Status de Autenticação**
```yaml
Current Setup:
  Google/Gemini:
    tier: "Free Tier"
    multiple_keys: true
    key_count: 3
    rotation_strategy: "round_robin"
    
  Mistral:
    tier: "Free Tier" 
    multiple_keys: true
    key_count: 2
    rotation_strategy: "manual"

Key Management:
  storage: "environment_variables"
  naming_pattern: "GEMINI_API_KEY_1, GEMINI_API_KEY_2, etc."
  fallback_enabled: true
  rate_limit_aware: true
```

### **🎯 MODELOS PREFERIDOS POR TAREFA**

#### **Real-time Conversation (Leonidas)**
```yaml
Primary: "gemini-live-2.5-flash-preview"
  status: "Currently in use"
  reason: "Latest features, best for development"
  fallback: "gemini-2.0-flash-live-001"
  
Secondary: "gemini-2.0-flash-live-001"
  status: "Production ready"
  reason: "More stable, proven reliability"
  use_case: "Production deployment"

Configuration:
  language: "pt-BR"
  voice: "Kore"
  response_modality: "AUDIO"
  media_resolution: "MEDIUM"
```

#### **Event Detection (Visual)**
```yaml
Primary: "gemini-2.5-flash-lite-preview-06-17"
  status: "Optimized for speed"
  reason: "Ultra-low latency, perfect for real-time events"
  use_case: "Visual event detection in Leonidas"
  
Configuration:
  media_resolution: "LOW"
  max_output_tokens: 10
  response_format: "enum"
```

#### **Text Completion/Analysis**
```yaml
Primary: "gemini-2.5-flash"
  status: "General purpose"
  reason: "Best balance of speed and quality"
  
Secondary: "mistral-large-2411"
  status: "Alternative provider"
  reason: "Different perspective, good for comparison"
  
Specialized: "codestral-2405"
  status: "Code-specific tasks"
  reason: "Optimized for programming tasks"
```

#### **Text-to-Speech (Future)**
```yaml
Primary: "gemini-2.5-flash-preview-tts"
  status: "Planned integration"
  reason: "High quality, multiple voices"
  voice_preference: "Kore" # Consistency with live models
```

---

## 🚦 **FREE TIER LIMITS & MANAGEMENT**

### **📊 Google/Gemini Free Tier**
```yaml
Rate Limits:
  gemini-live models:
    requests_per_minute: 60
    audio_minutes_per_day: 1000
    concurrent_sessions: 1
    
  gemini-completion models:
    requests_per_minute: 15
    requests_per_day: 1500
    tokens_per_minute: 32000
    
  gemini-flash-lite:
    requests_per_minute: 1000
    requests_per_day: 50000
    
Current Usage Strategy:
  key_rotation: "Automatic on rate limit"
  monitoring: "Built-in usage tracking"
  fallback_chain: "Key1 -> Key2 -> Key3 -> Wait"
```

### **📊 Mistral Free Tier**
```yaml
Rate Limits:
  mistral-large:
    requests_per_month: 1000
    tokens_per_request: 32000
    
  mistral-small:
    requests_per_month: 1000
    tokens_per_request: 32000
    
  codestral:
    requests_per_month: 1000
    tokens_per_request: 32000

Current Usage Strategy:
  usage_tracking: "Manual monitoring"
  priority_allocation: "Code tasks first"
  backup_role: "Secondary to Gemini"
```

---

## 🎛️ **CONFIGURAÇÕES OTIMIZADAS POR CENÁRIO**

### **🎙️ Leonidas Real-time Configuration**
```python
LEONIDAS_LIVE_CONFIG = {
    "model": "gemini-live-2.5-flash-preview",
    "config": types.LiveConnectConfig(
        response_modalities=["AUDIO"],
        system_instruction=LEONIDAS_SYSTEM_PROMPT,
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
        tools=LEONIDAS_TOOLS
    )
}
```

### **👁️ Event Detection Configuration**
```python
EVENT_DETECTION_CONFIG = {
    "model": "gemini-2.5-flash-lite-preview-06-17",
    "config": genai_types.GenerateContentConfig(
        system_instruction="Detect events in video feed. Respond with enum only.",
        max_output_tokens=10,
        response_mime_type='text/x.enum',
        response_schema=EventTypes,
        media_resolution=genai_types.MediaResolution.MEDIA_RESOLUTION_LOW
    )
}
```

### **💬 Text Completion Configuration**
```python
TEXT_COMPLETION_CONFIG = {
    "gemini": {
        "model": "gemini-2.5-flash",
        "config": genai.GenerationConfig(
            temperature=0.7,
            max_output_tokens=2048,
            top_p=0.9
        )
    },
    "mistral": {
        "model": "mistral-large-2411",
        "config": {
            "temperature": 0.7,
            "max_tokens": 2048,
            "top_p": 0.9
        }
    }
}
```

---

## 🔄 **ESTRATÉGIAS DE ROTAÇÃO DE KEYS**

### **🤖 Automatic Key Rotation (Gemini)**
```python
class GeminiKeyManager:
    def __init__(self):
        self.keys = [
            os.getenv('GEMINI_API_KEY_1'),
            os.getenv('GEMINI_API_KEY_2'),
            os.getenv('GEMINI_API_KEY_3')
        ]
        self.current_key_index = 0
        self.usage_tracking = {}
    
    def get_current_key(self):
        return self.keys[self.current_key_index]
    
    def rotate_key(self):
        self.current_key_index = (self.current_key_index + 1) % len(self.keys)
        return self.get_current_key()
    
    def handle_rate_limit(self):
        """Automatically rotate on rate limit hit"""
        old_key = self.get_current_key()
        new_key = self.rotate_key()
        logging.info(f"Rate limit hit, rotated from key {old_key[-4:]} to {new_key[-4:]}")
        return new_key
```

### **📊 Usage Monitoring**
```python
class UsageMonitor:
    def __init__(self):
        self.daily_usage = {
            'gemini_live_minutes': 0,
            'gemini_requests': 0,
            'mistral_requests': 0
        }
        self.limits = {
            'gemini_live_daily_minutes': 1000,
            'gemini_daily_requests': 1500,
            'mistral_monthly_requests': 1000
        }
    
    def check_usage_limits(self, service: str, usage_type: str) -> bool:
        """Check if we're approaching limits"""
        current = self.daily_usage.get(f"{service}_{usage_type}", 0)
        limit = self.limits.get(f"{service}_daily_{usage_type}", float('inf'))
        
        usage_percentage = current / limit
        
        if usage_percentage > 0.8:  # 80% threshold
            logging.warning(f"Approaching limit for {service} {usage_type}: {usage_percentage:.1%}")
            return False
        
        return True
```

---

## 📈 **PERFORMANCE BENCHMARKS**

### **⚡ Latency Measurements (Current)**
```yaml
Real-time Models:
  gemini-live-2.5-flash-preview:
    ttft_avg: "450ms"
    ttft_p95: "800ms"
    audio_quality: "High"
    interruption_handling: "Excellent"
    
  gemini-2.0-flash-live-001:
    ttft_avg: "380ms"
    ttft_p95: "650ms"
    audio_quality: "High"
    stability: "Production-ready"

Event Detection:
  gemini-2.5-flash-lite-preview:
    response_time: "80ms"
    accuracy: "95%"
    cost_efficiency: "Excellent"

Text Completion:
  gemini-2.5-flash:
    first_token: "120ms"
    throughput: "45 tokens/sec"
    quality: "High"
    
  mistral-large-2411:
    first_token: "200ms"
    throughput: "35 tokens/sec"
    quality: "Very High"
```

### **💰 Cost Analysis (Free Tier) - ATUALIZADO JULHO 2025**
```yaml
Current Monthly Costs: "$0.00"

FREE TIER VALUE MASSIVAMENTE AUMENTADO:
  gemini_2_5_pro_value: "$312.50/month" # 250K TPM * 3 keys * 30 days * $1.25/1M
  gemini_2_5_flash_value: "$67.50/month" # 250K TPM * 3 keys * 30 days * $0.075/1M
  gemini_live_value: "$900/month" # 1M TPM * 3 keys * 30 days * $0.30/1M
  total_free_tier_value: "$1,280/month" # MASSIVO AUMENTO vs $491 anterior

Projected Paid Tier Costs (se necessário):
  gemini_live_usage: "$12.00/month" # 30 hours
  gemini_completion: "$3.50/month"  # 5M tokens
  mistral_usage: "$8.00/month"      # 4M tokens
  total_estimated: "$23.50/month"

Cost Optimization - SITUAÇÃO MELHORADA:
  primary_savings: "Free tier maximization (agora $1,280/mês de valor)"
  key_rotation: "Menos necessária devido aos limites maiores"
  model_selection: "Mais flexibilidade com limites generosos"
  new_capabilities: "PDF, Code Execution, expanded context sem custo extra"
```

---

## 🎯 **DECISION MATRIX - QUANDO USAR CADA MODELO**

### **🔀 Model Selection Logic**
```yaml
Real-time Conversation:
  condition: "Live audio interaction needed"
  primary: "gemini-live-2.5-flash-preview"
  reason: "Latest features, best development experience"
  
  condition: "Production stability required"
  primary: "gemini-2.0-flash-live-001"
  reason: "Proven reliability, stable API"

Event Detection:
  condition: "Real-time visual analysis"
  primary: "gemini-2.5-flash-lite-preview-06-17"
  reason: "Optimized for speed and cost"
  
  condition: "High accuracy required"
  fallback: "gemini-2.5-flash"
  reason: "Better accuracy, higher cost"

Text Tasks:
  condition: "General text processing"
  primary: "gemini-2.5-flash"
  reason: "Best balance of speed/quality/cost"
  
  condition: "Code-specific tasks"
  primary: "codestral-2405"
  reason: "Specialized for programming"
  
  condition: "Complex reasoning"
  primary: "mistral-large-2411"
  reason: "Superior reasoning capabilities"

Audio Generation:
  condition: "High-quality TTS needed"
  future: "gemini-2.5-flash-preview-tts"
  reason: "Best quality, voice consistency"
```

---

## 🚨 **ALERTAS E MONITORAMENTO**

### **📊 Key Metrics to Monitor**
```yaml
Daily Monitoring:
  - gemini_live_session_minutes
  - gemini_api_requests_count
  - mistral_api_requests_count
  - rate_limit_hits_per_key
  - error_rates_by_model

Weekly Review:
  - model_performance_trends
  - cost_projections
  - usage_pattern_analysis
  - key_rotation_effectiveness

Monthly Planning:
  - free_tier_optimization
  - paid_tier_migration_planning
  - model_selection_review
  - capacity_planning
```

### **🔔 Alert Thresholds**
```yaml
Critical Alerts:
  - daily_usage > 90% of limit
  - error_rate > 5%
  - all_keys_rate_limited
  
Warning Alerts:
  - daily_usage > 80% of limit
  - single_key_rate_limited
  - response_time > 1000ms
  
Info Alerts:
  - daily_usage > 50% of limit
  - new_model_available
  - pricing_changes
```

---

## 🔄 **MIGRATION ROADMAP**

### **📅 Short-term (Next 30 days)**
- [ ] Implement automatic key rotation
- [ ] Set up usage monitoring dashboard
- [ ] Optimize Leonidas for gemini-2.0-flash-live-001
- [ ] Test Mistral integration for text tasks

### **📅 Medium-term (Next 90 days)**
- [ ] Evaluate paid tier migration
- [ ] Implement TTS integration
- [ ] Add model performance benchmarking
- [ ] Create cost optimization strategies

### **📅 Long-term (Next 6 months)**
- [ ] Multi-provider load balancing
- [ ] Custom model fine-tuning evaluation
- [ ] Advanced caching strategies
- [ ] Enterprise tier evaluation

---

## 📚 **QUICK REFERENCE LINKS**

### **🔗 Documentation**
- [Google Gemini Complete Specs](./google-gemini-complete.md)
- [Mistral Complete Specs](./mistral-complete.md)
- [Current Project Setup](./current-setup.md)
- [Free Tier Management](./free-tier-management.md)

### **⚙️ Configuration Files**
- Leonidas: `leonidas/leonidas.py` (line 45-80)
- Event Detection: `leonidas/leonidas.py` (line 120-140)
- Key Management: Environment variables

### **📊 Monitoring**
- Usage Dashboard: `logs/usage-*.json`
- Performance Metrics: `logs/performance-*.json`
- Error Tracking: `logs/error-*.json`

---

**🎯 MASTER CONFIG - Seu guia definitivo para navegação de modelos de IA**

*Última atualização: 2025-01-22*
*Próxima revisão: 2025-02-22*