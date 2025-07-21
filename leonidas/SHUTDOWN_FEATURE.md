# 🔴 Funcionalidade de Shutdown do Leonidas v2

## Visão Geral

O Leonidas v2 agora possui a capacidade de se desligar automaticamente quando solicitado pelo usuário. Esta funcionalidade foi implementada através de uma nova ferramenta (`shutdown_system`) que permite ao modelo Gemini controlar seu próprio ciclo de vida.

## Como Funciona

### 1. Solicitação do Usuário
O usuário pode solicitar o desligamento do sistema de várias formas:
- "Por favor, desligue o sistema"
- "Pode encerrar o Leonidas?"
- "Quero sair do programa"
- "Finalize a sessão"
- "Shutdown do sistema"

### 2. Processamento pelo Modelo
Quando o modelo detecta uma solicitação de shutdown, ele:

1. **Analisa** a solicitação usando a ferramenta `think`
2. **Confirma** com o usuário se realmente deseja desligar
3. **Executa** a ferramenta `shutdown_system` com confirmação
4. **Responde** com uma mensagem de despedida
5. **Sinaliza** para o sistema encerrar graciosamente

### 3. Encerramento Gracioso
O sistema principal detecta a solicitação de shutdown e:
- Para o loop de processamento
- Exibe mensagem informativa
- Encerra todos os recursos (áudio, conexões, etc.)
- Salva logs da sessão

## Implementação Técnica

### Nova Ferramenta: `shutdown_system`

```python
genai_types.FunctionDeclaration(
    name='shutdown_system',
    description=(
        'Desligue o sistema Leonidas quando solicitado pelo usuário. '
        'Use apenas quando o usuário explicitamente pedir para desligar, '
        'encerrar, sair ou finalizar o sistema. Confirme antes de executar.'
    ),
    behavior='NON_BLOCKING',
    parameters=genai_types.Schema(
        type=genai_types.Type.OBJECT,
        properties={
            'confirmation': genai_types.Schema(
                type=genai_types.Type.BOOLEAN,
                description='Confirmação de que o usuário realmente quer desligar o sistema'
            ),
            'reason': genai_types.Schema(
                type=genai_types.Type.STRING,
                description='Motivo para o desligamento (ex: solicitação do usuário, fim da sessão)'
            )
        },
        required=['confirmation', 'reason']
    )
)
```

### Handler de Shutdown

```python
async def _handle_shutdown_system(self, call_id: str, args: dict) -> content_api.ProcessorPart:
    """Handle system shutdown requests."""
    
    confirmation = args.get('confirmation', False)
    reason = args.get('reason', 'No reason provided')
    
    if not confirmation:
        # Nega shutdown sem confirmação
        return response_with_denial()
    
    # Aceita shutdown com confirmação
    self.shutdown_requested = True
    self.shutdown_reason = reason
    
    return response_with_confirmation()
```

### Detecção no Loop Principal

```python
# No loop principal de run_leonidas_v2
async for part in agent(endless_stream()):
    # Verifica se shutdown foi solicitado
    if orchestrator.shutdown_requested:
        logging.info(f"SHUTDOWN SOLICITADO: {orchestrator.shutdown_reason}")
        print(f"🔴 Sistema sendo desligado: {orchestrator.shutdown_reason}")
        break
```

## Segurança e Validação

### Confirmação Obrigatória
- A ferramenta `shutdown_system` **requer** `confirmation=True`
- Solicitações sem confirmação são **automaticamente negadas**
- O modelo deve confirmar explicitamente com o usuário

### Logging Completo
- Todas as tentativas de shutdown são **registradas nos logs**
- Histórico da conversa **preserva** eventos de shutdown
- Métricas de uso da ferramenta são **rastreadas**

### Encerramento Gracioso
- Recursos são **liberados adequadamente**
- Conexões são **fechadas corretamente**
- Logs da sessão são **salvos automaticamente**

## Exemplos de Uso

### Exemplo 1: Shutdown Bem-sucedido
```
Usuário: "Por favor, desligue o sistema"

Leonidas: [usa think para analisar]
"Entendo que você quer encerrar o sistema. Posso confirmar que deseja realmente desligar o Leonidas?"

Usuário: "Sim, pode desligar"

Leonidas: [usa shutdown_system com confirmation=True]
"Sistema será desligado em breve. Obrigado por usar o Leonidas!"

Sistema: 🔴 Sistema sendo desligado: Solicitação do usuário
[Encerramento gracioso]
```

### Exemplo 2: Shutdown Negado (sem confirmação clara)
```
Usuário: "Não sei se quero sair..."

Leonidas: [usa think para analisar]
"Parece que você está indeciso. Quer continuar nossa conversa ou prefere encerrar?"

[Sistema continua funcionando normalmente]
```

## Benefícios

### 1. **Controle do Usuário**
- Usuário tem controle total sobre quando encerrar
- Não precisa usar Ctrl+C ou fechar janela
- Encerramento natural através da conversa

### 2. **Inteligência Contextual**
- Modelo entende diferentes formas de solicitar shutdown
- Confirma intenção antes de executar
- Responde de forma natural e educada

### 3. **Robustez do Sistema**
- Encerramento gracioso preserva dados
- Logs são salvos adequadamente
- Recursos são liberados corretamente

### 4. **Experiência do Usuário**
- Interação mais natural e intuitiva
- Feedback claro sobre o que está acontecendo
- Despedida educada do sistema

## Testes

Execute o arquivo de teste para verificar a funcionalidade:

```bash
python leonidas/test_shutdown.py
```

O teste verifica:
- ✅ Negação de shutdown sem confirmação
- ✅ Aceitação de shutdown com confirmação
- ✅ Registro no histórico da conversa
- ✅ Atualização de métricas
- ✅ Flags de controle do sistema

## Considerações de Desenvolvimento

### Futuras Melhorias
1. **Timeout de confirmação**: Cancelar shutdown se usuário não confirmar em X segundos
2. **Shutdown programado**: Permitir agendamento de desligamento
3. **Múltiplos níveis**: Diferentes tipos de shutdown (pausa, hibernação, encerramento)
4. **Integração com sistema**: Desligar computador junto com o Leonidas

### Debugging
- Use `--debug` para ver logs detalhados de shutdown
- Verifique `orchestrator.shutdown_requested` para status
- Monitore métricas de uso da ferramenta `shutdown_system`

## Conclusão

A funcionalidade de shutdown torna o Leonidas v2 mais autônomo e user-friendly, permitindo que o modelo controle seu próprio ciclo de vida de forma inteligente e segura. Esta implementação segue as melhores práticas de segurança e usabilidade, garantindo uma experiência natural para o usuário.