# Mistral API - Complete API Specification

## 🟠 **MISTRAL AI API - ESPECIFICAÇÃO COMPLETA DA API**

Este arquivo documenta **todas** as capacidades, endpoints, padrões e limitações da API da Mistral AI, complementando as especificações dos modelos.

---

## 📊 **API OVERVIEW**

### **🎯 API Architecture**
```yaml
API Name: "Mistral AI API"
Base URL: "https://api.mistral.ai"
Current Version: "v1"
Protocol: "REST"
Authentication: "Bearer Token (API Key)"
SDKs Available: ["Python", "Node.js", "REST"]

API Categories:
  chat_completions: "Chat-based text generation"
  completions: "Text completion (legacy)"
  embeddings: "Text embeddings"
  models: "Model information"
  fine_tuning: "Model fine-tuning"
  moderation: "Content moderation"
```

### **🔑 Authentication**
```yaml
Authentication Method: "Bearer Token"
Header: "Authorization: Bearer YOUR_API_KEY"
API Key Format: "Alphanumeric string"
Scope: "Full API access per key"

Environment Variable: "MISTRAL_API_KEY"
Security: "Keep API keys secure, rotate regularly"
```

---

## 💬 **CHAT COMPLETIONS API**

### **🚀 Primary Endpoint**
```yaml
Endpoint: "POST /v1/chat/completions"
Purpose: "Generate chat-based responses"
Input: "Messages array with roles"
Output: "Generated response"
Streaming: "Supported via stream parameter"
```

#### **Basic Chat Completion**
```python
import requests
import json

class MistralClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.mistral.ai/v1"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def chat_completion(self, model: str, messages: list, **kwargs) -> dict:
        """Basic chat completion"""
        url = f"{self.base_url}/chat/completions"
        
        payload = {
            "model": model,
            "messages": messages,
            **kwargs
        }
        
        response = requests.post(url, headers=self.headers, json=payload)
        response.raise_for_status()
        
        return response.json()

# Usage example
client = MistralClient(api_key="your_api_key")

response = client.chat_completion(
    model="mistral-large-2411",
    messages=[
        {"role": "user", "content": "Hello, how are you?"}
    ]
)

print(response["choices"][0]["message"]["content"])
```

#### **Streaming Chat Completion**
```python
def stream_chat_completion(self, model: str, messages: list, **kwargs):
    """Streaming chat completion"""
    url = f"{self.base_url}/chat/completions"
    
    payload = {
        "model": model,
        "messages": messages,
        "stream": True,
        **kwargs
    }
    
    response = requests.post(
        url, 
        headers=self.headers, 
        json=payload, 
        stream=True
    )
    response.raise_for_status()
    
    for line in response.iter_lines():
        if line:
            line = line.decode('utf-8')
            if line.startswith('data: '):
                data = line[6:]  # Remove 'data: ' prefix
                if data == '[DONE]':
                    break
                try:
                    chunk = json.loads(data)
                    if chunk["choices"][0]["delta"].get("content"):
                        yield chunk["choices"][0]["delta"]["content"]
                except json.JSONDecodeError:
                    continue

# Usage
for chunk in client.stream_chat_completion(
    model="mistral-large-2411",
    messages=[{"role": "user", "content": "Tell me a story"}]
):
    print(chunk, end='', flush=True)
```

### **📨 Message Format**
```python
# Message structure
messages = [
    {
        "role": "system",
        "content": "You are a helpful assistant."
    },
    {
        "role": "user", 
        "content": "What is the capital of France?"
    },
    {
        "role": "assistant",
        "content": "The capital of France is Paris."
    },
    {
        "role": "user",
        "content": "What about Italy?"
    }
]

# Supported roles
SUPPORTED_ROLES = ["system", "user", "assistant"]
```

### **🎛️ Generation Parameters**
```python
# Complete parameter set
generation_params = {
    "model": "mistral-large-2411",
    "messages": messages,
    
    # Generation control
    "temperature": 0.7,        # 0.0 to 1.0
    "top_p": 0.9,             # 0.0 to 1.0
    "max_tokens": 2048,       # Max output tokens
    "min_tokens": 1,          # Min output tokens
    
    # Sampling control
    "random_seed": 42,        # For reproducible outputs
    
    # Response format
    "response_format": {      # For JSON mode
        "type": "json_object"
    },
    
    # Streaming
    "stream": False,          # Enable streaming
    
    # Safety
    "safe_prompt": True       # Enable safety filtering
}
```

---

## 🛠️ **FUNCTION CALLING**

### **🔧 Function Declaration**
```python
# Define functions
functions = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get current weather for a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City name"
                    },
                    "unit": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                        "description": "Temperature unit"
                    }
                },
                "required": ["location"]
            }
        }
    }
]

# Chat completion with functions
response = client.chat_completion(
    model="mistral-large-2411",
    messages=[
        {"role": "user", "content": "What's the weather in Paris?"}
    ],
    tools=functions,
    tool_choice="auto"  # "auto", "none", or specific function
)
```

### **🔄 Function Call Handling**
```python
def handle_function_calls(response: dict) -> dict:
    """Handle function calls in response"""
    message = response["choices"][0]["message"]
    
    if message.get("tool_calls"):
        # Execute function calls
        function_responses = []
        
        for tool_call in message["tool_calls"]:
            function_name = tool_call["function"]["name"]
            function_args = json.loads(tool_call["function"]["arguments"])
            
            # Execute function (implement your function logic)
            if function_name == "get_weather":
                result = get_weather(function_args["location"], function_args.get("unit", "celsius"))
            else:
                result = {"error": f"Unknown function: {function_name}"}
            
            function_responses.append({
                "tool_call_id": tool_call["id"],
                "role": "tool",
                "name": function_name,
                "content": json.dumps(result)
            })
        
        # Continue conversation with function results
        messages = [
            {"role": "user", "content": "What's the weather in Paris?"},
            message,  # Assistant's function call
            *function_responses  # Function results
        ]
        
        # Get final response
        final_response = client.chat_completion(
            model="mistral-large-2411",
            messages=messages
        )
        
        return final_response
    
    return response
```

---

## 📊 **EMBEDDINGS API**

### **🔢 Text Embeddings**
```yaml
Endpoint: "POST /v1/embeddings"
Purpose: "Generate text embeddings"
Input: "Text or array of texts"
Output: "Vector embeddings"
Models: ["mistral-embed"]
```

```python
def get_embeddings(self, texts: list[str], model: str = "mistral-embed") -> dict:
    """Get text embeddings"""
    url = f"{self.base_url}/embeddings"
    
    payload = {
        "model": model,
        "input": texts
    }
    
    response = requests.post(url, headers=self.headers, json=payload)
    response.raise_for_status()
    
    return response.json()

# Usage
embeddings_response = client.get_embeddings([
    "Hello world",
    "How are you?",
    "Goodbye"
])

for i, embedding in enumerate(embeddings_response["data"]):
    print(f"Text {i}: {len(embedding['embedding'])} dimensions")
    print(f"First 5 values: {embedding['embedding'][:5]}")
```

### **🔍 Embedding Use Cases**
```python
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

class EmbeddingUtils:
    def __init__(self, client: MistralClient):
        self.client = client
    
    def semantic_search(self, query: str, documents: list[str], top_k: int = 5) -> list:
        """Semantic search using embeddings"""
        # Get embeddings for query and documents
        all_texts = [query] + documents
        embeddings_response = self.client.get_embeddings(all_texts)
        
        embeddings = [item["embedding"] for item in embeddings_response["data"]]
        query_embedding = np.array(embeddings[0]).reshape(1, -1)
        doc_embeddings = np.array(embeddings[1:])
        
        # Calculate similarities
        similarities = cosine_similarity(query_embedding, doc_embeddings)[0]
        
        # Get top-k results
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            results.append({
                "document": documents[idx],
                "similarity": similarities[idx],
                "index": idx
            })
        
        return results
    
    def cluster_texts(self, texts: list[str], n_clusters: int = 3) -> dict:
        """Cluster texts using embeddings"""
        from sklearn.cluster import KMeans
        
        # Get embeddings
        embeddings_response = self.client.get_embeddings(texts)
        embeddings = np.array([item["embedding"] for item in embeddings_response["data"]])
        
        # Perform clustering
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        cluster_labels = kmeans.fit_predict(embeddings)
        
        # Organize results
        clusters = {}
        for i, (text, label) in enumerate(zip(texts, cluster_labels)):
            if label not in clusters:
                clusters[label] = []
            clusters[label].append({
                "text": text,
                "index": i
            })
        
        return clusters
```

---

## 📋 **MODELS API**

### **📊 List Available Models**
```python
def list_models(self) -> dict:
    """List available models"""
    url = f"{self.base_url}/models"
    
    response = requests.get(url, headers=self.headers)
    response.raise_for_status()
    
    return response.json()

# Usage
models = client.list_models()
for model in models["data"]:
    print(f"Model: {model['id']}")
    print(f"Created: {model['created']}")
    print(f"Owned by: {model['owned_by']}")
    print("---")
```

### **🔍 Model Information**
```python
def get_model_info(self, model_id: str) -> dict:
    """Get specific model information"""
    url = f"{self.base_url}/models/{model_id}"
    
    response = requests.get(url, headers=self.headers)
    response.raise_for_status()
    
    return response.json()

# Usage
model_info = client.get_model_info("mistral-large-2411")
print(f"Model capabilities: {model_info}")
```

---

## 🛡️ **MODERATION API**

### **🔒 Content Moderation**
```yaml
Endpoint: "POST /v1/moderations"
Purpose: "Moderate content for safety"
Input: "Text to moderate"
Output: "Moderation results"
Models: ["mistral-moderation"]
```

```python
def moderate_content(self, text: str, model: str = "mistral-moderation") -> dict:
    """Moderate content for safety"""
    url = f"{self.base_url}/moderations"
    
    payload = {
        "model": model,
        "input": text
    }
    
    response = requests.post(url, headers=self.headers, json=payload)
    response.raise_for_status()
    
    return response.json()

# Usage
moderation_result = client.moderate_content("This is a test message")

for result in moderation_result["results"]:
    print(f"Flagged: {result['flagged']}")
    for category, details in result["categories"].items():
        if details:
            print(f"  {category}: {result['category_scores'][category]}")
```

### **📊 Moderation Categories**
```yaml
Available Categories:
  sexual: "Sexual content"
  hate: "Hate speech"
  harassment: "Harassment"
  self-harm: "Self-harm content"
  sexual/minors: "Sexual content involving minors"
  hate/threatening: "Threatening hate speech"
  violence/graphic: "Graphic violence"
  self-harm/intent: "Intent to self-harm"
  self-harm/instructions: "Self-harm instructions"
  harassment/threatening: "Threatening harassment"
  violence: "Violence"

Threshold Levels:
  flagged: "Boolean flag for content"
  category_scores: "Confidence scores (0.0 to 1.0)"
```

---

## 🚦 **RATE LIMITS & QUOTAS**

### **📊 Free Tier Limits**
```yaml
Free Tier (per API key):
  requests_per_month: 1000
  tokens_per_request: 32000
  concurrent_requests: 1
  models_available: ["mistral-large-2411", "mistral-small-2409", "codestral-2405"]

Rate Limiting:
  requests_per_minute: "No specific limit (subject to monthly quota)"
  burst_capacity: "Limited"
  retry_after: "Provided in 429 response headers"
```

### **💰 Paid Tier Pricing**
```yaml
Pay-per-use Pricing:
  mistral_large_2411:
    input: "$2.00 per 1M tokens"
    output: "$6.00 per 1M tokens"
  
  mistral_small_2409:
    input: "$0.20 per 1M tokens"
    output: "$0.60 per 1M tokens"
  
  codestral_2405:
    input: "$0.20 per 1M tokens"
    output: "$0.60 per 1M tokens"
  
  mistral_embed:
    cost: "$0.10 per 1M tokens"
  
  mistral_moderation:
    cost: "$0.20 per 1M tokens"

Subscription Plans:
  developer: "$15/month + usage"
  pro: "$50/month + usage"
  enterprise: "Custom pricing"
```

### **🔍 Usage Monitoring**
```python
class MistralUsageMonitor:
    def __init__(self, client: MistralClient):
        self.client = client
        self.usage_log = []
    
    def track_request(self, model: str, input_tokens: int, output_tokens: int, cost: float = 0):
        """Track API usage"""
        usage_entry = {
            "timestamp": time.time(),
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "estimated_cost": cost
        }
        
        self.usage_log.append(usage_entry)
    
    def get_usage_summary(self, days: int = 30) -> dict:
        """Get usage summary for specified days"""
        cutoff_time = time.time() - (days * 24 * 3600)
        recent_usage = [entry for entry in self.usage_log if entry["timestamp"] > cutoff_time]
        
        if not recent_usage:
            return {"status": "no_data"}
        
        summary = {
            "total_requests": len(recent_usage),
            "total_tokens": sum(entry["total_tokens"] for entry in recent_usage),
            "total_cost": sum(entry["estimated_cost"] for entry in recent_usage),
            "models_used": list(set(entry["model"] for entry in recent_usage)),
            "daily_average": len(recent_usage) / days
        }
        
        return summary
```

---

## 🚨 **ERROR HANDLING**

### **📋 Common Error Codes**
```yaml
HTTP Status Codes:
  400: "Bad Request - Invalid request format"
  401: "Unauthorized - Invalid API key"
  403: "Forbidden - Insufficient permissions"
  404: "Not Found - Model or endpoint not found"
  422: "Unprocessable Entity - Request validation failed"
  429: "Too Many Requests - Rate limit exceeded"
  500: "Internal Server Error - Mistral server error"
  502: "Bad Gateway - Upstream server error"
  503: "Service Unavailable - Temporary service issue"

Mistral-Specific Errors:
  invalid_request_error: "Invalid request parameters"
  authentication_error: "API key authentication failed"
  permission_error: "Insufficient permissions"
  not_found_error: "Resource not found"
  rate_limit_error: "Rate limit exceeded"
  api_error: "Internal API error"
  overloaded_error: "Service overloaded"
```

### **🛠️ Robust Error Handling**
```python
import time
import random
from typing import Optional

class RobustMistralClient(MistralClient):
    def __init__(self, api_key: str, max_retries: int = 3):
        super().__init__(api_key)
        self.max_retries = max_retries
    
    def chat_completion_with_retry(self, model: str, messages: list, **kwargs) -> Optional[dict]:
        """Chat completion with retry logic"""
        for attempt in range(self.max_retries):
            try:
                return self.chat_completion(model, messages, **kwargs)
                
            except requests.exceptions.HTTPError as e:
                status_code = e.response.status_code
                
                if status_code == 429:  # Rate limit
                    retry_after = int(e.response.headers.get('retry-after', 60))
                    wait_time = retry_after + random.uniform(0, 5)
                    print(f"Rate limited. Waiting {wait_time:.1f} seconds...")
                    time.sleep(wait_time)
                    continue
                    
                elif status_code in [500, 502, 503]:  # Server errors
                    wait_time = (2 ** attempt) + random.uniform(0, 1)
                    print(f"Server error {status_code}. Retrying in {wait_time:.1f} seconds...")
                    time.sleep(wait_time)
                    continue
                    
                elif status_code in [400, 401, 403, 404, 422]:  # Client errors
                    print(f"Client error {status_code}: {e.response.text}")
                    return None
                    
                else:
                    print(f"Unexpected error {status_code}: {e.response.text}")
                    if attempt < self.max_retries - 1:
                        time.sleep(2 ** attempt)
                        continue
                    return None
                    
            except requests.exceptions.RequestException as e:
                print(f"Request error: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                return None
        
        print(f"Failed after {self.max_retries} attempts")
        return None
    
    def handle_response_errors(self, response: dict) -> bool:
        """Check response for errors"""
        if "error" in response:
            error = response["error"]
            print(f"API Error: {error.get('type', 'unknown')} - {error.get('message', 'No message')}")
            return False
        
        if "choices" not in response or not response["choices"]:
            print("No choices in response")
            return False
        
        choice = response["choices"][0]
        if choice.get("finish_reason") == "content_filter":
            print("Content was filtered")
            return False
        
        return True
```

---

## 📊 **PERFORMANCE OPTIMIZATION**

### **⚡ Best Practices**
```python
class MistralOptimizer:
    def __init__(self, client: MistralClient):
        self.client = client
        self.cache = {}
    
    def optimize_for_speed(self, model: str, messages: list) -> dict:
        """Optimize request for speed"""
        return self.client.chat_completion(
            model=model,
            messages=messages,
            temperature=0.3,  # Lower temperature for faster generation
            max_tokens=512,   # Limit output length
            top_p=0.8        # Reduce sampling space
        )
    
    def optimize_for_quality(self, model: str, messages: list) -> dict:
        """Optimize request for quality"""
        return self.client.chat_completion(
            model=model,
            messages=messages,
            temperature=0.7,  # Higher temperature for creativity
            max_tokens=2048,  # Allow longer responses
            top_p=0.9        # Broader sampling
        )
    
    def batch_process(self, requests: list[dict], delay: float = 0.1) -> list[dict]:
        """Process multiple requests with rate limiting"""
        results = []
        
        for i, request in enumerate(requests):
            try:
                result = self.client.chat_completion(**request)
                results.append(result)
                
                # Rate limiting
                if i < len(requests) - 1:  # Don't wait after last request
                    time.sleep(delay)
                    
            except Exception as e:
                results.append({"error": str(e)})
        
        return results
    
    def cache_response(self, key: str, response: dict, ttl: int = 3600):
        """Cache responses to reduce API calls"""
        self.cache[key] = {
            "response": response,
            "timestamp": time.time(),
            "ttl": ttl
        }
    
    def get_cached_response(self, key: str) -> Optional[dict]:
        """Get cached response if available and valid"""
        if key in self.cache:
            cached = self.cache[key]
            if time.time() - cached["timestamp"] < cached["ttl"]:
                return cached["response"]
            else:
                del self.cache[key]
        return None
```

---

## 🔧 **SDK & INTEGRATION**

### **🐍 Python SDK (Official)**
```bash
# Installation
pip install mistralai

# Alternative: Direct HTTP requests
pip install requests
```

### **📚 Official SDK Usage**
```python
from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage

# Initialize client
client = MistralClient(api_key="your_api_key")

# Chat completion
messages = [
    ChatMessage(role="user", content="Hello, how are you?")
]

response = client.chat(
    model="mistral-large-2411",
    messages=messages
)

print(response.choices[0].message.content)

# Streaming
for chunk in client.chat_stream(
    model="mistral-large-2411",
    messages=messages
):
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
```

### **🌐 Direct REST Integration**
```python
class DirectMistralAPI:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.mistral.ai/v1"
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        })
    
    def make_request(self, endpoint: str, method: str = "POST", **kwargs) -> dict:
        """Make direct API request"""
        url = f"{self.base_url}/{endpoint}"
        
        if method == "POST":
            response = self.session.post(url, json=kwargs)
        elif method == "GET":
            response = self.session.get(url, params=kwargs)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        response.raise_for_status()
        return response.json()
```

---

## 🔍 **ADVANCED FEATURES**

### **🎯 JSON Mode**
```python
def structured_output(self, model: str, messages: list, schema: dict) -> dict:
    """Generate structured JSON output"""
    # Add JSON instruction to system message
    system_message = {
        "role": "system",
        "content": f"You must respond with valid JSON that matches this schema: {json.dumps(schema)}"
    }
    
    structured_messages = [system_message] + messages
    
    response = self.chat_completion(
        model=model,
        messages=structured_messages,
        response_format={"type": "json_object"},
        temperature=0.1  # Low temperature for consistent structure
    )
    
    # Parse and validate JSON
    try:
        json_response = json.loads(response["choices"][0]["message"]["content"])
        return json_response
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON response: {e}"}

# Usage example
schema = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "sentiment": {"type": "string", "enum": ["positive", "negative", "neutral"]},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1}
    },
    "required": ["summary", "sentiment", "confidence"]
}

result = client.structured_output(
    model="mistral-large-2411",
    messages=[{"role": "user", "content": "Analyze this text: 'I love this product!'"}],
    schema=schema
)
```

### **🔄 Conversation Management**
```python
class ConversationManager:
    def __init__(self, client: MistralClient, model: str):
        self.client = client
        self.model = model
        self.conversations = {}
    
    def start_conversation(self, conversation_id: str, system_prompt: str = None) -> str:
        """Start a new conversation"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        self.conversations[conversation_id] = {
            "messages": messages,
            "created_at": time.time(),
            "last_activity": time.time()
        }
        
        return conversation_id
    
    def send_message(self, conversation_id: str, message: str) -> str:
        """Send message in conversation"""
        if conversation_id not in self.conversations:
            raise ValueError(f"Conversation {conversation_id} not found")
        
        conversation = self.conversations[conversation_id]
        
        # Add user message
        conversation["messages"].append({
            "role": "user",
            "content": message
        })
        
        # Get response
        response = self.client.chat_completion(
            model=self.model,
            messages=conversation["messages"]
        )
        
        assistant_message = response["choices"][0]["message"]["content"]
        
        # Add assistant response to conversation
        conversation["messages"].append({
            "role": "assistant",
            "content": assistant_message
        })
        
        conversation["last_activity"] = time.time()
        
        return assistant_message
    
    def get_conversation_history(self, conversation_id: str) -> list:
        """Get conversation history"""
        if conversation_id not in self.conversations:
            return []
        
        return self.conversations[conversation_id]["messages"]
    
    def cleanup_old_conversations(self, max_age_hours: int = 24):
        """Clean up old conversations"""
        cutoff_time = time.time() - (max_age_hours * 3600)
        
        to_remove = []
        for conv_id, conv_data in self.conversations.items():
            if conv_data["last_activity"] < cutoff_time:
                to_remove.append(conv_id)
        
        for conv_id in to_remove:
            del self.conversations[conv_id]
        
        return len(to_remove)
```

---

## 📚 **RESOURCES & DOCUMENTATION**

### **🔗 Official Documentation**
- **Main API Docs**: [docs.mistral.ai](https://docs.mistral.ai)
- **API Reference**: [docs.mistral.ai/api](https://docs.mistral.ai/api)
- **Python SDK**: [github.com/mistralai/client-python](https://github.com/mistralai/client-python)
- **Pricing**: [mistral.ai/pricing](https://mistral.ai/pricing)

### **🛠️ Development Tools**
- **API Playground**: [console.mistral.ai](https://console.mistral.ai)
- **Model Comparison**: [mistral.ai/models](https://mistral.ai/models)
- **Fine-tuning**: [docs.mistral.ai/fine-tuning](https://docs.mistral.ai/fine-tuning)

### **📊 Monitoring & Support**
- **Console Dashboard**: [console.mistral.ai](https://console.mistral.ai)
- **Status Page**: [status.mistral.ai](https://status.mistral.ai)
- **Community**: [discord.gg/mistralai](https://discord.gg/mistralai)
- **Support**: [mistral.ai/contact](https://mistral.ai/contact)

---

**🟠 MISTRAL API COMPLETE - Sua referência definitiva para a API Mistral**

*Última atualização: 2025-01-22*
*Próxima revisão: Mensal (toda primeira segunda-feira do mês)*