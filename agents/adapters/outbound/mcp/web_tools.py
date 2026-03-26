"""
WebToolsAdapter — Ferramentas web para agentes habilitados.

Ferramentas disponíveis:
  search_web(query)                  → DuckDuckGo, retorna links reais
  fetch_page(url)                    → Baixa e extrai texto de uma página
  browser_open(url)                  → Abre URL no Playwright (headless)
  browser_get_content()              → Texto visível da página atual
  browser_click(selector)            → Clica em elemento (CSS ou texto)
  browser_type(selector, text)       → Digita em campo de entrada
  browser_find_elements(query)       → Localiza elementos na página
  browser_screenshot()               → Screenshot descrito por Gemini/texto

Estado do browser é mantido por chat_id — cada conversa tem sua própria
sessão de navegador, isolada das demais.
"""

from __future__ import annotations

import logging
from html.parser import HTMLParser
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Tool definitions — OpenAI/Ollama function calling format
# ---------------------------------------------------------------------------

WEB_TOOL_DEFINITIONS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": (
                "Busca na internet informações atualizadas, notícias, documentação técnica, "
                "preços, CVEs, repositórios, ou qualquer coisa que precise de dados frescos. "
                "Retorna links reais com resumos. Sempre use esta ferramenta quando precisar "
                "de informações que podem ter mudado após o seu treinamento."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "A busca a realizar. Seja específico para melhores resultados.",
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_page",
            "description": (
                "Baixa e lê o conteúdo textual completo de uma URL. "
                "Use para ler documentação, artigos, páginas de repositórios, etc."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL completa para acessar."}
                },
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "browser_open",
            "description": (
                "Abre uma URL num navegador automatizado (Playwright). "
                "Use para tarefas de automação: login, formulários, navegação em apps web. "
                "O estado do browser persiste entre chamadas na mesma conversa."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL para abrir no browser."}
                },
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "browser_get_content",
            "description": "Retorna o texto visível da página atual no browser.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "browser_click",
            "description": (
                "Clica em um elemento na página atual. "
                "Aceita seletor CSS (ex: 'button#login', 'input[type=submit]') "
                "ou texto visível (ex: 'Entrar', 'Sign In')."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "selector": {
                        "type": "string",
                        "description": "Seletor CSS ou texto do botão/link para clicar.",
                    }
                },
                "required": ["selector"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "browser_type",
            "description": "Digita texto em um campo de entrada na página atual.",
            "parameters": {
                "type": "object",
                "properties": {
                    "selector": {
                        "type": "string",
                        "description": "Seletor CSS do campo (ex: '#username', 'input[name=email]').",
                    },
                    "text": {
                        "type": "string",
                        "description": "Texto a digitar no campo.",
                    },
                },
                "required": ["selector", "text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "browser_find_elements",
            "description": "Localiza e lista elementos na página atual por texto ou seletor CSS.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Texto visível ou seletor CSS para buscar.",
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "browser_screenshot",
            "description": (
                "Tira um screenshot da página atual e descreve o que está visível. "
                "Útil para entender o estado de uma página ou confirmar uma ação."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
]


# ---------------------------------------------------------------------------
# HTML text extractor
# ---------------------------------------------------------------------------


class _TextExtractor(HTMLParser):
    """Minimal HTML → plain text, skipping scripts/styles/nav."""

    _SKIP_TAGS = {"script", "style", "head", "nav", "footer", "aside", "noscript"}

    def __init__(self) -> None:
        super().__init__()
        self._texts: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list) -> None:
        if tag in self._SKIP_TAGS:
            self._skip_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in self._SKIP_TAGS and self._skip_depth > 0:
            self._skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._skip_depth == 0:
            text = data.strip()
            if text:
                self._texts.append(text)

    def get_text(self) -> str:
        return " ".join(self._texts)


# ---------------------------------------------------------------------------
# WebToolsAdapter
# ---------------------------------------------------------------------------


class WebToolsAdapter:
    """
    Executes web tools (search, fetch, browser automation) for an agent.

    One instance per agent. Browser sessions are keyed by chat_id so each
    conversation has its own isolated browser context.

    Args:
        media_adapter: Optional MediaPort for screenshot description via vision model.
    """

    def __init__(self, media_adapter: Optional[Any] = None) -> None:
        self._media = media_adapter
        self._playwright: Optional[Any] = None
        self._browser: Optional[Any] = None
        self._pages: dict[str, Any] = {}   # chat_id → playwright Page

    @property
    def definitions(self) -> list[dict]:
        return WEB_TOOL_DEFINITIONS

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def start(self) -> None:
        """Start Playwright and launch headless browser."""
        try:
            from playwright.async_api import async_playwright
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-dev-shm-usage"],
            )
            logger.info("WebToolsAdapter: Playwright browser started")
        except Exception:
            logger.exception("WebToolsAdapter: failed to start Playwright")

    async def stop(self) -> None:
        """Close all browser sessions and stop Playwright."""
        for page in list(self._pages.values()):
            try:
                await page.context.close()
            except Exception:
                pass
        self._pages.clear()
        if self._browser:
            try:
                await self._browser.close()
            except Exception:
                pass
        if self._playwright:
            try:
                await self._playwright.stop()
            except Exception:
                pass
        logger.info("WebToolsAdapter: Playwright stopped")

    # ------------------------------------------------------------------
    # Dispatcher
    # ------------------------------------------------------------------

    async def execute(self, name: str, args: dict, chat_id: str = "") -> str:
        """Execute a named tool and return the result as string."""
        try:
            if name == "search_web":
                return await self._search_web(args.get("query", ""))
            if name == "fetch_page":
                return await self._fetch_page(args.get("url", ""))
            if name == "browser_open":
                return await self._browser_open(args.get("url", ""), chat_id)
            if name == "browser_get_content":
                return await self._browser_get_content(chat_id)
            if name == "browser_click":
                return await self._browser_click(args.get("selector", ""), chat_id)
            if name == "browser_type":
                return await self._browser_type(
                    args.get("selector", ""), args.get("text", ""), chat_id
                )
            if name == "browser_find_elements":
                return await self._browser_find_elements(args.get("query", ""), chat_id)
            if name == "browser_screenshot":
                return await self._browser_screenshot(chat_id)
            return f"Ferramenta desconhecida: {name}"
        except Exception:
            logger.exception("Tool execution failed: %s(%s)", name, args)
            return f"Erro ao executar {name}: verifique os parâmetros."

    # ------------------------------------------------------------------
    # Tool implementations
    # ------------------------------------------------------------------

    async def _search_web(self, query: str) -> str:
        if not query:
            return "Query vazia."

        # Try DDGS API first, then fall back to browser-based search
        result = await self._search_ddgs(query)
        if result is not None:
            return result

        logger.info("DDGS failed, falling back to browser-based search")
        return await self._search_via_browser(query)

    async def _search_ddgs(self, query: str) -> Optional[str]:
        """Try DuckDuckGo API search. Returns None if all attempts fail."""
        import asyncio

        def _sync_search() -> list:
            from duckduckgo_search import DDGS
            with DDGS() as ddgs:
                return list(ddgs.text(query, max_results=6))

        for attempt in range(2):
            if attempt > 0:
                await asyncio.sleep(2.0)
            try:
                results = await asyncio.to_thread(_sync_search)
                if not results:
                    return None
                return self._format_search_results(query, results)
            except ImportError:
                return "Erro: pacote duckduckgo-search não instalado."
            except Exception as e:
                logger.warning("DDGS attempt %d failed: %s", attempt + 1, e)
        return None

    # Patterns that indicate a CAPTCHA / bot-detection page — NEVER send to LLM
    _CAPTCHA_MARKERS = [
        "detectaram tráfego incomum",
        "unusual traffic",
        "are not a robot",
        "não é um robô",
        "captcha",
        "verify you are human",
        "verificar que você é humano",
        "blocked",
    ]

    def _is_captcha(self, text: str) -> bool:
        lower = text.lower()
        return any(m in lower for m in self._CAPTCHA_MARKERS)

    async def _search_via_browser(self, query: str) -> str:
        """Fallback: use Playwright to search Bing (less aggressive bot detection)."""
        if not self._browser:
            return await self._search_via_httpx(query)
        try:
            import urllib.parse
            context = await self._browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent=(
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
                ),
                locale="pt-BR",
            )
            page = await context.new_page()
            try:
                encoded = urllib.parse.quote_plus(query)
                url = f"https://www.bing.com/search?q={encoded}&setlang=pt-BR"
                await page.goto(url, wait_until="domcontentloaded", timeout=15000)

                # Extract structured results from Bing
                results = await page.evaluate("""() => {
                    const out = [];
                    const items = document.querySelectorAll('li.b_algo');
                    for (let i = 0; i < Math.min(items.length, 6); i++) {
                        const el = items[i];
                        const linkEl = el.querySelector('h2 a');
                        const snippetEl = el.querySelector('.b_caption p, .b_lineclamp2');
                        if (linkEl) {
                            out.push({
                                title: linkEl.textContent.trim(),
                                href: linkEl.href || '',
                                body: snippetEl ? snippetEl.textContent.trim() : ''
                            });
                        }
                    }
                    return out;
                }""")

                logger.info("Browser Bing search got %d results", len(results))
                if results:
                    return self._format_search_results(query, results)

                # Fallback: grab visible text, but filter CAPTCHA
                body_text = await page.inner_text("body")
                if body_text and len(body_text) > 100:
                    if self._is_captcha(body_text):
                        logger.warning("Browser search returned CAPTCHA page — skipping")
                        return await self._search_via_httpx(query)
                    text = body_text[:3000]
                    logger.info("Browser search: using raw page text (%d chars)", len(text))
                    return f"Resultados de busca para: {query}\n\n{text}"

                return await self._search_via_httpx(query)
            finally:
                await context.close()
        except Exception as e:
            logger.warning("Browser search failed: %s", e)
            return await self._search_via_httpx(query)

    async def _search_via_httpx(self, query: str) -> str:
        """Last resort: Bing search via httpx (no JS needed)."""
        import urllib.parse
        encoded = urllib.parse.quote_plus(query)
        try:
            async with httpx.AsyncClient(
                timeout=15.0,
                follow_redirects=True,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
                    ),
                    "Accept-Language": "pt-BR,pt;q=0.9",
                },
            ) as client:
                resp = await client.get(
                    f"https://www.bing.com/search?q={encoded}&setlang=pt-BR",
                )
                resp.raise_for_status()
                parser = _TextExtractor()
                parser.feed(resp.text)
                text = parser.get_text()

                if self._is_captcha(text):
                    logger.warning("httpx search returned CAPTCHA — giving up")
                    return f"Não consegui buscar informações sobre: {query}. Tente novamente em alguns minutos."

                if text and len(text) > 50:
                    if len(text) > 3000:
                        text = text[:3000]
                    return f"Resultados de busca para: {query}\n\n{text}"
                return f"Nenhum resultado encontrado para: {query}"
        except Exception as e:
            logger.warning("httpx search fallback failed: %s", e)
            return f"Não consegui buscar informações sobre: {query}. Tente novamente em alguns minutos."

    @staticmethod
    def _format_search_results(query: str, results: list) -> str:
        """Format a list of search result dicts into readable text."""
        lines = [f"Resultados de busca para: {query}\n"]
        for i, r in enumerate(results, 1):
            lines.append(f"{i}. {r.get('title', '')}")
            href = r.get('href', '')
            if href:
                lines.append(f"   URL: {href}")
            body = r.get("body", "")[:250]
            if body:
                lines.append(f"   {body}")
            lines.append("")
        return "\n".join(lines)

    async def _fetch_page(self, url: str) -> str:
        if not url:
            return "URL vazia."
        try:
            async with httpx.AsyncClient(
                timeout=15.0,
                follow_redirects=True,
                headers={"User-Agent": "Mozilla/5.0 (compatible; Snowden/1.0)"},
            ) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                parser = _TextExtractor()
                parser.feed(resp.text)
                text = parser.get_text()
                if len(text) > 6000:
                    text = text[:6000] + "\n[...conteúdo truncado...]"
                return f"Conteúdo de {url}:\n\n{text}" if text else f"Página {url} não contém texto legível."
        except Exception as e:
            return f"Erro ao acessar {url}: {e}"

    async def _get_or_create_page(self, chat_id: str):
        """Return existing page for chat_id or create a new one."""
        if not self._browser:
            raise RuntimeError("Browser não inicializado — chame start() antes.")
        page = self._pages.get(chat_id)
        if page is None:
            context = await self._browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
            )
            page = await context.new_page()
            self._pages[chat_id] = page
        return page

    async def _browser_open(self, url: str, chat_id: str) -> str:
        if not url:
            return "URL vazia."
        try:
            page = await self._get_or_create_page(chat_id)
            await page.goto(url, wait_until="domcontentloaded", timeout=20000)
            title = await page.title()
            return f"Página aberta: {title}\nURL atual: {page.url}"
        except Exception as e:
            return f"Erro ao abrir {url}: {e}"

    async def _browser_get_content(self, chat_id: str) -> str:
        page = self._pages.get(chat_id)
        if page is None:
            return "Nenhuma página aberta. Use browser_open primeiro."
        try:
            text = await page.inner_text("body")
            if len(text) > 5000:
                text = text[:5000] + "\n[...truncado...]"
            return text or "Página sem conteúdo textual visível."
        except Exception as e:
            return f"Erro ao ler conteúdo: {e}"

    async def _browser_click(self, selector: str, chat_id: str) -> str:
        page = self._pages.get(chat_id)
        if page is None:
            return "Nenhuma página aberta. Use browser_open primeiro."
        try:
            # Try CSS selector first, then visible text
            try:
                await page.click(selector, timeout=5000)
            except Exception:
                await page.get_by_text(selector).first.click(timeout=5000)
            try:
                await page.wait_for_load_state("domcontentloaded", timeout=5000)
            except Exception:
                pass
            return f"Clicado em '{selector}'. URL atual: {page.url}"
        except Exception as e:
            return f"Não encontrei '{selector}' para clicar: {e}"

    async def _browser_type(self, selector: str, text: str, chat_id: str) -> str:
        page = self._pages.get(chat_id)
        if page is None:
            return "Nenhuma página aberta. Use browser_open primeiro."
        try:
            await page.fill(selector, text, timeout=5000)
            return f"Digitado em '{selector}'."
        except Exception as e:
            return f"Não consegui digitar em '{selector}': {e}"

    async def _browser_find_elements(self, query: str, chat_id: str) -> str:
        page = self._pages.get(chat_id)
        if page is None:
            return "Nenhuma página aberta. Use browser_open primeiro."
        try:
            # Try CSS selector
            elements = await page.query_selector_all(query)
            if not elements:
                # Try text search
                elements = await page.query_selector_all(f"text={query}")
            if not elements:
                return f"Nenhum elemento encontrado para: {query}"
            results = []
            for el in elements[:8]:
                tag = await el.evaluate("el => el.tagName.toLowerCase()")
                try:
                    text = (await el.inner_text()).strip()[:100]
                except Exception:
                    text = ""
                results.append(f"<{tag}> {text}")
            return "Elementos encontrados:\n" + "\n".join(results)
        except Exception as e:
            return f"Erro ao buscar elementos: {e}"

    async def _browser_screenshot(self, chat_id: str) -> str:
        page = self._pages.get(chat_id)
        if page is None:
            return "Nenhuma página aberta. Use browser_open primeiro."
        try:
            screenshot_bytes = await page.screenshot(type="jpeg", quality=70)
            # Describe with vision model if available
            if self._media and hasattr(self._media, "describe_image"):
                description = await self._media.describe_image(screenshot_bytes)
                return f"Screenshot da página ({page.url}):\n{description}"
            # Fallback: return page text
            text = await page.inner_text("body")
            return f"Página atual ({page.url}):\n{text[:2000]}"
        except Exception as e:
            return f"Erro ao tirar screenshot: {e}"
