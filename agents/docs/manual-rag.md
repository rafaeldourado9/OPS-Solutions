# Manual de Uso — RAG (Retrieval Augmented Generation)

O RAG é o sistema que permite ao agente responder perguntas com base em documentos da empresa. Em vez de depender só do conhecimento geral do LLM, o agente consulta manuais, catálogos, scripts e procedimentos que você adicionou.

---

## O que é o RAG neste sistema

Quando o usuário faz uma pergunta, o sistema:

1. Transforma a pergunta em um vetor numérico (embedding)
2. Busca os trechos de documentos mais parecidos com aquela pergunta no Qdrant
3. Injeta esses trechos no system prompt antes do LLM responder
4. O LLM responde baseado no que encontrou nos documentos

O agente nunca "memoriza" os documentos — ele busca sob demanda, a cada mensagem relevante.

---

## Tipos de documento suportados

| Formato | Como é processado |
|---------|------------------|
| PDF | Extrai texto página a página |
| DOCX / DOC | Extrai parágrafos |
| TXT / MD | Lê diretamente |
| JPG / PNG / WEBP | Gemini descreve a imagem em texto |

---

## Como adicionar documentos via WhatsApp

Esta é a forma mais prática. Funciona diretamente no chat do WhatsApp, sem precisar de acesso ao servidor.

**Pré-requisito:** Seu número precisa estar na lista `admin_phones` do `business.yml`.

### Passo a passo

**1. Ativar o modo RAG**

No chat do WhatsApp com o agente, envie:
```
/rag
```

O sistema responde:
```
RAG ativado.

Manda o documento agora (PDF, DOCX, TXT, JPG ou PNG).
/rag cancel para cancelar.
```

**2. Enviar o documento**

Envie o arquivo como anexo no WhatsApp. Formatos aceitos:
- PDF
- DOCX (Word)
- TXT
- JPG ou PNG (imagens com texto, tabelas de preço, cardápios fotografados, etc.)

O sistema baixa o arquivo e responde:
```
Arquivo 'catalogo.pdf' recebido.

Qual é esse documento?
Exemplo: "manual", "precos", "catalogo"

/rag cancel para cancelar.
```

**3. Dar um nome ao documento**

Envie um nome curto e descritivo para o documento:
```
catalogo de produtos 2024
```

O sistema processa e responde:
```
'catalogo de produtos 2024' ingerido com sucesso (47 chunks). O agente já pode usar esse documento.
```

Pronto. O agente já usa esse conteúdo nas respostas.

---

## Como adicionar documentos via linha de comando

Para ingerir um diretório inteiro de uma vez (útil na configuração inicial de um novo agente):

```bash
python scripts/ingest.py --agent ops_solutions
```

Isso processa todos os arquivos dentro de `agents/ops_solutions/docs/` e os adiciona ao RAG.

Para ingerir um arquivo específico:
```bash
python scripts/ingest.py --agent ops_solutions --file agents/ops_solutions/docs/manual.pdf
```

---

## Comandos /rag disponíveis no WhatsApp

Todos os comandos abaixo só funcionam para números na lista `admin_phones`.

### `/rag`
Inicia o fluxo de ingestão de documento.

```
/rag
```

### `/rag list`
Lista todos os documentos já ingeridos com o número de chunks de cada um.

```
/rag list
```

Resposta exemplo:
```
Documentos no RAG:

1. catalogo de produtos 2024 (47 chunks)
2. manual de instalacao (23 chunks)
3. tabela de precos (8 chunks)

/rag clear <nome> para remover um documento.
```

### `/rag clear <nome>`
Remove um documento do RAG pelo nome exato que você deu na hora da ingestão.

```
/rag clear tabela de precos
```

Resposta:
```
Documento 'tabela de precos' removido do RAG.
```

### `/rag cancel`
Cancela uma sessão RAG que está em andamento (se você ativou `/rag` mas não quer mais ingerir nada).

```
/rag cancel
```

---

## Como o agente usa os documentos

Depois de ingerir, o agente busca automaticamente os trechos relevantes a cada mensagem. Você não precisa fazer nada — isso acontece nos bastidores.

**Exemplo:**

Você ingeriu um PDF com a tabela de preços. Quando o usuário pergunta:
```
Quanto custa o plano premium?
```

O sistema:
1. Busca "plano premium preço" na coleção de documentos
2. Encontra o trecho relevante: "Plano Premium: R$ 199,00/mês"
3. Injeta no prompt: `=== DOCUMENTOS DA EMPRESA === ... Plano Premium: R$ 199,00/mês ...`
4. O LLM responde baseado nisso

---

## Comportamento com `rag_mandatory`

### `rag_mandatory: false` (padrão para consultoria)
O agente responde mesmo sem encontrar documentos relevantes — usa o conhecimento geral do LLM. Bom para agentes de consultoria onde o conhecimento técnico do modelo já é suficiente.

### `rag_mandatory: true` (recomendado para atendimento)
Se nenhum documento relevante for encontrado, o agente responde com a mensagem configurada em `unknown_answer` em vez de inventar uma resposta.

```yaml
anti_hallucination:
  rag_mandatory: true
  unknown_answer: "Não tenho essa informação disponível. Posso verificar com nossa equipe!"
```

---

## Como ingerir imagens com texto

Fotos de cardápios, tabelas manuscritas, capturas de tela, etiquetas de produto — tudo funciona.

**Via WhatsApp:**
1. `/rag`
2. Envie a foto
3. Dê o nome: `cardapio semana`

O Gemini descreve a imagem em texto detalhado antes de gerar os embeddings. Se a foto tiver texto legível (placa de preços, lista de produtos), ele extrai o conteúdo automaticamente.

**Qualidade da imagem:**
- Boa iluminação e foco melhoram muito a extração
- Texto impresso é mais preciso que manuscrito
- Imagens de resolução muito baixa podem perder detalhes

---

## Estrutura interna dos chunks

Cada documento é dividido em pedaços de aproximadamente 500 caracteres com 60 caracteres de sobreposição entre eles. Isso garante que frases que ficam na "fronteira" entre dois chunks apareçam nos dois, sem perda de contexto.

```
Documento original (1.200 caracteres)
│
├── Chunk 1: caracteres 0-499
├── Chunk 2: caracteres 440-939    ← sobreposição de 60 chars
└── Chunk 3: caracteres 880-1.199
```

Para cada busca, o sistema retorna os K chunks mais relevantes (configurável em `semantic_k` no `business.yml`).

---

## Boas práticas para documentos

**Organize por tema:** Em vez de um PDF gigante com tudo, crie arquivos separados por categoria (preços, procedimentos, FAQ, etc.). Isso melhora a precisão da busca.

**Use linguagem clara:** Documentos com jargão muito técnico sem explicação podem confundir a busca semântica.

**Nomes descritivos:** O nome que você dá no momento da ingestão aparece no `/rag list` e nos logs. Use nomes como `precos_outubro_2024` em vez de `doc1`.

**Atualize quando mudar:** Se os preços mudaram, use `/rag clear precos_antigos` e ingira o novo arquivo. O RAG não atualiza automaticamente.

**Imagens complementam texto:** Se você tem um catálogo em PDF mas as fotos dos produtos trazem informações (número de série, modelo, cor), ingira as fotos separadamente além do PDF.

---

## Verificar se o RAG está funcionando

Para testar se um documento foi ingerido corretamente, faça uma pergunta ao agente sobre um conteúdo específico que está naquele documento. Se ele responder corretamente sem inventar, o RAG está funcionando.

Para depuração mais detalhada, verifique os logs do servidor:
```bash
docker compose logs -f agent
```

Procure por linhas como:
```
Context built for chat_id=...: recent=15 semantic=8 rules=4
```

O número em `rules=4` indica quantos chunks de documentos foram encontrados para aquela consulta. Se estiver sempre em `rules=0`, os documentos não foram ingeridos corretamente ou a pergunta não tem semelhança com nenhum chunk.
