● Plano completo escrito. Resumo dos pontos principais:

  - CRM separado em D:\CRM\crm\ com arquitetura hexagonal propria
  - Zero modificacoes no codigo dos agents — apenas env var WEBHOOK_URL aponta para o CRM proxy
  - WAHA Proxy no CRM intercepta mensagens para takeover humano via Redis
  - Propostas DOCX com placeholders auto-detectados + geracao PDF
  - Premissas customizaveis (%, valor fixo, ilimitadas por tenant)
  - Multi-tenant com RLS no PostgreSQL
  - Real-time via WebSocket para conversas
  - 10 sprints comecando pelo scaffolding + auth

● User approved Claude's plan
  ⎿  Plan saved to: C:\Users\Rafael Dourado\.claude\plans\quiet-discovering-pelican.md · /plan to edit
     Plano: CRM White-Label com Arquitetura Hexagonal                                                                                                                                                                     
     Contexto                                                                                                                                                                                                      
  
     Construir um CRM white-label multi-tenant que se integra com o framework de agentes WhatsApp existente (D:\CRM\agents\) sem modificar o codigo dos agentes. O CRM sera um sistema separado (D:\CRM\crm\) que
     consome eventos dos agentes, gerencia configuracoes via filesystem compartilhado, e permite takeover humano via proxy de webhook WAHA.

     Inspiracoes: helenacrm.com, zarpon.com.br. Diferencial: propostas comerciais automatizadas via templates DOCX + RAG.

     ---
     Arquitetura de Integracao (CRM <-> Agents)

     WAHA Gateway (porta 3000)
         |
         | POST /webhook
         v
     CRM Webhook Proxy (porta 8001)  ──── Verifica Redis: takeover ativo?
         |                                    |
         | SIM: armazena + WebSocket          | NAO: forward para agents + armazena
         v                                    v
     Operador (chat humano)           Agents API (porta 8000, inalterado)
                                              |
                                              | push_event (fire-and-forget)
                                              v
                                      CRM Webhook Receiver (/webhooks/agent-events)
                                              |
                                              v
                                      PostgreSQL CRM + WebSocket (real-time)

     Mudanca necessaria nos agents: Apenas a env var WEBHOOK_URL no docker-compose aponta para o CRM proxy em vez do agents diretamente.

     ---
     Estrutura do Projeto

     D:\CRM\crm\
     ├── core/
     │   ├── domain/           # Entidades puras (Tenant, Customer, Lead, Quote, Premise, Contract, Product, Conversation)
     │   ├── ports/
     │   │   ├── inbound/      # Interfaces de servico (CustomerServicePort, QuoteServicePort, etc.)
     │   │   └── outbound/     # Interfaces de repositorio + gateways externos
     │   └── use_cases/        # Um diretorio por modulo (customers/, leads/, quotes/, conversations/, etc.)
     ├── adapters/
     │   ├── inbound/
     │   │   ├── api/          # FastAPI app, routes, middleware (auth, tenant_context)
     │   │   └── websocket/    # ConnectionManager, real-time conversations
     │   └── outbound/
     │       ├── persistence/  # SQLAlchemy models, Alembic migrations, repositorios Postgres
     │       ├── agents/       # agent_api_gateway, waha_direct_gateway, config_writer, rag_client
     │       ├── messaging/    # RabbitMQ adapter
     │       ├── cache/        # Redis adapter
     │       ├── storage/      # MinIO adapter (DOCX/PDF files)
     │       └── documents/    # docx_template_engine, pdf_exporter
     ├── infrastructure/       # config (pydantic-settings), security (JWT), logging (structlog)
     ├── tests/
     │   ├── unit/             # TDD - mocks nos ports
     │   ├── integration/      # Servicos reais via docker-compose
     │   └── bdd/              # pytest-bdd (features + steps)
     ├── docker-compose.yml
     ├── Dockerfile
     ├── alembic.ini
     └── requirements.txt

     ---
     Modulos e Entidades

     ┌────────────┬─────────────────────────────────────────────────┬────────────────────────────────────────────────────────────────────────────────────────┐
     │   Modulo   │                    Entidades                    │                                       Descricao                                        │
     ├────────────┼─────────────────────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────┤
     │ Tenants    │ Tenant, TenantSettings                          │ Multi-tenant white-label (logo, cores, plano)                                          │
     ├────────────┼─────────────────────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────┤
     │ Auth       │ User, Role                                      │ JWT auth, roles: admin/manager/operator                                                │
     ├────────────┼─────────────────────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────┤
     │ Clientes   │ Customer                                        │ CRUD + auto-criacao via evento new_contact do agente                                   │
     ├────────────┼─────────────────────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────┤
     │ Leads      │ Lead, LeadStage                                 │ Pipeline Kanban (new -> contacted -> qualified -> proposal -> negotiation -> won/lost) │
     ├────────────┼─────────────────────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────┤
     │ Premissas  │ Premise                                         │ % imposto, % comissao, % lucro, % locomocao + custom ilimitado                         │
     ├────────────┼─────────────────────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────┤
     │ Orcamentos │ Quote, QuoteItem, QuoteTemplate, AppliedPremise │ Calculo com premissas, templates DOCX com placeholders, geracao PDF                    │
     ├────────────┼─────────────────────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────┤
     │ Contratos  │ Contract                                        │ Gerado a partir de orcamento aprovado                                                  │
     ├────────────┼─────────────────────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────┤
     │ Estoque    │ Product, StockMovement                          │ CRUD produtos, movimentacoes (entrada/saida/ajuste), alerta estoque baixo              │
     ├────────────┼─────────────────────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────┤
     │ Agentes    │ AgentConfiguration                              │ Leitura/escrita business.yml, upload RAG, gerencia docs                                │
     ├────────────┼─────────────────────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────┤
     │ Conversas  │ ConversationView, TakeoverSession, CRMMessage   │ Fila em tempo real, takeover humano, WebSocket                                         │
     ├────────────┼─────────────────────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────┤
     │ Dashboard  │ KPIs, Metrics                                   │ Totais, graficos temporais, metricas de conversas                                      │
     └────────────┴─────────────────────────────────────────────────┴────────────────────────────────────────────────────────────────────────────────────────┘

     ---
     Multi-Tenancy

     Estrategia: Row-Level Isolation (RLS) com coluna tenant_id em todas as tabelas.
     - Middleware extrai tenant_id do JWT e seta SET app.current_tenant.
     - RLS policies no PostgreSQL como segunda barreira.
     - Todas as queries incluem WHERE tenant_id = :tenant_id.

     ---
     Human Takeover (Mecanismo)

     1. Operador clica "Assumir" -> CRM seta Redis key takeover:{agent_id}:{chat_id} (TTL 4h)
     2. WAHA proxy verifica Redis antes de forwarding:
       - Takeover ativo: mensagem vai para CRM + WebSocket (nao chega no agent)
       - Sem takeover: forward para agents + armazena copia no CRM
     3. Operador envia mensagem via CRM -> CRM chama WAHA REST diretamente (POST /api/sendText)
     4. Operador clica "Devolver" -> deleta Redis key, proximo msg vai para agent normalmente

     ---
     Sistema de Propostas DOCX

     1. Tenant faz upload de DOCX com placeholders: {nome_cliente}, {valor_total}, {material}
     2. CRM extrai placeholders via regex em python-docx
     3. (Opcional) LLM valida e descreve cada placeholder
     4. Na geracao do orcamento: CRM substitui placeholders com dados reais
     5. Converte DOCX -> PDF via LibreOffice headless
     6. Compartilha via link publico ou envia PDF pelo WhatsApp

     ---
     Stack

     ┌────────────┬────────────────────────────────────────────────┐
     │ Componente │                   Tecnologia                   │
     ├────────────┼────────────────────────────────────────────────┤
     │ Backend    │ FastAPI + asyncio                              │
     ├────────────┼────────────────────────────────────────────────┤
     │ DB CRM     │ PostgreSQL 16 (separado do agents)             │
     ├────────────┼────────────────────────────────────────────────┤
     │ Cache      │ Redis (db=1, agents usa db=0)                  │
     ├────────────┼────────────────────────────────────────────────┤
     │ Broker     │ RabbitMQ                                       │
     ├────────────┼────────────────────────────────────────────────┤
     │ Storage    │ MinIO (S3-compatible)                          │
     ├────────────┼────────────────────────────────────────────────┤
     │ Migrations │ Alembic                                        │
     ├────────────┼────────────────────────────────────────────────┤
     │ Auth       │ JWT (PyJWT)                                    │
     ├────────────┼────────────────────────────────────────────────┤
     │ DOCX       │ python-docx                                    │
     ├────────────┼────────────────────────────────────────────────┤
     │ PDF        │ LibreOffice headless                           │
     ├────────────┼────────────────────────────────────────────────┤
     │ Logs       │ structlog                                      │
     ├────────────┼────────────────────────────────────────────────┤
     │ Testes     │ pytest + pytest-bdd                            │
     ├────────────┼────────────────────────────────────────────────┤
     │ Frontend   │ Next.js 14 + TypeScript + Tailwind + shadcn/ui │
     └────────────┴────────────────────────────────────────────────┘

     ---
     Docker Compose (CRM)

     Servicos novos: crm-api (8001), crm-postgres (5433), rabbitmq (5672/15672), minio (9000/9001).
     Conecta na mesma rede Docker dos agents para acessar Redis, Qdrant, Gateway, Agents API.

     Volume compartilhado: ../agents/agents:/app/shared-agents para ler/escrever business.yml.

     ---
     Sprints

     ┌────────┬─────────────────────────────────────────────────────────┬──────┐
     │ Sprint │                          Foco                           │ Dias │
     ├────────┼─────────────────────────────────────────────────────────┼──────┤
     │ 0      │ Scaffolding, Docker, Auth (tenant + user + JWT)         │ 5    │
     ├────────┼─────────────────────────────────────────────────────────┼──────┤
     │ 1      │ Clientes + Webhook receiver + WAHA proxy (pass-through) │ 5    │
     ├────────┼─────────────────────────────────────────────────────────┼──────┤
     │ 2      │ Conversas + WebSocket real-time                         │ 5    │
     ├────────┼─────────────────────────────────────────────────────────┼──────┤
     │ 3      │ Human Takeover completo                                 │ 5    │
     ├────────┼─────────────────────────────────────────────────────────┼──────┤
     │ 4      │ Leads + Pipeline Kanban                                 │ 4    │
     ├────────┼─────────────────────────────────────────────────────────┼──────┤
     │ 5      │ Premissas + Motor de orcamentos                         │ 5    │
     ├────────┼─────────────────────────────────────────────────────────┼──────┤
     │ 6      │ Templates DOCX + Geracao PDF                            │ 5    │
     ├────────┼─────────────────────────────────────────────────────────┼──────┤
     │ 7      │ Contratos + Estoque                                     │ 4    │
     ├────────┼─────────────────────────────────────────────────────────┼──────┤
     │ 8      │ Config de agentes via UI + RAG management               │ 4    │
     ├────────┼─────────────────────────────────────────────────────────┼──────┤
     │ 9      │ Dashboard + Analytics                                   │ 4    │
     ├────────┼─────────────────────────────────────────────────────────┼──────┤
     │ 10     │ White-label theming + Hardening + Load test             │ 5    │
     └────────┴─────────────────────────────────────────────────────────┴──────┘

     ---
     Arquivos Criticos para Integracao

     - agents/core/ports/crm_port.py — Schema do CRMEvent (contrato webhook)
     - agents/adapters/outbound/crm/crm_event_adapter.py — Formato exato do POST
     - agents/adapters/inbound/waha_webhook.py — Payload WAHA que o proxy deve parsear
     - agents/infrastructure/config_loader.py — Schema do business.yml para CRM ler/escrever
     - agents/adapters/outbound/gateway/waha_adapter.py — API WAHA para mensagens diretas no takeover

     ---
     Verificacao

     1. docker-compose up -> todos os servicos healthy
     2. GET /health retorna 200 com status dos servicos
     3. Agent envia mensagem -> CRM recebe via webhook -> customer criado automaticamente
     4. Operador ve conversa em tempo real no WebSocket
     5. Takeover: mensagem do cliente NAO chega no agent, operador responde direto
     6. Resume: proximo msg flui para agent normalmente
     7. Criar orcamento com premissas -> total calculado corretamente
     8. Upload DOCX -> placeholders detectados -> geracao PDF funcional
     9. Testes: pytest tests/unit/ -v + pytest tests/bdd/ -v all green

     ---
     Comecamos pelo Sprint 0

     Criar a estrutura hexagonal do CRM, Docker Compose, modelos base (Tenant, User), auth JWT, health check.
