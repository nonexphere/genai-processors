# Leonidas Master Directive - Complete Project Navigation Map

## 🎯 **DIRETIVA MESTRE DO PROJETO LEONIDAS**

Este é o steering rule principal e mapa completo de navegação que direciona todo o desenvolvimento do projeto Leonidas. É o ponto de entrada único para entender a arquitetura, objetivos, recursos disponíveis e direcionamento estratégico do projeto.

---

## 📊 **VISÃO EXECUTIVA DO PROJETO**

### **🎯 Missão Central**
Leonidas é um **sistema de IA colaborativa em tempo real** projetado para funcionar como um **parceiro técnico sênior** que trabalha lado a lado com desenvolvedores, arquitetando, especificando e construindo software complexo.

### **🏆 Proposta de Valor Única**
- **Colaboração Técnica Real-time**: Conversação bidirecional com áudio e vídeo
- **Análise Contextual Inteligente**: Percepção visual do ambiente de desenvolvimento  
- **Arquitetura Cognitiva Dual**: Sistema 1 (reativo) + Sistema 2 (analítico)
- **Especialização Técnica**: Foco em arquitetura de software e desenvolvimento

### **📈 Status Atual: FASE 1 COMPLETA → FASE 2 PRONTA PARA INICIAR**
- ✅ **Sistema de conversação real-time funcional**
- ✅ **Detecção de eventos e tratamento de interrupções**
- ✅ **Integração Gemini Live API estável**
- 🔄 **Evolução arquitetural: de "comentarista" para "colaborador"**
- 📋 **Próximo: Sistema cognitivo avançado e memória persistente**

---

## 🏗️ **ARQUITETURA COMPLETA DO PROJETO**

### **📁 Estrutura de Diretórios (MAPA COMPLETO)**

```
genai-processors/                    # 🏠 ROOT PROJECT
├── leonidas/                        # 🎯 FOCO PRINCIPAL - PROJETO LEONIDAS
│   ├── leonidas.py                  # 🚀 IMPLEMENTAÇÃO PRINCIPAL (933 linhas)
│   ├── leonidas_cli.py              # 🖥️ Interface CLI robusta
│   ├── README.md                    # 📖 Documentação completa v2
│   ├── REQUIREMENTS.md              # 📋 Especificações detalhadas
│   └── tests/                       # 🧪 Testes automatizados
├── genai_processors/                # 📚 BIBLIOTECA CORE (20+ processadores)
│   ├── core/                        # 🔧 Processadores fundamentais
│   ├── contrib/                     # 🤝 Contribuições da comunidade
│   └── examples/                    # 💡 Exemplos de uso
├── .kiro/steering/                  # 🧭 STEERING RULES (16 documentos)
├── examples/                        # 🎨 Exemplos práticos
├── resource/                        # 📚 Recursos e documentação
├── logs/                           # 📊 Logs de sessão
├── README.md                        # 📖 Documentação principal do projeto
├── LEONIDAS_EXECUTIVE_SUMMARY.md   # 📊 Resumo executivo
├── pyproject.toml                   # ⚙️ Configuração do projeto Python
└── CONTRIBUTING.md                  # 🤝 Guia de contribuição
```

### **🎯 FOCO ABSOLUTO: PASTA `leonidas/`**

**ATENÇÃO CRÍTICA**: Todo desenvolvimento deve ser focado na pasta `leonidas/`. Esta contém:

- **`leonidas/leonidas.py`** (933 linhas) - Implementação principal com arquitetura modular
- **`leonidas/leonidas_cli.py`** - Interface CLI completa e robusta  
- **`leonidas/README.md`** - Documentação abrangente da v2
- **`leonidas/REQUIREMENTS.md`** - Especificações técnicas detalhadas (5 seções principais)
- **`leonidas/tests/`** - Suite de testes automatizados

---

## 🧭 **MAPA COMPLETO DE STEERING RULES**

### **📚 INVENTÁRIO COMPLETO (16 STEERING RULES)**

#### **🥇 TIER 1 - ESSENCIAIS PARA LEONIDAS (PRIORIDADE MÁXIMA)**
1. **`.kiro/steering/00_leonidas-main-directive.md`** - 🎯 **ESTE DOCUMENTO** - Diretiva mestre
2. **`.kiro/steering/gemini-models-complete-reference.md`** - 📖 Referência completa de modelos Gemini
3. **`.kiro/steering/gemini-live-api-implementation.md`** - 🔌 Implementação da API Live
4. **`.kiro/steering/gemini-function-scheduling-patterns.md`** - ⚙️ Function calling avançado

#### **🥈 TIER 2 - FUNCIONALIDADES AVANÇADAS (ALTA PRIORIDADE)**
5. **`.kiro/steering/gemini-performance-optimization.md`** - ⚡ Otimização de performance
6. **`.kiro/steering/gemini-state-machine-patterns.md`** - 🔄 Gerenciamento de estado
7. **`.kiro/steering/gemini-context-transcription-management.md`** - 💭 Contexto e transcrição
8. **`.kiro/steering/gemini-audio-processing-pipeline.md`** - 🎵 Processamento de áudio
9. **`.kiro/steering/gemini-realtime-systems-complete.md`** - ⏱️ Sistemas em tempo real

#### **🥉 TIER 3 - BIBLIOTECA GENAI-PROCESSORS (USAR SELETIVAMENTE)**
10. **`.kiro/steering/genai-processors-complete-reference.md`** - 📚 Referência completa da biblioteca
11. **`.kiro/steering/genai-processors-architecture.md`** - 🏗️ Arquitetura da biblioteca
12. **`.kiro/steering/genai-processors-development.md`** - 👨‍💻 Padrões de desenvolvimento
13. **`.kiro/steering/genai-processors-workflows.md`** - 🔄 Workflows complexos
14. **`.kiro/steering/genai-processors-integration.md`** - 🔗 Integração externa
15. **`.kiro/steering/genai-processors-caching.md`** - 💾 Sistema de cache
16. **`.kiro/steering/genai-processors-debugging.md`** - 🐛 Debug e observabilidade

### **🎯 ESTRATÉGIA DE USO DOS STEERING RULES**

#### **Para Desenvolvimento Principal (Leonidas):**
- **SEMPRE** consultar Tier 1 primeiro
- **FREQUENTEMENTE** usar Tier 2 para funcionalidades específicas
- **SELETIVAMENTE** consultar Tier 3 apenas quando necessário para genai-processors

#### **Para Resolução de Problemas:**
- **Performance**: `.kiro/steering/gemini-performance-optimization.md`
- **Bugs**: `.kiro/steering/genai-processors-debugging.md`
- **Estado**: `.kiro/steering/gemini-state-machine-patterns.md`
- **Áudio**: `.kiro/steering/gemini-audio-processing-pipeline.md`

---

## 🚀 **ROADMAP DETALHADO E PRIORIDADES**

### **📋 FASE 1: FUNDAÇÃO** ✅ **COMPLETA**
- ✅ Sistema básico de conversação em tempo real
- ✅ Detecção de eventos e tratamento de interrupções
- ✅ Implementação de máquina de estados
- ✅ Suporte multi-interface (CLI, WebSocket)
- ✅ Prompts em português brasileiro

### **🔄 FASE 2: INTELIGÊNCIA APRIMORADA** 📍 **ATUAL - PRONTA PARA INICIAR**
**Duração**: 2-3 semanas | **Status**: Pronto para desenvolvimento

#### **Semana 1: Otimização de Modelos**
- [ ] Migração para `gemini-2.0-flash-live-001` (estabilidade)
- [ ] Otimização de prompts para colaboração técnica
- [ ] Aprimoramento de declarações de função
- [ ] Implementação de monitoramento básico

#### **Semana 2: Sistema Cognitivo**
- [ ] Implementação do CognitiveAnalyzer (Sistema 2)
- [ ] Pipeline de processamento paralelo
- [ ] Lógica de intervenção e thresholds
- [ ] Integração de insights cognitivos

#### **Semana 3: Gerenciamento de Sessão**
- [ ] Logger estruturado de sessões
- [ ] Gerenciamento de estado de conversação
- [ ] Geração de resumos de sessão
- [ ] Memória básica entre turnos

### **📈 FASE 3: PRONTIDÃO PARA PRODUÇÃO** 🔮 **PLANEJADA**
**Duração**: 3-4 semanas | **Prioridade**: Média

- [ ] Sistema de memória persistente
- [ ] Monitoramento avançado e alertas
- [ ] Configurações específicas por ambiente
- [ ] Automação de deployment

### **🌟 FASE 4: RECURSOS AVANÇADOS** 🔮 **FUTURO**
**Duração**: 4-6 semanas | **Prioridade**: Baixa

- [ ] Suporte a colaboração multi-usuário
- [ ] Integração com ferramentas de desenvolvimento
- [ ] Capacidades de raciocínio avançado
- [ ] Fine-tuning de modelos customizados

---

## ⚙️ **ESPECIFICAÇÕES TÉCNICAS COMPLETAS**

### **🎛️ Stack Tecnológico Atual**
```yaml
Core Framework: genai-processors (biblioteca própria)
Linguagem: Python 3.11+
Modelos IA:
  - Principal: gemini-live-2.5-flash-preview (conversação)
  - Eventos: gemini-2.5-flash-lite-preview-06-17 (detecção)
  - Futuro: gemini-2.0-flash-live-001 (estabilidade)
Áudio:
  - Entrada: 16kHz PCM 16-bit
  - Saída: 24kHz PCM 16-bit  
  - Voz: Kore (otimizada para português)
Linguagem: Português Brasileiro
Interfaces: CLI, WebSocket
Deployment: Desenvolvimento local
```

### **🏗️ Arquitetura Modular Atual**
```python
# Arquitetura implementada em leonidas.py
InputManager → LeonidasOrchestrator → OutputManager
     ↓              ↓                    ↓
  Camera/Mic    Gemini Live API      Speakers
  Video/Audio   Tool Execution       Rate Limit
  Future I/O    State Management     Future I/O
```

### **🔧 Configuração Padrão Leonidas**
```python
LEONIDAS_CONFIG = types.LiveConnectConfig(
    response_modalities=["AUDIO"],
    system_instruction=LEONIDAS_SYSTEM_PROMPT,  # 5 seções principais
    speech_config={
        'language_code': 'pt-BR',
        'voice_config': {'prebuilt_voice_config': {'voice_name': 'Kore'}}
    },
    tools=LEONIDAS_TOOLS,  # 5 ferramentas avançadas
    media_resolution=types.MediaResolution.MEDIA_RESOLUTION_MEDIUM
)
```

### **🛠️ Sistema de Ferramentas Avançado**
```python
LEONIDAS_TOOLS = [
    'think',           # 🧠 Raciocínio obrigatório e verboso
    'change_state',    # 🔄 Gerenciamento de estado próprio
    'get_context',     # 💭 Acesso à memória de conversação
    'get_time',        # ⏰ Informações temporais
    'shutdown_system'  # 🔌 Desligamento controlado
]
```

---

## 📋 **DIRETRIZES DE DESENVOLVIMENTO COMPLETAS**

### **🎯 Princípios Fundamentais**
1. **FOCO ABSOLUTO**: Pasta `leonidas/` é o centro de tudo
2. **COLABORADOR, NÃO ASSISTENTE**: Leonidas é um parceiro técnico sênior
3. **PORTUGUÊS BRASILEIRO**: Toda implementação e comunicação
4. **MODULARIDADE**: Arquitetura InputManager → Orchestrator → OutputManager
5. **TEMPO REAL**: Conversação fluida com interrupção graceful

### **🔧 Padrões de Código Obrigatórios**
```python
# 1. Logging estruturado
logger.info("Operação", extra={'extra_data': structured_data})

# 2. Tratamento de erros graceful
try:
    result = await operation()
except Exception as e:
    logger.error(f"Erro: {e}")
    # Recuperação graceful

# 3. Função think obrigatória
await self._handle_think(call_id, {
    'analysis': 'Análise detalhada...',
    'reasoning': 'Processo de raciocínio...',
    'plan': 'Próxima ação...'
})

# 4. Gerenciamento de estado
await self.state_machine.transition(
    AgentAction.START_PROCESSING,
    {'context': 'informação relevante'}
)
```

### **🚫 O QUE EVITAR ABSOLUTAMENTE**
- ❌ Não trabalhar fora da pasta `leonidas/`
- ❌ Não usar modelos Gemini obsoletos
- ❌ Não implementar em inglês
- ❌ Não ignorar os steering rules Tier 1
- ❌ Não sobrecarregar com todos os steering rules simultaneamente
- ❌ Não quebrar a arquitetura modular estabelecida
- ❌ **NÃO REINVENTAR A RODA**: Não implementar funcionalidades que já existem ou podem ser compostas com `genai-processors`. A biblioteca é a fonte de verdade para padrões de processamento de stream.

---

## 🎯 **OBJETIVOS E MÉTRICAS DE SUCESSO**

### **📊 Métricas Técnicas**
- **Latência**: < 500ms para primeira resposta
- **Taxa de Sucesso**: > 95% de conversas completadas
- **Qualidade de Áudio**: Taxa de interrupção < 10%
- **Disponibilidade**: > 99% uptime em produção

### **👥 Métricas de Experiência**
- **Satisfação do Usuário**: > 4.5/5 em pesquisas
- **Produtividade**: Redução de 30% no tempo de desenvolvimento
- **Adoção**: > 80% dos desenvolvedores usando regularmente
- **Retenção**: > 90% de usuários ativos mensalmente

### **🎯 Objetivos por Fase**

#### **Curto Prazo (Fase 2 - Próximas 3 semanas):**
1. ✅ Finalizar sistema cognitivo avançado
2. ✅ Implementar memória de sessão
3. ✅ Otimizar performance para produção
4. ✅ Completar monitoramento básico

#### **Médio Prazo (Fase 3 - 1-2 meses):**
1. 🔄 Deploy em ambiente de produção
2. 🔄 Sistema de memória persistente
3. 🔄 Monitoramento avançado e alertas
4. 🔄 Configurações por ambiente

#### **Longo Prazo (Fase 4 - 3-6 meses):**
1. 🔮 Colaboração multi-usuário
2. 🔮 Integração com IDEs
3. 🔮 Capacidades de raciocínio avançado
4. 🔮 Fine-tuning customizado

---

## 🧭 **GUIA DE NAVEGAÇÃO E USO**

### **🚀 Para Desenvolvimento Ativo**
1. **SEMPRE** consulte este documento primeiro
2. **IDENTIFIQUE** qual Tier de steering rules você precisa
3. **FOQUE** na pasta `leonidas/` exclusivamente
4. **SIGA** os padrões de código estabelecidos
5. **TESTE** com métricas de qualidade definidas

### **🐛 Para Debugging e Troubleshooting**
1. **Performance**: Use `.kiro/steering/gemini-performance-optimization.md`
2. **Bugs de Estado**: Use `.kiro/steering/gemini-state-machine-patterns.md`
3. **Problemas de Áudio**: Use `.kiro/steering/gemini-audio-processing-pipeline.md`
4. **Erros de API**: Use `.kiro/steering/gemini-live-api-implementation.md`
5. **Logs**: Verifique pasta `logs/` com estrutura JSON

### **📚 Para Aprendizado e Referência**
1. **Conceitos Básicos**: `.kiro/steering/genai-processors-architecture.md`
2. **Padrões Avançados**: `.kiro/steering/genai-processors-workflows.md`
3. **Integração Externa**: `.kiro/steering/genai-processors-integration.md`
4. **Cache e Performance**: `.kiro/steering/genai-processors-caching.md`

### **🔄 Para Evolução Contínua**
1. **Monitore** métricas de sucesso definidas
2. **Atualize** este steering rule conforme evolução
3. **Mantenha** foco na missão central
4. **Documente** decisões arquiteturais importantes

---

## 💡 **RECURSOS E FERRAMENTAS DISPONÍVEIS**

### **📚 Biblioteca GenAI Processors (20+ Processadores)**
- **Audio I/O**: PyAudioIn, PyAudioOut, RateLimitAudio
- **Modelos**: GenaiModel, LiveProcessor, OllamaModel
- **Texto**: MatchProcessor, JinjaTemplate, Preamble
- **Visual**: VideoIn, EventDetection
- **Integração**: GoogleDrive, GitHub, PdfProcessor

### **🎨 Exemplos Práticos Disponíveis**
- **Real-time Live**: Audio-in/Audio-out com Google Search
- **Research Agent**: Agente de pesquisa com 3 sub-processadores
- **Live Commentary**: Agente de comentários com detecção de eventos

### **🔧 Ferramentas de Desenvolvimento**
- **CLI Robusta**: `leonidas/leonidas_cli.py` com argumentos completos
- **Logging Estruturado**: JSON logs com extra_data em `logs/`
- **Testes Automatizados**: Suite de testes em `leonidas/tests/`
- **Monitoramento**: Métricas de performance integradas

---

## 🔄 **PROCESSO DE EVOLUÇÃO CONTÍNUA**

### **📈 Atualizações Regulares**
Este steering rule deve ser atualizado a cada milestone importante, mantendo sempre:
- ✅ Foco na pasta `leonidas/`
- ✅ Priorização das fases de desenvolvimento
- ✅ Padrões específicos do projeto
- ✅ Integração com Gemini Live API
- ✅ Desenvolvimento em português brasileiro

### **🎯 Indicadores de Necessidade de Atualização**
- 🔄 Conclusão de fases do roadmap
- 🔄 Mudanças significativas na arquitetura
- 🔄 Novos steering rules adicionados
- 🔄 Feedback importante dos usuários
- 🔄 Mudanças nos modelos Gemini disponíveis

---

## 🏆 **CONCLUSÃO E CALL TO ACTION**

**Leonidas representa uma oportunidade única** de criar um assistente de IA verdadeiramente colaborativo para desenvolvimento de software. Com uma **base sólida implementada** (Fase 1 completa) e um **roadmap claro** para evolução, o projeto está posicionado para se tornar uma ferramenta essencial.

### **🎯 PRÓXIMOS PASSOS IMEDIATOS**
1. **INICIAR FASE 2**: Sistema cognitivo avançado
2. **OTIMIZAR MODELOS**: Migração para versões estáveis
3. **IMPLEMENTAR MONITORAMENTO**: Métricas de produção
4. **PREPARAR DEPLOY**: Ambiente de produção

### **📞 LEMBRE-SE**
- 🎯 **Este é o steering MESTRE** - consulte primeiro, sempre
- 📁 **Foco absoluto na pasta `leonidas/`**
- 🥇 **Tier 1 steering rules são essenciais**
- 🇧🇷 **Português brasileiro em tudo**
- 🤝 **Leonidas é um colaborador, não assistente**

---

**🚀 LEONIDAS V2 - Onde colaboração IA encontra inteligência humana.**
