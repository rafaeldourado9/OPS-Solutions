"""
tool_loop — Executa LLM com tool calling em loop até resposta final.

O loop funciona assim:
  1. Detecta se a query precisa de dados atuais → força search_web
  2. Chama LLM com as tools disponíveis
  3. Se o LLM retornar tool_call → executa a tool → adiciona resultado às msgs → repete
  4. Se o LLM retornar texto → retorna como resposta final
  5. Após max_iterations → força resposta final sem tools

Compatível com Ollama (llama3.1, qwen2.5) e Gemini.
"""

from __future__ import annotations

import logging
import re
from typing import Callable, Awaitable

logger = logging.getLogger(__name__)

# Keywords that signal the query needs live/current data from the web
_NEEDS_SEARCH_PATTERNS = [
    r"cota[çc][aã]o", r"pre[çc]o\s+(atual|hoje|agora)",
    r"d[oó]lar\s*(hoje|atual|agora)?", r"euro\s*(hoje|atual|agora)?",
    r"bitcoin|btc|cripto|ethereum|eth",
    r"not[ií]cia", r"acontec(eu|endo)",
    r"tempo\s*(hoje|agora|atual)", r"previs[aã]o",
    r"quem\s+(criou|inventou|fez|desenvolveu|fundou|é o criador)",
    r"(quando|onde)\s+(foi|será|acontec)",
    r"(resultado|placar|score)\s+(do|da|de)",
    r"(estreou|lan[çc]ou|saiu|lançamento)",
    r"(atual|hoje|agora|neste momento|recente)",
    r"(quanto\s+(custa|vale|está|tá))",
    r"(qual|quais)\s+.*(maior|menor|melhor|pior|mais)\s+.*(mundo|brasil|2024|2025|2026)",
]
_NEEDS_SEARCH_RE = re.compile("|".join(_NEEDS_SEARCH_PATTERNS), re.IGNORECASE)


async def run_tool_loop(
    llm,
    messages: list[dict],
    system: str,
    tools: list[dict],
    tool_executor: Callable[[str, dict], Awaitable[str]],
    max_iterations: int = 6,
) -> str:
    """
    Run the LLM with tool calling until it produces a final text response.

    Args:
        llm:            LLM adapter with call_with_tools() method.
        messages:       Initial message list.
        system:         System prompt.
        tools:          Tool definitions (OpenAI function calling format).
        tool_executor:  Async callable(name, args) → result string.
        max_iterations: Max tool call rounds before forcing final response.

    Returns:
        Final text response from the LLM.
    """
    if not hasattr(llm, "call_with_tools"):
        # LLM doesn't support tool calling — generate normally
        chunks: list[str] = []
        async for chunk in llm.stream_response(messages, system=system):
            chunks.append(chunk)
        return "".join(chunks)

    conversation = list(messages)

    # --- Pre-search: if the user query clearly needs current data, force
    # a search_web call BEFORE the LLM decides, so it has fresh context.
    has_search_tool = any(
        t.get("function", {}).get("name") == "search_web" for t in tools
    )
    last_user_msg = ""
    for m in reversed(messages):
        if m.get("role") == "user":
            last_user_msg = m.get("content", "")
            break

    if has_search_tool and _NEEDS_SEARCH_RE.search(last_user_msg):
        logger.info("tool_loop: query needs current data — forcing search_web")
        pre_result = await tool_executor("search_web", {"query": last_user_msg})
        logger.info("tool_loop: pre-search returned %d chars", len(pre_result))

        # Inject the search result as context so the LLM can use it
        conversation.append({
            "role": "assistant",
            "content": "",
            "tool_calls": [{
                "id": "call_presearch",
                "type": "function",
                "function": {"name": "search_web", "arguments": {"query": last_user_msg}},
            }],
        })
        conversation.append({
            "role": "tool",
            "tool_call_id": "call_presearch",
            "content": pre_result,
        })

    for iteration in range(max_iterations):
        result = await llm.call_with_tools(conversation, system, tools)

        if result["type"] == "text":
            return result["content"]

        # Tool call
        call_id: str = result.get("id", f"call_{iteration}")
        name: str = result["name"]
        args: dict = result.get("args", {})

        logger.info(
            "tool_loop[iter=%d]: calling %s(%s)", iteration + 1, name, args
        )

        tool_result = await tool_executor(name, args)

        logger.info(
            "tool_loop[iter=%d]: %s returned %d chars",
            iteration + 1, name, len(str(tool_result)),
        )

        # Append assistant tool call + tool result to conversation
        # Uses OpenAI/Ollama format — GeminiAdapter converts on its side
        conversation.append({
            "role": "assistant",
            "content": "",
            "tool_calls": [{
                "id": call_id,
                "type": "function",
                "function": {"name": name, "arguments": args},
            }],
        })
        conversation.append({
            "role": "tool",
            "tool_call_id": call_id,
            "content": str(tool_result),
        })

    # Max iterations reached — get final response without tools.
    # Clean the conversation: collapse tool_call/tool messages into a
    # plain assistant+user pair so the LLM never sees (or echoes) the
    # raw function-call syntax like "[Chamando ferramenta: ...]".
    logger.warning("tool_loop: max_iterations=%d reached — forcing final response", max_iterations)

    clean_msgs: list[dict] = []
    tool_summary_parts: list[str] = []

    for msg in conversation:
        role = msg.get("role", "")
        if role == "assistant" and msg.get("tool_calls"):
            # Collect tool call names for summary, skip the raw message
            for tc in msg["tool_calls"]:
                fn = tc.get("function", {})
                tool_summary_parts.append(f"Dados sobre {fn.get('name', 'consulta')}:")
            continue
        if role == "tool":
            # Attach abbreviated result to summary
            content = str(msg.get("content", ""))[:500]
            tool_summary_parts.append(content)
            continue
        clean_msgs.append(msg)

    # Inject a single user-like summary of what tools returned
    if tool_summary_parts:
        clean_msgs.append({
            "role": "user",
            "content": "\n".join(tool_summary_parts),
        })

    chunks = []
    async for chunk in llm.stream_response(clean_msgs, system=system):
        chunks.append(chunk)
    response = "".join(chunks)

    # Safety net: strip any leaked tool-call markers
    import re
    response = re.sub(r"\[Chamando ferramenta:.*?\]", "", response)
    response = re.sub(r"\[Resultado da ferramenta\]:?.*?(?=\n|$)", "", response)
    return response.strip()
