# Diferenciais Competitivos

O que torna este framework diferente de outras soluções de agente WhatsApp existentes.

---

## 1. Zero código para criar um novo agente

A maioria dos frameworks exige que o desenvolvedor escreva código para configurar um novo agente — handlers, prompts no código, integrações hardcoded.

Aqui, um agente novo é criado assim:

```bash
mkdir agents/nova_empresa
cp agents/template/business.yml agents/nova_empresa/
# editar o YAML
```

Zero linha de código. Persona, comportamento, LLM, debounce, RAG, CRM — tudo no YAML. Uma pessoa sem conhecimento de programação consegue configurar um agente completo.

---

## 2. Multi-agente por comando, em um único número

A inovação central do sistema de roteamento: múltiplos agentes diferentes atendem pelo **mesmo número de WhatsApp**.

O usuário escolhe com qual agente quer falar digitando `/nome-do-agente`. A escolha persiste no Redis por 30 dias — sem precisar repetir o comando.

```
/agentes
→ Agentes disponíveis:
  /maya — Maya (Study.io)
  /rafael — Rafael (OPS Solution)
  /sair — voltar ao padrão
```

Adicionar um novo agente ao sistema não exige configuração de roteamento — ele aparece automaticamente no `/agentes` e ganha seu comando `/{id}` e `/{name}`.

---

## 3. Comportamento humano configurável por agente

Cada agente tem sua própria velocidade de "digitação", pausas entre mensagens e debounce.

```yaml
messaging:
  debounce_seconds: 2.5
  typing_delay_per_char: 0.04
  min_pause_between_parts: 1.2
  max_pause_between_parts: 2.8
```

Isso cria ritmos diferentes por agente: a Maya é mais calorosa e pausada; o Rafael é objetivo e rápido. O usuário sente que está falando com pessoas diferentes — não com instâncias do mesmo bot.

---

## 4. CRM invisível para o agente

A maioria das soluções acopla o agente ao CRM — o agente "sabe" que existe um CRM e chama APIs dele diretamente.

Aqui, o agente nunca sabe que existe um CRM. Eventos são publicados passivamente via `CRMPort.push_event()` (fire-and-forget). Se o CRM cair, o agente continua funcionando normalmente — a única consequência é que o evento não foi registrado.

Para vender o agente sem CRM: injetar `NullCRMAdapter`. Zero mudança de código.

---

## 5. Debounce de mensagens via Redis (não sleep)

Agentes WhatsApp simples usam `sleep()` para esperar mensagens rápidas. Com 100 usuários simultâneos, isso cria 100 corrotinas dormindo.

O debounce via Redis Keyspace Notifications é externo ao processo. O Redis gerencia os timers. O Python só acorda quando há trabalho real para fazer.

Benefício adicional: se o serviço reiniciar, os buffers sobrevivem no Redis. Mensagens não são perdidas.

---

## 6. Interrupção de geração por nova mensagem

Se o usuário manda uma nova mensagem enquanto o agente está gerando e enviando a resposta anterior, o envio antigo para imediatamente — sem enviar mensagens stale ou fora de contexto.

O mecanismo é simples e robusto: `task_id` único por ciclo, verificado no Redis antes de cada envio. Sem cancelamento forçado de corrotines, sem locks complexos.

---

## 7. Context window híbrido (recente + semântico + RAG)

Agentes simples enviam as últimas N mensagens ao LLM. Isso desperdiça tokens com contexto irrelevante e perde memórias importantes de conversas antigas.

O context window híbrido combina:
- **Recência**: últimas 15 mensagens (contexto imediato)
- **Semântica**: as 6 mensagens passadas mais similares à query atual (memória de longo prazo)
- **RAG**: os 4 chunks de documentos mais relevantes (fundamentação em regras de negócio)

Custo típico: ~2.000 tokens. Histórico completo custaria 15.000–20.000 tokens por request.

---

## 8. LLM Router com fallback automático

Dois LLMs em hierarquia:
- Queries simples → Ollama local (zero custo, baixa latência)
- Queries complexas → Gemini Pro (maior capacidade)
- Gemini fora do ar → Circuit Breaker → fallback automático para Ollama

O usuário nunca percebe a troca. O desenvolvedor não precisa fazer nada. O circuit breaker fecha automaticamente quando o Gemini volta.

---

## 9. RAG administrável pelo WhatsApp

Admin pode adicionar, listar e remover documentos do RAG diretamente pelo WhatsApp — sem precisar de acesso ao servidor, CLI ou painel.

```
/rag → inicia fluxo de ingestão
→ envia o arquivo (PDF, DOCX, imagem)
→ nomeia o documento
→ documento disponível para o agente imediatamente
```

Telefones autorizados ficam no `business.yml`. Qualquer outro número não vê esses comandos.

---

## 10. Agente proativo (não apenas reativo)

Além de responder mensagens, o agente pode iniciar conversas:

- **Motivação diária**: mensagem no horário configurado (ex: 18h)
- **Alerta de inatividade**: avisa se o usuário sumiu por 2+ dias
- **Lembrete de calendário**: notifica eventos 2 dias antes

Isso é especialmente valioso para agentes de acompanhamento (educação, saúde, coaching) onde o engajamento proativo é parte do serviço.

---

## 11. Fake Gateway para desenvolvimento seguro

Env var `USE_FAKE_GATEWAY=true` ativa um adapter que descarta todas as mensagens com log de warning. Nenhuma mensagem acidental chega ao usuário em ambiente de desenvolvimento.

O código de produção não sabe que o gateway é fake — a interface é idêntica.

---

## 12. Totalmente auditável

Sem caixas pretas. Cada decisão do pipeline é explícita:

- O system prompt é uma string Python visível
- O context window é montado por código próprio, com logs do que foi incluído
- O split de resposta é uma função testada
- O routing de LLM é um `if` com keywords explícitas

Quando o agente se comporta de forma inesperada, é possível inspecionar exatamente o que aconteceu em cada etapa.

---

## Comparativo

| Característica | Framework próprio | LangChain/LlamaIndex | Soluções prontas |
|---|---|---|---|
| Novo agente sem código | Sim | Não | Depende |
| Multi-agente, 1 número | Sim (por comando) | Não nativo | Não |
| CRM desacoplado | Sim (invisível) | Não | Não |
| Debounce de mensagens | Redis externo | Não | Às vezes |
| Interrupção de geração | Sim (task_id) | Não | Não |
| RAG admin pelo WhatsApp | Sim | Não | Não |
| Agente proativo | Sim | Não | Raramente |
| Auditabilidade total | Sim | Parcial (caixa preta) | Não |
| Comportamento humano config. | Sim (por agente) | Não | Não |
| Fallback LLM automático | Sim (circuit breaker) | Parcial | Não |
