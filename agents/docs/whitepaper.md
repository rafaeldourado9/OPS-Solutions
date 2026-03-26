# WhatsApp Agent Framework
## Por que isso não existe no mercado — e por que importa

> Documento técnico para stakeholders
> Versão 1.0 — 2026

---

## Índice

1. [O Problema Real](#1-o-problema-real)
2. [O que Construímos](#2-o-que-construímos)
3. [Arquitetura Geral](#3-arquitetura-geral)
4. [Como uma Mensagem Vira uma Resposta](#4-como-uma-mensagem-vira-uma-resposta)
5. [Memória — O que Torna o Agente Inteligente](#5-memória--o-que-torna-o-agente-inteligente)
6. [Multi-Agente num Único Número](#6-multi-agente-num-único-número)
7. [Comportamento Humano por Design](#7-comportamento-humano-por-design)
8. [Por que é Impossível Replicar com n8n ou Ferramentas Visuais](#8-por-que-é-impossível-replicar-com-n8n-ou-ferramentas-visuais)
9. [Comparativo de Mercado](#9-comparativo-de-mercado)
10. [Modelo de Negócio](#10-modelo-de-negócio)
11. [Infraestrutura e Escalabilidade](#11-infraestrutura-e-escalabilidade)

---

## 1. O Problema Real

Agentes de WhatsApp existentes falham de formas previsíveis e custosas:

**Problema 1 — Parecem robô**
Respondem com uma mensagem única de 400 palavras. No WhatsApp real, pessoas escrevem em partes curtas, com pausas naturais. Um bloco de texto longo quebra a ilusão imediatamente.

**Problema 2 — Respondem múltiplas vezes para uma única intenção**
Usuário digita "oi", "tudo bem?", "preciso de uma cotação" em 5 segundos. A maioria dos sistemas responde três vezes, uma para cada mensagem. Isso é spam automatizado.

**Problema 3 — Não lembram do que foi dito**
Sem memória real, cada sessão começa do zero. O usuário precisa repetir contexto. Isso destrói a experiência e a conversão.

**Problema 4 — Alucinam quando não sabem algo**
Sem base de conhecimento específica da empresa, o LLM inventa informações — preços, prazos, políticas. Em ambientes comerciais, isso gera problemas jurídicos e de reputação.

**Problema 5 — São presos a uma empresa**
Cada implementação existente é construída do zero para uma empresa. Não existe reuso. Mudar o agente significa reescrever tudo.

---

## 2. O que Construímos

Um **framework de agentes WhatsApp** que resolve todos esses problemas simultaneamente, com uma propriedade rara: **o mesmo código atende qualquer empresa**. A diferença entre o agente da Empresa X e da Empresa Y está apenas em arquivos de configuração e documentos.

### Três agentes funcionando hoje no mesmo número

```
┌─────────────────────────────────────────────────────────────┐
│                  Um único número WhatsApp                   │
│                                                             │
│   ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│   │    Rafael    │  │     Maya     │  │     Snowden     │  │
│   │ Consultor de │  │  Assistente  │  │  Arquiteto de   │  │
│   │   Software   │  │  de Estudos  │  │    Software     │  │
│   │  (default)   │  │  (Study.io)  │  │   (ArchLab)     │  │
│   └──────────────┘  └──────────────┘  └─────────────────┘  │
│                                                             │
│   O usuário escolhe com quem fala digitando /maya          │
│   ou /snowden. /sair volta para Rafael.                    │
└─────────────────────────────────────────────────────────────┘
```

Cada agente tem:
- Personalidade própria definida em texto
- Base de conhecimento própria (documentos ingeridos via RAG)
- Memória separada por conversa
- Configurações de comportamento (velocidade de digitação, pausa entre mensagens, etc.)
- Proatividade programável (envia mensagens sem que o usuário precise iniciar)

---

## 3. Arquitetura Geral

O sistema é construído sobre **Arquitetura Hexagonal** (também chamada de Ports & Adapters). Isso significa que o núcleo inteligente do agente nunca sabe com qual tecnologia está falando. Ele só conhece interfaces.

```
╔══════════════════════════════════════════════════════════════════╗
║                          CORE (núcleo)                          ║
║                                                                  ║
║   ┌─────────────────┐    ┌──────────────────┐                   ║
║   │   USE CASES     │    │     DOMAIN       │                   ║
║   │                 │    │                  │                   ║
║   │ ProcessMessage  │    │ Message          │                   ║
║   │ BuildContext    │    │ Conversation     │                   ║
║   │ IngestDocuments │    │ Memory           │                   ║
║   └────────┬────────┘    └──────────────────┘                   ║
║            │ usa apenas interfaces (ports)                       ║
║   ┌────────▼────────────────────────────────────────────────┐   ║
║   │                      PORTS                              │   ║
║   │  LLMPort  MemoryPort  GatewayPort  MediaPort  CRMPort   │   ║
║   └────────┬────────────────────────────────────────────────┘   ║
╚════════════╪═════════════════════════════════════════════════════╝
             │ implementado por
╔════════════▼═════════════════════════════════════════════════════╗
║                        ADAPTERS                                  ║
║                                                                  ║
║  Inbound              Outbound                                   ║
║  ────────             ────────────────────────────────────────   ║
║  WAHA Webhook    LLM: Gemini Adapter │ Ollama Adapter            ║
║  (FastAPI)       Mem: Qdrant + Postgres (híbrido)                ║
║                  GW:  WAHA Adapter (envia msgs)                  ║
║                  Med: Gemini Media (áudio, imagem, vídeo)        ║
║                  CRM: Event Adapter │ Null Adapter               ║
╚══════════════════════════════════════════════════════════════════╝
             │
╔════════════▼═════════════════════════════════════════════════════╗
║                     INFRAESTRUTURA                               ║
║                                                                  ║
║   Redis          Qdrant          PostgreSQL      WAHA            ║
║   (debounce,     (memória        (histórico      (gateway        ║
║   rate limit,    semântica,      completo,       WhatsApp,       ║
║   agent mode)    RAG)            auditoria)      media)          ║
╚══════════════════════════════════════════════════════════════════╝
```

### Por que Hexagonal?

**Substituição sem reescrita**: trocar o Qdrant por Pinecone amanhã é implementar um novo adapter. O núcleo não muda uma linha.

**Testabilidade total**: os use cases são testados com mocks das interfaces. Sem banco, sem rede, sem WAHA.

**Reuso real**: `ProcessMessageUseCase` é idêntico para Rafael, Maya e Snowden. Só a configuração muda.

**Venda isolada**: o agente pode ser entregue ao cliente sem CRM, sem banco, em qualquer configuração — basta trocar os adapters.

---

## 4. Como uma Mensagem Vira uma Resposta

Este é o fluxo completo, do WhatsApp do usuário até a resposta chegando de volta.

```
  USUÁRIO                 SISTEMA                          LLM
     │                      │                               │
     │  "oi"                │                               │
     ├─────────────────────►│                               │
     │                      │ push buffer Redis             │
     │                      │ SET debounce:chat TTL=3s      │
     │  "tudo bem?"         │                               │
     ├─────────────────────►│                               │
     │                      │ push buffer Redis             │
     │                      │ RESET debounce:chat TTL=3s    │
     │  "preciso de ajuda"  │                               │
     ├─────────────────────►│                               │
     │                      │ push buffer Redis             │
     │                      │ RESET debounce:chat TTL=3s    │
     │                      │                               │
     │         [3 segundos sem nova mensagem]                │
     │                      │                               │
     │              Redis expira a chave                    │
     │              Worker recebe evento                    │
     │                      │                               │
     │                      │◄── get_and_clear_buffer ──────│
     │                      │    ["oi", "tudo bem?",        │
     │                      │     "preciso de ajuda"]       │
     │                      │                               │
     │              ┌───────▼────────┐                      │
     │              │ BuildContext   │                      │
     │              │                │                      │
     │              │ recentes: 15   │                      │
     │              │ semântico: k=6 │                      │
     │              │ RAG docs: k=4  │                      │
     │              └───────┬────────┘                      │
     │                      │                               │
     │                      ├── stream_response() ─────────►│
     │                      │◄── chunk chunk chunk ─────────│
     │                      │                               │
     │              split_response()                        │
     │              ["Olá!", "Tudo certo.",                 │
     │               "Como posso ajudar?"]                  │
     │                      │                               │
     │  [typing...]         │                               │
     │◄─────────────────────│                               │
     │  "Olá!"              │                               │
     │◄─────────────────────│                               │
     │  [pausa 1.2s]        │                               │
     │  [typing...]         │                               │
     │◄─────────────────────│                               │
     │  "Tudo certo."       │                               │
     │◄─────────────────────│                               │
     │  [pausa 0.9s]        │                               │
     │  [typing...]         │                               │
     │◄─────────────────────│                               │
     │  "Como posso ajudar?"│                               │
     │◄─────────────────────│                               │
     │                      │                               │
```

### O detalhe que muda tudo: o debounce

A chave técnica aqui é o uso de **Redis Keyspace Notifications**. Cada vez que o usuário manda uma mensagem, a chave `debounce:{chat_id}` é recriada com TTL de 3 segundos. Quando ninguém manda nada por 3 segundos, o Redis emite um evento de expiração. Um worker assíncrono escuta esse evento e processa o buffer completo.

Isso não é um `sleep()`. É o Redis gerenciando o timer de forma externa. Com 500 usuários simultâneos, 500 timers são gerenciados pelo Redis sem nenhuma corrotina dormindo na aplicação.

---

## 5. Memória — O que Torna o Agente Inteligente

### O problema do contexto

Um histórico de 200 mensagens tem ~20.000 tokens. Isso é caro, lento, e confunde o modelo (fenômeno chamado de *lost in the middle* — LLMs tendem a ignorar o meio do contexto em janelas grandes).

### A solução: contexto híbrido em 3 camadas

```
  QUERY DO USUÁRIO
  "qual foi aquele prazo que você mencionou semana passada?"
         │
         ▼
  ┌──────────────────────────────────────────────────────┐
  │              CONSTRUÇÃO DO CONTEXTO                  │
  │                                                      │
  │  Camada 1: Mensagens Recentes (sempre incluídas)    │
  │  ┌────────────────────────────────────────────┐     │
  │  │ Última hora de conversa — 15 mensagens     │     │
  │  │ Contexto imediato, cronológico             │     │
  │  └────────────────────────────────────────────┘     │
  │                                                      │
  │  Camada 2: Memória Semântica (Qdrant)               │
  │  ┌────────────────────────────────────────────┐     │
  │  │ Embedding da query → busca por             │     │
  │  │ similaridade em todas as mensagens do      │     │
  │  │ histórico → top 6 mais relevantes          │     │
  │  │ (pode ser de semanas atrás)                │     │
  │  └────────────────────────────────────────────┘     │
  │                                                      │
  │  Camada 3: RAG — Base de Conhecimento              │
  │  ┌────────────────────────────────────────────┐     │
  │  │ Busca nos documentos ingeridos             │     │
  │  │ (manuais, apostilas, scripts, PDFs)        │     │
  │  │ top 4 trechos mais relevantes              │     │
  │  └────────────────────────────────────────────┘     │
  │                                                      │
  │  RESULTADO: ~2.000 tokens de contexto útil          │
  │  vs. ~20.000 tokens do histórico bruto              │
  └──────────────────────────────────────────────────────┘
         │
         ▼
  SYSTEM PROMPT COM PERSONA + GROUNDING + CONTEXTO
         │
         ▼
       LLM
```

### Por que isso importa comercialmente

Um agente sem memória semântica precisa de um histórico enorme para parecer coerente. Histórico enorme = custo alto de tokens + risco de alucinação por contexto poluído. O sistema recupera exatamente o que é relevante, não o que é recente.

---

## 6. Multi-Agente num Único Número

Esta é a característica mais rara. Um único número de WhatsApp pode atender clientes de diferentes perfis com agentes completamente distintos.

```
  NÚMERO ÚNICO: +55 11 9xxxx-xxxx
         │
         ▼
  ┌──────────────────────────────────────────────────────┐
  │               ROTEADOR DE AGENTES                    │
  │                                                      │
  │  1. Redis tem active_agent:{chat_id}?               │
  │     SIM → usa o agente armazenado                   │
  │     NÃO ↓                                           │
  │                                                      │
  │  2. Algum agente tem target_phones com              │
  │     esse número?                                    │
  │     SIM → usa esse agente específico                │
  │     NÃO ↓                                           │
  │                                                      │
  │  3. Catch-all → Rafael (ops_solutions)              │
  └──────────────┬───────────────────────────────────────┘
                 │
        ┌────────┴─────────┐
        │                  │
   /snowden            /maya
        │                  │
        ▼                  ▼
  ┌──────────┐      ┌──────────┐
  │ Snowden  │      │   Maya   │
  │ ArchLab  │      │ Study.io │
  └──────────┘      └──────────┘

  /sair em qualquer agente → volta para Rafael
```

### Isolamento total

Cada agente tem:
- Namespace próprio no Redis (keys: `debounce:{agent_id}:{chat_id}`)
- Coleção separada no Qdrant (`snowden_chats`, `maya_chats`)
- Configurações completamente independentes

É **impossível** vazar contexto entre agentes. Um usuário falando com Snowden nunca contamina a memória de uma conversa com Maya.

---

## 7. Comportamento Humano por Design

### O problema de parecer humano

LLMs geram texto em blocos. Mandar um bloco de 300 palavras numa única mensagem WhatsApp destrói a experiência — parece MUITO robô.

### A solução em camadas

```
  RESPOSTA DO LLM:
  "Entendo a situação. Esse problema que você descreveu é
   clássico em sistemas distribuídos.

   A raiz costuma ser falta de idempotência no produtor de
   eventos. Você já verificou se as mensagens estão sendo
   publicadas mais de uma vez?"

         │
         ▼ split_response()
         │
  ┌──────────────────────────────────────────────────────┐
  │  Parte 1: "Entendo a situação."                      │
  │  Parte 2: "Esse problema que você descreveu é        │
  │            clássico em sistemas distribuídos."       │
  │  Parte 3: "A raiz costuma ser falta de idempotência  │
  │            no produtor de eventos."                  │
  │  Parte 4: "Você já verificou se as mensagens estão   │
  │            sendo publicadas mais de uma vez?"        │
  └──────────────────────────────────────────────────────┘
         │
         ▼ para cada parte:
         │
  [1] verifica se ainda é a tarefa ativa (sem interrupção)
  [2] send_typing(True)
  [3] sleep( len(parte) × 0.025s )   ← simula velocidade de digitação
  [4] send_message(parte)
  [5] sleep( random entre 0.6s e 1.8s ) ← pausa humana

  RESULTADO NO WHATSAPP DO USUÁRIO:
  ┌────────────────────────────────┐
  │ ✎ digitando...                 │
  │ Entendo a situação.            │
  │  [pausa]                       │
  │ ✎ digitando...                 │
  │ Esse problema que você...      │
  │  [pausa]                       │
  │  ...                           │
  └────────────────────────────────┘
```

### Interrupção inteligente

Se o usuário mandar nova mensagem enquanto o agente está respondendo, o sistema detecta e abandona a resposta atual silenciosamente. Cada tarefa tem um `task_id` único armazenado no Redis. Antes de enviar cada parte, o agente verifica se ainda é a tarefa ativa. Se não for, para.

---

## 8. Por que é Impossível Replicar com n8n ou Ferramentas Visuais

O n8n é excelente para automação de workflows lineares — integrar APIs, processar dados, enviar notificações. Mas um agente conversacional em tempo real tem requisitos estruturalmente incompatíveis com ferramentas visuais de workflow.

```
  COMPARAÇÃO DE CAPACIDADES
  ═══════════════════════════════════════════════════════════════

  FUNCIONALIDADE               n8n        ESTE SISTEMA
  ─────────────────────────────────────────────────────────────
  Debounce de mensagens        ✗          ✓ Redis Keyspace
  (burst handling)             Não existe    Notifications

  Memória semântica            ✗          ✓ Qdrant com
  por conversa                 Sem suporte   embeddings por chat

  Contexto híbrido             ✗          ✓ Recente + semântico
  (recente + semântico + RAG)  Impossível    + RAG simultâneos

  Multi-agente num número      ✗          ✓ Roteamento Redis
                               Sem suporte   com fallback

  Streaming de LLM             ✗          ✓ AsyncIterator
  com cancelamento             Bloqueante    com task_id

  Typing indicator dinâmico    ✗          ✓ Proporcional ao
  proporcional ao texto        Sem suporte   tamanho da parte

  Interrupção de geração       ✗          ✓ task_id por chat
  por nova mensagem            Impossível    verificado a cada part

  RAG por agente               ✗          ✓ Coleção Qdrant
  (coleções separadas)         Sem suporte   separada por agent_id

  Proatividade com LLM         ✗          ✓ LLM gera insight
  (insight gerado pelo modelo) Templates     único a cada dia
                               estáticos

  Comportamento injetável      ✗          ✓ YAML + docs
  via documentos               Hardcoded     (PDFs, DOCXs)

  Escalabilidade               ~10/min    100+ simultâneos
  (chats simultâneos)          (limitado     (async nativo,
                               por workflow) pool de conexões)
  ─────────────────────────────────────────────────────────────
```

### O problema fundamental do n8n para este caso

O n8n executa **workflows**: A → B → C → fim. Cada execução é independente e stateless. Um agente conversacional não é um workflow — é um **processo com estado persistente, assíncrono, que reage a eventos externos e gerencia múltiplas conversas em paralelo**.

Para simular o debounce no n8n seria necessário:
1. Workflow A recebe mensagem e grava no banco
2. Workflow B verifica o banco a cada N segundos (polling)
3. Workflow C processa quando o timer passa

Isso cria condições de corrida com múltiplos usuários, polling ineficiente e latência imprevisível. O sistema aqui usa o Redis como componente de tempo — é o próprio banco que notifica quando o timer expira, sem polling.

---

## 9. Comparativo de Mercado

```
  SOLUÇÕES EXISTENTES vs. ESTE FRAMEWORK
  ═══════════════════════════════════════════════════════════════════

  SOLUÇÃO         TIPO              LIMITAÇÕES CRÍTICAS
  ─────────────────────────────────────────────────────────────────
  ManyChat        Visual builder    Sem LLM real. Fluxos rígidos.
                                    Sem memória. Sem RAG.

  Botpress        Visual builder    LLM por fora. Sem debounce.
                                    Sem memória semântica.
                                    Uma empresa por instância.

  Voiceflow       Visual builder    Focado em voz. Sem WhatsApp
                                    nativo. Sem comportamento humano.

  n8n + GPT       Automação +       Stateless. Sem debounce. Sem
                  API call          multi-agente. Sem memória real.

  LangChain +     Framework +       Complexo. Sem debounce nativo.
  WhatsApp        integração        Sem comportamento humano.
                  manual            Sem multi-agente num número.

  Soluções        Enterprise        Fechadas. Custosas. Uma empresa
  enterprise      (Salesforce,      por contrato. Sem reuso.
  (Intercom,      Zendesk AI)       Sem personalidade injetável.
  Salesforce AI)

  ─────────────────────────────────────────────────────────────────

  ESTE FRAMEWORK  Hexagonal +       Multi-agente num número.
                  Redis +           Debounce real. Memória semântica.
                  Qdrant +          RAG por agente. Comportamento
                  FastAPI async     humano. Reusável via YAML.
                                    Open. Deployável em qualquer EC2.

  ─────────────────────────────────────────────────────────────────
```

---

## 10. Modelo de Negócio

A arquitetura foi desenhada para suportar três modelos de receita independentes:

### Modelo 1 — Agente como produto empacotado

```
  FRAMEWORK (código fonte)
         │
         ├── agents/empresa_x/  ← entregue ao cliente X
         │       business.yml       como container Docker
         │       docs/              sem acesso ao código
         │
         ├── agents/empresa_y/  ← entregue ao cliente Y
         │       business.yml       configuração diferente
         │       docs/              mesma base de código
         │
         └── agents/empresa_z/  ...
```

O cliente recebe um container Docker configurado para o negócio dele. Não tem acesso ao código do framework. Troca de provedor LLM, personalidade, base de conhecimento — tudo via arquivos de configuração.

### Modelo 2 — SaaS multi-tenant

Uma instância única do framework atende múltiplos clientes simultaneamente. O isolamento é garantido pela arquitetura (namespaces Redis, coleções Qdrant separadas).

### Modelo 3 — Marketplace de agentes

Agentes especializados (jurídico, médico, financeiro, educacional) construídos uma vez e vendidos como produto. A base de conhecimento (RAG) é o diferencial de cada agente.

---

## 11. Infraestrutura e Escalabilidade

```
  STACK DE PRODUÇÃO (AWS EC2 com GPU)
  ══════════════════════════════════════════════════════════

  ┌─────────────────────────────────────────────────────┐
  │                 EC2 g4dn.xlarge                     │
  │         (4 vCPU, 16GB RAM, T4 GPU 16GB)             │
  │                                                     │
  │  ┌─────────┐  ┌─────────┐  ┌──────────────────┐   │
  │  │  Redis  │  │ Qdrant  │  │   PostgreSQL     │   │
  │  │debounce │  │memória  │  │  histórico       │   │
  │  │rate lim.│  │semântica│  │  completo        │   │
  │  └─────────┘  └─────────┘  └──────────────────┘   │
  │                                                     │
  │  ┌─────────┐  ┌─────────────────────────────────┐  │
  │  │  WAHA   │  │           Ollama                │  │
  │  │WhatsApp │  │  llama3.1:8b  (CPU/GPU)         │  │
  │  │gateway  │  │  nomic-embed-text (embeddings)  │  │
  │  └────┬────┘  └─────────────────────────────────┘  │
  │       │                                             │
  │  ┌────▼────────────────────────────────────────┐   │
  │  │          FastAPI Agent Framework            │   │
  │  │   ops_solutions │ maya │ snowden             │   │
  │  └─────────────────────────────────────────────┘   │
  └─────────────────────────────────────────────────────┘

  Todos os serviços se comunicam via Docker bridge network.
  Nenhuma porta interna exposta ao mundo externo.
  WAHA conecta de dentro para os servidores do WhatsApp (outbound).

  CAPACIDADE ESTIMADA:
  ┌──────────────────────────────────────────────────────┐
  │  Chats simultâneos (sem GPU, Gemini primário): 200+  │
  │  Chats simultâneos (com GPU, Ollama primário):  50+  │
  │  Latência média de resposta (Gemini Flash):    2-4s  │
  │  Latência média de resposta (Ollama 8b GPU):   3-6s  │
  │  Tempo de ingestão de PDF (10 páginas):        ~30s  │
  └──────────────────────────────────────────────────────┘
```

### Decisões de infraestrutura deliberadas

**Por que Redis e não apenas asyncio.sleep()?**
Com 200 usuários simultâneos, 200 corrotinas dormindo ocupam memória e criam condições de corrida em restarts. O Redis gerencia os timers externamente — um restart da aplicação não perde timers em andamento.

**Por que Qdrant e não pgvector?**
Coleções separadas por agente sem configuração extra, filtros nativos por `chat_id`, e performance de busca consistente em alta concorrência. pgvector paga o overhead transacional do PostgreSQL em cada busca semântica.

**Por que YAML e não banco de configuração?**
A configuração do agente é versionável no git, legível por pessoas não técnicas, e pode ser editada sem acesso ao código. Uma pessoa de negócios pode alterar a personalidade do agente sem envolver desenvolvimento.

**Por que arquitetura hexagonal e não monolito simples?**
O agente pode ser vendido sem CRM (troca `CRMEventAdapter` por `NullCRMAdapter`), pode trocar Qdrant por Pinecone (novo adapter), pode usar qualquer LLM (implementa `LLMPort`), pode escutar qualquer canal além do WhatsApp (novo adapter inbound). Nenhuma dessas mudanças toca o núcleo.

---

## Conclusão

O que foi construído não é um chatbot. É uma **infraestrutura para agentes conversacionais** com propriedades que não existem combinadas em nenhuma solução acessível no mercado:

- **Comportamento humano** não como feature, mas como componente de infraestrutura
- **Memória real** com busca semântica, não histórico linear
- **Multi-agente** num único canal com isolamento total
- **Reusabilidade** por design — o código nunca muda, a configuração sim
- **Escalabilidade honesta** — testado para concorrência real, não protótipo de demo

A barreira de entrada é alta. Não por falta de tecnologias disponíveis — todas são open source. Mas porque combinar Redis Keyspace Notifications, embeddings por conversa, contexto híbrido, streaming assíncrono com cancelamento, e simulação de comportamento humano de forma que funcione em produção requer um nível de engenharia que ferramentas visuais não alcançam por design.

---

*Documento gerado internamente — confidencial*
