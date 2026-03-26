# Arquitetura do Framework

## Estilo Arquitetural: Hexagonal (Ports & Adapters)

A arquitetura hexagonal — também chamada de Ports & Adapters — é o padrão central de todo o framework. A ideia é simples: o **core da aplicação** (domínio + casos de uso) nunca importa nada de infraestrutura. Ele só conhece interfaces abstratas chamadas **ports**. Os detalhes de implementação (Redis, Qdrant, Gemini, WAHA) vivem nos **adapters**, completamente fora do core.

```
┌──────────────────────────────────────────────────────────────┐
│                         CORE                                 │
│                                                              │
│   domain/              use_cases/           ports/           │
│   ────────             ──────────           ──────           │
│   Message              ProcessMessage       LLMPort          │
│   Conversation         BuildContext         MemoryPort       │
│   Memory               IngestDocuments      GatewayPort      │
│                        GenerateReport       MediaPort        │
│                                             CRMPort          │
│                                             CalendarPort     │
└─────────────────────────┬────────────────────────────────────┘
                          │  depende apenas de interfaces
┌─────────────────────────▼────────────────────────────────────┐
│                      ADAPTERS                                │
│                                                              │
│   inbound/                  outbound/                        │
│   ────────                  ────────                         │
│   WAHAWebhook               GeminiAdapter    QdrantAdapter   │
│                             OllamaAdapter    WAHAGateway     │
│                             GeminiMedia      CRMWebhook      │
│                             GoogleCalendar   PostgresRepo    │
└──────────────────────────────────────────────────────────────┘
```

### Por que hexagonal aqui?

**Reuso real entre empresas.** `ProcessMessageUseCase` é idêntico para qualquer agente. O que muda são os adapters injetados — e eles são escolhidos pelo YAML da empresa.

**Testabilidade sem infraestrutura.** Os casos de uso são testados com fakes e mocks dos ports. Nenhum teste de unidade precisa de Redis, Qdrant ou rede.

**Substituição de infraestrutura a custo zero.** Trocar Qdrant por Pinecone é implementar `PineconeAdapter` satisfazendo `MemoryPort`. O core não sabe que a troca aconteceu.

**Venda isolada de componentes.** O agente pode ser empacotado e vendido sem o CRM. Basta injetar `NullCRMAdapter` no lugar do `CRMEventAdapter`.

---

## Camadas em detalhe

### Core — `core/`

Contém somente domínio e lógica de negócio. Zero dependências externas. Pode ser testado isoladamente.

#### `core/domain/`

Entidades puras que representam os conceitos do negócio.

**`message.py`**
```
Message
  id: UUID4 (auto-gerado)
  role: "user" | "assistant" | "system"
  content: str
  timestamp: datetime UTC (imutável após criação)
  media_type: Optional[str]

MediaMessage(Message)
  media_url: Optional[str]
  media_data: Optional[bytes]

Conversation
  messages: List[Message]
  to_llm_messages() → lista OpenAI-style
  last_user_message() → Message | None
```

Decisão: mensagens são **imutáveis por padrão** (Pydantic frozen). Elimina bugs de mutação acidental de estado em pipelines assíncronos concorrentes.

#### `core/ports/`

Interfaces abstratas (ABCs Python) que definem contratos. O core importa apenas estas interfaces — nunca as implementações.

| Port | Contrato principal |
|---|---|
| `LLMPort` | `stream_response(messages, system_prompt)` → `AsyncIterator[str]` |
| `MemoryPort` | `save_message()`, `search_semantic()`, `get_recent()`, `search_business_rules()` |
| `GatewayPort` | `send_message()`, `send_typing()`, `send_document()` |
| `MediaPort` | `transcribe_audio()`, `describe_image()`, `describe_video()`, `generate_image()` |
| `CRMPort` | `push_event(event: CRMEvent)` |
| `CalendarPort` | `create_event()`, `list_events()` |

#### `core/use_cases/`

Orquestradores de lógica de negócio. Cada caso de uso recebe ports por injeção de dependência no construtor.

**`ProcessMessageUseCase`** — o orquestrador principal

Fluxo interno:
1. Constrói context window via `BuildContextUseCase`
2. Monta system prompt com persona + bloco RAG (grounding)
3. Roteia para LLM correto (Gemini ou Ollama) via classificador de complexidade
4. Consome a resposta via streaming
5. Detecta prefixos especiais (`GERAR_IMAGEM:`, `CRIAR_EVENTO:`)
6. Divide a resposta em partes curtas (`split_response`)
7. Para cada parte: verifica task_id (interrupção), envia typing, aguarda delay, envia texto
8. Salva no histórico, dispara evento CRM

**`BuildContextUseCase`** — context window híbrido

Três fontes combinadas numa única chamada:
```
recent_messages  = get_recent(chat_id, n=15)          # contexto imediato
semantic_matches = search_semantic(chat_id, query, k=6) # relevância semântica
business_rules   = search_business_rules(query, k=4)   # RAG dos documentos
```
O resultado é um `ContextWindow` injetado no system prompt. Custo típico: ~2.000 tokens em vez de 20.000+ com histórico completo.

**`IngestDocumentsUseCase`** — pipeline de RAG

Suporta PDF (PyMuPDF), DOCX (python-docx), TXT, MD e imagens (Gemini). Faz chunking semântico com overlap, gera embeddings via Ollama (`nomic-embed-text`) e persiste no Qdrant.

---

### Adapters — `adapters/`

Implementações concretas dos ports. Conhecem Redis, Qdrant, HTTP, Gemini API, etc.

#### Inbound

**`WAHAWebhookAdapter`** (`adapters/inbound/waha_webhook.py`)

FastAPI router que recebe eventos do WAHA e os converte para o domínio do core.

Responsabilidades:
- Parse do payload WAHA (engine NOWEB — campo `type` ausente)
- Detecção de tipo de mídia por MIME quando `type` não existe
- Download de mídia via 5 estratégias em cascata
- Interceptação de comandos admin (`/rag`, `/gerar_relatorio`)
- **Roteamento multi-agente** por sessão + Redis + telefone
- Push para o buffer do debouncer

#### Outbound — LLM

**`GeminiAdapter`**: usa `google-generativeai`, suporta streaming nativo, tem circuit breaker integrado.

**`OllamaAdapter`**: HTTP direto para Ollama local, sem dependência de SDK externo.

Ambos implementam `LLMPort` com o mesmo contrato — o core não sabe qual está sendo usado.

#### Outbound — Memory

**`HybridMemoryAdapter`**: combina Qdrant (busca semântica) + PostgreSQL (histórico relacional) numa única implementação de `MemoryPort`.

**`QdrantAdapter`**: gerencia duas coleções por agente — `{agent_id}_chats` (histórico com embeddings) e `{agent_id}_rules` (documentos RAG). Todos os filtros incluem `agent_id` para garantir isolamento total entre empresas.

**`PostgresMessageRepository`**: persistência durável do histórico completo via SQLAlchemy async.

#### Outbound — Gateway

**`WAHAAdapter`**: envia mensagens e typing indicators via HTTP para o WAHA. Inclui session name configurável por agente.

**`FakeGatewayAdapter`**: descarta todas as mensagens com log de warning. Ativado via `USE_FAKE_GATEWAY=true`. Usado em desenvolvimento e testes para evitar mensagens acidentais em produção.

#### Outbound — Media

**`GeminiMediaAdapter`**: usa Gemini 2.0 Flash para transcrição de áudio, descrição de imagens/vídeos e geração de imagens. Um único modelo para todas as modalidades.

#### Outbound — CRM

**`CRMEventAdapter`**: HTTP POST fire-and-forget para o webhook do CRM. Falhas são logadas e ignoradas — o agente nunca é bloqueado por falha no CRM.

**`NullCRMAdapter`**: implementação vazia que descarta todos os eventos. Para deploys sem CRM.

---

## Design Patterns aplicados

| Pattern | Onde | Por quê |
|---|---|---|
| **Ports & Adapters** | Toda a arquitetura | Isolamento entre core e infraestrutura |
| **Dependency Injection** | Construtores dos use cases | Testabilidade e troca de adapters sem recompilação |
| **Strategy** | LLM Router (Gemini vs Ollama) | Algoritmo de seleção de LLM intercambiável |
| **Circuit Breaker** | GeminiAdapter | Evitar cascata de falhas quando API externa cai |
| **Null Object** | NullCRMAdapter, NullMemoryAdapter, FakeGatewayAdapter | Remove IFs de verificação de nulidade no core |
| **Repository** | QdrantAdapter, PostgresAdapter | Abstração de persistência com query interface uniforme |
| **Registry** | AgentRegistry | Lookup centralizado de instâncias de agentes |
| **Factory** | `build_agent_instance()` | Construção e wiring de todos os adapters de um agente |
| **Observer** (simplificado) | CRMPort.push_event() | Eventos publicados passivamente sem acoplamento |
| **State Machine** | CircuitBreaker (CLOSED/OPEN/HALF_OPEN) | Transições de estado explícitas e auditáveis |
| **Template Method** | LLMPort (stream + generate) | Interface base com dois modos de uso |

---

## Estrutura de pastas

```
whatsapp-agent/
│
├── core/                        # Zero dependências externas
│   ├── domain/                  # Entidades de negócio
│   ├── ports/                   # Interfaces abstratas (ABCs)
│   └── use_cases/               # Orquestradores de negócio
│
├── adapters/                    # Implementações concretas
│   ├── inbound/                 # Webhook WAHA → domínio
│   └── outbound/                # Domínio → serviços externos
│       ├── llm/                 # Gemini, Ollama
│       ├── memory/              # Qdrant, Postgres, Hybrid
│       ├── gateway/             # WAHA, Fake
│       ├── media/               # Gemini multimodal
│       ├── crm/                 # Webhook, Null
│       ├── calendar/            # Google Calendar, Null
│       └── document/            # PDF generation
│
├── infrastructure/              # Serviços transversais
│   ├── redis_client.py          # Pool + MessageDebouncer + listener
│   ├── config_loader.py         # YAML → BusinessConfig tipado
│   ├── circuit_breaker.py       # 3-state FSM
│   ├── rate_limiter.py          # Fixed-window por chat_id
│   ├── activity_tracker.py      # Timestamps de atividade no Redis
│   ├── proactive_scheduler.py   # Background task de proatividade
│   └── rag_session.py           # Estado de sessão RAG admin
│
├── api/
│   ├── main.py                  # FastAPI app + lifespan
│   ├── dependencies.py          # Factory de AgentInstance
│   └── agent_registry.py        # Registry com roteamento por sessão/telefone/comando
│
├── agents/                      # Um diretório por empresa
│   ├── maya/business.yml
│   └── ops_solutions/business.yml
│
└── tests/
    ├── unit/                    # Testam core com mocks
    ├── integration/             # Testam adapters contra serviços reais
    └── load/                    # Locust para 100+ conexões simultâneas
```
