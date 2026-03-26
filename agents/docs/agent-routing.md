# Sistema de Roteamento Multi-Agente

## Visão geral

O framework suporta múltiplos agentes rodando em um único processo, atendendo pelo mesmo número de WhatsApp. O roteamento determina qual agente responde a cada mensagem.

---

## Camadas de roteamento (em ordem de prioridade)

```
Mensagem chega
       │
       ▼
┌─────────────────────────────────┐
│  1. Comando de agente?          │  /maya, /rafael, /ops_solutions
│     /{agent_id} ou /{name}      │  → persiste no Redis (30 dias)
└─────────────┬───────────────────┘
              │ não é comando
              ▼
┌─────────────────────────────────┐
│  2. Redis active_agent:{id}?    │  usuário já escolheu um agente antes
│     chave válida no Redis       │  → usa o agente persistido
└─────────────┬───────────────────┘
              │ sem chave Redis
              ▼
┌─────────────────────────────────┐
│  3. target_phones configurado?  │  agente restrito a números específicos
│     número do remetente bate?   │  → usa o agente restrito
└─────────────┬───────────────────┘
              │ sem match
              ▼
┌─────────────────────────────────┐
│  4. Catch-all                   │  agente sem target_phones
│                                 │  → agente padrão (ex: ops_solutions)
└─────────────────────────────────┘
```

---

## Comandos disponíveis

### Trocar de agente

Qualquer usuário pode digitar um comando para escolher com qual agente quer conversar. O comando é reconhecido automaticamente a partir dos agentes carregados — sem configuração manual.

Dois formatos aceitos (case-insensitive):
- `/{agent_id}` — usa o ID da pasta do agente
- `/{agent.name}` — usa o campo `name:` do `business.yml`

**Exemplos:**
```
/maya           → ativa o agente Maya (id: maya)
/ops_solutions  → ativa o agente Rafael (id: ops_solutions)
/rafael         → ativa o agente Rafael (pelo name: "Rafael")
```

### Listar agentes disponíveis

```
/agentes
```

Resposta automática:
```
Agentes disponíveis:
  /maya — Maya (Study.io)
  /ops_solutions — Rafael (OPS Solution)

/sair — voltar ao atendimento padrão
```

### Voltar ao padrão

```
/sair
/default
/inicio
```

Qualquer um dos três remove a chave Redis e volta para o agente catch-all.

---

## Persistência da escolha

Quando o usuário digita `/maya`, o sistema salva:

```
Redis SETEX active_agent:{chat_id}  2592000  "maya"
                                    (30 dias em segundos)
```

A partir deste momento, **todas as mensagens deste `chat_id`** são roteadas para a Maya — sem precisar repetir o comando. O usuário não precisa saber que existe um sistema de roteamento.

A chave expira automaticamente após 30 dias de inatividade. Quando o usuário retorna após esse período, cai no catch-all novamente.

---

## Como o AgentRegistry funciona

O `AgentRegistry` é a estrutura central de roteamento em memória. Ele mantém um índice de todos os agentes registrados e resolve qual agente deve tratar uma mensagem.

### Estrutura interna

```python
_by_session: dict[str, list[AgentInstance]]
# ex: {"default": [ops_solutions_instance, maya_instance]}
```

Múltiplos agentes podem compartilhar a mesma session WAHA. A ordem de registro é preservada.

### Método principal: `get_by_session_and_phone`

```python
def get_by_session_and_phone(session: str, chat_id: str) -> AgentInstance | None:
    # 1. Busca agentes da session
    candidates = _by_session.get(session)

    # 2. Single-agent fallback (só 1 agente registrado)
    if not candidates and len(all) == 1:
        return all[0]

    phone = normalize_phone(chat_id)  # extrai dígitos do JID

    # 3. Agente com target_phones que bate com o remetente
    for inst in candidates:
        if inst.config.agent.target_phones and phone in target_phones:
            return inst

    # 4. Catch-all (sem target_phones)
    for inst in candidates:
        if not inst.config.agent.target_phones:
            return inst

    return candidates[0]  # last resort
```

### Método de busca por comando: `get_by_command`

```python
def get_by_command(command: str) -> AgentInstance | None:
    cmd = command.lstrip("/").lower()
    for inst in all_instances():
        if inst.agent_id.lower() == cmd:
            return inst
        if inst.config.agent.name.lower() == cmd:
            return inst
    return None
```

---

## Como adicionar um novo agente

Não há configuração de roteamento para fazer. O sistema descobre os agentes automaticamente.

```bash
# 1. Cria a pasta do agente
mkdir -p agents/nova_empresa/docs

# 2. Cria o business.yml
cp agents/template/business.yml agents/nova_empresa/business.yml
# edita name, persona, llm, etc.

# 3. Adiciona ao AGENT_IDS no docker-compose
AGENT_IDS=maya,ops_solutions,nova_empresa

# 4. Sobe
docker-compose up -d --build agent
```

A partir daí, `/nova_empresa` e `/{name do agente}` funcionam automaticamente.

---

## Configurações relevantes no `business.yml`

```yaml
agent:
  waha_session: "default"    # session WAHA que este agente escuta
  target_phones: []          # lista de telefones exclusivos (vazio = catch-all)
                             # ex: ["5511999999999"]
```

### Cenários de configuração

**Um agente para todos (padrão):**
```yaml
target_phones: []  # catch-all
```

**Agente exclusivo para um número:**
```yaml
target_phones: ["5511999999999"]  # só responde a este número
```

**Múltiplos agentes, mesmo número:**
```yaml
# agente_vip/business.yml
target_phones: ["5511111111111", "5511222222222"]  # clientes VIP

# ops_solutions/business.yml
target_phones: []  # todos os outros
```

---

## Diagrama de estado por chat_id

```
Estado inicial (novo chat)
         │
         │ qualquer mensagem
         ▼
[agente catch-all responde]
         │
         │ usuário digita /maya
         ▼
[Redis: active_agent = "maya"]
         │
         │ qualquer mensagem
         ▼
[Maya responde automaticamente]
         │
         ├── usuário digita /sair ──────► [Redis key deletada]
         │                                       │
         │                                       │ qualquer mensagem
         │                                       ▼
         │                               [catch-all responde]
         │
         └── 30 dias sem mensagem ──────► [Redis key expira]
                                                 │
                                                 │ nova mensagem
                                                 ▼
                                         [catch-all responde]
```
