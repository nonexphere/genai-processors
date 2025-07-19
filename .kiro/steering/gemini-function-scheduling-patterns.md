# Gemini Function Calling & Scheduling Patterns

## 📋 **FUNCTION CALLING & SCHEDULING COMPLETE GUIDE**

This steering rule provides comprehensive patterns for advanced function calling, scheduling, and async function management in Gemini Live API applications, based on analysis of Leonidas and production implementations.

## 🔧 **FUNCTION CALLING ARCHITECTURE**

### **1. Advanced Function Declaration System**

#### **Comprehensive Function Declaration Manager**
```python
from google.genai import types as genai_types
import asyncio
import time
import uuid
from typing import Dict, List, Callable, Optional, Any
from enum import Enum
import dataclasses

class FunctionBehavior(Enum):
    """Function execution behaviors."""
    BLOCKING = "BLOCKING"
    NON_BLOCKING = "NON_BLOCKING"

class FunctionScheduling(Enum):
    """Function response scheduling strategies."""
    WHEN_IDLE = "WHEN_IDLE"
    INTERRUPT = "INTERRUPT"
    SILENT = "SILENT"
    IMMEDIATE = "IMMEDIATE"

@dataclasses.dataclass
class FunctionCallContext:
    """Context for function call execution."""
    call_id: str
    function_name: str
    arguments: dict
    start_time: float
    behavior: FunctionBehavior
    scheduling: FunctionScheduling
    metadata: dict = dataclasses.field(default_factory=dict)
    result: Optional[Any] = None
    error: Optional[str] = None
    completed: bool = False

class AdvancedFunctionManager:
    """Advanced function calling and scheduling manager."""
    
    def __init__(self, session):
        self.session = session
        self.registered_functions = {}
        self.active_calls = {}
        self.call_history = collections.deque(maxlen=1000)
        
        # Scheduling queues
        self.idle_queue = asyncio.Queue()
        self.interrupt_queue = asyncio.Queue()
        self.immediate_queue = asyncio.Queue()
        
        # Processing state
        self.is_processing = False
        self.processing_tasks = []
        
        # Metrics
        self.function_metrics = {
            'total_calls': 0,
            'successful_calls': 0,
            'failed_calls': 0,
            'average_execution_time': 0.0,
            'calls_by_function': collections.defaultdict(int),
            'calls_by_scheduling': collections.defaultdict(int)
        }
    
    def register_function(self, 
                         name: str,
                         description: str,
                         handler: Callable,
                         behavior: FunctionBehavior = FunctionBehavior.NON_BLOCKING,
                         parameters: Optional[dict] = None,
                         default_scheduling: FunctionScheduling = FunctionScheduling.WHEN_IDLE) -> genai_types.FunctionDeclaration:
        """Register a function with advanced configuration."""
        
        # Create function declaration
        function_declaration = genai_types.FunctionDeclaration(
            name=name,
            description=description,
            behavior=behavior.value,
            parameters=parameters or {
                'type': 'object',
                'properties': {},
                'required': []
            }
        )
        
        # Store function metadata
        self.registered_functions[name] = {
            'declaration': function_declaration,
            'handler': handler,
            'behavior': behavior,
            'default_scheduling': default_scheduling,
            'call_count': 0,
            'success_count': 0,
            'error_count': 0
        }
        
        return function_declaration
    
    async def handle_function_call(self, function_call) -> str:
        """Handle incoming function call from Gemini."""
        call_id = function_call.id
        function_name = function_call.name
        arguments = function_call.args if hasattr(function_call, 'args') else {}
        
        # Create call context
        context = FunctionCallContext(
            call_id=call_id,
            function_name=function_name,
            arguments=arguments,
            start_time=time.time(),
            behavior=FunctionBehavior.NON_BLOCKING,  # Default from Gemini
            scheduling=self.registered_functions.get(function_name, {}).get('default_scheduling', FunctionScheduling.WHEN_IDLE)
        )
        
        # Store active call
        self.active_calls[call_id] = context
        
        # Update metrics
        self.function_metrics['total_calls'] += 1
        self.function_metrics['calls_by_function'][function_name] += 1
        
        # Execute function
        try:
            if function_name in self.registered_functions:
                handler = self.registered_functions[function_name]['handler']
                
                # Execute handler
                if asyncio.iscoroutinefunction(handler):
                    result = await handler(context)
                else:
                    result = handler(context)
                
                context.result = result
                context.completed = True
                
                # Update function-specific metrics
                self.registered_functions[function_name]['call_count'] += 1
                self.registered_functions[function_name]['success_count'] += 1
                self.function_metrics['successful_calls'] += 1
                
            else:
                raise ValueError(f"Unknown function: {function_name}")
                
        except Exception as e:
            context.error = str(e)
            context.completed = True
            
            # Update error metrics
            if function_name in self.registered_functions:
                self.registered_functions[function_name]['error_count'] += 1
            self.function_metrics['failed_calls'] += 1
            
            logging.error(f"Function call error [{function_name}]: {e}")
        
        # Calculate execution time
        execution_time = time.time() - context.start_time
        
        # Update average execution time
        total_calls = self.function_metrics['total_calls']
        current_avg = self.function_metrics['average_execution_time']
        self.function_metrics['average_execution_time'] = (
            (current_avg * (total_calls - 1) + execution_time) / total_calls
        )
        
        # Add to history
        self.call_history.append(context)
        
        # Schedule response based on function configuration
        await self._schedule_function_response(context)
        
        return call_id
    
    async def _schedule_function_response(self, context: FunctionCallContext):
        """Schedule function response based on scheduling strategy."""
        
        self.function_metrics['calls_by_scheduling'][context.scheduling.value] += 1
        
        if context.scheduling == FunctionScheduling.IMMEDIATE:
            await self.immediate_queue.put(context)
        elif context.scheduling == FunctionScheduling.INTERRUPT:
            await self.interrupt_queue.put(context)
        elif context.scheduling == FunctionScheduling.WHEN_IDLE:
            await self.idle_queue.put(context)
        elif context.scheduling == FunctionScheduling.SILENT:
            # Send silent response immediately
            await self._send_silent_response(context)
        
        # Start processing if not already running
        if not self.is_processing:
            await self._start_response_processing()
    
    async def _start_response_processing(self):
        """Start response processing tasks."""
        if self.is_processing:
            return
        
        self.is_processing = True
        
        # Start processing tasks for different scheduling types
        immediate_task = asyncio.create_task(self._process_immediate_responses())
        interrupt_task = asyncio.create_task(self._process_interrupt_responses())
        idle_task = asyncio.create_task(self._process_idle_responses())
        
        self.processing_tasks = [immediate_task, interrupt_task, idle_task]
    
    async def _process_immediate_responses(self):
        """Process immediate function responses."""
        while self.is_processing:
            try:
                context = await asyncio.wait_for(self.immediate_queue.get(), timeout=1.0)
                await self._send_function_response(context)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logging.error(f"Immediate response processing error: {e}")
    
    async def _process_interrupt_responses(self):
        """Process interrupt function responses."""
        while self.is_processing:
            try:
                context = await asyncio.wait_for(self.interrupt_queue.get(), timeout=1.0)
                await self._send_function_response(context, scheduling=genai_types.FunctionResponseScheduling.INTERRUPT)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logging.error(f"Interrupt response processing error: {e}")
    
    async def _process_idle_responses(self):
        """Process idle function responses."""
        while self.is_processing:
            try:
                context = await asyncio.wait_for(self.idle_queue.get(), timeout=1.0)
                await self._send_function_response(context, scheduling=genai_types.FunctionResponseScheduling.WHEN_IDLE)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logging.error(f"Idle response processing error: {e}")
    
    async def _send_function_response(self, 
                                    context: FunctionCallContext,
                                    scheduling: Optional[genai_types.FunctionResponseScheduling] = None):
        """Send function response to Gemini."""
        
        try:
            # Prepare response
            if context.error:
                response_data = {'error': context.error}
            else:
                response_data = context.result if context.result is not None else {}
            
            # Create function response
            function_response = genai_types.FunctionResponse(
                id=context.call_id,
                name=context.function_name,
                response=response_data,
                scheduling=scheduling or genai_types.FunctionResponseScheduling.WHEN_IDLE
            )
            
            # Send response
            await self.session.send_tool_response(function_responses=[function_response])
            
            logging.debug(f"Function response sent: {context.function_name} [{context.call_id}]")
            
        except Exception as e:
            logging.error(f"Failed to send function response: {e}")
    
    async def _send_silent_response(self, context: FunctionCallContext):
        """Send silent function response."""
        function_response = genai_types.FunctionResponse(
            id=context.call_id,
            name=context.function_name,
            response={},
            scheduling=genai_types.FunctionResponseScheduling.SILENT
        )
        
        await self.session.send_tool_response(function_responses=[function_response])
    
    async def cancel_function_call(self, call_id: str) -> bool:
        """Cancel an active function call."""
        if call_id in self.active_calls:
            context = self.active_calls[call_id]
            context.completed = True
            context.error = "Cancelled"
            
            # Send cancellation response
            await self._send_silent_response(context)
            
            del self.active_calls[call_id]
            return True
        
        return False
    
    async def stop_processing(self):
        """Stop function response processing."""
        self.is_processing = False
        
        # Cancel processing tasks
        for task in self.processing_tasks:
            if not task.done():
                task.cancel()
        
        if self.processing_tasks:
            await asyncio.gather(*self.processing_tasks, return_exceptions=True)
        
        self.processing_tasks.clear()
    
    def get_function_metrics(self) -> dict:
        """Get comprehensive function call metrics."""
        return {
            'overall': {
                'total_calls': self.function_metrics['total_calls'],
                'successful_calls': self.function_metrics['successful_calls'],
                'failed_calls': self.function_metrics['failed_calls'],
                'success_rate': (
                    self.function_metrics['successful_calls'] / max(1, self.function_metrics['total_calls'])
                ),
                'average_execution_time_ms': self.function_metrics['average_execution_time'] * 1000
            },
            'by_function': {
                name: {
                    'total_calls': info['call_count'],
                    'successful_calls': info['success_count'],
                    'failed_calls': info['error_count'],
                    'success_rate': info['success_count'] / max(1, info['call_count'])
                }
                for name, info in self.registered_functions.items()
            },
            'by_scheduling': dict(self.function_metrics['calls_by_scheduling']),
            'active_calls': len(self.active_calls),
            'queue_sizes': {
                'immediate': self.immediate_queue.qsize(),
                'interrupt': self.interrupt_queue.qsize(),
                'idle': self.idle_queue.qsize()
            }
        }
```

### **2. Leonidas-Style Function Implementations**

#### **Collaborative Agent Functions**
```python
class LeonidasFunctionHandlers:
    """Function handlers for Leonidas-style collaborative agents."""
    
    def __init__(self, agent_state_machine, input_queue: asyncio.Queue):
        self.state_machine = agent_state_machine
        self.input_queue = input_queue
        self.active_commentating_id = None
        self.wait_for_user_contexts = {}
    
    async def handle_start_commentating(self, context: FunctionCallContext) -> dict:
        """Handle start_commentating function call."""
        
        # Extract parameters
        message = context.arguments.get('message', 'Continue analysis...')
        analysis_type = context.arguments.get('analysis_type', 'general')
        focus_area = context.arguments.get('focus_area', '')
        
        # Store active commentating ID
        self.active_commentating_id = context.call_id
        
        # Update state machine
        await self.state_machine.transition(
            AgentAction.START_PROCESSING,
            {'function_call_id': context.call_id, 'analysis_type': analysis_type}
        )
        
        # Determine scheduling based on current state
        if self.state_machine.current_state == AgentState.SPEAKING:
            context.scheduling = FunctionScheduling.INTERRUPT
        else:
            context.scheduling = FunctionScheduling.WHEN_IDLE
        
        # Create response message
        response_message = self._create_commentating_message(message, analysis_type, focus_area)
        
        return {
            'output': response_message,
            'analysis_type': analysis_type,
            'focus_area': focus_area,
            'will_continue': True
        }
    
    async def handle_wait_for_user(self, context: FunctionCallContext) -> dict:
        """Handle wait_for_user function call."""
        
        # Extract parameters
        wait_reason = context.arguments.get('wait_reason', 'user_input')
        expected_duration = context.arguments.get('expected_duration', 30.0)
        
        # Store wait context
        self.wait_for_user_contexts[context.call_id] = {
            'start_time': time.time(),
            'wait_reason': wait_reason,
            'expected_duration': expected_duration
        }
        
        # Update state machine
        await self.state_machine.transition(
            AgentAction.WAIT_FOR_USER,
            {'function_call_id': context.call_id, 'wait_reason': wait_reason}
        )
        
        # Always use silent scheduling for wait_for_user
        context.scheduling = FunctionScheduling.SILENT
        
        # Schedule timeout if needed
        if expected_duration > 0:
            asyncio.create_task(
                self._handle_wait_timeout(context.call_id, expected_duration)
            )
        
        return {}  # Empty response for silent scheduling
    
    async def handle_analyze_context(self, context: FunctionCallContext) -> dict:
        """Handle context analysis function call."""
        
        analysis_focus = context.arguments.get('analysis_focus', 'general')
        include_visual = context.arguments.get('include_visual', True)
        include_audio = context.arguments.get('include_audio', True)
        
        # Perform context analysis
        analysis_result = await self._perform_context_analysis(
            analysis_focus, include_visual, include_audio
        )
        
        return {
            'analysis': analysis_result,
            'focus': analysis_focus,
            'timestamp': time.time()
        }
    
    def _create_commentating_message(self, base_message: str, analysis_type: str, focus_area: str) -> str:
        """Create contextual commentating message."""
        
        message_templates = {
            'code_review': f"Iniciando análise de código. {base_message}",
            'architecture_analysis': f"Analisando arquitetura do sistema. {base_message}",
            'debugging': f"Iniciando processo de debug. {base_message}",
            'general_collaboration': f"Continuando colaboração. {base_message}"
        }
        
        template = message_templates.get(analysis_type, base_message)
        
        if focus_area:
            template += f" Focando em: {focus_area}."
        
        return template
    
    async def _perform_context_analysis(self, focus: str, include_visual: bool, include_audio: bool) -> str:
        """Perform context analysis based on current state."""
        
        analysis_parts = []
        
        # Analyze current state
        current_state = self.state_machine.current_state
        analysis_parts.append(f"Estado atual: {current_state.value}")
        
        # Analyze recent activity
        if hasattr(self.state_machine, 'state_history'):
            recent_transitions = list(self.state_machine.state_history)[-5:]
            if recent_transitions:
                analysis_parts.append(f"Transições recentes: {len(recent_transitions)}")
        
        # Add focus-specific analysis
        if focus == 'performance':
            analysis_parts.append("Analisando métricas de performance...")
        elif focus == 'errors':
            analysis_parts.append("Verificando logs de erro...")
        elif focus == 'user_interaction':
            analysis_parts.append("Analisando padrões de interação do usuário...")
        
        return "; ".join(analysis_parts)
    
    async def _handle_wait_timeout(self, call_id: str, timeout_duration: float):
        """Handle wait_for_user timeout."""
        
        await asyncio.sleep(timeout_duration)
        
        # Check if still waiting
        if call_id in self.wait_for_user_contexts:
            wait_context = self.wait_for_user_contexts[call_id]
            
            # Send timeout message
            timeout_message = self._create_timeout_message(wait_context['wait_reason'])
            
            self.input_queue.put_nowait(
                content_api.ProcessorPart(
                    timeout_message,
                    role='system',
                    metadata={'timeout': True, 'original_call_id': call_id}
                )
            )
            
            # Clean up wait context
            del self.wait_for_user_contexts[call_id]
    
    def _create_timeout_message(self, wait_reason: str) -> str:
        """Create timeout message based on wait reason."""
        
        timeout_messages = {
            'user_input': 'Tempo limite para resposta do usuário. Retomando análise.',
            'action_required': 'Ação esperada não foi realizada. Continuando.',
            'processing_time': 'Tempo de processamento excedido. Prosseguindo.',
            'question_response': 'Pergunta não foi respondida. Continuando análise.'
        }
        
        return timeout_messages.get(wait_reason, 'Tempo limite atingido. Retomando.')
```

### **3. Advanced Function Scheduling Patterns**

#### **Dynamic Scheduling System**
```python
class DynamicFunctionScheduler:
    """Dynamic function scheduling based on context and priority."""
    
    def __init__(self):
        self.scheduling_rules = {}
        self.priority_queues = {
            'critical': asyncio.PriorityQueue(),
            'high': asyncio.PriorityQueue(),
            'normal': asyncio.PriorityQueue(),
            'low': asyncio.PriorityQueue()
        }
        self.context_analyzer = ContextAnalyzer()
    
    def add_scheduling_rule(self, 
                           function_name: str,
                           condition: Callable[[FunctionCallContext], bool],
                           scheduling: FunctionScheduling,
                           priority: str = 'normal'):
        """Add dynamic scheduling rule."""
        
        if function_name not in self.scheduling_rules:
            self.scheduling_rules[function_name] = []
        
        self.scheduling_rules[function_name].append({
            'condition': condition,
            'scheduling': scheduling,
            'priority': priority
        })
    
    async def determine_scheduling(self, context: FunctionCallContext) -> tuple[FunctionScheduling, str]:
        """Determine optimal scheduling for function call."""
        
        function_name = context.function_name
        
        # Check dynamic rules
        if function_name in self.scheduling_rules:
            for rule in self.scheduling_rules[function_name]:
                if rule['condition'](context):
                    return rule['scheduling'], rule['priority']
        
        # Analyze context for automatic scheduling
        context_analysis = await self.context_analyzer.analyze(context)
        
        # Determine scheduling based on context
        if context_analysis['urgency'] > 0.8:
            return FunctionScheduling.INTERRUPT, 'critical'
        elif context_analysis['urgency'] > 0.6:
            return FunctionScheduling.IMMEDIATE, 'high'
        elif context_analysis['can_wait']:
            return FunctionScheduling.WHEN_IDLE, 'normal'
        else:
            return FunctionScheduling.IMMEDIATE, 'normal'
    
    async def schedule_function_call(self, context: FunctionCallContext):
        """Schedule function call with dynamic priority."""
        
        scheduling, priority = await self.determine_scheduling(context)
        context.scheduling = scheduling
        
        # Add to appropriate priority queue
        priority_score = self._calculate_priority_score(context, priority)
        await self.priority_queues[priority].put((priority_score, context))
    
    def _calculate_priority_score(self, context: FunctionCallContext, priority: str) -> float:
        """Calculate priority score for queue ordering."""
        
        base_scores = {
            'critical': 1000,
            'high': 100,
            'normal': 10,
            'low': 1
        }
        
        base_score = base_scores.get(priority, 10)
        
        # Adjust based on function type
        function_adjustments = {
            'start_commentating': 1.2,
            'wait_for_user': 0.8,
            'analyze_context': 1.0
        }
        
        adjustment = function_adjustments.get(context.function_name, 1.0)
        
        # Consider age (older calls get higher priority)
        age_factor = time.time() - context.start_time
        
        return base_score * adjustment + age_factor

class ContextAnalyzer:
    """Analyze context for scheduling decisions."""
    
    async def analyze(self, context: FunctionCallContext) -> dict:
        """Analyze function call context."""
        
        analysis = {
            'urgency': 0.5,
            'can_wait': True,
            'user_waiting': False,
            'system_busy': False
        }
        
        # Analyze function type
        if context.function_name == 'start_commentating':
            analysis['urgency'] = 0.7
            analysis['can_wait'] = False
        elif context.function_name == 'wait_for_user':
            analysis['urgency'] = 0.3
            analysis['can_wait'] = True
            analysis['user_waiting'] = True
        
        # Analyze arguments for urgency indicators
        if 'urgent' in str(context.arguments).lower():
            analysis['urgency'] += 0.2
        
        if 'immediate' in str(context.arguments).lower():
            analysis['urgency'] += 0.3
            analysis['can_wait'] = False
        
        # Cap urgency at 1.0
        analysis['urgency'] = min(1.0, analysis['urgency'])
        
        return analysis
```

### **4. Function Call Monitoring & Analytics**

#### **Comprehensive Function Analytics**
```python
class FunctionCallAnalytics:
    """Comprehensive analytics for function calls."""
    
    def __init__(self):
        self.call_data = []
        self.performance_metrics = collections.defaultdict(list)
        self.error_patterns = collections.defaultdict(list)
        self.scheduling_effectiveness = collections.defaultdict(list)
    
    def record_function_call(self, context: FunctionCallContext):
        """Record function call for analytics."""
        
        call_record = {
            'timestamp': context.start_time,
            'function_name': context.function_name,
            'execution_time': time.time() - context.start_time if context.completed else None,
            'success': context.completed and context.error is None,
            'error': context.error,
            'scheduling': context.scheduling.value,
            'arguments': context.arguments,
            'metadata': context.metadata
        }
        
        self.call_data.append(call_record)
        
        # Update performance metrics
        if call_record['execution_time'] is not None:
            self.performance_metrics[context.function_name].append(call_record['execution_time'])
        
        # Record errors
        if call_record['error']:
            self.error_patterns[context.function_name].append({
                'error': call_record['error'],
                'timestamp': call_record['timestamp'],
                'arguments': call_record['arguments']
            })
        
        # Record scheduling effectiveness
        self.scheduling_effectiveness[context.scheduling.value].append({
            'function': context.function_name,
            'success': call_record['success'],
            'execution_time': call_record['execution_time']
        })
    
    def generate_analytics_report(self) -> dict:
        """Generate comprehensive analytics report."""
        
        if not self.call_data:
            return {'status': 'no_data'}
        
        total_calls = len(self.call_data)
        successful_calls = len([call for call in self.call_data if call['success']])
        
        # Function performance analysis
        function_performance = {}
        for func_name, exec_times in self.performance_metrics.items():
            if exec_times:
                function_performance[func_name] = {
                    'average_execution_time_ms': (sum(exec_times) / len(exec_times)) * 1000,
                    'min_execution_time_ms': min(exec_times) * 1000,
                    'max_execution_time_ms': max(exec_times) * 1000,
                    'call_count': len(exec_times)
                }
        
        # Error analysis
        error_analysis = {}
        for func_name, errors in self.error_patterns.items():
            if errors:
                error_types = collections.Counter([error['error'] for error in errors])
                error_analysis[func_name] = {
                    'total_errors': len(errors),
                    'error_types': dict(error_types),
                    'error_rate': len(errors) / len([call for call in self.call_data if call['function_name'] == func_name])
                }
        
        # Scheduling effectiveness
        scheduling_analysis = {}
        for scheduling_type, calls in self.scheduling_effectiveness.items():
            if calls:
                success_rate = len([call for call in calls if call['success']]) / len(calls)
                avg_exec_time = sum([call['execution_time'] for call in calls if call['execution_time']]) / len([call for call in calls if call['execution_time']])
                
                scheduling_analysis[scheduling_type] = {
                    'call_count': len(calls),
                    'success_rate': success_rate,
                    'average_execution_time_ms': avg_exec_time * 1000 if avg_exec_time else 0
                }
        
        return {
            'overview': {
                'total_calls': total_calls,
                'successful_calls': successful_calls,
                'success_rate': successful_calls / total_calls,
                'unique_functions': len(set([call['function_name'] for call in self.call_data]))
            },
            'function_performance': function_performance,
            'error_analysis': error_analysis,
            'scheduling_effectiveness': scheduling_analysis,
            'recommendations': self._generate_recommendations()
        }
    
    def _generate_recommendations(self) -> list:
        """Generate optimization recommendations."""
        recommendations = []
        
        # Check for slow functions
        for func_name, exec_times in self.performance_metrics.items():
            if exec_times:
                avg_time = sum(exec_times) / len(exec_times)
                if avg_time > 1.0:  # > 1 second
                    recommendations.append(f"Function '{func_name}' has high execution time ({avg_time:.2f}s)")
        
        # Check error rates
        for func_name, errors in self.error_patterns.items():
            func_calls = len([call for call in self.call_data if call['function_name'] == func_name])
            error_rate = len(errors) / func_calls if func_calls > 0 else 0
            
            if error_rate > 0.1:  # > 10% error rate
                recommendations.append(f"Function '{func_name}' has high error rate ({error_rate:.1%})")
        
        # Check scheduling effectiveness
        for scheduling_type, calls in self.scheduling_effectiveness.items():
            if calls:
                success_rate = len([call for call in calls if call['success']]) / len(calls)
                if success_rate < 0.9:  # < 90% success rate
                    recommendations.append(f"Scheduling type '{scheduling_type}' has low success rate ({success_rate:.1%})")
        
        return recommendations
```

This comprehensive function calling and scheduling guide provides all the patterns needed for sophisticated real-time applications with advanced function management, dynamic scheduling, and comprehensive analytics.