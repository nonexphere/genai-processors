# Mistral Models - Complete Specification

## 🟠 **MISTRAL AI MODELS - ESPECIFICAÇÃO COMPLETA**

Este arquivo centraliza **todas** as informações sobre modelos Mistral AI, organizadas por categoria e com foco nas necessidades do projeto como alternativa ao Google/Gemini.

---

## 📊 **OVERVIEW GERAL DOS MODELOS MISTRAL**

### **🎯 Categorização por Uso**
```yaml
Completion Models:
  flagship: "mistral-large-2411"
  balanced: "mistral-small-2409"
  code_specialist: "codestral-2405"
  code_mamba: "codestral-mamba-2407"

Specialized Models:
  multimodal: "pixtral-12b-2409"
  embeddings: "mistral-embed"
  moderation: "mistral-moderation"

Experimental Models:
  next_gen: "mistral-next"
  research: "Various experimental models"
```

### **💰 Pricing Overview (Free vs Paid)**
```yaml
Free Tier Limits:
  all_models:
    requests_per_month: 1000
    tokens_per_request: 32000
    concurrent_requests: 1

Paid Tier Pricing:
  mistral_large_2411: "$2.00 input, $6.00 output per 1M tokens"
  mistral_small_2409: "$0.20 input, $0.60 output per 1M tokens"
  codestral_2405: "$0.20 input, $0.60 output per 1M tokens"
  pixtral_12b: "$0.15 input, $0.15 output per 1M tokens"
  mistral_embed: "$0.10 per 1M tokens"
```

---

## 💬 **COMPLETION MODELS**

### **🏆 mistral-large-2411**
```yaml
Model ID: "mistral-large-2411"
Status: "Stable - Flagship Model"
Type: "Text Completion"
Parameters: "~123B (estimated)"
Training Cutoff: "2024-07-XX"
Release Date: "2024-11-XX"
Recommended For: "Complex reasoning, high-quality output"

Core Capabilities:
  ✅ Advanced reasoning and analysis
  ✅ Complex problem solving
  ✅ Multi-language support (100+ languages)
  ✅ Function calling
  ✅ JSON mode
  ✅ Code generation (80+ languages)
  ✅ Long context understanding
  ✅ Mathematical reasoning
  ✅ Creative writing

Technical Specs:
  context_window: "128,000 tokens"
  max_output_tokens: "8,000 tokens"
  typical_latency: "1-4 seconds first token"
  throughput: "15-30 tokens/second"
  languages_supported: "100+"

Free Tier Limits:
  requests_per_month: 1000
  tokens_per_request: 32000
  concurrent_requests: 1

Paid Tier Pricing:
  input: "$2.00 per 1M tokens"
  output: "$6.00 per 1M tokens"

Strengths:
  ✅ Superior reasoning capabilities
  ✅ Excellent multilingual performance
  ✅ Strong mathematical abilities
  ✅ High-quality creative output
  ✅ Reliable function calling

Use Cases for Leonidas:
  primary_use: "Complex analysis and reasoning"
  fallback_for: "When Gemini models unavailable"
  comparison_testing: "A/B testing against Gemini"
```

#### **Configuration for Leonidas**
```python
LEONIDAS_MISTRAL_CONFIG = {
    "model": "mistral-large-2411",
    "temperature": 0.7,
    "max_tokens": 2048,
    "top_p": 0.9,
    "stream": False,
    "safe_prompt": True
}

# Function calling setup
MISTRAL_FUNCTIONS = [
    {
        "type": "function",
        "function": {
            "name": "think",
            "description": "Raciocínio detalhado e verboso sobre o problema",
            "parameters": {
                "type": "object",
                "properties": {
                    "analysis": {"type": "string", "description": "Análise detalhada"},
                    "reasoning": {"type": "string", "description": "Processo de raciocínio"},
                    "plan": {"type": "string", "description": "Plano de ação"}
                },
                "required": ["analysis", "reasoning", "plan"]
            }
        }
    }
]
```

### **⚡ mistral-small-2409**
```yaml
Model ID: "mistral-small-2409"
Status: "Stable - Balanced Performance"
Type: "Text Completion"
Parameters: "~22B (estimated)"
Training Cutoff: "2024-04-XX"
Release Date: "2024-09-XX"
Recommended For: "General purpose, cost-effective"

Core Capabilities:
  ✅ Fast generation
  ✅ Good reasoning quality
  ✅ Multi-language support (50+ languages)
  ✅ Function calling
  ✅ JSON mode
  ✅ Code generation
  ✅ Cost effective

Technical Specs:
  context_window: "128,000 tokens"
  max_output_tokens: "8,000 tokens"
  typical_latency: "500ms-2s first token"
  throughput: "25-50 tokens/second"
  languages_supported: "50+"

Free Tier Limits:
  requests_per_month: 1000
  tokens_per_request: 32000
  concurrent_requests: 1

Paid Tier Pricing:
  input: "$0.20 per 1M tokens"
  output: "$0.60 per 1M tokens"

Strengths:
  ✅ Excellent cost-performance ratio
  ✅ Fast response times
  ✅ Good general capabilities
  ✅ Reliable for most tasks

Use Cases for Leonidas:
  primary_use: "General text processing"
  cost_optimization: "When budget is a concern"
  high_volume: "For frequent API calls"
```

### **💻 codestral-2405**
```yaml
Model ID: "codestral-2405"
Status: "Stable - Code Specialist"
Type: "Code Completion/Generation"
Parameters: "~22B (estimated)"
Training Cutoff: "2024-03-XX"
Release Date: "2024-05-XX"
Recommended For: "Programming tasks, code analysis"

Specialized Capabilities:
  ✅ Code completion
  ✅ Code generation (80+ languages)
  ✅ Code explanation and documentation
  ✅ Bug detection and fixing
  ✅ Code review and optimization
  ✅ Fill-in-the-middle (FIM)
  ✅ Repository-level understanding

Supported Languages:
  primary: ["Python", "JavaScript", "TypeScript", "Java", "C++", "C#", "Go", "Rust"]
  web: ["HTML", "CSS", "React", "Vue", "Angular", "PHP"]
  data: ["SQL", "R", "MATLAB", "Jupyter", "Pandas"]
  systems: ["C", "Assembly", "Shell", "PowerShell"]
  mobile: ["Swift", "Kotlin", "Dart", "Flutter"]
  other: ["Ruby", "Scala", "Haskell", "Lua", "Perl"]

Technical Specs:
  context_window: "32,000 tokens"
  max_output_tokens: "4,000 tokens"
  typical_latency: "300ms-1s first token"
  throughput: "30-60 tokens/second"

Free Tier Limits:
  requests_per_month: 1000
  tokens_per_request: 32000
  concurrent_requests: 1

Paid Tier Pricing:
  input: "$0.20 per 1M tokens"
  output: "$0.60 per 1M tokens"

Integration Potential for Leonidas:
  use_cases: ["Code analysis", "Architecture review", "Bug detection"]
  advantages: ["Specialized for code", "Fast generation", "Cost effective"]
```

#### **Code Analysis Configuration**
```python
CODESTRAL_CONFIG = {
    "model": "codestral-2405",
    "temperature": 0.1,  # Low for consistent code
    "max_tokens": 2048,
    "top_p": 0.95,
    "stream": True,
    "safe_prompt": True
}

# Code analysis prompt template
CODE_ANALYSIS_PROMPT = """
Analise o seguinte código e forneça:
1. Resumo da funcionalidade
2. Possíveis problemas ou bugs
3. Sugestões de melhoria
4. Padrões de design identificados

Código:
{code}
"""
```

### **🐍 codestral-mamba-2407**
```yaml
Model ID: "codestral-mamba-2407"
Status: "Stable - Mamba Architecture"
Type: "Code Completion"
Architecture: "Mamba (State Space Model)"
Release Date: "2024-07-XX"
Recommended For: "Long code sequences, efficient processing"

Unique Features:
  ✅ Mamba architecture (not Transformer)
  ✅ Linear scaling with sequence length
  ✅ Efficient long-context processing
  ✅ Fast inference
  ✅ Memory efficient

Technical Specs:
  context_window: "256,000 tokens" # Much larger than transformer models
  max_output_tokens: "4,000 tokens"
  typical_latency: "200ms-800ms first token"
  throughput: "40-80 tokens/second"
  memory_efficiency: "Superior to transformers"

Advantages:
  ✅ Handles very long code files
  ✅ Fast processing of large contexts
  ✅ Memory efficient
  ✅ Good for repository-level analysis

Use Cases:
  ✅ Large codebase analysis
  ✅ Long file processing
  ✅ Repository understanding
  ✅ Efficient code completion
```

---

## 🎯 **SPECIALIZED MODELS**

### **🖼️ pixtral-12b-2409**
```yaml
Model ID: "pixtral-12b-2409"
Status: "Stable - Multimodal"
Type: "Vision-Language Model"
Parameters: "12B"
Release Date: "2024-09-XX"
Recommended For: "Image analysis, visual understanding"

Core Capabilities:
  ✅ Image understanding and analysis
  ✅ Text generation from images
  ✅ Visual question answering
  ✅ Image description and captioning
  ✅ OCR and text extraction
  ✅ Chart and diagram analysis
  ✅ Multi-image comparison

Supported Image Formats:
  formats: ["JPEG", "PNG", "WebP", "GIF", "BMP"]
  max_resolution: "2048x2048 pixels"
  max_file_size: "20MB"
  max_images_per_request: "5"

Technical Specs:
  context_window: "128,000 tokens"
  max_output_tokens: "8,000 tokens"
  typical_latency: "2-5 seconds first token"
  image_processing_time: "1-3 seconds"

Free Tier Limits:
  requests_per_month: 1000
  images_per_request: 5
  concurrent_requests: 1

Paid Tier Pricing:
  input: "$0.15 per 1M tokens"
  output: "$0.15 per 1M tokens"
  images: "$0.002 per image"

Potential for Leonidas:
  use_cases: ["Visual analysis", "Screenshot analysis", "Diagram understanding"]
  integration: "Alternative to Gemini vision capabilities"
```

### **🔢 mistral-embed**
```yaml
Model ID: "mistral-embed"
Status: "Stable - Embeddings"
Type: "Text Embeddings"
Dimensions: "1024"
Release Date: "2024-XX-XX"
Recommended For: "Semantic search, clustering, similarity"

Core Capabilities:
  ✅ High-quality text embeddings
  ✅ Multilingual support
  ✅ Semantic similarity
  ✅ Clustering and classification
  ✅ Retrieval augmented generation (RAG)

Technical Specs:
  embedding_dimensions: "1024"
  max_input_length: "8,192 tokens"
  typical_latency: "100-500ms"
  batch_processing: "Up to 100 texts"

Free Tier Limits:
  requests_per_month: 1000
  texts_per_request: 100
  concurrent_requests: 1

Paid Tier Pricing:
  cost: "$0.10 per 1M tokens"

Use Cases:
  ✅ Semantic search
  ✅ Document similarity
  ✅ Content clustering
  ✅ RAG applications
  ✅ Recommendation systems
```

### **🛡️ mistral-moderation**
```yaml
Model ID: "mistral-moderation"
Status: "Stable - Content Safety"
Type: "Content Moderation"
Release Date: "2024-XX-XX"
Recommended For: "Content filtering, safety checks"

Moderation Categories:
  sexual: "Sexual content detection"
  hate: "Hate speech detection"
  harassment: "Harassment detection"
  self_harm: "Self-harm content"
  violence: "Violence detection"
  illegal: "Illegal activity detection"

Technical Specs:
  max_input_length: "32,000 tokens"
  typical_latency: "200-800ms"
  accuracy: ">95% for most categories"
  languages_supported: "50+"

Free Tier Limits:
  requests_per_month: 1000
  concurrent_requests: 1

Paid Tier Pricing:
  cost: "$0.20 per 1M tokens"

Integration Benefits:
  ✅ Content safety for Leonidas
  ✅ User input filtering
  ✅ Output validation
  ✅ Compliance requirements
```

---

## 🧪 **EXPERIMENTAL MODELS**

### **🔬 mistral-next**
```yaml
Model ID: "mistral-next"
Status: "Experimental - Next Generation"
Type: "Advanced Reasoning"
Release Date: "TBD"
Recommended For: "Cutting-edge capabilities testing"

Experimental Features:
  ✅ Enhanced reasoning
  ✅ Improved multilingual
  ✅ Better code understanding
  ✅ Advanced function calling
  ⚠️ Unstable API
  ⚠️ May change without notice
  ⚠️ No SLA guarantees

Usage Guidelines:
  ✅ Research and experimentation
  ✅ Feature preview
  ❌ Production applications
  ❌ Critical workflows

Access:
  availability: "Limited beta"
  requirements: "Special access required"
```

---

## 🔧 **CONFIGURATION PATTERNS**

### **🎛️ Standard Configurations**

#### **Basic Text Completion**
```python
def create_mistral_completion(client, model: str, messages: list):
    return client.chat_completion(
        model=model,
        messages=messages,
        temperature=0.7,
        max_tokens=2048,
        top_p=0.9,
        stream=False
    )
```

#### **Function Calling Setup**
```python
def create_mistral_function_config(functions: list):
    return {
        "model": "mistral-large-2411",
        "messages": messages,
        "tools": functions,
        "tool_choice": "auto",
        "temperature": 0.3,
        "max_tokens": 1024
    }
```

#### **JSON Mode Configuration**
```python
def create_json_mode_config():
    return {
        "model": "mistral-large-2411",
        "messages": messages,
        "response_format": {"type": "json_object"},
        "temperature": 0.1,
        "max_tokens": 2048
    }
```

#### **Streaming Configuration**
```python
def create_streaming_config():
    return {
        "model": "mistral-large-2411",
        "messages": messages,
        "stream": True,
        "temperature": 0.7,
        "max_tokens": 2048
    }
```

---

## 🚦 **RATE LIMITS & QUOTAS DETALHADOS**

### **📊 Free Tier Limits (Per API Key)**
```yaml
All Models:
  requests_per_month: 1000
  tokens_per_request: 32000
  concurrent_requests: 1
  
Model-Specific Limits:
  mistral_large_2411:
    context_window: 128000
    max_output: 8000
  
  mistral_small_2409:
    context_window: 128000
    max_output: 8000
  
  codestral_2405:
    context_window: 32000
    max_output: 4000
  
  pixtral_12b:
    context_window: 128000
    max_output: 8000
    max_images: 5
  
  mistral_embed:
    max_input: 8192
    batch_size: 100
  
  mistral_moderation:
    max_input: 32000
```

### **💰 Paid Tier Pricing**
```yaml
Text Models:
  mistral_large_2411: "$2.00 input, $6.00 output per 1M tokens"
  mistral_small_2409: "$0.20 input, $0.60 output per 1M tokens"
  codestral_2405: "$0.20 input, $0.60 output per 1M tokens"
  codestral_mamba: "$0.20 input, $0.60 output per 1M tokens"

Multimodal:
  pixtral_12b: "$0.15 input, $0.15 output per 1M tokens + $0.002 per image"

Specialized:
  mistral_embed: "$0.10 per 1M tokens"
  mistral_moderation: "$0.20 per 1M tokens"

Volume Discounts:
  tier_1: "10M+ tokens/month: 10% discount"
  tier_2: "100M+ tokens/month: 20% discount"
  tier_3: "1B+ tokens/month: Custom pricing"
```

---

## 🔍 **MODEL SELECTION GUIDE**

### **🎯 Decision Matrix**
```yaml
Complex Reasoning:
  best: "mistral-large-2411"
  alternative: "mistral-small-2409 (cost-effective)"

Code Tasks:
  specialized: "codestral-2405"
  long_context: "codestral-mamba-2407"

General Purpose:
  balanced: "mistral-small-2409"
  premium: "mistral-large-2411"

Visual Tasks:
  multimodal: "pixtral-12b-2409"

Embeddings:
  semantic_search: "mistral-embed"

Content Safety:
  moderation: "mistral-moderation"

Experimental:
  research: "mistral-next"
```

### **🚀 Performance Comparison**
```yaml
Latency (First Token):
  fastest: "codestral-mamba-2407 (200-800ms)"
  fast: "mistral-small-2409 (500ms-2s)"
  medium: "mistral-large-2411 (1-4s)"
  multimodal: "pixtral-12b-2409 (2-5s)"

Quality:
  highest: "mistral-large-2411"
  balanced: "mistral-small-2409"
  specialized: "codestral-2405 (for code)"
  visual: "pixtral-12b-2409 (for images)"

Cost Efficiency:
  most_efficient: "mistral-small-2409"
  code_efficient: "codestral-2405"
  premium: "mistral-large-2411"
  multimodal: "pixtral-12b-2409"

Context Length:
  longest: "codestral-mamba-2407 (256K tokens)"
  standard: "mistral-large-2411, mistral-small-2409 (128K tokens)"
  code_focused: "codestral-2405 (32K tokens)"
```

---

## 🛠️ **TROUBLESHOOTING GUIDE**

### **🚨 Common Issues**

#### **Rate Limit Errors**
```python
# Error: 429 Too Many Requests
# Solution: Implement exponential backoff
def handle_rate_limit(client, request_func, *args, **kwargs):
    max_retries = 5
    for attempt in range(max_retries):
        try:
            return request_func(*args, **kwargs)
        except Exception as e:
            if "429" in str(e) and attempt < max_retries - 1:
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                time.sleep(wait_time)
                continue
            raise
```

#### **Authentication Errors**
```python
# Error: 401 Unauthorized
# Solution: Verify API key
def verify_mistral_key(api_key: str) -> bool:
    try:
        client = MistralClient(api_key=api_key)
        response = client.chat_completion(
            model="mistral-small-2409",
            messages=[{"role": "user", "content": "Test"}]
        )
        return True
    except:
        return False
```

#### **Model Unavailable**
```python
# Error: Model not found
# Solution: Use fallback model
MISTRAL_FALLBACKS = {
    'mistral-large-2411': 'mistral-small-2409',
    'codestral-2405': 'mistral-small-2409',
    'pixtral-12b-2409': 'mistral-large-2411'
}

def get_model_with_fallback(preferred_model: str, client):
    try:
        return client.chat_completion(model=preferred_model, messages=[])
    except:
        fallback = MISTRAL_FALLBACKS.get(preferred_model)
        if fallback:
            return client.chat_completion(model=fallback, messages=[])
        raise
```

---

## 📊 **INTEGRATION WITH LEONIDAS**

### **🔄 Mistral as Gemini Alternative**
```python
class MistralGeminiAdapter:
    """Adapter to use Mistral models as Gemini alternatives"""
    
    def __init__(self, mistral_client, gemini_client):
        self.mistral_client = mistral_client
        self.gemini_client = gemini_client
        self.model_mapping = {
            'gemini-2.5-pro': 'mistral-large-2411',
            'gemini-2.5-flash': 'mistral-small-2409',
            'gemini-code-assist': 'codestral-2405'
        }
    
    async def generate_with_fallback(self, model: str, prompt: str, use_mistral_first: bool = False):
        """Generate with automatic fallback between providers"""
        
        primary_client = self.mistral_client if use_mistral_first else self.gemini_client
        fallback_client = self.gemini_client if use_mistral_first else self.mistral_client
        
        try:
            if use_mistral_first:
                mistral_model = self.model_mapping.get(model, 'mistral-large-2411')
                return await self._call_mistral(mistral_model, prompt)
            else:
                return await self._call_gemini(model, prompt)
                
        except Exception as e:
            logging.warning(f"Primary provider failed: {e}, trying fallback")
            
            if use_mistral_first:
                return await self._call_gemini(model, prompt)
            else:
                mistral_model = self.model_mapping.get(model, 'mistral-large-2411')
                return await self._call_mistral(mistral_model, prompt)
    
    async def _call_mistral(self, model: str, prompt: str):
        """Call Mistral API"""
        response = self.mistral_client.chat_completion(
            model=model,
            messages=[{"role": "user", "content": prompt}]
        )
        return response["choices"][0]["message"]["content"]
    
    async def _call_gemini(self, model: str, prompt: str):
        """Call Gemini API"""
        gemini_model = genai.GenerativeModel(model)
        response = gemini_model.generate_content(prompt)
        return response.text
```

### **📊 A/B Testing Framework**
```python
class ModelComparisonFramework:
    """Framework for comparing Mistral vs Gemini models"""
    
    def __init__(self):
        self.test_results = []
    
    async def compare_models(self, prompt: str, test_cases: list):
        """Compare model responses for given test cases"""
        
        for test_case in test_cases:
            gemini_response = await self._test_gemini(test_case['model'], prompt)
            mistral_response = await self._test_mistral(test_case['mistral_equivalent'], prompt)
            
            comparison = {
                'prompt': prompt,
                'gemini_model': test_case['model'],
                'mistral_model': test_case['mistral_equivalent'],
                'gemini_response': gemini_response,
                'mistral_response': mistral_response,
                'timestamp': time.time(),
                'metrics': self._calculate_metrics(gemini_response, mistral_response)
            }
            
            self.test_results.append(comparison)
        
        return self.test_results
    
    def _calculate_metrics(self, response1: str, response2: str) -> dict:
        """Calculate comparison metrics"""
        return {
            'length_difference': abs(len(response1) - len(response2)),
            'similarity_score': self._calculate_similarity(response1, response2),
            'response_quality': self._assess_quality(response1, response2)
        }
```

---

## 📚 **RESOURCES & DOCUMENTATION**

### **🔗 Official Links**
- **Main Documentation**: [docs.mistral.ai](https://docs.mistral.ai)
- **API Reference**: [docs.mistral.ai/api](https://docs.mistral.ai/api)
- **Model Cards**: [docs.mistral.ai/models](https://docs.mistral.ai/models)
- **Pricing**: [mistral.ai/pricing](https://mistral.ai/pricing)
- **Console**: [console.mistral.ai](https://console.mistral.ai)

### **🛠️ Development Tools**
- **Python SDK**: `pip install mistralai`
- **API Playground**: [console.mistral.ai/playground](https://console.mistral.ai/playground)
- **Model Comparison**: [mistral.ai/models](https://mistral.ai/models)

### **📊 Monitoring & Analytics**
- **Usage Dashboard**: Mistral Console
- **API Monitoring**: Built-in usage tracking
- **Performance Metrics**: Response time and quality tracking

---

**🟠 MISTRAL COMPLETE - Sua referência definitiva para modelos Mistral**

*Última atualização: 2025-01-22*
*Próxima revisão: Mensal (toda primeira segunda-feira do mês)*