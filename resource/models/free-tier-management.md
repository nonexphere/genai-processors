# Free Tier Management - Maximizing Usage Strategy

## 💳 **GESTÃO COMPLETA DE FREE TIERS**

Este arquivo documenta estratégias avançadas para maximizar o uso dos Free Tiers do Google/Gemini e Mistral, incluindo rotação de keys, monitoramento de quotas e otimizações de custo.

---

## 🎯 **ESTRATÉGIA GERAL DE FREE TIER**

### **🧠 Filosofia de Uso**
```yaml
Primary Goal: "Maximize development velocity within free limits"
Secondary Goal: "Prepare for smooth paid tier migration"
Tertiary Goal: "Learn usage patterns for cost optimization"

Key Principles:
  1. "Use cheapest appropriate model for each task"
  2. "Rotate keys intelligently to extend limits"
  3. "Monitor usage to prevent unexpected cutoffs"
  4. "Cache results to reduce API calls"
  5. "Optimize prompts to reduce token usage"
```

### **📊 Current Free Tier Value**
```yaml
Google/Gemini (3 keys):
  live_api_value: "$360/month" # 3000 minutes * $0.40/min
  completion_value: "$67.50/month" # 4500 requests * $0.015 avg
  flash_lite_value: "$37.50/month" # 150K requests * $0.00025
  total_google_value: "$465/month"

Mistral (2 keys):
  large_model_value: "$24/month" # 2000 requests * $0.012 avg
  small_model_value: "$2.40/month" # 2000 requests * $0.0012 avg
  total_mistral_value: "$26.40/month"

TOTAL FREE TIER VALUE: "$491.40/month"
```

---

## 🔑 **ADVANCED KEY ROTATION STRATEGIES**

### **🤖 Intelligent Key Manager**
```python
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class AdvancedKeyManager:
    def __init__(self):
        self.providers = {
            'gemini': {
                'keys': [
                    os.getenv('GEMINI_API_KEY_1'),
                    os.getenv('GEMINI_API_KEY_2'),
                    os.getenv('GEMINI_API_KEY_3')
                ],
                'current_index': 0,
                'usage_tracking': {},
                'rate_limits': {
                    'live_api': {'per_minute': 60, 'per_day': 1000},
                    'completion': {'per_minute': 15, 'per_day': 1500},
                    'flash_lite': {'per_minute': 1000, 'per_day': 50000}
                }
            },
            'mistral': {
                'keys': [
                    os.getenv('MISTRAL_API_KEY_1'),
                    os.getenv('MISTRAL_API_KEY_2')
                ],
                'current_index': 0,
                'usage_tracking': {},
                'rate_limits': {
                    'all_models': {'per_month': 1000}
                }
            }
        }
        self.usage_history = self._load_usage_history()
    
    def get_best_key(self, provider: str, model_type: str) -> tuple[str, int]:
        """Get the best available key for a specific use case"""
        provider_config = self.providers[provider]
        keys = provider_config['keys']
        
        # Check usage for each key
        best_key_index = 0
        lowest_usage = float('inf')
        
        for i, key in enumerate(keys):
            if not key:
                continue
                
            current_usage = self._get_current_usage(provider, i, model_type)
            limit = self._get_limit(provider, model_type)
            
            usage_percentage = current_usage / limit if limit > 0 else 0
            
            if usage_percentage < lowest_usage:
                lowest_usage = usage_percentage
                best_key_index = i
        
        provider_config['current_index'] = best_key_index
        return keys[best_key_index], best_key_index
    
    def record_usage(self, provider: str, key_index: int, model_type: str, 
                    tokens_used: int = 0, requests: int = 1, audio_minutes: float = 0):
        """Record usage for a specific key"""
        today = datetime.now().strftime('%Y-%m-%d')
        hour = datetime.now().strftime('%H')
        
        usage_key = f"{provider}_{key_index}_{today}"
        
        if usage_key not in self.usage_history:
            self.usage_history[usage_key] = {
                'requests_by_hour': {},
                'tokens_by_model': {},
                'audio_minutes': 0,
                'total_requests': 0
            }
        
        # Record hourly requests
        if hour not in self.usage_history[usage_key]['requests_by_hour']:
            self.usage_history[usage_key]['requests_by_hour'][hour] = 0
        self.usage_history[usage_key]['requests_by_hour'][hour] += requests
        
        # Record tokens by model
        if model_type not in self.usage_history[usage_key]['tokens_by_model']:
            self.usage_history[usage_key]['tokens_by_model'][model_type] = 0
        self.usage_history[usage_key]['tokens_by_model'][model_type] += tokens_used
        
        # Record audio minutes
        self.usage_history[usage_key]['audio_minutes'] += audio_minutes
        self.usage_history[usage_key]['total_requests'] += requests
        
        # Save to disk
        self._save_usage_history()
    
    def check_rate_limit_status(self, provider: str, key_index: int, model_type: str) -> dict:
        """Check current rate limit status for a key"""
        current_usage = self._get_current_usage(provider, key_index, model_type)
        limits = self._get_limit(provider, model_type)
        
        # Calculate usage percentages
        minute_usage = self._get_minute_usage(provider, key_index, model_type)
        hour_usage = self._get_hour_usage(provider, key_index, model_type)
        day_usage = current_usage
        
        return {
            'key_index': key_index,
            'model_type': model_type,
            'minute_usage': minute_usage,
            'hour_usage': hour_usage,
            'day_usage': day_usage,
            'limits': limits,
            'usage_percentages': {
                'minute': minute_usage / limits.get('per_minute', 1) if limits.get('per_minute') else 0,
                'hour': hour_usage / limits.get('per_hour', 1) if limits.get('per_hour') else 0,
                'day': day_usage / limits.get('per_day', 1) if limits.get('per_day') else 0
            },
            'recommended_action': self._get_recommendation(minute_usage, hour_usage, day_usage, limits)
        }
    
    def _get_recommendation(self, minute_usage: int, hour_usage: int, day_usage: int, limits: dict) -> str:
        """Get recommendation based on current usage"""
        minute_pct = minute_usage / limits.get('per_minute', 1) if limits.get('per_minute') else 0
        hour_pct = hour_usage / limits.get('per_hour', 1) if limits.get('per_hour') else 0
        day_pct = day_usage / limits.get('per_day', 1) if limits.get('per_day') else 0
        
        if minute_pct > 0.9:
            return "CRITICAL: Switch key immediately"
        elif minute_pct > 0.8:
            return "WARNING: Consider switching key"
        elif hour_pct > 0.8:
            return "CAUTION: Monitor closely"
        elif day_pct > 0.8:
            return "INFO: Approaching daily limit"
        else:
            return "OK: Normal usage"
```

### **📊 Usage Monitoring Dashboard**
```python
class UsageDashboard:
    def __init__(self, key_manager: AdvancedKeyManager):
        self.key_manager = key_manager
    
    def generate_daily_report(self) -> dict:
        """Generate comprehensive daily usage report"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        report = {
            'date': today,
            'providers': {},
            'total_value_used': 0,
            'recommendations': []
        }
        
        # Analyze each provider
        for provider_name, provider_config in self.key_manager.providers.items():
            provider_report = {
                'keys': [],
                'total_requests': 0,
                'total_value': 0,
                'efficiency_score': 0
            }
            
            for i, key in enumerate(provider_config['keys']):
                if not key:
                    continue
                
                key_usage = self._analyze_key_usage(provider_name, i, today)
                provider_report['keys'].append(key_usage)
                provider_report['total_requests'] += key_usage['total_requests']
                provider_report['total_value'] += key_usage['estimated_value']
            
            # Calculate efficiency score
            provider_report['efficiency_score'] = self._calculate_efficiency_score(provider_report)
            report['providers'][provider_name] = provider_report
            report['total_value_used'] += provider_report['total_value']
        
        # Generate recommendations
        report['recommendations'] = self._generate_recommendations(report)
        
        return report
    
    def _analyze_key_usage(self, provider: str, key_index: int, date: str) -> dict:
        """Analyze usage for a specific key on a specific date"""
        usage_key = f"{provider}_{key_index}_{date}"
        usage_data = self.key_manager.usage_history.get(usage_key, {})
        
        return {
            'key_index': key_index,
            'total_requests': usage_data.get('total_requests', 0),
            'audio_minutes': usage_data.get('audio_minutes', 0),
            'tokens_by_model': usage_data.get('tokens_by_model', {}),
            'hourly_distribution': usage_data.get('requests_by_hour', {}),
            'estimated_value': self._calculate_estimated_value(provider, usage_data),
            'efficiency_rating': self._calculate_key_efficiency(usage_data)
        }
    
    def _calculate_estimated_value(self, provider: str, usage_data: dict) -> float:
        """Calculate estimated dollar value of usage"""
        if provider == 'gemini':
            # Gemini pricing estimates
            audio_value = usage_data.get('audio_minutes', 0) * 0.40  # $0.40/minute
            
            tokens_value = 0
            for model, tokens in usage_data.get('tokens_by_model', {}).items():
                if 'flash' in model:
                    tokens_value += tokens * 0.000075  # $0.075 per 1M tokens
                elif 'pro' in model:
                    tokens_value += tokens * 0.00125   # $1.25 per 1M tokens
            
            return audio_value + tokens_value
        
        elif provider == 'mistral':
            # Mistral pricing estimates
            total_value = 0
            for model, tokens in usage_data.get('tokens_by_model', {}).items():
                if 'large' in model:
                    total_value += tokens * 0.002  # $2 per 1M tokens
                elif 'small' in model:
                    total_value += tokens * 0.0002  # $0.2 per 1M tokens
            
            return total_value
        
        return 0.0
    
    def print_dashboard(self):
        """Print formatted dashboard to console"""
        report = self.generate_daily_report()
        
        print("=" * 80)
        print(f"📊 FREE TIER USAGE DASHBOARD - {report['date']}")
        print("=" * 80)
        
        for provider_name, provider_data in report['providers'].items():
            print(f"\n🔵 {provider_name.upper()} PROVIDER")
            print(f"Total Requests: {provider_data['total_requests']}")
            print(f"Estimated Value: ${provider_data['total_value']:.2f}")
            print(f"Efficiency Score: {provider_data['efficiency_score']:.1f}/10")
            
            for key_data in provider_data['keys']:
                print(f"  Key {key_data['key_index'] + 1}: {key_data['total_requests']} requests, ${key_data['estimated_value']:.2f}")
        
        print(f"\n💰 TOTAL VALUE USED TODAY: ${report['total_value_used']:.2f}")
        
        if report['recommendations']:
            print(f"\n📋 RECOMMENDATIONS:")
            for rec in report['recommendations']:
                print(f"  • {rec}")
        
        print("=" * 80)
```

---

## 🎯 **OPTIMIZATION STRATEGIES**

### **⚡ Token Usage Optimization**
```python
class TokenOptimizer:
    def __init__(self):
        self.optimization_rules = {
            'system_prompts': {
                'max_length': 500,  # tokens
                'compression_ratio': 0.7,
                'essential_keywords': ['português', 'colaborativo', 'técnico']
            },
            'user_inputs': {
                'max_context': 2000,  # tokens
                'summarization_threshold': 1500,
                'compression_method': 'extractive'
            },
            'function_calls': {
                'parameter_optimization': True,
                'result_caching': True,
                'batch_processing': True
            }
        }
    
    def optimize_prompt(self, prompt: str, context: str = "") -> str:
        """Optimize prompt to reduce token usage while maintaining quality"""
        # Remove redundant phrases
        optimized = self._remove_redundancy(prompt)
        
        # Compress context if too long
        if len(context) > self.optimization_rules['user_inputs']['max_context']:
            context = self._compress_context(context)
        
        # Combine efficiently
        if context:
            optimized = f"{optimized}\n\nContext: {context}"
        
        return optimized
    
    def _remove_redundancy(self, text: str) -> str:
        """Remove redundant phrases and words"""
        # Common redundant phrases in Portuguese
        redundant_phrases = [
            "por favor",
            "se possível",
            "caso seja necessário",
            "de forma detalhada",
            "com precisão"
        ]
        
        optimized = text
        for phrase in redundant_phrases:
            optimized = optimized.replace(phrase, "")
        
        # Remove extra whitespace
        optimized = " ".join(optimized.split())
        
        return optimized
    
    def estimate_tokens(self, text: str) -> int:
        """Rough token estimation (1 token ≈ 4 characters for Portuguese)"""
        return len(text) // 4
```

### **💾 Intelligent Caching System**
```python
class FreeTrierCache:
    def __init__(self, max_size_mb: int = 100):
        self.max_size_mb = max_size_mb
        self.cache_dir = "cache/free_tier/"
        self.cache_index = {}
        self.hit_count = 0
        self.miss_count = 0
        
        os.makedirs(self.cache_dir, exist_ok=True)
        self._load_cache_index()
    
    def get_cache_key(self, provider: str, model: str, prompt: str, params: dict) -> str:
        """Generate deterministic cache key"""
        import hashlib
        
        cache_data = {
            'provider': provider,
            'model': model,
            'prompt': prompt,
            'params': sorted(params.items())
        }
        
        cache_string = json.dumps(cache_data, sort_keys=True)
        return hashlib.md5(cache_string.encode()).hexdigest()
    
    def get(self, cache_key: str) -> Optional[dict]:
        """Get cached response"""
        if cache_key in self.cache_index:
            cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
            if os.path.exists(cache_file):
                try:
                    with open(cache_file, 'r') as f:
                        cached_data = json.load(f)
                    
                    # Check if cache is still valid (24 hours)
                    cache_age = time.time() - cached_data.get('timestamp', 0)
                    if cache_age < 86400:  # 24 hours
                        self.hit_count += 1
                        return cached_data['response']
                except:
                    pass
        
        self.miss_count += 1
        return None
    
    def set(self, cache_key: str, response: dict, estimated_cost: float = 0):
        """Cache response"""
        cache_data = {
            'response': response,
            'timestamp': time.time(),
            'estimated_cost': estimated_cost
        }
        
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        
        try:
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f)
            
            self.cache_index[cache_key] = {
                'file': cache_file,
                'timestamp': cache_data['timestamp'],
                'cost_saved': estimated_cost
            }
            
            self._save_cache_index()
            self._cleanup_old_cache()
            
        except Exception as e:
            print(f"Cache write error: {e}")
    
    def get_cache_stats(self) -> dict:
        """Get cache performance statistics"""
        total_requests = self.hit_count + self.miss_count
        hit_rate = self.hit_count / total_requests if total_requests > 0 else 0
        
        total_cost_saved = sum(
            entry.get('cost_saved', 0) 
            for entry in self.cache_index.values()
        )
        
        return {
            'hit_rate': hit_rate,
            'total_requests': total_requests,
            'cache_hits': self.hit_count,
            'cache_misses': self.miss_count,
            'total_cost_saved': total_cost_saved,
            'cache_size_mb': self._get_cache_size_mb()
        }
```

---

## 📈 **USAGE ANALYTICS & FORECASTING**

### **📊 Usage Pattern Analysis**
```python
class UsageAnalytics:
    def __init__(self, key_manager: AdvancedKeyManager):
        self.key_manager = key_manager
    
    def analyze_usage_patterns(self, days: int = 30) -> dict:
        """Analyze usage patterns over specified days"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        patterns = {
            'hourly_distribution': {},
            'daily_trends': {},
            'model_preferences': {},
            'efficiency_trends': {},
            'cost_projections': {}
        }
        
        # Analyze hourly distribution
        for hour in range(24):
            patterns['hourly_distribution'][hour] = self._get_hourly_usage(hour, start_date, end_date)
        
        # Analyze daily trends
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            patterns['daily_trends'][date_str] = self._get_daily_usage(date_str)
            current_date += timedelta(days=1)
        
        # Analyze model preferences
        patterns['model_preferences'] = self._analyze_model_usage(start_date, end_date)
        
        # Calculate efficiency trends
        patterns['efficiency_trends'] = self._calculate_efficiency_trends(start_date, end_date)
        
        # Project costs
        patterns['cost_projections'] = self._project_costs(patterns)
        
        return patterns
    
    def _project_costs(self, patterns: dict) -> dict:
        """Project future costs based on usage patterns"""
        # Calculate average daily usage
        daily_values = [day_data.get('estimated_value', 0) for day_data in patterns['daily_trends'].values()]
        avg_daily_cost = sum(daily_values) / len(daily_values) if daily_values else 0
        
        # Project monthly cost
        monthly_projection = avg_daily_cost * 30
        
        # Calculate when we might hit free tier limits
        current_usage_rate = self._calculate_current_usage_rate()
        
        return {
            'avg_daily_cost': avg_daily_cost,
            'monthly_projection': monthly_projection,
            'free_tier_exhaustion_date': self._calculate_exhaustion_date(current_usage_rate),
            'recommended_paid_tier_date': self._recommend_paid_tier_date(monthly_projection),
            'cost_optimization_potential': self._calculate_optimization_potential(patterns)
        }
    
    def generate_usage_report(self) -> str:
        """Generate comprehensive usage report"""
        patterns = self.analyze_usage_patterns()
        
        report = f"""
📊 FREE TIER USAGE ANALYSIS REPORT
{'='*50}

📈 USAGE PATTERNS:
• Peak usage hours: {self._get_peak_hours(patterns['hourly_distribution'])}
• Average daily requests: {self._get_avg_daily_requests(patterns['daily_trends'])}
• Most used models: {self._get_top_models(patterns['model_preferences'])}

💰 COST ANALYSIS:
• Current daily cost equivalent: ${patterns['cost_projections']['avg_daily_cost']:.2f}
• Monthly projection: ${patterns['cost_projections']['monthly_projection']:.2f}
• Free tier value utilized: {self._calculate_free_tier_utilization():.1%}

🎯 OPTIMIZATION OPPORTUNITIES:
• Cache hit rate improvement: {self._calculate_cache_opportunity():.1%}
• Token usage optimization: {self._calculate_token_optimization():.1%}
• Model selection optimization: {self._calculate_model_optimization():.1%}

📅 RECOMMENDATIONS:
{self._generate_usage_recommendations(patterns)}
        """
        
        return report.strip()
```

---

## 🚨 **ALERT SYSTEM**

### **📢 Proactive Monitoring**
```python
class FreeTrierAlertSystem:
    def __init__(self, key_manager: AdvancedKeyManager):
        self.key_manager = key_manager
        self.alert_thresholds = {
            'daily_usage_warning': 0.8,    # 80% of daily limit
            'daily_usage_critical': 0.95,  # 95% of daily limit
            'hourly_usage_warning': 0.9,   # 90% of hourly limit
            'key_exhaustion_warning': 2,   # 2 keys exhausted
            'cost_projection_warning': 400 # $400/month equivalent
        }
        self.alert_history = []
    
    def check_all_alerts(self) -> List[dict]:
        """Check all alert conditions"""
        alerts = []
        
        # Check usage alerts for each provider
        for provider_name in self.key_manager.providers.keys():
            alerts.extend(self._check_provider_alerts(provider_name))
        
        # Check system-wide alerts
        alerts.extend(self._check_system_alerts())
        
        # Store alerts
        for alert in alerts:
            self.alert_history.append({
                **alert,
                'timestamp': datetime.now().isoformat()
            })
        
        return alerts
    
    def _check_provider_alerts(self, provider: str) -> List[dict]:
        """Check alerts for a specific provider"""
        alerts = []
        provider_config = self.key_manager.providers[provider]
        
        exhausted_keys = 0
        total_usage = 0
        
        for i, key in enumerate(provider_config['keys']):
            if not key:
                continue
            
            # Check key-specific usage
            for model_type in provider_config['rate_limits'].keys():
                status = self.key_manager.check_rate_limit_status(provider, i, model_type)
                
                # Daily usage alerts
                day_usage_pct = status['usage_percentages']['day']
                if day_usage_pct >= self.alert_thresholds['daily_usage_critical']:
                    alerts.append({
                        'type': 'CRITICAL',
                        'category': 'daily_usage',
                        'provider': provider,
                        'key_index': i,
                        'model_type': model_type,
                        'message': f"{provider} key {i+1} {model_type}: {day_usage_pct:.1%} of daily limit used",
                        'recommendation': "Switch to next key immediately"
                    })
                    exhausted_keys += 1
                elif day_usage_pct >= self.alert_thresholds['daily_usage_warning']:
                    alerts.append({
                        'type': 'WARNING',
                        'category': 'daily_usage',
                        'provider': provider,
                        'key_index': i,
                        'model_type': model_type,
                        'message': f"{provider} key {i+1} {model_type}: {day_usage_pct:.1%} of daily limit used",
                        'recommendation': "Monitor closely, prepare to switch key"
                    })
                
                # Hourly usage alerts
                hour_usage_pct = status['usage_percentages'].get('minute', 0) * 60  # Approximate
                if hour_usage_pct >= self.alert_thresholds['hourly_usage_warning']:
                    alerts.append({
                        'type': 'WARNING',
                        'category': 'hourly_usage',
                        'provider': provider,
                        'key_index': i,
                        'model_type': model_type,
                        'message': f"{provider} key {i+1} {model_type}: High hourly usage detected",
                        'recommendation': "Reduce request frequency or switch key"
                    })
                
                total_usage += status['day_usage']
        
        # Check key exhaustion
        if exhausted_keys >= self.alert_thresholds['key_exhaustion_warning']:
            alerts.append({
                'type': 'CRITICAL',
                'category': 'key_exhaustion',
                'provider': provider,
                'message': f"{exhausted_keys} keys exhausted for {provider}",
                'recommendation': "Consider paid tier migration or wait for reset"
            })
        
        return alerts
    
    def send_alerts(self, alerts: List[dict]):
        """Send alerts via configured channels"""
        if not alerts:
            return
        
        # Console alerts (always enabled)
        self._send_console_alerts(alerts)
        
        # File alerts (for logging)
        self._send_file_alerts(alerts)
        
        # Future: Email, Slack, Discord, etc.
    
    def _send_console_alerts(self, alerts: List[dict]):
        """Send alerts to console"""
        print("\n" + "🚨" * 20)
        print("FREE TIER ALERTS")
        print("🚨" * 20)
        
        for alert in alerts:
            icon = "🔴" if alert['type'] == 'CRITICAL' else "🟡"
            print(f"{icon} {alert['type']}: {alert['message']}")
            print(f"   💡 {alert['recommendation']}")
        
        print("🚨" * 20 + "\n")
```

---

## 🎯 **MIGRATION PLANNING**

### **📅 Paid Tier Migration Strategy**
```yaml
Migration Triggers:
  usage_based:
    - "Daily free tier exhaustion > 3 days/week"
    - "Monthly equivalent cost > $300"
    - "Development velocity significantly impacted"
  
  time_based:
    - "After 3 months of consistent development"
    - "Before production deployment"
    - "When team size > 2 developers"
  
  feature_based:
    - "Need for higher rate limits"
    - "Requirement for premium models"
    - "SLA requirements for production"

Migration Plan:
  phase_1: "Single paid account for primary developer"
  phase_2: "Team account with shared billing"
  phase_3: "Production-grade setup with monitoring"
  
Cost Optimization Post-Migration:
  - "Maintain free tier keys for development"
  - "Use paid tier only for production/critical tasks"
  - "Implement advanced caching and optimization"
```

### **💰 Cost Optimization Roadmap**
```python
class CostOptimizationPlanner:
    def __init__(self):
        self.optimization_strategies = [
            {
                'name': 'Advanced Caching',
                'potential_savings': 0.4,  # 40% reduction
                'implementation_effort': 'Medium',
                'timeline': '1 week'
            },
            {
                'name': 'Prompt Optimization',
                'potential_savings': 0.25,  # 25% reduction
                'implementation_effort': 'Low',
                'timeline': '2 days'
            },
            {
                'name': 'Model Selection Optimization',
                'potential_savings': 0.3,  # 30% reduction
                'implementation_effort': 'Medium',
                'timeline': '1 week'
            },
            {
                'name': 'Request Batching',
                'potential_savings': 0.2,  # 20% reduction
                'implementation_effort': 'High',
                'timeline': '2 weeks'
            }
        ]
    
    def calculate_optimization_potential(self, current_monthly_cost: float) -> dict:
        """Calculate potential cost savings"""
        total_potential_savings = 0
        optimization_plan = []
        
        for strategy in self.optimization_strategies:
            savings = current_monthly_cost * strategy['potential_savings']
            total_potential_savings += savings
            
            optimization_plan.append({
                **strategy,
                'monthly_savings': savings,
                'roi_timeline': self._calculate_roi_timeline(strategy)
            })
        
        return {
            'current_cost': current_monthly_cost,
            'potential_savings': total_potential_savings,
            'optimized_cost': current_monthly_cost - total_potential_savings,
            'optimization_plan': sorted(optimization_plan, key=lambda x: x['monthly_savings'], reverse=True)
        }
```

---

**💳 FREE TIER MANAGEMENT - Maximizando valor, minimizando custos**

*Última atualização: 2025-01-22*
*Próxima revisão: Semanal (toda segunda-feira)*