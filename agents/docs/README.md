# WhatsApp Agent Framework — Documentação

> Documentação técnica completa do framework. Leia em ordem se estiver chegando agora no projeto.

---

## Índice

| Documento | O que você vai encontrar |
|---|---|
| [architecture.md](./architecture.md) | Arquitetura hexagonal, camadas, portas e adapters |
| [system-design.md](./system-design.md) | Infraestrutura, fluxo de dados, decisões de stack |
| [agent-routing.md](./agent-routing.md) | Sistema de roteamento multi-agente por comando |
| [technical-decisions.md](./technical-decisions.md) | Trade-offs e decisões técnicas justificadas |
| [differentials.md](./differentials.md) | Diferenciais competitivos do framework |
| [manual-configuracao-business-yml.md](./manual-configuracao-business-yml.md) | Como configurar um agente via YAML |
| [manual-rag.md](./manual-rag.md) | Como usar o sistema de RAG |

---

## O que é este projeto

Um **framework de agentes WhatsApp reutilizável** onde toda a identidade, comportamento e regras de negócio de um agente vivem em arquivos de configuração — não em código.

A mesma base de código serve uma clínica médica, uma consultoria de TI e uma assistente de estudos pessoal. A diferença entre eles é apenas um arquivo `business.yml` e uma pasta de documentos.

## Princípios que guiaram todas as decisões

1. **O core nunca sabe o que está fora dele.** Nenhum import de Redis, Qdrant ou Gemini no `core/`.
2. **Configuração, não código.** Novo agente = nova pasta + YAML. Zero linha de código.
3. **Comportamento humano injetável.** Velocidade de digitação, pausas e debounce são configuráveis por agente.
4. **CRM invisível.** O agente não sabe que existe um CRM. Eventos são publicados de forma passiva.
5. **Degradação graciosa.** Gemini caiu? Ollama assume. Qdrant lento? Resposta sem contexto semântico.
