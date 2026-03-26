# Manual de Configuração — business.yml

O `business.yml` é o único arquivo que você precisa editar para criar ou personalizar um agente. Nenhuma linha de código é alterada — toda a identidade, comportamento e infraestrutura do agente vêm deste arquivo.

Ele fica em `agents/<nome-do-agente>/business.yml`.

---

## Estrutura geral

```
agents/
  ops_solutions/
    business.yml      ← este arquivo
    docs/             ← documentos para o RAG
```

---

## Seção `agent` — Identidade do agente

```yaml
agent:
  name: "Rafael"
  company: "OPS Solution"
  language: "pt-BR"
  admin_phones: ["5511947880561"]
  persona: |
    ...
```

### `name`
Nome do agente. Aparece no log e é usado na persona para o LLM saber como se identificar.

```yaml
name: "Sofia"
```

Não precisa ser o nome exibido no WhatsApp (isso é configurado direto no WAHA). É o nome interno que o LLM usa para se referir a si mesmo na persona.

---

### `company`
Nome da empresa que o agente representa. Usado no log e pode ser referenciado na persona.

```yaml
company: "Empresa X Ltda"
```

---

### `language`
Código de idioma BCP 47. Define em qual língua o agente deve responder por padrão.

```yaml
language: "pt-BR"   # Português brasileiro (padrão)
language: "en-US"   # Inglês americano
language: "es-AR"   # Espanhol argentino
```

O sistema injeta uma instrução no system prompt: `Idioma: pt-BR.` — reforço extra para o LLM não mudar de idioma.

---

### `admin_phones`
Lista de números de telefone com permissão para usar comandos administrativos no WhatsApp (como `/rag`).

```yaml
admin_phones: ["5511947880561", "5521999999999"]
```

**Formato obrigatório:** somente dígitos, com código do país e DDD, sem espaços, parênteses ou hífens.

```
55          → código do Brasil
11          → DDD de São Paulo
947880561   → número (9 dígitos para celular)
```

Se a lista estiver vazia (`[]`), ninguém pode usar comandos admin. O agente ainda funciona normalmente para conversas.

---

### `persona`
O coração do agente. É o system prompt que define quem o agente é, como fala, o que sabe e como se comporta.

```yaml
persona: |
  Você é Sofia, atendente da Loja X.
  ...
```

O `|` do YAML preserva quebras de linha, então você pode escrever em blocos com quantas linhas quiser.

**O que colocar na persona:**

**1. Identidade**
```
Você é [Nome], [cargo] da [empresa].
```

**2. Expertise** — O que o agente sabe responder com autoridade.
```
EXPERTISE: vendas de eletrônicos, garantia, troca e suporte pós-venda.
```

**3. Estilo de escrita** — Como o agente se comunica no WhatsApp. Este bloco é crítico para parecer humano.
```
COMO VOCÊ ESCREVE NO WHATSAPP:
- SEJA BREVE: 1-2 frases por mensagem
- Quebre em várias mensagens pequenas
- NUNCA usa emojis
- NUNCA usa listas ou markdown
- Faça UMA pergunta por vez
```

**4. Resposta a mídias** — Como processar áudios, imagens e vídeos recebidos.
```
RESPONDENDO A MÍDIAS:
Quando receber [contexto: mensagem de voz], interprete a transcrição e responda ao conteúdo. Não mencione que foi um áudio.
```

**5. Triggers automáticos** — Frases exatas que o sistema detecta para acionar funções.

Para geração de relatório PDF:
```
GERAÇÃO DE RELATÓRIO:
Quando o levantamento estiver completo, diga EXATAMENTE:
"Vou gerar o relatório agora"
```

Para geração de imagem:
```
GERAÇÃO DE IMAGENS:
Quando pedirem uma imagem, responda APENAS com:
GERAR_IMAGEM: [descrição em inglês]
```

**6. Exemplos de conversa** — Demonstrações de como o agente deve responder. Quanto mais exemplos reais, melhor o comportamento.
```
EXEMPLOS:
Cliente: "preciso de ajuda"
Sofia: "Claro! Com o quê posso te ajudar?"
```

**Dica:** A persona é injetada diretamente no system prompt do LLM. Escreva como se estivesse dando instruções diretas ao modelo — sem floreios, direto ao ponto.

---

## Seção `llm` — Modelo de linguagem

```yaml
llm:
  provider: "gemini"
  model: "gemini-2.5-flash-preview-05-20"
  fallback_provider: "ollama"
  fallback_model: "llama3.1:8b"
  temperature: 0.7
  max_tokens: 500
```

### `provider`
Qual provedor de LLM usar como principal.

```yaml
provider: "gemini"    # Google Gemini (recomendado, requer GEMINI_API_KEY)
provider: "ollama"    # Modelos locais via Ollama (sem custo de API)
```

### `model`
Nome do modelo dentro do provedor escolhido.

```yaml
# Para Gemini:
model: "gemini-2.5-flash-preview-05-20"      # Rápido, barato, bom para chat
model: "gemini-1.5-pro"        # Mais inteligente, mais caro, contexto longo

# Para Ollama:
model: "llama3.1:8b"           # Leve, roda em GPU modesta
model: "llama3.1:70b"          # Muito capaz, exige GPU potente
model: "mistral:7b"            # Boa alternativa ao llama
```

### `fallback_provider` e `fallback_model`
LLM de reserva para consultas simples. O sistema detecta automaticamente se a pergunta é simples (sem palavras-chave complexas, menos de 20 palavras) e usa o fallback em vez do primário — economizando tokens e acelerando a resposta.

```yaml
fallback_provider: "ollama"
fallback_model: "llama3.1:8b"
```

Para desabilitar o fallback (usar sempre o provedor primário):
```yaml
fallback_provider: ""
fallback_model: ""
```

### `temperature`
Controla a criatividade/aleatoriedade das respostas.

```yaml
temperature: 0.3   # Conservador — mais determinístico, menos alucinação (atendimento formal)
temperature: 0.7   # Equilibrado — natural sem perder coerência (recomendado para chat)
temperature: 1.0   # Criativo — mais variação, risco maior de inventar informações
```

**Regra prática:** Quanto mais o agente precisa seguir um script ou responder com dados precisos, menor a temperatura. Para conversas abertas e naturais, valores entre 0.6 e 0.8 funcionam bem.

### `max_tokens`
Limite máximo de tokens (palavras/pedaços de palavras) que o LLM pode gerar em uma única resposta.

```yaml
max_tokens: 300    # Forçar respostas muito curtas
max_tokens: 500    # Padrão para chat de WhatsApp
max_tokens: 1000   # Para respostas técnicas longas
```

Lembre que o agente divide a resposta em várias mensagens WhatsApp — mesmo 500 tokens viram 5-8 mensagens curtas separadas, que parecem naturais.

---

## Seção `messaging` — Comportamento de envio

```yaml
messaging:
  debounce_seconds: 3.0
  max_message_chars: 150
  typing_delay_per_char: 0.025
  min_pause_between_parts: 0.8
  max_pause_between_parts: 2.0
```

### `debounce_seconds`
Tempo (em segundos) que o agente espera após a **última** mensagem do usuário antes de começar a processar.

```yaml
debounce_seconds: 2.5   # Mais rápido, ideal para respostas objetivas
debounce_seconds: 3.0   # Padrão — dá tempo do usuário terminar o raciocínio
debounce_seconds: 5.0   # Mais paciente, para usuários que enviam áudios longos
```

**Como funciona:** O usuário envia "oi", "tudo bem?", "preciso de ajuda" em 2 segundos. Com `debounce_seconds: 3.0`, o agente espera 3 segundos após o "preciso de ajuda" e responde **uma única vez** consolidando tudo. Sem isso, responderia 3 vezes separadas.

### `max_message_chars`
Tamanho máximo de cada mensagem enviada no WhatsApp (em caracteres).

```yaml
max_message_chars: 120   # Mensagens muito curtas, estilo SMS
max_message_chars: 150   # Padrão WhatsApp — soa natural
max_message_chars: 300   # Permite explicações um pouco mais longas
```

Respostas maiores são automaticamente cortadas em várias mensagens menores no limite de uma frase.

### `typing_delay_per_char`
Segundos de delay de "digitação" por caractere antes de enviar cada mensagem.

```yaml
typing_delay_per_char: 0.02   # Digitador rápido
typing_delay_per_char: 0.04   # Digitador médio (padrão original)
typing_delay_per_char: 0.025  # Equilibrado — parece humano sem demorar demais
```

Uma mensagem de 100 caracteres com `0.025` = 2.5 segundos de "digitando..." antes de aparecer.

### `min_pause_between_parts` e `max_pause_between_parts`
Intervalo aleatório (em segundos) entre o envio de cada parte da resposta.

```yaml
min_pause_between_parts: 0.8    # Pausa mínima entre mensagens
max_pause_between_parts: 2.0    # Pausa máxima
```

O sistema sorteia um valor entre min e max para cada pausa, criando variação natural. Com 3 mensagens, as pausas podem ser 1.2s, 0.9s, 1.7s — como uma pessoa real digitando.

---

## Seção `memory` — Memória e contexto

```yaml
memory:
  qdrant_collection: "ops_solutions_chats"
  qdrant_rag_collection: "ops_solutions_rules"
  semantic_k: 8
  max_recent_messages: 30
  embedding_model: "nomic-embed-text"
```

### `qdrant_collection`
Nome da coleção no Qdrant onde ficam guardadas as memórias de conversas (embeddings das mensagens).

```yaml
qdrant_collection: "ops_solutions_chats"
```

**Regra:** Use um nome único por agente. Se dois agentes usarem o mesmo nome, eles compartilham memória — o que provavelmente é um erro.

Convenção recomendada: `{nome_empresa}_chats`

### `qdrant_rag_collection`
Nome da coleção onde ficam os documentos ingeridos via RAG (manuais, scripts, catálogos, etc.).

```yaml
qdrant_rag_collection: "ops_solutions_rules"
```

Esta é a coleção que o comando `/rag` popula quando você envia documentos. O agente busca aqui quando precisa responder perguntas sobre a empresa.

Convenção recomendada: `{nome_empresa}_rules`

### `semantic_k`
Quantas memórias de conversas passadas buscar por similaridade semântica a cada resposta.

```yaml
semantic_k: 4    # Menos contexto, mais rápido
semantic_k: 8    # Padrão — bom equilíbrio
semantic_k: 12   # Mais contexto histórico, ligeiramente mais lento
```

Por exemplo: o usuário pergunta sobre "preço do produto X". Com `semantic_k: 8`, o sistema busca as 8 mensagens mais parecidas com esse tema no histórico do chat — mesmo que tenham sido trocadas dias atrás.

### `max_recent_messages`
Quantas mensagens recentes são sempre incluídas no contexto (independente de similaridade).

```yaml
max_recent_messages: 15   # Contexto curto, bom para conversas rápidas
max_recent_messages: 30   # Padrão — cobre uma conversa longa
max_recent_messages: 50   # Memória longa, gasta mais tokens
```

Essas são as N mensagens mais recentes da conversa atual, sempre presentes. É a "memória de curto prazo" do agente.

### `embedding_model`
Modelo Ollama usado para transformar textos em vetores numéricos (para busca semântica).

```yaml
embedding_model: "nomic-embed-text"   # Recomendado — leve, rápido e preciso
```

Não mude isso a menos que saiba o que está fazendo. Trocar o modelo de embedding torna inválida toda a memória já armazenada (os vetores ficam incompatíveis).

---

## Seção `anti_hallucination` — Controle de alucinação

```yaml
anti_hallucination:
  rag_mandatory: false
  unknown_answer: "Não tenho essa informação disponível."
  grounding_enabled: true
```

### `rag_mandatory`
Se `true`, o agente **se recusa a responder** qualquer pergunta que não tenha contexto relevante nos documentos do RAG.

```yaml
rag_mandatory: true    # Agente só responde com base em documentos — ideal para atendimento formal
rag_mandatory: false   # Agente pode responder livremente mesmo sem documentos — bom para consultoria
```

**Quando usar `true`:** Atendimento de e-commerce, suporte técnico, qualquer cenário onde o agente não pode inventar informações.

**Quando usar `false`:** Agentes de consultoria, coaching, ou onde o conhecimento geral do LLM é desejado.

### `unknown_answer`
Mensagem padrão enviada quando `rag_mandatory: true` e nenhum documento relevante foi encontrado.

```yaml
unknown_answer: "Não tenho essa informação disponível. Posso verificar com a equipe técnica."
```

Personalize conforme o tom da empresa. Seja honesto mas não robotizado.

### `grounding_enabled`
Se `true`, injeta os documentos RAG encontrados diretamente no system prompt antes da resposta.

```yaml
grounding_enabled: true    # Sempre ativo — o LLM vê os documentos como contexto explícito
grounding_enabled: false   # O LLM responde apenas com seu treinamento
```

Mantenha `true` na maioria dos casos. Isso é o que faz o agente "ler" os documentos antes de responder.

---

## Seção `media` — Processamento de mídia

```yaml
media:
  audio_model: "gemini-2.5-flash-preview-05-20"
  image_model: "gemini-2.5-flash-preview-05-20"
  video_model: "gemini-2.5-flash-preview-05-20"
  video_frame_interval: 5
```

### `audio_model`
Modelo Gemini usado para transcrever áudios (PTT/voz).

```yaml
audio_model: "gemini-2.5-flash-preview-05-20"   # Rápido e preciso para PT-BR
audio_model: "gemini-1.5-pro"     # Mais preciso para sotaques difíceis
```

O agente recebe o áudio, transcreve com este modelo e processa a transcrição como texto normal.

### `image_model`
Modelo Gemini usado para descrever imagens recebidas no chat e para gerar imagens quando solicitado.

```yaml
image_model: "gemini-2.5-flash-preview-05-20"   # Boa visão, rápido
image_model: "gemini-1.5-pro"     # Mais detalhado para imagens complexas
```

### `video_model`
Modelo Gemini usado para entender vídeos recebidos no chat.

```yaml
video_model: "gemini-2.5-flash-preview-05-20"   # Suporta vídeos até ~1h
video_model: "gemini-1.5-pro"     # Melhor para vídeos técnicos longos
```

### `video_frame_interval`
*Parâmetro legado — não tem efeito com Gemini (que analisa o vídeo inteiro).*

Mantido para compatibilidade com versões que usavam extração de frames via ffmpeg+LLaVA.

---

## Seção `crm` — Integração com CRM externo

```yaml
crm:
  enabled: false
  events_webhook: "${CRM_WEBHOOK_URL}"
  push_events:
    - new_contact
    - message_received
    - agent_response_sent
    - conversation_closed
```

### `enabled`
Liga ou desliga a integração com CRM.

```yaml
enabled: false   # Sem CRM — o agente funciona normalmente mas não notifica ninguém
enabled: true    # Ativo — eventos são enviados ao webhook configurado
```

### `events_webhook`
URL para onde os eventos são enviados via HTTP POST.

```yaml
events_webhook: "${CRM_WEBHOOK_URL}"   # Lê da variável de ambiente CRM_WEBHOOK_URL
events_webhook: "https://meucrm.com/webhook/whatsapp"   # URL direta (não recomendado em produção)
```

O formato `${VARIAVEL}` lê automaticamente da variável de ambiente correspondente — nunca coloque URLs ou credenciais diretamente no arquivo YAML se ele for versionado no git.

### `push_events`
Quais eventos disparar para o CRM.

```yaml
push_events:
  - new_contact          # Primeira mensagem de um número novo
  - message_received     # Toda mensagem recebida do usuário
  - agent_response_sent  # Toda resposta enviada pelo agente
  - conversation_closed  # Quando a conversa é encerrada
```

Remova eventos que você não precisa para reduzir volume de requisições.

---

## Referência rápida — Valores recomendados por tipo de agente

### Atendimento de e-commerce / suporte
```yaml
llm:
  temperature: 0.3
  max_tokens: 300
messaging:
  max_message_chars: 150
  debounce_seconds: 2.5
anti_hallucination:
  rag_mandatory: true
```

### Consultoria / agente especialista
```yaml
llm:
  temperature: 0.7
  max_tokens: 500
messaging:
  max_message_chars: 150
  debounce_seconds: 3.0
anti_hallucination:
  rag_mandatory: false
```

### Vendas / SDR
```yaml
llm:
  temperature: 0.6
  max_tokens: 400
messaging:
  max_message_chars: 120
  debounce_seconds: 3.0
anti_hallucination:
  rag_mandatory: true
```

---

## Variáveis de ambiente referenciadas

O `business.yml` pode referenciar variáveis de ambiente com a sintaxe `${NOME}`. Coloque-as no arquivo `.env` na raiz do projeto:

```bash
# .env
GEMINI_API_KEY=AIza...
WAHA_URL=http://localhost:3000
WAHA_API_KEY=sua-chave
REDIS_URL=redis://localhost:6379/0
QDRANT_URL=http://localhost:6333
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/whatsapp_agent
OLLAMA_URL=http://localhost:11434
CRM_WEBHOOK_URL=https://seu-crm.com/webhook/whatsapp
AGENT_ID=ops_solutions
```
