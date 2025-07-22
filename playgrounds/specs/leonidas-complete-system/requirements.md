# Leonidas Complete System - Requirements Document v1.4

## Introduction

O projeto Leonidas visa criar uma **interface de IA multimodal (voz e visão)** que atua como um **colaborador de desenvolvimento de software** baseado em uma arquitetura de **Federação de Agentes Especialistas Multicamadas**. Diferente de assistentes reativos passivos, Leonidas deve possuir a capacidade de **pensamento de ordem superior**, aprendizado contínuo e intervenção proativa (mas criteriosa) com insights e correções relevantes, simulando um parceiro de trabalho humano. 

Seu objetivo é não apenas responder a comandos, mas ser um parceiro que compreende o contexto, o estado do mundo e age de forma intencional. O sistema deve ser primariamente um **ouvinte atento**, falando apenas quando necessário, solicitado pelo usuário ou por um insight valioso de seus sistemas internos. Ele não preenche o silêncio.

**Objetivos Principais:**
- **Estabilidade e Modularidade:** Construir uma arquitetura robusta e flexível baseada em processadores desacoplados (Agentes Especialistas)
- **Comportamento Humano-Cêntrico:** O agente deve ser primariamente um ouvinte atento, falando apenas quando necessário
- **Inteligência Contextual (Modelo de Mundo):** Leonidas deve entender o que está sendo trabalhado, utilizando o histórico da conversa, análise do ambiente visual, sonoro e contexto de tarefas
- **Capacidades Flexíveis:** O agente deve ter a capacidade de realizar ações no ambiente e de raciocinar explicitamente sobre suas decisões
- **Aprendizado Contínuo:** A arquitetura deve suportar mecanismos para que Leonidas possa "aprender" e aprimorar seu desempenho

## Requirements

### Requirement 1: Arquitetura de Federação de Agentes Especialistas

**User Story:** Como um desenvolvedor, eu quero que Leonidas seja construído com uma arquitetura modular e robusta, para que o sistema seja estável, expansível e mantenha separação clara de responsabilidades.

#### Acceptance Criteria

1. WHEN o sistema é inicializado THEN deve instanciar múltiplos agentes especialistas independentes operando em paralelo
2. WHEN agentes se comunicam THEN deve usar exclusivamente o Barramento de Sinais Unificado com formato JSON padronizado
3. WHEN um agente falha THEN outros agentes devem continuar operando sem interrupção
4. WHEN novos agentes são adicionados THEN devem integrar-se sem modificar agentes existentes
5. WHEN o sistema processa entrada THEN apenas o Motor de Orquestração (Leonidas) pode gerar saída de áudio

### Requirement 2: Motor de Orquestração Principal (Leonidas Agent)

**User Story:** Como um usuário, eu quero interagir com um único ponto focal inteligente que orquestra todas as capacidades do sistema, para que tenha uma experiência coerente e natural.

#### Acceptance Criteria

1. WHEN recebe estímulo significativo THEN deve executar ciclo THINK-ACT explícito
2. WHEN está em estado THINKING THEN deve acessar current_world_state para contexto
3. WHEN recebe Sinal de Intervenção com prioridade alta THEN deve interromper ação atual
4. WHEN gera fala THEN deve enviar transcrição para context_bus como agent_utterance
5. WHEN executa ferramenta THEN deve enviar resultado para context_bus como tool_output
6. WHEN está em estado IDLE THEN deve permanecer em silêncio até receber estímulo

### Requirement 3: Barramento de Sinais Unificado

**User Story:** Como um arquiteto de sistema, eu quero um mecanismo de comunicação padronizado entre agentes, para que o sistema seja desacoplado e facilmente extensível.

#### Acceptance Criteria

1. WHEN agente envia sinal de contexto THEN deve usar substream_name='context_bus' com formato JSON padronizado
2. WHEN agente envia sinal de intervenção THEN deve usar substream_name='intervention_bus' com prioridade definida
3. WHEN múltiplos sinais de intervenção chegam THEN deve processar por ordem de prioridade (critical > high > medium > low)
4. WHEN sinal é malformado THEN deve ser rejeitado sem afetar outros sinais
5. WHEN agente se desconecta THEN barramento deve continuar operando para outros agentes

### Requirement 4: Agente de Percepção Visual

**User Story:** Como um usuário, eu quero que Leonidas perceba e entenda meu ambiente visual, para que possa colaborar de forma contextualizada com meu trabalho.

#### Acceptance Criteria

1. WHEN analisa frames de vídeo THEN deve emitir visual_state para context_bus periodicamente
2. WHEN detecta gesto explícito THEN deve emitir gesture_detected para intervention_bus com prioridade high
3. WHEN detecta evento visual crítico THEN deve emitir critical_event_visual com prioridade critical
4. WHEN nova pessoa entra no campo de visão THEN deve emitir new_presence com prioridade medium
5. WHEN não há atividade visual relevante THEN deve reduzir frequência de sinais

### Requirement 5: Agente de Análise de Diálogo

**User Story:** Como um usuário, eu quero que Leonidas entenda quem está falando e para quem, para que possa responder apropriadamente em conversas multi-participantes.

#### Acceptance Criteria

1. WHEN processa fala THEN deve identificar speaker_id único e consistente
2. WHEN fala é direcionada a Leonidas THEN deve definir target="LEONIDAS"
3. WHEN detecta pergunta direta ou comando THEN deve definir is_interrupt=true
4. WHEN classifica intenção THEN deve usar categorias predefinidas (QUERY, COMMAND, STATEMENT, etc.)
5. WHEN processa própria fala de Leonidas THEN deve usar speaker_id="LEONIDAS"

### Requirement 6: Agente de Análise Sonora

**User Story:** Como um usuário, eu quero que Leonidas perceba sons ambientais relevantes, para que possa reagir apropriadamente ao contexto sonoro do ambiente.

#### Acceptance Criteria

1. WHEN detecta sons rotineiros THEN deve emitir ambient_sound para context_bus
2. WHEN detecta som crítico ou disruptivo THEN deve emitir ambient_critical_sound para intervention_bus
3. WHEN detecta alarme ou sirene THEN deve usar prioridade critical
4. WHEN detecta silêncio prolongado THEN deve emitir NO_SOUND_DETECTED ocasionalmente
5. WHEN classifica som THEN deve incluir confidence score e duration_ms

### Requirement 7: Agente de Raciocínio Cognitivo

**User Story:** Como um usuário, eu quero que Leonidas tenha capacidade de pensamento profundo e análise de longo prazo, para que possa fornecer insights valiosos e correções inteligentes.

#### Acceptance Criteria

1. WHEN processa contexto acumulado THEN deve gerar world_model_summary periodicamente
2. WHEN identifica erro de Leonidas THEN deve emitir cognitive_correction com prioridade high
3. WHEN tem insight valioso THEN deve emitir cognitive_insight com prioridade apropriada
4. WHEN analisa sessão THEN deve gerar memory_update para persistência
5. WHEN opera THEN deve ter latência maior mas análise mais profunda que outros agentes

### Requirement 8: Modelo de Mundo (World Model)

**User Story:** Como um sistema inteligente, eu quero manter consciência global do estado atual, para que possa tomar decisões informadas e contextualmente apropriadas.

#### Acceptance Criteria

1. WHEN é atualizado THEN deve seguir estrutura JSON definida em WORLD_MODEL_SPEC
2. WHEN inclui timestamp THEN deve usar formato UTC padronizado
3. WHEN descreve sessão atual THEN deve incluir current_task e recent_actions
4. WHEN reporta estado sensorial THEN deve incluir active_speakers e visual_focus
5. WHEN inclui memória THEN deve referenciar snippets relevantes da MemoryStore

### Requirement 9: Sistema de Capacidades (Tools)

**User Story:** Como um usuário, eu quero que Leonidas possa executar ações práticas no ambiente, para que seja um colaborador efetivo e não apenas consultivo.

#### Acceptance Criteria

1. WHEN usa capacidade speak THEN deve gerar áudio e enviar transcrição para context_bus
2. WHEN usa capacidade listen THEN deve ativar VAD por duração especificada
3. WHEN usa capacidade think THEN deve registrar thought_process sem gerar áudio
4. WHEN usa execute_tool THEN deve invocar ferramenta externa e retornar resultado
5. WHEN usa update_system_config THEN deve modificar comportamento em tempo de execução

### Requirement 10: Integração com Gemini Live API

**User Story:** Como um desenvolvedor, eu quero que Leonidas use as capacidades mais avançadas do Gemini Live API, para que tenha performance e qualidade de conversação superiores.

#### Acceptance Criteria

1. WHEN se conecta THEN deve usar gemini-live-2.5-flash-preview para conversação principal
2. WHEN processa eventos visuais THEN deve usar gemini-2.5-flash-lite-preview-06-17 para detecção rápida
3. WHEN configura áudio THEN deve usar voice_name='Kore' para português brasileiro
4. WHEN gerencia contexto THEN deve implementar rolling prompts com compressão inteligente
5. WHEN detecta interrupção THEN deve usar interruption handling nativo da API

### Requirement 11: Gerenciamento de Memória e Contexto

**User Story:** Como um usuário, eu quero que Leonidas lembre de interações passadas e mantenha contexto de longo prazo, para que nossa colaboração seja contínua e evolutiva.

#### Acceptance Criteria

1. WHEN armazena informação THEN deve usar MemoryStore com formato JSONL inicialmente
2. WHEN recupera contexto THEN deve usar RAG (Retrieval Augmented Generation)
3. WHEN comprime contexto THEN deve preservar informações de alta importância
4. WHEN classifica importância THEN deve usar ImportanceClassifier com keywords e heurísticas
5. WHEN persiste sessão THEN deve salvar checkpoints periódicos

### Requirement 12: Configuração Dinâmica do Sistema

**User Story:** Como um usuário, eu quero poder ajustar o comportamento de Leonidas via linguagem natural, para que possa personalizar a experiência conforme minhas preferências.

#### Acceptance Criteria

1. WHEN recebe comando de configuração THEN deve usar update_system_config tool
2. WHEN altera speech_rate THEN deve afetar velocidade da fala imediatamente
3. WHEN modifica persona_style THEN deve ajustar tom e estilo de comunicação
4. WHEN ativa/desativa agentes THEN deve modificar active_agents list
5. WHEN ajusta verbosity_level THEN deve controlar detalhamento das respostas

### Requirement 13: Performance e Latência Real-time

**User Story:** Como um usuário, eu quero que Leonidas responda rapidamente e mantenha fluidez na conversação, para que a interação seja natural e eficiente.

#### Acceptance Criteria

1. WHEN processa áudio THEN deve manter latência TTFT menor que 500ms
2. WHEN gerencia buffers THEN deve evitar overruns e underruns
3. WHEN detecta eventos THEN deve processar com latência menor que 100ms
4. WHEN comprime contexto THEN deve manter performance sem degradação perceptível
5. WHEN monitora sistema THEN deve coletar métricas de performance continuamente

### Requirement 14: Robustez e Recuperação de Erros

**User Story:** Como um usuário, eu quero que Leonidas seja resiliente a falhas e se recupere graciosamente de erros, para que tenha uma experiência confiável.

#### Acceptance Criteria

1. WHEN agente falha THEN outros agentes devem continuar operando
2. WHEN conexão é perdida THEN deve tentar reconexão automática com backoff exponencial
3. WHEN recebe entrada malformada THEN deve rejeitar sem afetar processamento
4. WHEN detecta loop infinito THEN deve interromper e reportar erro
5. WHEN sistema sobrecarrega THEN deve degradar graciosamente mantendo funcionalidade core

### Requirement 15: Consciência Contextual Abrangente

**User Story:** Como um sistema inteligente, eu quero manter consciência contextual multifacetada (espacial, temporal, histórica e conversacional), para que possa tomar decisões informadas e contextualmente apropriadas.

#### Acceptance Criteria

1. WHEN mantém contexto espacial THEN deve conhecer localização física específica (ex: "P Sul, Ceilândia, Brasília-DF")
2. WHEN mantém contexto temporal THEN deve conhecer data e hora exatas atuais
3. WHEN mantém contexto histórico THEN deve conhecer eventos mundiais relevantes que moldam o presente
4. WHEN mantém contexto conversacional THEN deve lembrar de interações atuais e passadas para coerência
5. WHEN integra contextos THEN deve usar todos os tipos de contexto para informar decisões e respostas

### Requirement 16: Diarização e Autenticação de Múltiplos Falantes

**User Story:** Como um usuário em ambiente multi-participante, eu quero que Leonidas identifique e autentique diferentes falantes, para que possa interagir apropriadamente com cada pessoa.

#### Acceptance Criteria

1. WHEN múltiplas pessoas falam THEN deve separar e identificar N vozes distintas
2. WHEN isola voz individual THEN deve atribuir identificador único e persistente (ex: "Falante_A", "Falante_B")
3. WHEN reconhece falante conhecido THEN deve autenticar identidade usando características de voz
4. WHEN falante se dirige a Leonidas THEN deve identificar que a fala é direcionada a ele
5. WHEN responde THEN deve considerar identidade e histórico do falante específico

### Requirement 17: Mecanismo de Interrupção Inteligente

**User Story:** Como um usuário, eu quero que Leonidas possa ser interrompido graciosamente e fazer transições suaves, para que a conversação seja natural mesmo com eventos inesperados.

#### Acceptance Criteria

1. WHEN recebe sinal de interrupção de alta prioridade THEN deve pausar tarefa atual sem interromper abruptamente
2. WHEN evento crítico ocorre durante fala THEN deve fazer transição suave (ex: "com licença por esse barulho...")
3. WHEN retoma após interrupção THEN deve continuar contexto anterior de forma coerente
4. WHEN múltiplas interrupções ocorrem THEN deve priorizar por criticidade e relevância
5. WHEN interrupção é resolvida THEN deve retomar fluxo original ou adaptar conforme necessário

### Requirement 18: Controle Total por Linguagem Natural

**User Story:** Como um usuário, eu quero controlar e reconfigurar completamente o comportamento de Leonidas através de comandos em linguagem natural, para que possa personalizar a experiência dinamicamente.

#### Acceptance Criteria

1. WHEN recebe comando de velocidade THEN deve ajustar speech_rate imediatamente (ex: "fale mais devagar")
2. WHEN recebe comando de especialidade THEN deve adaptar estilo e vocabulário (ex: "explique como especialista em finanças")
3. WHEN recebe comando de personalidade THEN deve modificar tom e abordagem comunicativa
4. WHEN recebe comando de fluxo THEN deve alterar workflow e prioridades de processamento
5. WHEN recebe comando de configuração THEN deve modificar qualquer parâmetro do sistema via linguagem natural

### Requirement 19: Detecção Avançada de Eventos Sonoros

**User Story:** Como um usuário, eu quero que Leonidas identifique e classifique precisamente eventos sonoros não-verbais, para que possa reagir apropriadamente ao ambiente acústico.

#### Acceptance Criteria

1. WHEN detecta veículo THEN deve classificar tipo e intensidade (ex: "motocicleta em alta velocidade")
2. WHEN detecta alarme THEN deve identificar tipo específico (ex: "sirene de ambulância", "alarme de incêndio")
3. WHEN detecta evento doméstico THEN deve reconhecer ações cotidianas (ex: "porta batendo", "telefone tocando")
4. WHEN detecta múltiplos sons THEN deve separar e classificar eventos simultâneos
5. WHEN som afeta comunicação THEN deve adaptar volume e clareza da resposta

### Requirement 20: Memória Visual Associativa

**User Story:** Como um usuário, eu quero que Leonidas crie e mantenha memória visual de objetos e pessoas, para que possa reconhecer e referenciar elementos visuais ao longo do tempo.

#### Acceptance Criteria

1. WHEN vê objeto pela primeira vez THEN deve criar entrada na memória visual com características
2. WHEN reconhece objeto conhecido THEN deve associar com memória existente e histórico
3. WHEN pessoa entra em cena THEN deve tentar reconhecer face e associar com identidade conhecida
4. WHEN objetos interagem THEN deve registrar relações e padrões de interação
5. WHEN referencia visualmente THEN deve usar memória para contextualizar descrições e respostas

### Requirement 21: Implementação Incremental

**User Story:** Como um desenvolvedor, eu quero implementar o sistema em fases bem definidas, para que possa validar cada componente antes de adicionar complexidade.

#### Acceptance Criteria

1. WHEN implementa Fase 0 THEN deve ter estrutura básica e SystemConfig funcionando
2. WHEN implementa Fase 1 THEN deve ter percepção visual e diálogo básico com barramento
3. WHEN implementa Fase 2 THEN deve ter capacidade think() e tools básicas funcionando
4. WHEN implementa Fase 3 THEN deve ter análise sonora integrada
5. WHEN implementa Fase 4 THEN deve ter CognitiveReasoningAgent e World Model operacional
6. WHEN implementa Fase 5 THEN deve ter MemoryStore e capacidades avançadas completas