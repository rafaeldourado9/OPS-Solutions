# Plano de Sprints — CRM White-Label Completo

## Context

O CRM multi-tenant com agentes WhatsApp tem todos os modulos CRUD funcionando (Leads, Customers, Quotes, Contracts, Inventory, Dashboard, Settings, Conversations), mas faltam features criticas para entregar a plataforma pronta:

1. **Multi-WhatsApp** — gateway suporta apenas 1 numero; planos prometem ate 3
2. **Enforcement de planos** — nenhum middleware valida limites (agentes, numeros, usuarios)
3. **Templates unificados** — pagina so mostra contratos; orcamentos tem backend mas nao aparece na UI
4. **Agent flows** — sistema de fluxos entre agentes nao existe
5. **Ollama agent interno** — agente leve para acoes na plataforma nao existe
6. **Formato numero WhatsApp** — UI mostra formato errado
7. **Trial enforcement** — `trial_ends_at` existe mas middleware `_trial_check_middleware` ja implementado (verificar se funciona)

Modulos que JA FUNCIONAM e NAO precisam de rewrite:
- Leads (Kanban completo com transicoes), Customers, Quotes (wizard 3-step + PDF), Contracts, Inventory, Dashboard (5 KPIs + graficos), Settings (7 tabs), Conversations (isolamento por agent_id OK)

---

## Sprint 1 — Multi-WhatsApp & Isolamento de Numeros (5 dias)

**Objetivo:** Cada tenant pode conectar ate 3 numeros WhatsApp, cada um com seu QR code e sessao independente.

### 1.1 Gateway: Suporte a multiplas sessoes
- **`agents/gateway/src/whatsapp.js`** — Refatorar de sessao unica para mapa de sessoes
  - `sessions = new Map()` — cada sessao tem seu proprio socket Baileys
  - `createSession(sessionName)` — cria socket + auth store separado
  - `removeSession(sessionName)` — desconecta e limpa
  - QR code por sessao (nao mais variavel global `_currentQr`)
- **`agents/gateway/src/routes.js`** — Todas as rotas recebem `session` como query param
  - `GET /api/qr?session=xxx` — QR da sessao especifica
  - `GET /health?session=xxx` — status da sessao especifica
  - `GET /api/sessions` — lista todas as sessoes ativas
  - `POST /api/sessions` — cria nova sessao
  - `DELETE /api/sessions/:name` — remove sessao
  - `POST /api/sendText?session=xxx` — envio por sessao
- Webhook inclui `session` no payload para roteamento correto

### 1.2 CRM: Modelo de numeros WhatsApp por tenant
- **Nova tabela `crm_whatsapp_numbers`**: id, tenant_id, session_name, phone_number, label, agent_id (FK nullable), is_active, connected_at, created_at
- **Nova migration** `018_whatsapp_numbers.py`
- **Novo dominio** `crm/core/domain/whatsapp_number.py`
- **Novo repositorio** + port
- **Novas rotas** `crm/adapters/inbound/api/routes/whatsapp_routes.py`:
  - `GET /api/v1/whatsapp/numbers` — lista numeros do tenant
  - `POST /api/v1/whatsapp/numbers` — adiciona numero (cria sessao no gateway)
  - `DELETE /api/v1/whatsapp/numbers/:id` — remove numero
  - `GET /api/v1/whatsapp/numbers/:id/qr` — QR code
  - `GET /api/v1/whatsapp/numbers/:id/status` — status conexao
  - `POST /api/v1/whatsapp/numbers/:id/restart`
  - `POST /api/v1/whatsapp/numbers/:id/logout`

### 1.3 Frontend: Tab WhatsApp redesenhada
- **`AgentConfigPage.tsx`** tab "WhatsApp" — lista de numeros conectados
  - Card por numero: telefone formatado (+55 11 99999-9999), status (conectado/desconectado), agente associado, botoes restart/logout
  - Botao "Adicionar numero" — abre modal com QR code
  - Limite visual baseado no plano (1 starter, 3 pro, ilimitado enterprise)

### 1.4 Roteamento de mensagens por numero
- **`handle_gateway_proxy.py`** — identifica qual numero recebeu a mensagem via `session` no payload
- Lookup `whatsapp_numbers` para encontrar o `agent_id` associado aquele numero
- Se numero nao tem agente associado, usa o `active_agent_id` do tenant

### Verificacao
- Conectar 2 numeros diferentes no mesmo tenant
- Enviar mensagem para cada numero → cada um roteia para o agente correto
- Desconectar 1 numero → outro continua funcionando
- QR codes independentes

---

## Sprint 2 — Enforcement de Planos & Limites (3 dias)

**Objetivo:** Planos (Starter/Pro/Enterprise) realmente limitam recursos. Trial expira e bloqueia.

### 2.1 Middleware de limites
- **`crm/adapters/inbound/api/middleware/plan_limits.py`** (novo)
  - Define limites por plano:
    ```
    PLAN_LIMITS = {
      "starter": {"max_whatsapp": 1, "max_agents": 1, "max_users": 3},
      "pro": {"max_whatsapp": 3, "max_agents": 4, "max_users": 999},
      "enterprise": {"max_whatsapp": 999, "max_agents": 999, "max_users": 999},
    }
    ```
  - Dependency `check_plan_limit(resource, tenant_id)` usada nas rotas de criacao

### 2.2 Aplicar limites nos endpoints
- `POST /api/v1/whatsapp/numbers` — verifica `max_whatsapp`
- `POST /api/v1/agents/instances` — verifica `max_agents`
- `POST /api/v1/users/invite` — verifica `max_users`
- Retorna 403 com mensagem clara: "Limite do plano Starter: maximo 1 numero WhatsApp. Faca upgrade para Pro."

### 2.3 Trial enforcement (verificar existente)
- **`_trial_check_middleware`** em `main.py` ja existe (linhas 46-89) — verificar se funciona corretamente
- Ajustar: trial de 14 dias setado no registro (`register_tenant.py`)
- Frontend: `TrialBanner.tsx` ja existe — verificar se aparece

### 2.4 Plan "Agent Solo"
- Adicionar "agent_solo" ao backend de pagamentos (`payment_routes.py` linha 51)
- Limites: 1 WhatsApp, 1 agente, 1 usuario, sem CRM (apenas agente)

### Verificacao
- Tenant starter tenta criar 2o numero → erro 403
- Tenant pro cria ate 3 numeros → OK
- Trial expira → 402 em todas as rotas (exceto auth/settings/subscription)
- Upgrade de plano → limites expandem imediatamente

---

## Sprint 3 — Templates Unificados (2 dias)

**Objetivo:** Pagina de Templates gerencia DOCX tanto para orcamentos quanto contratos, com placeholders customizaveis.

### 3.1 Unificar UI
- **`TemplatesPage.tsx`** — adicionar tabs ou filtro: "Orcamentos" | "Contratos"
  - Tab Orcamentos: usa `templatesApi` (quote templates) — backend ja existe completo
  - Tab Contratos: usa `contractTemplatesApi` — ja funciona
  - Ambas mostram: nome, variaveis/placeholders, acoes (gerar, deletar)
- Quote templates tem feature extra: mapeamento de campos CRM (campo → variavel DOCX)

### 3.2 Melhorar UX de variaveis
- Mostrar preview das variaveis encontradas no DOCX com `{placeholder}` syntax
- Para quote templates: mostrar dropdown de campos CRM disponiveis para cada variavel
- Para contract templates: input livre de valores

### Verificacao
- Upload de DOCX com placeholders → variaveis extraidas corretamente
- Gerar PDF de orcamento com template → substitui valores reais
- Gerar PDF de contrato com template → substitui valores manuais

---

## Sprint 4 — Formato WhatsApp & Ajustes de UI (1 dia)

**Objetivo:** Correcoes visuais e de UX.

### 4.1 Formato de numero
- **`ConversationsPage.tsx`** e **`AgentConfigPage.tsx`** — formatar numeros como +55 (11) 99999-9999
- Funcao utilitaria `formatPhoneNumber(jid: string)` que extrai numero do formato Baileys (`5511999999999@s.whatsapp.net`)

### 4.2 Tab "Instancias" renomeada
- **`AgentConfigPage.tsx`** — tab "Instancias" vira "Agentes" (gerencia os ate 4 agentes do tenant)
- Manter funcionalidade atual: criar/ativar/deletar agentes
- Adicionar indicador visual de qual numero WhatsApp esta associado a cada agente

### Verificacao
- Numeros exibidos no formato correto em toda a UI
- Tab "Agentes" lista agentes com numero associado

---

## Sprint 5 — RAG por Agente Individual (2 dias)

**Objetivo:** Cada um dos ate 4 agentes tem sua propria base de conhecimento RAG.

### 5.1 Backend (ja parcialmente implementado)
- Cada agente ja tem colecao Qdrant isolada: `{agent_id}_rules` — criado em `create_agent()`
- **`agent_routes.py`** RAG routes ja aceitam `agent_id` param — verificar se funciona
- Garantir que upload de documento RAG vai para a colecao do agente ativo/selecionado

### 5.2 Frontend
- **`AgentConfigPage.tsx`** tab RAG — adicionar seletor de agente antes da lista de documentos
- Ao trocar agente selecionado, recarregar lista de documentos daquele agente
- Upload envia `agent_id` no form data (ja suportado no backend)

### Verificacao
- Upload documento para agente A → aparece apenas no RAG do agente A
- Agente B nao ve documentos do agente A
- Deletar documento de agente A → nao afeta agente B

---

## Sprint 6 — Agent Flows (5 dias) [FUTURO]

**Objetivo:** Agentes podem se comunicar entre si e executar acoes na plataforma.

> **Nota:** Este sprint e mais complexo e pode ser adiado para uma segunda fase. Requer design mais detalhado.

### 6.1 Conceito
- Flow = sequencia de acoes que um agente pode disparar
- Acoes: enviar mensagem para outro agente, criar orcamento, registrar cliente, mover lead
- Triggers: palavra-chave, intencao detectada, evento do CRM

### 6.2 Implementacao basica
- Nova tabela `crm_agent_flows`: id, tenant_id, agent_id, trigger_type, trigger_config, actions (JSONB)
- Novas rotas CRUD para flows
- Engine de execucao: quando trigger dispara, executa acoes sequencialmente
- UI: builder visual de flows (drag-and-drop simplificado)

### 6.3 Ollama Agent Interno
- Agente leve rodando Ollama que escuta eventos dos outros agentes
- Pode executar: criar orcamento, registrar estoque, cadastrar cliente
- Configurado via flow, nao via UI separada

---

## Sprint 7 — Testes & Documentacao (3 dias)

### 7.1 Testes de integracao
- Pytest fixtures com tenant de teste
- Testar: criacao de tenant → onboarding → conectar WhatsApp → enviar mensagem → conversa aparece → lead criado
- Testar: limites de plano (criar mais agentes que o permitido)
- Testar: isolamento (tenant A nao ve dados do tenant B)

### 7.2 Documentacao
- `docs/architecture.md` — diagrama atualizado
- `docs/sprint-guide.md` — este documento convertido
- `docs/api-reference.md` — endpoints organizados por modulo
- `docs/deployment.md` — guia de deploy com docker-compose

### Verificacao
- `pytest` passa em todos os testes
- Documentacao cobre todos os modulos

---

## Ordem de Execucao Recomendada

| Sprint | Dias | Prioridade | Dependencias |
|--------|------|------------|--------------|
| Sprint 1 (Multi-WhatsApp) | 5 | CRITICA | Nenhuma |
| Sprint 2 (Planos & Limites) | 3 | CRITICA | Sprint 1 |
| Sprint 3 (Templates) | 2 | ALTA | Nenhuma |
| Sprint 4 (UI fixes) | 1 | MEDIA | Nenhuma |
| Sprint 5 (RAG por agente) | 2 | ALTA | Nenhuma |
| Sprint 6 (Agent Flows) | 5 | BAIXA | Sprint 1+2 |
| Sprint 7 (Testes & Docs) | 3 | ALTA | Todos |

**Sprints 1+2 sao bloqueantes** — sem multi-WhatsApp e enforcement de planos, a plataforma nao pode ser vendida.

**Sprints 3, 4, 5 podem rodar em paralelo** apos Sprint 1.

**Sprint 6 e opcional para v1** — pode ser entregue como v1.1.

---

## Nota sobre Gemini API Key

O agente NAO responde mensagens atualmente porque a API key do Gemini esta invalida. Isso NAO e um bug de codigo — o usuario precisa gerar uma nova chave em https://aistudio.google.com/apikey e salvar em Settings > Integracoes.

---

## Arquivos Criticos por Sprint

### Sprint 1
- `agents/gateway/src/whatsapp.js` — refatorar para multi-sessao
- `agents/gateway/src/routes.js` — adicionar param session em todas rotas
- `crm/adapters/inbound/api/routes/whatsapp_routes.py` (novo)
- `crm/core/domain/whatsapp_number.py` (novo)
- `crm/adapters/outbound/persistence/models/whatsapp_number_model.py` (novo)
- `crm/adapters/outbound/persistence/migrations/versions/018_whatsapp_numbers.py` (novo)
- `crm/core/use_cases/conversations/handle_gateway_proxy.py` — roteamento por numero
- `frontend/src/pages/app/AgentConfigPage.tsx` — redesign tab WhatsApp

### Sprint 2
- `crm/adapters/inbound/api/middleware/plan_limits.py` (novo)
- `crm/adapters/inbound/api/routes/agent_routes.py` — add limit check
- `crm/adapters/inbound/api/routes/payment_routes.py` — add agent_solo plan
- `crm/adapters/inbound/api/routes/user_routes.py` — add limit check

### Sprint 3
- `frontend/src/pages/app/TemplatesPage.tsx` — unificar quote + contract templates

### Sprint 4
- `frontend/src/pages/app/ConversationsPage.tsx` — formato numero
- `frontend/src/pages/app/AgentConfigPage.tsx` — renomear tab

### Sprint 5
- `frontend/src/pages/app/AgentConfigPage.tsx` — seletor de agente no RAG tab
- `crm/adapters/inbound/api/routes/agent_routes.py` — verificar RAG routes com agent_id
