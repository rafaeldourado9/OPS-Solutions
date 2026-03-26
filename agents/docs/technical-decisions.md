# Decisões Técnicas

Registro de decisões de design tomadas durante o desenvolvimento. Cada item explica o problema, a alternativa considerada e o porquê da escolha feita.

---

## 1. Debounce via Redis Keyspace Notifications

**Problema:** Cliente envia "oi", "tudo bem?", "preciso de ajuda" em 2 segundos. O agente não pode responder 3 vezes.

**Alternativa descartada:** `asyncio.sleep(2.5)` por mensagem.

Com 100 chats simultâneos, isso cria 100 corrotinas dormindo. Com 1.000 usuários, começaria a pesar. Além disso, se a aplicação reiniciar durante o sleep, a mensagem é perdida.

**Decisão:** Redis com Keyspace Notifications.

```
RPUSH buffer:{agent_id}:{chat_id}  mensagem
SETEX debounce:{agent_id}:{chat_id}  2.5  "1"
```

Quando `debounce:...` expira, o Redis emite `__keyevent@0__:expired`. O listener Python acorda e processa o buffer. Os timers são gerenciados externamente, o processo Python não precisa manter estado de sleep. O buffer sobrevive a restarts.

Configuração obrigatória no Redis: `notify-keyspace-events KEA`.

---

## 2. Context Window Híbrido em vez de Histórico Completo

**Problema:** Histórico de 200 mensagens cabe mal no contexto e custa caro em tokens.

**Alternativa descartada:** Enviar as últimas N mensagens por janela deslizante.

Histórico recente é bom para continuidade imediata, mas perde conversas relevantes de semanas atrás ("como você me disse na última sessão...").

**Decisão:** Três fontes combinadas.

| Fonte | Tamanho | Objetivo |
|---|---|---|
| Recente | 15 mensagens | Continuidade imediata |
| Semântico | 6 mais similares | Memória de longo prazo relevante |
| RAG | 4 chunks | Fundamentação nos documentos |

Custo típico: ~2.000 tokens. Histórico completo de 200 mensagens custaria 15.000–20.000 tokens por request.

---

## 3. LLM Router (Gemini vs Ollama)

**Problema:** Usar Gemini Pro para "oi, tudo bem?" é desperdício de API. Usar Ollama para calcular um orçamento detalhado é arriscado.

**Alternativa descartada:** Usar sempre o mesmo LLM.

**Decisão:** Classificador de complexidade simples.

```python
COMPLEX_KEYWORDS = [
    "contrato", "prazo", "valor", "quanto", "orçamento",
    "problema", "reclamação", "garantia", "cálculo", "comparar"
]

is_complex = (
    any(kw in text.lower() for kw in COMPLEX_KEYWORDS)
    or len(text.split()) > 20
)
```

Queries simples → Ollama local (zero custo, baixa latência).
Queries complexas → Gemini (melhor raciocínio, maior contexto).

Essa regra não é perfeita, mas é suficientemente boa e tem custo de classificação próximo de zero.

---

## 4. Circuit Breaker no Gemini Adapter

**Problema:** Gemini API fora do ar. Cada request começa a acumular timeouts, bloqueando o event loop.

**Alternativa descartada:** Retry com backoff no adapter.

Retry por si só não protege contra falha prolongada — continua tentando enquanto a API está down.

**Decisão:** Circuit Breaker em 3 estados.

```
CLOSED ──(3 falhas)──► OPEN ──(60s)──► HALF_OPEN ──(sucesso)──► CLOSED
                                              └──(falha)──► OPEN
```

Em `OPEN`, o adapter falha imediatamente sem tentar a rede. O `LLMRouter` detecta a exceção `CircuitOpenError` e cai para o Ollama. O usuário não percebe a interrupção no Gemini.

---

## 5. Interrupção de Geração por Nova Mensagem

**Problema:** Agente está gerando resposta longa quando o usuário manda nova mensagem. Enviar a resposta antiga seria confuso.

**Alternativa descartada:** Cancelar a corrotina via `asyncio.CancelledError`.

Cancelar corrotines em Python requer coordenação cuidadosa e pode deixar locks abertos.

**Decisão:** `task_id` único por ciclo de processamento, verificado antes de cada envio.

```python
# Ao iniciar o processamento:
task_id = str(uuid4())
await redis.setex(f"active_task:{chat_id}", 30, task_id)

# Antes de cada envio de parte da resposta:
active = await redis.get(f"active_task:{chat_id}")
if active != task_id:
    return  # substituído por tarefa mais nova — descarta silenciosamente
```

Se nova mensagem chega, ela substitui o `active_task` no Redis. O processamento anterior percebe que não é mais ativo e para naturalmente, sem cancelamento forçado.

---

## 6. Roteamento Multi-Agente por Comando em vez de Múltiplos Números

**Problema original:** Dois agentes (Maya e ops_solutions) precisam operar no mesmo número de WhatsApp.

**Alternativa 1 descartada:** Dois números de WhatsApp, dois containers WAHA.

Custo operacional alto (dois chips/planos), complexidade de gestão.

**Alternativa 2 descartada:** Roteamento por número do remetente (`target_phones`).

Exige cadastro manual de cada número que vai usar cada agente. Não escala.

**Decisão:** Roteamento por comando (`/nome-do-agente`) com persistência no Redis.

Usuário digita `/maya` uma vez. Redis guarda `active_agent:{chat_id} = "maya"` por 30 dias. Todas as mensagens seguintes vão para a Maya automaticamente.

Benefícios adicionais:
- Novos agentes não exigem nenhuma configuração de roteamento
- O próprio usuário controla com qual agente está falando
- `/agentes` lista automaticamente o que está disponível
- A chave expira sozinha — sem limpeza manual

---

## 7. YAML por Agente em vez de Banco de Dados de Configuração

**Problema:** Como configurar comportamento diferente por empresa sem alterar código?

**Alternativa descartada:** Configurações no banco de dados com painel admin.

Painel admin exige desenvolvimento extra, autenticação, UI. Muda o escopo do projeto.

**Decisão:** YAML por empresa em `agents/{id}/business.yml`.

```
agents/
  ops_solutions/business.yml
  maya/business.yml
  nova_empresa/business.yml   ← nova empresa = nova pasta
```

Vantagens:
- Legível por humanos sem treinamento técnico
- Versionável no git (histórico de mudanças de comportamento)
- Interpolação de env vars para secrets (`${GEMINI_API_KEY}`)
- Pydantic valida o schema ao subir — erros de config são detectados no startup
- Zero interface para criar/editar — editor de texto é suficiente

---

## 8. NullObject Pattern para Adapters Opcionais

**Problema:** Nem todo deploy precisa de CRM, calendar ou memória persistente. Como desabilitar sem IFs espalhados pelo código?

**Decisão:** Implementações Null para cada adapter opcional.

```python
# Em vez de:
if crm_enabled:
    await crm.push_event(event)

# Com Null Object:
await crm.push_event(event)  # NullCRMAdapter simplesmente não faz nada
```

Adapters Null disponíveis:
- `NullCRMAdapter` — `push_event()` silencioso
- `NullMemoryAdapter` — operações de memória sem efeito
- `NullCalendarAdapter` — calendar sem operações
- `NullMediaAdapter` — transcrição/descrição retorna string vazia
- `FakeGatewayAdapter` — mensagens descartadas com log de warning

Ativação via env vars (`USE_NULL_MEMORY=true`, `USE_FAKE_GATEWAY=true`) ou config YAML (`calendar.enabled: false`).

---

## 9. Fake Gateway para Desenvolvimento Seguro

**Problema:** Durante desenvolvimento e testes, o agente pode enviar mensagens reais para usuários se não houver proteção.

**Decisão:** `FakeGatewayAdapter` com ativação por env var.

```python
if os.environ.get("USE_FAKE_GATEWAY", "").lower() == "true":
    logger.warning("FAKE GATEWAY ATIVO - Mensagens NÃO serão enviadas!")
    return FakeGatewayAdapter()
```

O `FakeGatewayAdapter` implementa `GatewayPort` completamente, mas descarta todas as mensagens. O código de produção não muda — só o adapter injetado muda.

---

## 10. Sem LangChain ou LlamaIndex

**Decisão:** Framework próprio, sem abstrações de orquestração de LLM.

LangChain e LlamaIndex oferecem atalhos mas criam caixas pretas. Quando o agente se comporta de forma inesperada, é impossível inspecionar exatamente o que foi enviado ao LLM.

Neste projeto, cada componente do pipeline é explícito:
- O system prompt é uma string Python, visível e editável
- O context window é montado por código próprio, com logs
- O split de resposta é uma função com testes unitários
- O routing de LLM é um `if` com keywords explícitas

Custo: mais código para escrever inicialmente.
Benefício: comportamento completamente auditável e debugável.

---

## 11. Embeddings Locais com nomic-embed-text

**Problema:** Embeddings via API (OpenAI, Gemini) adicionam latência de rede em cada busca semântica.

**Decisão:** `nomic-embed-text` rodando no Ollama local.

768 dimensões, qualidade boa em português, zero latência de rede, zero custo por request. Para o volume típico deste projeto (dezenas de buscas por segundo), é mais que suficiente.

---

## 12. PostgreSQL + Qdrant em vez de só pgvector

**Alternativa descartada:** pgvector para tudo (histórico + busca semântica no mesmo banco).

**Decisão:** Responsabilidades separadas.

| Qdrant | PostgreSQL |
|---|---|
| Busca semântica por similaridade | Histórico completo e auditável |
| Filtros por `agent_id` e `chat_id` | Queries SQL para análise |
| Performance de ANN otimizada | Durabilidade relacional garantida |

pgvector seria uma dependência adicional no PostgreSQL (extensão), com performance de busca inferior ao Qdrant para buscas concorrentes. Separar responsabilidades mantém cada sistema fazendo o que faz melhor.

---

## 13. Proactive Scheduler como Background Task

**Problema:** Como a Maya envia mensagens de motivação diária e alertas de inatividade sem que o usuário inicie a conversa?

**Decisão:** `asyncio.create_task()` iniciado no lifespan do FastAPI.

```python
scheduler = ProactiveScheduler(...)
scheduler.start()  # cria task assíncrona em background
```

O scheduler roda no mesmo event loop do FastAPI, sem processo separado. Verifica uma vez por dia no horário configurado (`daily_motivation_time: "18:00"`). Erros são capturados e logados — nunca interrompem o loop.

Shutdown gracioso via `scheduler.stop()` no lifespan cleanup.
