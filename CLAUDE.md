# CRM White-Label — Guia de Arquitetura e Decisoes

## Visao Geral

CRM white-label multi-tenant que integra com o framework de agentes WhatsApp existente (`agents/`)
sem modificar o codigo dos agentes. O CRM (`crm/`) consome eventos dos agentes via webhook,
gerencia configuracoes via filesystem compartilhado, e permite takeover humano via proxy.

Inspiracoes: helenacrm.com, zarpon.com.br
Diferencial: propostas DOCX automatizadas + agentes IA configurados por nicho + onboarding guiado

---

## Principio Fundamental: Isolamento de Agentes

Cada agente em `agents/agents/{agent_id}/` e uma unidade autonoma e isolada:

- `business.yml` — configuracao completa (persona, empresa, LLM, RAG, CRM webhook)
- `docs/` — documentos RAG exclusivos do agente
- Colecoes Qdrant isoladas: `{agent_id}_chats` (memoria) e `{agent_id}_rules` (RAG)
- Pode ser empacotado como Docker image independente e vendido/licenciado separadamente
- O CRM nunca conhece o interior do agente — comunicacao apenas por webhook events e filesystem

**Contrato de integracao:**
- CRM escreve `business.yml` via port `AgentConfigPort` (filesystem adapter)
- Agente le `business.yml` na inicializacao via `config_loader.py`
- Agente envia eventos ao CRM via `CRM_WEBHOOK_URL` (env var, nunca hardcoded)
- CRM nunca chama codigo interno do agente — apenas REST API e filesystem

---

## Arquitetura de Integracao

```
Gateway WhatsApp (Baileys, porta 3000)
    |
    | POST /webhook
    v
CRM Webhook Proxy (porta 8001)  ──── Redis: takeover:{session}:{chat_id} ativo?
    |                                    |
    | SIM: armazena + WebSocket          | NAO: forward para agents + armazena copia
    v                                    v
Operador (chat humano)           Agents API (porta 8000, inalterado)
                                         |
                                         | push_event (fire-and-forget)
                                         v
                                 CRM /webhooks/agent-events
                                         |
                                         v
                                 PostgreSQL + WebSocket real-time
```

**Nota:** O gateway usa Baileys (biblioteca Node.js), NAO o WAHA oficial. Isso afeta como as
sessoes sao gerenciadas e como o proxy deve tratar o formato dos payloads.

---

## Stack Tecnica

| Componente | Tecnologia |
|---|---|
| Backend CRM | FastAPI + asyncio |
| Frontend | React + TypeScript + Vite + Tailwind CSS |
| DB CRM | PostgreSQL 16 (porta 5433, separado dos agents) |
| Cache | Redis db=1 (agents usa db=0) |
| Storage | MinIO S3-compatible (avatars, logos, DOCX, PDF) |
| Migrations | Alembic |
| Auth | JWT (PyJWT) |
| LLM | Gemini APENAS (sem Ollama, sem OpenAI) |
| DOCX | python-docx |
| PDF | LibreOffice headless |
| Logs | structlog |
| Testes | pytest + pytest-bdd |
| Agents | Node.js + Baileys + framework proprio |

**LLM: Gemini e o unico provedor suportado.** A API key e fornecida pelo usuario em
Settings > Integracoes e armazenada no servidor — NUNCA exposta no frontend ou no business.yml.

---

## Estrutura do Projeto CRM

```
crm/
├── core/
│   ├── domain/           # Entidades puras (sem dependencias externas)
│   ├── ports/
│   │   ├── inbound/      # Interfaces de servico
│   │   └── outbound/     # Interfaces de repositorio e gateways
│   └── use_cases/        # Um diretorio por modulo
├── adapters/
│   ├── inbound/
│   │   └── api/          # FastAPI: routes, middleware (auth, tenant_context)
│   └── outbound/
│       ├── persistence/  # SQLAlchemy models, Alembic, repositorios Postgres
│       ├── agents/       # filesystem_agent_config, waha_direct_gateway, qdrant_rag
│       ├── documents/    # docx_template_engine, pdf_exporter
│       ├── email/        # smtp_adapter (para notificacoes internas)
│       ├── llm/          # gemini_analyzer (analise de templates, classificacao)
│       ├── payments/     # mercadopago adapter (assinaturas)
│       └── storage/      # MinIO adapter
├── infrastructure/       # config (pydantic-settings), security (JWT)
├── tasks/                # Celery tasks (background jobs)
└── alembic.ini
```

---

## Multi-Tenancy

- Coluna `tenant_id` em todas as tabelas
- Middleware extrai `tenant_id` do JWT e injeta no contexto
- Todas as queries incluem `WHERE tenant_id = :tenant_id`
- RLS no PostgreSQL como segunda barreira de seguranca

**Campos chave no modelo Tenant:**
- `agent_id` — agente primario registrado
- `active_agent_id` — agente atualmente ativo (pode diferir do primario)
- `get_active_agent_id()` — retorna `active_agent_id` se definido, senao `agent_id`

---

## Sistema de Agentes

### Identificacao de Agentes
- `agent_id` = nome do diretorio em `agents/agents/{agent_id}/`
- `tenant.agent_id` = agente primario (criado no onboarding)
- `tenant.active_agent_id` = agente ativo para novas conversas
- Conversas sao taggeadas com o `agent_id` que as processou

### business.yml — Campos Essenciais

```yaml
name: "Nome do Assistente"
company: "Nome da Empresa"        # auto-preenchido do tenant no create
language: "pt"
persona: |
  Descricao livre da personalidade e instrucoes do agente.
  Escrito pelo usuario, sem instrucoes tecnicas.
tts: false
crm:
  enabled: true
  events_webhook: "${CRM_WEBHOOK_URL}"   # env var, nunca hardcoded
llm:
  provider: gemini
  model: gemini-2.0-flash
  api_key: "${GEMINI_API_KEY}"          # env var, NUNCA no frontend
```

### Campos Removidos do business.yml
- Sem `ollama` — Gemini e o unico provedor
- Sem `api_key` direta — sempre via env var
- Sem instrucoes tecnicas na persona — usuario escreve linguagem natural

### Criacao de Agente (via CRM)
1. CRM copia `agents/agents/template/` para `agents/agents/{agent_id}/`
2. Preenche `company` com `tenant.name` automaticamente
3. Salva `business.yml` via `FilesystemAgentConfigAdapter`
4. Cria colecoes Qdrant: `{agent_id}_chats` e `{agent_id}_rules`
5. Registra `tenant.agent_id = agent_id`

---

## Onboarding Wizard (pos-signup)

Fluxo obrigatorio para novos usuarios, full-screen dark design (`#0F0F0F`).
Marcado como concluido em `localStorage.setItem('onboarding_{tenant.id}', 'done')`.

**5 passos:**
1. **Nicho** — selecao do segmento de mercado (define persona pre-configurada)
2. **Empresa** — nome da empresa, logo (opcional)
3. **Gemini API Key** — usuario insere sua chave (salva em Settings, nunca no frontend)
4. **Agente** — nome do assistente, `agent_id` auto-gerado (slug do nome)
5. **WhatsApp** — conectar numero (QR code via gateway)

**Nichos disponíveis:** Clinicas, Imoveis, E-commerce, Restaurantes, Academia, Energia Solar, Generico

Cada nicho tem uma persona pre-escrita em portugues informal, warm, sem jargao tecnico.

**Redirect logic:**
- Apos signup: redireciona para `/app/onboarding`
- Em AppLayout: se `localStorage.getItem('onboarding_{tenant.id}')` e null, redireciona para onboarding
- Apos onboarding: redireciona para `/app/dashboard`

---

## Human Takeover

1. Operador clica "Assumir" → CRM seta `takeover:{session}:{chat_id}` no Redis (TTL 4h)
2. Gateway proxy verifica Redis:
   - Takeover ativo: mensagem vai para CRM + WebSocket (NAO chega no agente)
   - Sem takeover: forward para agents + armazena copia no CRM
3. Operador envia mensagem via CRM → CRM chama gateway REST diretamente
4. Operador clica "Devolver" → deleta Redis key, fluxo volta ao agente

---

## Conversas e Filtro por Agente

**Bug corrigido (2026-03-29):** `handle_gateway_proxy.py` usava `tenant.agent_id` (primario)
para taggear conversas criadas via gateway, causando split de conversas quando `active_agent_id`
diferia. Fix: usa `tenant.get_active_agent_id()` em todo o fluxo do proxy.

```python
# CORRETO
active_agent_id = tenant.get_active_agent_id()
conversation = await self._conversation_repo.get_by_chat_id(
    tenant.id, chat_id, agent_id=active_agent_id
)
```

O filtro de agente na UI de Conversas depende de que TODAS as conversas sejam taggeadas com
o `agent_id` correto desde a criacao.

---

## Sistema de Propostas DOCX

1. Tenant faz upload de DOCX com placeholders: `{nome_cliente}`, `{valor_total}`, etc.
2. CRM extrai placeholders via regex em python-docx
3. (Opcional) Gemini valida e descreve cada placeholder
4. Na geracao: CRM substitui placeholders com dados reais do orcamento
5. Converte DOCX → PDF via LibreOffice headless
6. Armazena no MinIO, disponibiliza link publico ou envia pelo WhatsApp

---

## Modulos e Entidades

| Modulo | Entidades | Descricao |
|---|---|---|
| Tenants | Tenant, TenantSettings | Multi-tenant white-label (logo, cores, plano, trial) |
| Auth | User, Role, PasswordResetToken | JWT, roles: admin/manager/operator, reset por email |
| Clientes | Customer | CRUD + auto-criacao via evento `new_contact` do agente |
| Leads | Lead, LeadStage | Pipeline Kanban (new→contacted→qualified→proposal→negotiation→won/lost) |
| Premissas | Premise | % imposto, % comissao, % lucro, % locomocao + custom ilimitado por tenant |
| Orcamentos | Quote, QuoteItem, QuoteTemplate, AppliedPremise | Calculo com premissas, templates DOCX, PDF |
| Contratos | Contract, ContractTemplate | Gerado a partir de orcamento aprovado, templates proprios |
| Estoque | Product, StockMovement | CRUD, movimentacoes (entrada/saida/ajuste), alerta de estoque baixo |
| Agentes | AgentConfiguration | Leitura/escrita business.yml, upload RAG, gerencia docs |
| Conversas | Conversation, Message, TakeoverSession | Fila real-time, takeover humano, WebSocket |
| Dashboard | KPIs, Metrics | Totais, graficos temporais, metricas de conversas |
| Pagamentos | MPSubscription | MercadoPago assinaturas (planos Starter/Pro/Enterprise) |

---

## Settings > Integracoes

O que aparece em Settings > Integracoes (NAO em AgentConfig):
- **Gemini API Key** — chave do usuario, armazenada no servidor criptografada
- **Webhook de Eventos** — URL externa para receber eventos do CRM (leads, conversas, etc.)

O que NAO aparece em nenhum lugar do frontend:
- API keys em texto plain apos salvas
- Configuracoes internas do runtime dos agentes

**Removido:** integracao SMTP do frontend (era confusa e raramente usada pelos usuarios finais).
SMTP ainda existe no backend para notificacoes internas (reset de senha, alertas de trial).

---

## AgentConfig UI — Principio de Simplicidade

A UI de configuracao de agente e minimalista por design. Usuarios finais nao sao tecnicos.

**Tabs:**
1. **Personalidade** — nome do assistente, nome da empresa, lingua, textarea de persona livre, TTS
2. **Documentos RAG** — upload de PDFs/DOCX para base de conhecimento
3. **Instancias WhatsApp** — conectar/desconectar numeros (ate 3 por tenant)

**Removido da UI de agente:**
- Campo de API key (movido para Settings)
- Temperatura / model display
- Configuracoes de Ollama
- Debounce / unknown_answer / instrucoes tecnicas
- "Agente padrao" — cada tenant cria o seu no onboarding

---

## Arquivos Criticos

### Integracao CRM ↔ Agents
- `agents/infrastructure/config_loader.py` — schema do `business.yml`
- `agents/adapters/inbound/waha_webhook.py` — payload do gateway (Baileys format)
- `crm/adapters/outbound/agents/filesystem_agent_config.py` — leitura/escrita do business.yml
- `crm/core/use_cases/conversations/handle_gateway_proxy.py` — proxy + takeover logic
- `crm/core/domain/tenant.py` — `get_active_agent_id()` method

### Auth e Multi-tenant
- `crm/adapters/inbound/api/routes/auth_routes.py` — register, login, integrations
- `crm/adapters/inbound/api/dependencies.py` — `get_current_tenant()` middleware
- `crm/infrastructure/config.py` — pydantic-settings, todas as env vars

### Frontend
- `frontend/src/pages/app/OnboardingWizardPage.tsx` — wizard pos-signup (5 passos)
- `frontend/src/pages/app/AgentConfigPage.tsx` — config simplificada
- `frontend/src/pages/app/SettingsPage.tsx` — integracoes (Gemini key + webhook)
- `frontend/src/components/app/AppLayout.tsx` — redirect para onboarding se nao concluido
- `frontend/src/store/authStore.ts` — JWT + tenant + user state

---

## Backlog de Features (nao implementadas)

### Alta Prioridade
- [ ] Multiplas instancias WhatsApp simultaneas (ate 3 numeros, 4 agentes por tenant)
- [ ] Classificacao de leads por agente via LLM (estagio automatico baseado na conversa)
- [ ] Dashboard avancado com graficos, metricas por agente, funil de conversao

### Media Prioridade
- [ ] Modulo de suporte prioritario (tickets + SLA)
- [ ] Relatorios complexos com export PDF e filtros avancados
- [ ] White-label visual completo (tenant usa propria logo/cores em toda a UI)
- [ ] Gestao de usuarios ilimitados por tenant (plano)

### Baixa Prioridade
- [ ] Notificacoes push / email para eventos criticos (lead ganho, estoque baixo)
- [ ] API publica para integracoes de terceiros
- [ ] Mobile app (React Native)

---

## Regras de Desenvolvimento

1. **Zero modificacoes no core dos agents** — CRM se adapta aos agents, nao o contrario
2. **Gemini only** — nao adicionar suporte a outros LLMs sem decisao explicita
3. **API keys nunca no frontend** — sempre via env var ou storage seguro no servidor
4. **Cada agente e isolavel** — codigo e configuracao em `agents/agents/{id}/` deve ser
   autocontido e empacotavel como Docker image independente
5. **Hexagonal em ambos os lados** — ports/adapters no CRM E nos agents; nenhuma camada
   de dominio conhece detalhes de infraestrutura
6. **Personas em linguagem natural** — sem instrucoes tecnicas ou YAML na persona do agente;
   usuario escreve como descreveria um funcionario para um colega
7. **Onboarding obrigatorio** — novos tenants SEMPRE passam pelo wizard antes de acessar o app
