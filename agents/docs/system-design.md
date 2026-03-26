# System Design

## Visão geral da infraestrutura

```
                    ┌─────────────────────────────────────────┐
                    │           WAHA (WhatsApp Gateway)        │
                    │   engine: NOWEB  |  session: default     │
                    └──────────────────┬──────────────────────┘
                                       │ POST /webhook
                                       ▼
                    ┌─────────────────────────────────────────┐
                    │         FastAPI (api/main.py)            │
                    │                                         │
                    │  WAHAWebhookAdapter                     │
                    │  ├─ detecção de mídiadetecção de mídia                   │
                    │  ├─ roteamento de agente                │
                    │  └─ push para debouncer                 │
                    └──────────┬──────────────────────────────┘
                               │
               ┌───────────────┼──────────────────────┐
               ▼               ▼                       ▼
        ┌────────────┐  ┌────────────┐         ┌────────────┐
        │   Redis    │  │   Qdrant   │         │ PostgreSQL │
        │            │  │            │         │            │
        │ debounce   │  │ embeddings │         │ histórico  │
        │ buffers    │  │ por chat   │         │ completo   │
        │ rate limit │  │ RAG rules  │         │            │
        │ agent mode │  │            │         │            │
        └────────────┘  └────────────┘         └────────────┘
               │
               │ keyspace expiry event
               ▼
        ┌────────────────────────────────────┐
        │     ProcessMessageUseCase          │
        │                                    │
        │  BuildContext → LLMRouter → LLM   │
        │  → split → typing → send          │
        └────────────────────────────────────┘
               │
       ┌───────┼───────┐
       ▼       ▼       ▼
   Gemini   Ollama   WAHA
   (API)   (local)  (send)
```

---

## Fluxo completo de uma mensagem

### 1. Recepção

O WAHA intercepta a mensagem do WhatsApp e faz HTTP POST no `/webhook` do FastAPI.

O payload WAHA (engine NOWEB) não inclui o campo `type` na maioria dos casos. O adapter detecta o tipo por MIME ou campos auxiliares.

### 2. Roteamento de agente

Com um único número de WhatsApp atendendo múltiplos agentes, o roteamento acontece em três camadas (em ordem de prioridade):

```
1. Redis active_agent:{chat_id}  →  agente persistido para este chat
2. target_phones do agente       →  agente restrito a números específicos
3. catch-all                     →  agente sem restrições de telefone
```

Comandos de troca (`/nome-do-agente`) atualizam a chave Redis com TTL de 30 dias.

### 3. Debounce

O adapter não processa a mensagem imediatamente. Ela é serializada como JSON e empurrada numa lista Redis:

```
RPUSH buffer:{agent_id}:{chat_id}  '{"text": "...", "chat_id": "..."}'
SETEX debounce:{agent_id}:{chat_id}  2.5  "1"
```

Cada nova mensagem do mesmo chat reseta o timer. Quando o timer expira sem nova mensagem, o Redis emite um evento keyspace que desperta o listener.

**Por que não `asyncio.sleep(2.5)` direto?**
Com 100+ chats simultâneos, 100 corrotinas dormindo consomem memória e criam race conditions. O Redis gerencia os timers externamente e emite um único evento. Em caso de restart da aplicação, os buffers sobrevivem no Redis — sem perda de mensagem.

### 4. Processamento

O callback keyspace extrai e limpa o buffer atomicamente:

```python
messages = await redis.lrange(f"buffer:{ns}:{chat_id}", 0, -1)
await redis.delete(f"buffer:{ns}:{chat_id}")
```

Múltiplas mensagens do usuário são consolidadas com quebra de linha e tratadas como uma única query.

### 5. Context window híbrido

O `BuildContextUseCase` monta o contexto combinando três fontes:

| Fonte | Tamanho | Objetivo |
|---|---|---|
| Mensagens recentes | N=15 (config) | Contexto imediato da conversa |
| Busca semântica no histórico | K=6 (config) | Lembrar conversas passadas relevantes |
| Regras de negócio (RAG) | K=4 (fixo) | Fundamentar respostas nos documentos da empresa |

**Custo típico: ~2.000 tokens** em vez de 20.000+ com histórico completo.

### 6. LLM Router

Antes de chamar o LLM, o sistema decide qual usar:

```python
COMPLEX_KEYWORDS = [
    "contrato", "prazo", "valor", "quanto", "orçamento",
    "problema", "reclamação", "garantia", "cálculo", "comparar"
]

def is_complex(text: str) -> bool:
    has_keyword = any(kw in text.lower() for kw in COMPLEX_KEYWORDS)
    is_long = len(text.split()) > 20
    return has_keyword or is_long
```

- Query simples → **Ollama local** (rápido, sem custo de API)
- Query complexa → **Gemini Pro** (maior capacidade de raciocínio)
- Gemini falhou → **Circuit Breaker** abre → fallback automático para Ollama

### 7. Anti-alucinação (4 camadas)

| Camada | Mecanismo |
|---|---|
| Temperature baixa | 0.3 a 0.7 (configurável por agente) — respostas mais determinísticas |
| RAG obrigatório | Se `rag_mandatory: true`, sistema não responde sem contexto relevante dos docs |
| System prompt com grounding | Bloco explícito: "responda SOMENTE com base no contexto abaixo" |
| Resposta padrão para desconhecido | Se RAG não encontrar nada com score suficiente, retorna `unknown_answer` do YAML |

### 8. Geração e envio

A resposta do LLM é consumida via streaming e dividida em partes curtas.

**Algoritmo de split:**
1. Divide por `\n\n` (parágrafos) primeiro
2. Se algum parágrafo ultrapassa `max_message_chars`, divide por `.` ou `!` ou `?`
3. Nunca corta no meio de uma frase

Para cada parte:
```
send_typing(True)
await asyncio.sleep(len(parte) * typing_delay_per_char)
send_typing(False)
send_message(parte)
await asyncio.sleep(random(min_pause, max_pause))
```

**Verificação de interrupção antes de cada envio:**
```python
active = await redis.get(f"active_task:{chat_id}")
if active != my_task_id:
    return  # nova mensagem chegou — abandona este envio
```

### 9. Persistência

Após o envio:
- Mensagens do usuário e do agente salvas no Qdrant (com embeddings) e no PostgreSQL (histórico)
- `ActivityTracker.touch(chat_id)` atualiza o timestamp de última atividade
- `CRMPort.push_event()` dispara evento fire-and-forget para o webhook do CRM

---

## Stack tecnológica — justificativas

### FastAPI + asyncio

100+ chats simultâneos exigem I/O assíncrono. FastAPI com asyncio processa webhooks concorrentes sem threads adicionais. O event loop do Python é suficiente para workloads I/O-bound como este.

### Redis

Quatro usos distintos no sistema:

| Uso | Chave | TTL |
|---|---|---|
| Buffer de mensagens | `buffer:{agent_id}:{chat_id}` | até expirar |
| Timer de debounce | `debounce:{agent_id}:{chat_id}` | 2.5s (configurável) |
| Task ativa (interrupção) | `active_task:{chat_id}` | 30s |
| Rate limit | `rate:{chat_id}` | 60s (janela) |
| Agente ativo por chat | `active_agent:{chat_id}` | 30 dias |
| Estado de sessão RAG | `rag_session:{agent_id}:{chat_id}` | 10 min |
| Última atividade | `activity:{agent_id}:{chat_id}` | 90 dias |

A configuração `notify-keyspace-events KEA` no Redis é obrigatória para o debounce funcionar.

### Qdrant

Escolhido sobre pgvector por:
- Coleções separadas por empresa sem configuração extra
- Filtros por `agent_id` e `chat_id` nativos no payload
- Performance de busca otimizada para 100+ chats simultâneos com buscas concorrentes

Duas coleções por agente:
- `{agent_id}_chats` — histórico de conversas com embeddings por mensagem
- `{agent_id}_rules` — chunks de documentos RAG com metadados de fonte

### PostgreSQL

Complementa o Qdrant com histórico relacional durável. O Qdrant prioriza velocidade de busca semântica; o PostgreSQL garante que nenhuma mensagem seja perdida e permite queries SQL para auditoria e análise.

### Gemini 2.0 Flash

Modelo principal por:
- Contexto longo (1M tokens) — histórico de conversas extensas sem truncagem
- Multimodal nativo — áudio, imagem, vídeo e texto no mesmo modelo
- API com streaming — respostas incrementais sem esperar geração completa

### Ollama (local)

Para queries simples e tarefas de embedding. Zero custo de API, zero latência de rede. `nomic-embed-text` para embeddings de 768 dimensões com boa qualidade em português.

---

## Escalabilidade

### Isolamento por chat_id

Cada chat é completamente isolado. O único recurso compartilhado são os connection pools. Configuração recomendada:

```
Qdrant pool:     20 conexões (suporta 100 buscas simultâneas com folga)
PostgreSQL pool: 20 conexões
Redis pool:      20 conexões
```

### Multi-agente em único processo

Múltiplos agentes rodam no mesmo processo FastAPI. Cada um tem:
- Seu próprio debouncer com namespace no Redis
- Suas próprias coleções no Qdrant
- Suas próprias configurações de LLM e comportamento

O overhead por agente adicional é apenas memória para as instâncias dos adapters — sem processos ou workers adicionais.

### Rate limiting

Fixed-window por `chat_id`: máximo 20 mensagens por 60 segundos por padrão. Configurável via env vars `RATE_LIMIT_MAX` e `RATE_LIMIT_WINDOW`.

Falha aberta: se o Redis estiver indisponível, o rate limiter permite a requisição passar. Prioridade é não bloquear o usuário por problema de infraestrutura.
