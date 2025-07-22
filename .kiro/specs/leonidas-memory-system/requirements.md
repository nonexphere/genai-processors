# Sistema de Memória e Contexto Avançado - Leonidas

## Introdução

Este documento especifica um sistema avançado de controle de contexto e memória para o Leonidas, permitindo persistência de conhecimento entre sessões e melhor continuidade conversacional. O sistema implementará um arquivo `summary.txt` que mantém o conhecimento acumulado, histórico de sessões estruturado, e processamento inteligente de resumos usando modelos Gemini.

## Requisitos

### Requisito 1: Sistema de Histórico de Sessões

**User Story:** Como desenvolvedor usando Leonidas, eu quero que todas as conversas sejam automaticamente salvas em arquivos de histórico únicos, para que eu possa revisar interações passadas e o sistema possa aprender com elas.

#### Acceptance Criteria

1. WHEN uma nova sessão do Leonidas é iniciada THEN o sistema SHALL criar um novo arquivo de histórico com timestamp único no formato `history_YYYYMMDD_HHMMSS.json`
2. WHEN uma interação ocorre durante a sessão THEN o sistema SHALL registrar no histórico atual: timestamp, role (user/assistant/system), conteúdo, metadata relevante, e estado do agente
3. WHEN a sessão é encerrada THEN o sistema SHALL finalizar e fechar o arquivo de histórico atual
4. WHEN múltiplas sessões são executadas THEN cada sessão SHALL ter seu próprio arquivo de histórico separado
5. WHEN o sistema precisa acessar histórico THEN ele SHALL conseguir listar e carregar arquivos de histórico por data/timestamp

### Requisito 2: Sistema de Resumo Persistente

**User Story:** Como usuário do Leonidas, eu quero que o sistema mantenha um resumo cumulativo de todas as interações passadas, para que ele tenha contexto sobre conversas anteriores e possa fornecer continuidade entre sessões.

#### Acceptance Criteria

1. WHEN o sistema é inicializado pela primeira vez THEN ele SHALL criar um arquivo `summary.txt` vazio se não existir
2. WHEN uma sessão é encerrada THEN o sistema SHALL processar o histórico da sessão usando um modelo Gemini para gerar um resumo estruturado
3. WHEN um resumo de sessão é gerado THEN ele SHALL ser integrado ao `summary.txt` existente, preservando informações importantes e removendo redundâncias
4. WHEN o `summary.txt` exceder um tamanho limite THEN o sistema SHALL comprimir automaticamente seções mais antigas mantendo informações críticas
5. WHEN uma nova sessão inicia THEN o sistema SHALL carregar o conteúdo do `summary.txt` como contexto inicial

### Requisito 3: Processador de Resumo Inteligente

**User Story:** Como sistema Leonidas, eu quero processar automaticamente históricos de sessão para extrair insights, decisões importantes, e contexto relevante, para que eu possa manter continuidade inteligente entre sessões.

#### Acceptance Criteria

1. WHEN o processador de resumo é acionado THEN ele SHALL usar um modelo Gemini (gemini-2.0-flash-live-001) para analisar o histórico da sessão
2. WHEN o histórico é processado THEN o sistema SHALL extrair: tópicos principais discutidos, decisões tomadas, tarefas pendentes, preferências do usuário, e contexto técnico relevante
3. WHEN um resumo é gerado THEN ele SHALL ser estruturado em seções: contexto_geral, decisoes_importantes, tarefas_pendentes, preferencias_usuario, e contexto_tecnico
4. WHEN múltiplos resumos existem THEN o sistema SHALL consolidá-los inteligentemente, evitando duplicação e mantendo informações mais recentes
5. WHEN o resumo é muito longo THEN o sistema SHALL aplicar compressão inteligente mantendo informações críticas

### Requisito 4: Inicialização Contextual Inteligente

**User Story:** Como usuário do Leonidas, eu quero que ele se lembre de conversas anteriores e contexto relevante quando inicio uma nova sessão, para que não precise repetir informações e ele possa continuar de onde paramos.

#### Acceptance Criteria

1. WHEN o Leonidas inicia uma nova sessão THEN ele SHALL carregar automaticamente o conteúdo do `summary.txt` como contexto inicial
2. WHEN o contexto inicial é carregado THEN o sistema SHALL usar a função `think` para processar o resumo e decidir como abordar a nova sessão
3. WHEN o processamento inicial é concluído THEN o Leonidas SHALL decidir se deve: cumprimentar mencionando contexto relevante, fazer perguntas de continuidade, ou aguardar silenciosamente
4. WHEN não há resumo disponível (primeira execução) THEN o sistema SHALL inicializar com comportamento padrão de primeira sessão
5. WHEN o resumo contém tarefas pendentes THEN o Leonidas SHALL mencioná-las proativamente na inicialização

### Requisito 5: Gerenciamento de Memória Durante Sessão

**User Story:** Como sistema Leonidas, eu quero gerenciar eficientemente a memória de conversação durante uma sessão ativa, para que eu possa manter contexto relevante sem exceder limites de token ou memória.

#### Acceptance Criteria

1. WHEN a memória de conversação atual excede um limite definido THEN o sistema SHALL aplicar compressão inteligente mantendo contexto crítico
2. WHEN informações importantes são identificadas durante a conversa THEN elas SHALL ser marcadas para preservação no resumo final
3. WHEN o usuário referencia conversas anteriores THEN o sistema SHALL conseguir acessar tanto o contexto da sessão atual quanto o resumo histórico
4. WHEN múltiplos tópicos são discutidos THEN o sistema SHALL organizar o contexto por tópicos para facilitar recuperação
5. WHEN a sessão é longa THEN o sistema SHALL periodicamente consolidar contexto antigo mantendo fluidez conversacional