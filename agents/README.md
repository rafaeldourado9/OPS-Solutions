# WhatsApp Agent Framework

Framework reutilizável para agentes de WhatsApp com arquitetura hexagonal. Um único código-base atende múltiplas empresas — cada uma com sua persona, documentos e configuração própria.

## Características

- **Core agnóstico**: o agente não sabe qual empresa está atendendo. Só o YAML muda.
- **CRM invisível**: eventos publicados via webhook sem acoplamento ao core.
- **Memória híbrida**: histórico confiável no PostgreSQL + busca semântica no Qdrant.
- **RAG automático**: ingere PDFs, DOCX e imagens; responde com base neles.
- **Debounce Redis**: 3 mensagens rápidas → 1 resposta coerente.
- **Mídia**: transcreve áudio (Whisper), descreve imagens/vídeos (LLaVA).
- **Multi-agente**: múltiplas empresas no mesmo processo, isoladas por WAHA session.
- **Hardening**: circuit breaker (Gemini), retry com backoff, rate limit por chat.

## Stack

| Camada | Tecnologia |
|---|---|
| Gateway WhatsApp | WAHA (self-hosted) |
| API | FastAPI + asyncio |
| Debounce | Redis Keyspace Notifications |
| Memória semântica | Qdrant |
| Histórico | PostgreSQL (async) |
| LLM principal | Gemini 1.5 Pro |
| LLM local | Ollama (llama3.1, llava, whisper) |
| Embeddings | nomic-embed-text (Ollama) |

## Setup rápido

### 1. Pré-requisitos

- Docker + Docker Compose
- Python 3.12+
- Chave de API do Gemini

### 2. Infraestrutura

```bash
cp .env.example .env
# Edite .env com suas chaves

docker-compose up -d
```

Serviços: Redis, Qdrant, PostgreSQL, WAHA, Ollama.

### 3. Modelos Ollama

```bash
docker exec -it whatsapp-agent-ollama-1 ollama pull llama3.1:8b
docker exec -it whatsapp-agent-ollama-1 ollama pull llava:13b
docker exec -it whatsapp-agent-ollama-1 ollama pull whisper:large-v3
docker exec -it whatsapp-agent-ollama-1 ollama pull nomic-embed-text
```

### 4. Instalar dependências Python

```bash
pip install -r requirements.txt
```

### 5. Configurar o agente

```bash
# Copie o template
cp agents/template/business.yml agents/minha_empresa/business.yml

# Edite com os dados da empresa
vim agents/minha_empresa/business.yml
```

### 6. Ingerir documentos (RAG)

```bash
# Coloque PDFs, DOCX, TXTs e imagens em agents/minha_empresa/docs/
python scripts/ingest.py --agent minha_empresa
```

### 7. Subir o agente

```bash
AGENT_ID=minha_empresa uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

### 8. Configurar webhook no WAHA

No painel WAHA (`http://localhost:3000`), configure o webhook para:
```
http://host.docker.internal:8000/webhook
```

### 9. Verificar

```bash
curl http://localhost:8000/health
```

---

## Multi-agente

```bash
# Dois agentes no mesmo processo (sessões WAHA separadas)
AGENT_IDS=empresa_x,empresa_y uvicorn api.main:app --port 8000
```

Cada agente precisa de uma sessão WAHA configurada com seu próprio número de WhatsApp.

---

## Criar novo agente

```bash
mkdir -p agents/nova_empresa/docs
cp agents/template/business.yml agents/nova_empresa/business.yml
vim agents/nova_empresa/business.yml

# Adicione documentos
cp manual.pdf agents/nova_empresa/docs/
python scripts/ingest.py --agent nova_empresa

AGENT_ID=nova_empresa uvicorn api.main:app --reload
```

Nenhuma linha de código alterada.

---

## Variáveis de ambiente

Ver `.env.example` — documentação completa de todas as variáveis.

Principais:

| Variável | Descrição | Padrão |
|---|---|---|
| `AGENT_ID` | Agente a carregar | `empresa_x` |
| `AGENT_IDS` | Múltiplos agentes (sobrescreve AGENT_ID) | — |
| `GEMINI_API_KEY` | Chave Gemini | — |
| `REDIS_URL` | URL Redis | `redis://localhost:6379/0` |
| `QDRANT_URL` | URL Qdrant | `http://localhost:6333` |
| `DATABASE_URL` | PostgreSQL async | `postgresql+asyncpg://...` |
| `WAHA_URL` | URL WAHA | `http://localhost:3000` |
| `OLLAMA_URL` | URL Ollama | `http://localhost:11434` |
| `LOG_JSON` | Logs em JSON (produção) | `false` |
| `RATE_LIMIT_MAX` | Máx mensagens/chat/janela | `20` |
| `USE_NULL_MEMORY` | Desativa memória (dev) | `false` |

---

## Testes

```bash
# Unitários (sem infraestrutura)
pytest tests/unit/

# Integração (sem Docker — adapters stubados)
USE_NULL_MEMORY=true USE_NULL_MEDIA=true pytest tests/integration/

# Tudo
pytest

# Carga (requer servidor rodando)
locust -f tests/load/locustfile.py --host http://localhost:8000
```

---

## Deploy com Docker

```bash
docker build -t whatsapp-agent .

docker run -d \
  --name whatsapp-agent \
  -p 8000:8000 \
  -e AGENT_ID=empresa_x \
  -e GEMINI_API_KEY=... \
  -e REDIS_URL=redis://redis:6379 \
  -e DATABASE_URL=postgresql+asyncpg://... \
  -e QDRANT_URL=http://qdrant:6333 \
  -e OLLAMA_URL=http://ollama:11434 \
  -e WAHA_URL=http://waha:3000 \
  -e LOG_JSON=true \
  whatsapp-agent
```

---

## Estrutura

```
core/           # Domínio e casos de uso (sem dependências externas)
  domain/       # Entidades: Message, Conversation, Memory
  ports/        # Interfaces: LLMPort, GatewayPort, MemoryPort, ...
  use_cases/    # ProcessMessage, BuildContext, IngestDocuments

adapters/
  inbound/      # WAHAWebhook (FastAPI)
  outbound/
    llm/        # GeminiAdapter, OllamaAdapter
    gateway/    # WAHAAdapter
    memory/     # QdrantAdapter, PostgresAdapter, HybridMemoryAdapter
    media/      # MultimodalAdapter (Whisper + LLaVA)
    crm/        # CRMEventAdapter, NullCRMAdapter

infrastructure/ # Redis, Postgres, CircuitBreaker, RateLimiter, Retry
api/            # FastAPI app, AgentRegistry, DI container
agents/         # Configs por empresa (business.yml + docs/)
scripts/        # ingest.py — CLI para ingestão de documentos
tests/
  unit/         # 95 testes, sem infraestrutura
  integration/  # Testes de fluxo com adapters stubados
  load/         # Locust
```
