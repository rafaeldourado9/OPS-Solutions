"""
GeminiAnalyzerAdapter — LLMAnalyzerPort implementation using Gemini REST API.

Uses httpx (already in requirements) to call the Gemini generateContent endpoint.
No additional SDK dependency needed.
"""

from __future__ import annotations

import json
import re

import httpx
import structlog

from core.ports.outbound.llm_analyzer_port import FieldSuggestion, LLMAnalyzerPort
from infrastructure.config import settings

logger = structlog.get_logger()

_GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "{model}:generateContent?key={key}"
)

_SYSTEM_PROMPT = """\
You are an expert at analyzing ANY type of business proposal document to identify \
variable fields that should be replaced with dynamic data in a template system.

This works for ANY business niche: solar energy, construction, IT services, insurance, \
law firms, healthcare, accounting, real estate, events, logistics, etc.

Your task: Given document text, identify ALL text patterns that appear to be \
placeholder/variable values — things that will differ for each client or quote.

Universal patterns to detect (niche-independent):
- Zero/empty monetary values: "R$ 0,00", "0.00", "0,00", "R$0", "000.000,00"
- Generic client names: "Nome do cliente", "NOME DO CLIENTE", "Cliente", "CLIENTE"
- Generic company names: "EMPRESA CLIENTE", "Razão Social", "CONTRATANTE"
- Generic dates: any specific date like "20/02/2026", "01/01/2025", "DD/MM/AAAA"
- Validity periods: "7 dias", "30 dias", "XX dias"
- Generic quantities: "000", "00", standalone "0" after a quantity label
- Measurement placeholders: "00 m²", "000 kW", "0.0 kWp", "000W", "0,00 kg"
- Generic product/service names: "PRODUTO X", "Serviço Y", "MODELO 000"
- Generic addresses/locations: "Rua X", "Cidade, Estado", blank address fields
- Generic percentages used as estimates: "0%", "00%"
- Generic phone/email: "(00) 00000-0000", "email@email.com"
- Document numbers: "0000/2025", "Nº 000"
- Signature/name placeholders at the end: all-caps names like "NOME DO CLIENTE", \
  "NOME DO VENDEDOR", "REPRESENTANTE"

Niche-specific examples (but detect equivalents in any niche):
- Solar: "000 kWp", "000 kW/mês", "MÓDULO X 000W", "INVERSOR Y 0000W"
- Construction: "000 m²", "000 m³", "Obra em [local]"
- IT: "Plano X", "000 usuários", "000 GB"
- Legal: "Contratante: NOME", "Valor dos honorários: R$ 0,00"

For each detected variable field, return a JSON object with:
- "original_text": the EXACT text as it appears (must match character-for-character)
- "placeholder_key": descriptive snake_case Portuguese key (e.g. "nome_cliente", "valor_total")
- "crm_field": best matching key from the CRM fields list, or "__manual__" if none fit
- "description": short Portuguese description of what this field represents
- "confidence": 0.0–1.0

CRM fields available:
{crm_fields}

Rules:
- Include ALL genuinely variable values — err on the side of MORE suggestions
- Do NOT include static labels, company boilerplate, legal text, or fixed terms
- Each "original_text" must exist verbatim in the document
- Return ONLY a valid JSON array, no markdown, no explanation
- If no variable fields found, return []
"""


class GeminiAnalyzerAdapter(LLMAnalyzerPort):

    def __init__(
        self,
        model: str | None = None,
        api_key: str | None = None,
    ) -> None:
        self._model = model or settings.gemini_analyzer_model
        self._api_key = api_key or settings.gemini_api_key

    async def analyze_document_fields(
        self,
        document_text: str,
        known_crm_fields: dict[str, str],
    ) -> list[FieldSuggestion]:
        if not self._api_key:
            logger.warning("gemini_analyzer.no_api_key")
            return []

        crm_fields_str = "\n".join(
            f'  "{k}": "{v}"' for k, v in known_crm_fields.items()
        )

        system = _SYSTEM_PROMPT.format(crm_fields=crm_fields_str)
        user_content = f"Document text:\n\n{document_text[:8000]}"

        payload = {
            "system_instruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": user_content}]}],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 2048,
                "responseMimeType": "application/json",
            },
        }

        url = _GEMINI_URL.format(model=self._model, key=self._api_key)

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()

            data = resp.json()
            raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
            return self._parse_suggestions(raw_text)

        except Exception as exc:
            logger.error("gemini_analyzer.error", error=str(exc))
            return []

    @staticmethod
    def _parse_suggestions(raw: str) -> list[FieldSuggestion]:
        # Strip markdown fences if present
        clean = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip())
        try:
            items = json.loads(clean)
        except json.JSONDecodeError:
            return []

        result: list[FieldSuggestion] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            original = item.get("original_text", "").strip()
            key = item.get("placeholder_key", "").strip()
            if not original or not key:
                continue
            result.append(
                FieldSuggestion(
                    original_text=original,
                    placeholder_key=key,
                    crm_field=item.get("crm_field", "__manual__"),
                    description=item.get("description", ""),
                    confidence=float(item.get("confidence", 1.0)),
                )
            )

        result.sort(key=lambda s: s.confidence, reverse=True)
        return result
