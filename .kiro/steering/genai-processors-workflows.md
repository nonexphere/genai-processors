# GenAI Processors Complex Workflow Patterns

## Advanced Workflow Architectures

### Multi-Agent Orchestration
```python
class MultiAgentOrchestrator(processor.Processor):
  """Orchestrate multiple specialized agents for complex tasks."""
  
  def __init__(self, agents: dict[str, processor.Processor]):
    self.agents = agents
    self.router = AgentRouter(agents.keys())
  
  async def call(self, content: AsyncIterable[content_api.ProcessorPart]) -> AsyncIterable[content_api.ProcessorPartTypes]:
    async for part in content:
      # Route to appropriate agent based on content analysis
      agent_name = await self.router.select_agent(part)
      selected_agent = self.agents[agent_name]
      
      # Process with selected agent
      async for result in selected_agent(streams.stream_content([part])):
        # Add agent metadata
        result.metadata['processed_by'] = agent_name
        yield result

# Usage example
research_agent = ResearchProcessor()
analysis_agent = AnalysisProcessor()  
creative_agent = CreativeProcessor()

orchestrator = MultiAgentOrchestrator({
  'research': research_agent,
  'analysis': analysis_agent,
  'creative': creative_agent
})
```

### Hierarchical Processing Pipeline
```python
class HierarchicalPipeline(processor.Processor):
  """Multi-level processing with escalation and delegation."""
  
  def __init__(self):
    # Level 1: Fast, simple processing
    self.l1_processor = SimpleProcessor()
    # Level 2: More complex analysis
    self.l2_processor = ComplexProcessor()
    # Level 3: Expert-level processing
    self.l3_processor = ExpertProcessor()
  
  async def call(self, content: AsyncIterable[content_api.ProcessorPart]) -> AsyncIterable[content_api.ProcessorPartTypes]:
    async for part in content:
      # Try Level 1 first
      l1_result = await self._try_level_1(part)
      if l1_result.metadata.get('confidence', 0) > 0.8:
        yield l1_result
        continue
      
      # Escalate to Level 2
      l2_result = await self._try_level_2(part, l1_result)
      if l2_result.metadata.get('confidence', 0) > 0.7:
        yield l2_result
        continue
      
      # Final escalation to Level 3
      l3_result = await self._try_level_3(part, l1_result, l2_result)
      yield l3_result
```

### Event-Driven Workflow System
```python
class EventDrivenWorkflow(processor.Processor):
  """Process content based on detected events and triggers."""
  
  def __init__(self):
    self.event_detector = EventDetectionProcessor()
    self.event_handlers = {
      'user_question': QuestionAnsweringProcessor(),
      'image_analysis': ImageAnalysisProcessor(),
      'code_review': CodeReviewProcessor(),
      'document_summary': SummaryProcessor()
    }
    self.default_handler = DefaultProcessor()
  
  async def call(self, content: AsyncIterable[content_api.ProcessorPart]) -> AsyncIterable[content_api.ProcessorPartTypes]:
    async for part in content:
      # Detect events in the content
      events = await self._detect_events(part)
      
      if not events:
        # No specific events detected, use default handler
        async for result in self.default_handler(streams.stream_content([part])):
          yield result
      else:
        # Process each detected event
        for event in events:
          handler = self.event_handlers.get(event.type, self.default_handler)
          
          # Create event-specific context
          event_part = content_api.ProcessorPart(
            part.text,
            role=part.role,
            metadata={**part.metadata, 'event': event.to_dict()}
          )
          
          async for result in handler(streams.stream_content([event_part])):
            result.metadata['triggered_by'] = event.type
            yield result
```

### Adaptive Processing Pipeline
```python
class AdaptivePipeline(processor.Processor):
  """Pipeline that adapts based on content characteristics and performance."""
  
  def __init__(self):
    self.processors = {
      'fast': FastProcessor(),
      'balanced': BalancedProcessor(),
      'thorough': ThoroughProcessor()
    }
    self.performance_tracker = PerformanceTracker()
    self.content_analyzer = ContentComplexityAnalyzer()
  
  async def call(self, content: AsyncIterable[content_api.ProcessorPart]) -> AsyncIterable[content_api.ProcessorPartTypes]:
    async for part in content:
      # Analyze content complexity
      complexity = await self.content_analyzer.analyze(part)
      
      # Select processor based on complexity and performance history
      processor_type = self._select_processor(complexity)
      selected_processor = self.processors[processor_type]
      
      # Process and track performance
      start_time = time.time()
      results = []
      
      async for result in selected_processor(streams.stream_content([part])):
        results.append(result)
        yield result
      
      # Update performance metrics
      processing_time = time.time() - start_time
      self.performance_tracker.record(processor_type, complexity, processing_time, len(results))
  
  def _select_processor(self, complexity: float) -> str:
    """Select processor based on complexity and performance history."""
    if complexity < 0.3:
      return 'fast'
    elif complexity < 0.7:
      return 'balanced'
    else:
      return 'thorough'
```

## Specialized Workflow Patterns

### Research and Knowledge Synthesis
```python
class ResearchWorkflow(processor.Processor):
  """Comprehensive research workflow with multiple information sources."""
  
  def __init__(self, sources: dict[str, processor.Processor]):
    self.sources = sources  # e.g., {'web': WebSearchProcessor(), 'docs': DocumentProcessor()}
    self.synthesizer = KnowledgeSynthesizer()
    self.fact_checker = FactCheckingProcessor()
    self.report_generator = ReportGenerator()
  
  async def call(self, content: AsyncIterable[content_api.ProcessorPart]) -> AsyncIterable[content_api.ProcessorPartTypes]:
    async for query_part in content:
      # Phase 1: Parallel information gathering
      source_results = {}
      
      # Split query to all sources
      source_streams = streams.split(
        streams.stream_content([query_part]), 
        n=len(self.sources)
      )
      
      # Process with each source in parallel
      tasks = []
      for (source_name, source_processor), source_stream in zip(self.sources.items(), source_streams):
        task = context.create_task(
          self._gather_from_source(source_name, source_processor, source_stream)
        )
        tasks.append(task)
      
      # Collect results from all sources
      for task in tasks:
        source_name, results = await task
        source_results[source_name] = results
      
      # Phase 2: Synthesize information
      synthesis_input = self._prepare_synthesis_input(query_part, source_results)
      synthesized_info = await streams.gather_stream(
        self.synthesizer(streams.stream_content([synthesis_input]))
      )
      
      # Phase 3: Fact checking
      for info_part in synthesized_info:
        fact_checked = await streams.gather_stream(
          self.fact_checker(streams.stream_content([info_part]))
        )
        
        # Phase 4: Generate final report
        for checked_part in fact_checked:
          async for report_part in self.report_generator(streams.stream_content([checked_part])):
            yield report_part
```

### Real-time Monitoring and Response
```python
class MonitoringWorkflow(processor.Processor):
  """Real-time monitoring with automated response capabilities."""
  
  def __init__(self):
    self.anomaly_detector = AnomalyDetectionProcessor()
    self.alert_processor = AlertProcessor()
    self.response_generator = ResponseGenerator()
    self.action_executor = ActionExecutor()
    
    # Thresholds for different response levels
    self.thresholds = {
      'info': 0.3,
      'warning': 0.6,
      'critical': 0.8
    }
  
  async def call(self, content: AsyncIterable[content_api.ProcessorPart]) -> AsyncIterable[content_api.ProcessorPartTypes]:
    async for data_part in content:
      # Detect anomalies
      anomaly_results = await streams.gather_stream(
        self.anomaly_detector(streams.stream_content([data_part]))
      )
      
      for anomaly_part in anomaly_results:
        severity = anomaly_part.metadata.get('severity_score', 0.0)
        
        # Determine response level
        response_level = self._determine_response_level(severity)
        
        # Generate appropriate response
        if response_level:
          # Create alert
          alert_part = content_api.ProcessorPart(
            anomaly_part.text,
            metadata={
              **anomaly_part.metadata,
              'response_level': response_level,
              'timestamp': time.time()
            }
          )
          
          # Process alert
          async for alert in self.alert_processor(streams.stream_content([alert_part])):
            yield alert
          
          # Generate and execute response if critical
          if response_level == 'critical':
            async for response in self.response_generator(streams.stream_content([alert_part])):
              # Execute automated response
              async for action in self.action_executor(streams.stream_content([response])):
                yield action
        
        # Always yield the original analysis
        yield anomaly_part
```

### Content Transformation Pipeline
```python
class ContentTransformationPipeline(processor.Processor):
  """Multi-stage content transformation with quality control."""
  
  def __init__(self):
    self.stages = [
      ('preprocess', PreprocessingProcessor()),
      ('transform', TransformationProcessor()),
      ('enhance', EnhancementProcessor()),
      ('validate', ValidationProcessor()),
      ('postprocess', PostprocessingProcessor())
    ]
    self.quality_checker = QualityAssuranceProcessor()
    self.rollback_handler = RollbackProcessor()
  
  async def call(self, content: AsyncIterable[content_api.ProcessorPart]) -> AsyncIterable[content_api.ProcessorPartTypes]:
    async for input_part in content:
      current_part = input_part
      stage_history = []
      
      # Process through each stage
      for stage_name, stage_processor in self.stages:
        try:
          # Process current part
          stage_results = await streams.gather_stream(
            stage_processor(streams.stream_content([current_part]))
          )
          
          if not stage_results:
            raise ProcessingError(f"No output from stage: {stage_name}")
          
          # Quality check
          for result_part in stage_results:
            quality_score = await self._check_quality(result_part)
            
            if quality_score < 0.7:  # Quality threshold
              # Attempt rollback and retry
              yield processor.debug(f"Quality check failed at stage {stage_name}, attempting rollback")
              
              rollback_result = await self._attempt_rollback(
                stage_name, current_part, stage_history
              )
              
              if rollback_result:
                current_part = rollback_result
              else:
                # Rollback failed, use original
                yield processor.status(f"Rollback failed, using original content")
                current_part = input_part
                break
            else:
              current_part = result_part
              stage_history.append((stage_name, current_part))
        
        except Exception as e:
          yield processor.debug(f"Error in stage {stage_name}: {e}")
          # Attempt recovery
          current_part = await self._recover_from_error(stage_name, current_part, e)
      
      # Yield final result
      current_part.metadata['transformation_stages'] = [name for name, _ in stage_history]
      yield current_part
```

### Collaborative Processing Network
```python
class CollaborativeNetwork(processor.Processor):
  """Network of processors that collaborate and share information."""
  
  def __init__(self, processors: dict[str, processor.Processor]):
    self.processors = processors
    self.collaboration_manager = CollaborationManager()
    self.shared_memory = SharedMemoryStore()
  
  async def call(self, content: AsyncIterable[content_api.ProcessorPart]) -> AsyncIterable[content_api.ProcessorPartTypes]:
    async for part in content:
      # Determine which processors should collaborate on this content
      collaboration_plan = await self.collaboration_manager.plan_collaboration(part, self.processors.keys())
      
      if len(collaboration_plan.participants) == 1:
        # Single processor handling
        processor_name = collaboration_plan.participants[0]
        async for result in self.processors[processor_name](streams.stream_content([part])):
          yield result
      else:
        # Multi-processor collaboration
        yield from self._execute_collaboration(part, collaboration_plan)
  
  async def _execute_collaboration(self, part: content_api.ProcessorPart, plan: CollaborationPlan):
    """Execute collaborative processing plan."""
    session_id = f"collab_{time.time()}"
    
    # Initialize shared context
    await self.shared_memory.create_session(session_id, plan.participants)
    
    try:
      # Phase 1: Independent processing
      independent_results = {}
      for processor_name in plan.participants:
        processor_instance = self.processors[processor_name]
        
        # Add collaboration context
        collab_part = content_api.ProcessorPart(
          part.text,
          role=part.role,
          metadata={
            **part.metadata,
            'collaboration_session': session_id,
            'processor_role': plan.roles.get(processor_name, 'participant')
          }
        )
        
        results = await streams.gather_stream(
          processor_instance(streams.stream_content([collab_part]))
        )
        independent_results[processor_name] = results
        
        # Share results with other processors
        await self.shared_memory.store_results(session_id, processor_name, results)
      
      # Phase 2: Collaborative refinement
      for round_num in range(plan.collaboration_rounds):
        refined_results = {}
        
        for processor_name in plan.participants:
          # Get shared context from other processors
          shared_context = await self.shared_memory.get_shared_context(
            session_id, processor_name
          )
          
          # Create refinement input
          refinement_input = content_api.ProcessorPart(
            part.text,
            metadata={
              **part.metadata,
              'collaboration_session': session_id,
              'round': round_num,
              'shared_context': shared_context,
              'previous_results': independent_results.get(processor_name, [])
            }
          )
          
          # Refine results
          processor_instance = self.processors[processor_name]
          refined = await streams.gather_stream(
            processor_instance(streams.stream_content([refinement_input]))
          )
          refined_results[processor_name] = refined
          
          # Update shared memory
          await self.shared_memory.update_results(session_id, processor_name, refined)
        
        independent_results = refined_results
      
      # Phase 3: Final synthesis
      synthesis_input = content_api.ProcessorPart(
        part.text,
        metadata={
          **part.metadata,
          'collaboration_session': session_id,
          'all_results': independent_results,
          'synthesis_phase': True
        }
      )
      
      # Use designated synthesizer or primary processor
      synthesizer_name = plan.synthesizer or plan.participants[0]
      synthesizer = self.processors[synthesizer_name]
      
      async for final_result in synthesizer(streams.stream_content([synthesis_input])):
        final_result.metadata['collaboration_participants'] = plan.participants
        final_result.metadata['collaboration_session'] = session_id
        yield final_result
    
    finally:
      # Cleanup shared memory
      await self.shared_memory.cleanup_session(session_id)
```

## Workflow Composition Utilities

### Dynamic Pipeline Builder
```python
class DynamicPipelineBuilder:
  """Build processing pipelines dynamically based on requirements."""
  
  def __init__(self, processor_registry: dict[str, type]):
    self.registry = processor_registry
  
  def build_pipeline(self, config: dict) -> processor.Processor:
    """Build a pipeline from configuration."""
    pipeline_steps = []
    
    for step_config in config['steps']:
      step_type = step_config['type']
      step_params = step_config.get('params', {})
      
      if step_type == 'parallel':
        # Build parallel processors
        parallel_processors = []
        for parallel_config in step_config['processors']:
          parallel_processor = self._build_single_processor(parallel_config)
          parallel_processors.append(parallel_processor)
        
        pipeline_steps.append(processor.parallel(parallel_processors))
      
      elif step_type == 'conditional':
        # Build conditional processor
        condition_func = self._build_condition(step_config['condition'])
        true_processor = self._build_single_processor(step_config['true_branch'])
        false_processor = self._build_single_processor(step_config['false_branch'])
        
        conditional_processor = ConditionalProcessor(
          condition_func, true_processor, false_processor
        )
        pipeline_steps.append(conditional_processor)
      
      else:
        # Build single processor
        single_processor = self._build_single_processor(step_config)
        pipeline_steps.append(single_processor)
    
    # Chain all steps together
    return processor.chain(pipeline_steps)
```

### Workflow Monitoring and Analytics
```python
class WorkflowAnalytics(processor.Processor):
  """Add comprehensive analytics to any workflow."""
  
  def __init__(self, wrapped_processor: processor.Processor, analytics_config: dict):
    self.wrapped_processor = wrapped_processor
    self.config = analytics_config
    self.metrics_collector = MetricsCollector()
    self.performance_tracker = PerformanceTracker()
  
  async def call(self, content: AsyncIterable[content_api.ProcessorPart]) -> AsyncIterable[content_api.ProcessorPartTypes]:
    workflow_id = f"workflow_{time.time()}"
    
    async for part in content:
      # Start tracking
      start_time = time.time()
      input_metrics = self._analyze_input(part)
      
      try:
        # Process with wrapped processor
        results = []
        async for result in self.wrapped_processor(streams.stream_content([part])):
          results.append(result)
          yield result
        
        # Collect output metrics
        output_metrics = self._analyze_outputs(results)
        processing_time = time.time() - start_time
        
        # Record successful processing
        await self.metrics_collector.record_success(
          workflow_id, input_metrics, output_metrics, processing_time
        )
        
      except Exception as e:
        # Record failure
        processing_time = time.time() - start_time
        await self.metrics_collector.record_failure(
          workflow_id, input_metrics, str(e), processing_time
        )
        raise
  
  def get_analytics_report(self) -> dict:
    """Generate comprehensive analytics report."""
    return {
      'performance_metrics': self.performance_tracker.get_summary(),
      'success_rate': self.metrics_collector.get_success_rate(),
      'error_patterns': self.metrics_collector.get_error_patterns(),
      'throughput_analysis': self.metrics_collector.get_throughput_analysis()
    }
```

These advanced workflow patterns enable building sophisticated AI systems that can handle complex, multi-step processing requirements with proper error handling, monitoring, and adaptive behavior.