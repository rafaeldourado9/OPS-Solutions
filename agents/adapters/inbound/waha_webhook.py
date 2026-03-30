"""
WAHAWebhookAdapter — FastAPI router for WAHA webhook events.

Handles WAHA NOWEB engine specifics:
- Messages arrive WITHOUT `type` field (NOWEB omits it)
- Media arrives with ack=2 (delivered to WAHA device) — this IS the real message
- @lid format used for unsaved contacts — we send back to @lid (WhatsApp resolves it)
- Media URL empty without NOWEB store — multiple download strategies used
- Multiple audios/photos in the same debounce window are grouped automatically

Admin RAG commands (for authorized numbers in business.yml → agent.admin_phones):
  /rag            → enter document ingestion flow
  /rag list       → list ingested documents
  /rag clear <X>  → delete document X from RAG
  /rag cancel     → cancel current RAG session
"""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import re
import tempfile
from pathlib import Path
from typing import Any, Optional

import httpx
from fastapi import APIRouter, HTTPException, Request, status

from core.ports.media_port import MediaPort
from infrastructure.rag_session import RagSessionStore
from infrastructure.redis_client import MessageDebouncer

logger = logging.getLogger(__name__)

router = APIRouter()

# ---------------------------------------------------------------------------
# Agent switch commands
# ---------------------------------------------------------------------------

_AGENT_MODE_TTL = 86400 * 30  # 30 days
_RESET_COMMANDS = {"/sair", "/default", "/inicio"}  # reset to default catch-all agent

# ---------------------------------------------------------------------------
# Media type detection (NOWEB doesn't always send `type` field)
# ---------------------------------------------------------------------------

_AUDIO_TYPES = {"ptt", "audio"}
_IMAGE_TYPES = {"image", "sticker"}
_VIDEO_TYPES = {"video"}
_DOCUMENT_TYPES = {"document"}

_LABEL = {
    "ptt":      ("um", "áudio"),
    "audio":    ("um", "áudio"),
    "image":    ("uma", "imagem"),
    "video":    ("um", "vídeo"),
    "document": ("um", "documento"),
    "sticker":  ("um", "sticker"),
}

# MIME type → message type mapping (for when NOWEB omits `type`)
_MIME_TO_TYPE = {
    "audio/ogg": "ptt",
    "audio/mpeg": "audio",
    "audio/mp4": "audio",
    "image/jpeg": "image",
    "image/png": "image",
    "image/webp": "image",
    "video/mp4": "video",
    "application/pdf": "document",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "document",
    "text/plain": "document",
}

# Document and image MIME types that can be ingested for RAG
_INGESTABLE_MIMES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
    "text/plain",
    "text/markdown",
    # Images — described by Gemini and stored as text chunks
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
    "image/gif",
}
_INGESTABLE_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt", ".md", ".jpg", ".jpeg", ".png", ".webp"}


def _detect_media_type(payload: dict) -> str:
    """
    Detect media type from payload, using `type` field first,
    then falling back to MIME type from the `media` object.
    """
    explicit = (payload.get("type") or "").lower()
    if explicit:
        return explicit

    media_obj = payload.get("media") or {}
    # Strip codec params: "audio/ogg; codecs=opus" → "audio/ogg"
    mime = (media_obj.get("mimetype") or "").lower().split(";")[0].strip()
    return _MIME_TO_TYPE.get(mime, "")


def _is_ingestable_document(payload: dict) -> bool:
    """Return True if this media message contains a document or image suitable for RAG ingestion."""
    media_obj = payload.get("media") or {}
    mime = (media_obj.get("mimetype") or "").lower()
    if mime in _INGESTABLE_MIMES:
        return True
    # Also check payload type for images (NOWEB may not include media object)
    msg_type = (payload.get("type") or "").lower()
    if msg_type in ("image", "sticker"):
        return True
    filename = (media_obj.get("filename") or "").lower()
    return any(filename.endswith(ext) for ext in _INGESTABLE_EXTENSIONS)


def _get_document_filename(payload: dict) -> str:
    """Extract filename from payload, falling back to a generic name."""
    media_obj = payload.get("media") or {}
    name = media_obj.get("filename") or ""
    if name:
        return name
    mime = (media_obj.get("mimetype") or "").lower()
    ext_map = {
        "application/pdf": ".pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
        "text/plain": ".txt",
        "image/jpeg": ".jpg",
        "image/jpg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
        "image/gif": ".gif",
    }
    # Fallback: check payload type for images
    msg_type = (payload.get("type") or "").lower()
    if msg_type == "image" and mime not in ext_map:
        return "imagem.jpg"
    return f"documento{ext_map.get(mime, '.bin')}"


# ---------------------------------------------------------------------------
# Admin phone check
# ---------------------------------------------------------------------------


def _normalize_phone(chat_id: str) -> str:
    """Extract digits-only phone number from a WhatsApp JID."""
    # Remove @c.us, @s.whatsapp.net, @lid suffixes
    number = re.sub(r"@.*$", "", chat_id)
    # Keep only digits
    return re.sub(r"\D", "", number)


def _is_admin(chat_id: str, admin_phones: list[str]) -> bool:
    """Return True if the sender is in the admin whitelist."""
    if not admin_phones:
        return False
    normalized = _normalize_phone(chat_id)
    return any(re.sub(r"\D", "", str(p)) == normalized for p in admin_phones)


# ---------------------------------------------------------------------------
# Media download — multiple strategies for NOWEB
# ---------------------------------------------------------------------------


async def _fetch_media_bytes(
    payload: dict[str, Any],
    waha_url: str,
    api_key: str,
    session: str,
    chat_id: str,
) -> Optional[bytes]:
    """
    Try every available strategy to download media bytes from WAHA NOWEB.

    Strategy order:
    1. `mediaUrl` from payload (works when NOWEB store is enabled)
    2. `media.url` inside the `media` object
    3. `media.data` as base64 (WAHA embeds media directly in some cases)
    4. WAHA messages endpoint with downloadMedia=true (fetch by chatId + msgId)
    5. WAHA files endpoint (if stored locally)
    """
    headers = {"X-Api-Key": api_key} if api_key else {}
    msg_id = payload.get("id", "")
    
    # DEBUG: Log entire payload structure
    logger.info("[MEDIA DEBUG] Payload keys: %s", list(payload.keys()))
    logger.info("[MEDIA DEBUG] hasMedia=%s, mediaUrl=%s", payload.get("hasMedia"), payload.get("mediaUrl"))
    media_obj = payload.get("media") or {}
    logger.info("[MEDIA DEBUG] media object keys: %s", list(media_obj.keys()))
    if media_obj:
        logger.info("[MEDIA DEBUG] media.url=%s, media.data exists=%s (len=%d)", 
                    media_obj.get("url"), 
                    bool(media_obj.get("data")),
                    len(media_obj.get("data", "")))

    # 1. mediaUrl from payload
    url1 = payload.get("mediaUrl", "") or ""
    if url1:
        logger.info("[MEDIA DEBUG] Trying strategy 1: mediaUrl=%s", url1)
        data = await _download_url(url1, headers)
        if data:
            return data

    # 2. media.url (rewrite host — payload may contain localhost, invalid inside Docker)
    url2 = media_obj.get("url") or ""
    if url2:
        from urllib.parse import urlparse, urlunparse
        parsed = urlparse(url2)
        waha_parsed = urlparse(waha_url)
        url2_fixed = urlunparse(parsed._replace(
            scheme=waha_parsed.scheme,
            netloc=waha_parsed.netloc,
        ))
        logger.info("[MEDIA DEBUG] Trying strategy 2: media.url=%s", url2_fixed)
        data = await _download_url(url2_fixed, headers)
        if data:
            return data

    # 3. media.data as base64
    b64 = media_obj.get("data") or ""
    if b64:
        logger.info("[MEDIA DEBUG] Strategy 3: Found base64 data, size=%d bytes", len(b64))
        try:
            return base64.b64decode(b64)
        except Exception as e:
            logger.warning("[MEDIA DEBUG] Failed to decode base64: %s", e)
    else:
        logger.warning("[MEDIA DEBUG] Strategy 3: No media.data in payload")

    # 4. WAHA messages endpoint with downloadMedia=true
    if chat_id and msg_id:
        logger.info("[MEDIA DEBUG] Trying strategy 4: WAHA messages API")
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(
                    f"{waha_url}/api/messages",
                    params={
                        "session": session,
                        "chatId": chat_id,
                        "downloadMedia": "true",
                        "limit": 50,
                    },
                    headers=headers,
                )
                if resp.status_code == 200:
                    messages = resp.json()
                    if isinstance(messages, list):
                        for msg in messages:
                            if msg.get("id") == msg_id:
                                # media.data as base64
                                mobj = msg.get("media") or {}
                                b64d = mobj.get("data") or ""
                                if b64d:
                                    try:
                                        return base64.b64decode(b64d)
                                    except Exception:
                                        pass
                                # or mediaUrl
                                murl = msg.get("mediaUrl") or mobj.get("url") or ""
                                if murl:
                                    d = await _download_url(murl, headers)
                                    if d:
                                        return d
        except Exception:
            pass

    # 5. WAHA files endpoint
    # NOWEB stores files using just the short ID (last segment after final underscore)
    # e.g. "false_179203215495244@lid_3A07F2B22590D0134AAA" → "3A07F2B22590D0134AAA"
    if msg_id:
        logger.info("[MEDIA DEBUG] Trying strategy 5: WAHA files API")
        short_id = msg_id.rsplit("_", 1)[-1] if "_" in msg_id else msg_id
        ids_to_try = list(dict.fromkeys([short_id, msg_id]))  # short first, dedup
        for candidate_id in ids_to_try:
            for ext in ["", ".ogg", ".oga", ".jpg", ".jpeg", ".png", ".mp4", ".pdf", ".docx"]:
                url5 = f"{waha_url}/api/files/{session}/{candidate_id}{ext}"
                data = await _download_url(url5, headers)
                if data:
                    return data

    logger.warning("All media download strategies failed for msg_id=%s", msg_id)
    return None


async def _download_url(url: str, headers: dict, timeout: float = 30.0) -> Optional[bytes]:
    """Download raw bytes from a URL, return None on failure."""
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code == 200 and resp.content:
                return resp.content
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# Media processing
# ---------------------------------------------------------------------------


async def _extract_document_text(data: bytes, payload: dict) -> str:
    """
    Extract plain text from a document received as a WhatsApp message.

    Supports PDF, DOCX, and plain text. Uses the same extraction functions
    as the RAG ingestion pipeline so behaviour is consistent.
    """
    import tempfile
    from pathlib import Path as _Path
    from core.use_cases.ingest_documents import (
        _extract_pdf,
        _extract_docx,
        _extract_text,
        _PDF_EXTS,
        _DOCX_EXTS,
        _TEXT_EXTS,
    )

    media_obj = payload.get("media") or {}
    mime = (media_obj.get("mimetype") or "").lower().split(";")[0].strip()
    filename = (media_obj.get("filename") or "").lower()

    # Determine extension from MIME or filename
    ext = ""
    if mime == "application/pdf" or filename.endswith(".pdf"):
        ext = ".pdf"
    elif mime in (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword",
    ) or filename.endswith((".docx", ".doc")):
        ext = ".docx"
    elif mime in ("text/plain", "text/markdown") or filename.endswith((".txt", ".md")):
        ext = ".txt"

    if not ext:
        return ""

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            tmp.write(data)
            tmp_path = _Path(tmp.name)

        if ext in _PDF_EXTS:
            return _extract_pdf(tmp_path)
        elif ext in _DOCX_EXTS:
            return _extract_docx(tmp_path)
        elif ext in _TEXT_EXTS:
            return _extract_text(tmp_path)
    except Exception:
        logger.exception("Failed to extract text from document (ext=%s)", ext)
    finally:
        if tmp_path:
            tmp_path.unlink(missing_ok=True)

    return ""


async def _process_media(
    payload: dict[str, Any],
    media: MediaPort,
    waha_url: str,
    waha_api_key: str,
    session: str,
    chat_id: str,
) -> str:
    """
    Download and process a media message into a text description.

    Detects media type from payload (handling NOWEB's missing `type` field),
    downloads the bytes via multiple strategies, then calls the appropriate
    MediaPort method (transcribe/describe).

    Returns a descriptive string ready for the debounce buffer.
    """
    msg_type = _detect_media_type(payload)
    caption = (payload.get("caption") or "").strip()
    article, label = _LABEL.get(msg_type, ("um", "mídia"))
    caption_note = f' — "{caption}"' if caption else ""
    fallback = f"[Usuário enviou {article} {label}{caption_note}]"

    data = await _fetch_media_bytes(payload, waha_url, waha_api_key, session, chat_id)
    if not data:
        logger.warning("Could not download media (type=%s) — using fallback", msg_type)
        return fallback

    description = ""
    try:
        if msg_type in _AUDIO_TYPES:
            text = await media.transcribe_audio(data)
            if text:
                description = (
                    f"{text}\n"
                    f"[contexto: mensagem de voz{caption_note} — responda ao conteúdo acima como se fosse texto normal]"
                )

        elif msg_type in _IMAGE_TYPES:
            text = await media.describe_image(data)
            if text:
                description = f"[Usuário enviou uma imagem{caption_note}] O que vi: {text}"

        elif msg_type in _VIDEO_TYPES:
            text = await media.describe_video(data)
            if text:
                description = f"[Usuário enviou um vídeo] Descrição: {text}"

        elif msg_type in _DOCUMENT_TYPES:
            text = await _extract_document_text(data, payload)
            if text:
                preview = text[:3000]  # cap to avoid flooding context
                description = (
                    f"[Usuário enviou um documento{caption_note}]\n"
                    f"Conteúdo:\n{preview}"
                    + (" [...]" if len(text) > 3000 else "")
                )
            else:
                description = fallback

        else:
            # Unknown type but has data — try image description
            logger.info("Unknown media type %r — attempting image description", msg_type)
            text = await media.describe_image(data)
            if text:
                description = f"[Usuário enviou uma mídia] O que vi: {text}"

    except Exception:
        logger.exception("Media processing failed for type=%s", msg_type)

    return description if description else fallback


# ---------------------------------------------------------------------------
# Admin RAG command helpers
# ---------------------------------------------------------------------------


async def _send_reply(
    chat_id: str,
    text: str,
    waha_url: str,
    waha_api_key: str,
    session: str,
) -> None:
    """Send an immediate reply directly via WAHA (bypasses debounce/LLM)."""
    headers = {"X-Api-Key": waha_api_key, "Content-Type": "application/json"} if waha_api_key else {"Content-Type": "application/json"}
    payload = {"chatId": chat_id, "text": text, "session": session}
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(f"{waha_url}/api/sendText", json=payload, headers=headers)
            resp.raise_for_status()
    except Exception:
        logger.exception("Failed to send admin reply to chat_id=%s", chat_id)


async def _handle_rag_command(
    chat_id: str,
    text: str,
    rag_store: RagSessionStore,
    instance,  # AgentInstance
    waha_url: str,
    waha_api_key: str,
    session: str,
) -> bool:
    """
    Check if text is an admin /rag command and handle it.

    Returns True if the message was handled as an admin command
    (should NOT be passed to the debounce buffer).
    """
    cmd = text.strip().lower()
    agent_id = instance.agent_id
    qdrant = instance.qdrant

    # /rag — start ingestion flow
    if cmd == "/rag":
        await rag_store.set_state(chat_id, "waiting_doc")
        await _send_reply(
            chat_id,
            "RAG ativado.\n\n"
            "Manda o documento agora (PDF, DOCX, TXT, JPG ou PNG).\n"
            "/rag cancel para cancelar.",
            waha_url, waha_api_key, session,
        )
        return True

    # /rag cancel
    if cmd == "/rag cancel":
        await rag_store.clear(chat_id)
        await _send_reply(chat_id, "Sessão RAG cancelada.", waha_url, waha_api_key, session)
        return True

    # /rag list
    if cmd == "/rag list":
        if qdrant is None:
            await _send_reply(chat_id, "RAG não disponível (sem Qdrant).", waha_url, waha_api_key, session)
            return True
        try:
            sources = await qdrant.list_document_sources(agent_id)
        except Exception:
            logger.exception("Failed to list RAG sources for agent=%s", agent_id)
            await _send_reply(chat_id, "Erro ao listar documentos.", waha_url, waha_api_key, session)
            return True

        if not sources:
            await _send_reply(
                chat_id,
                "Nenhum documento ingerido ainda.\n\nUse /rag para adicionar um.",
                waha_url, waha_api_key, session,
            )
        else:
            lines = ["Documentos no RAG:\n"]
            for i, s in enumerate(sources, 1):
                lines.append(f"{i}. {s['source']} ({s['chunks']} chunks)")
            lines.append("\n/rag clear <nome> para remover um documento.")
            await _send_reply(chat_id, "\n".join(lines), waha_url, waha_api_key, session)
        return True

    # /rag clear <nome>
    if cmd.startswith("/rag clear "):
        source_name = text.strip()[len("/rag clear "):].strip()
        if not source_name:
            await _send_reply(chat_id, "Uso: /rag clear <nome_do_documento>", waha_url, waha_api_key, session)
            return True
        if qdrant is None:
            await _send_reply(chat_id, "RAG não disponível (sem Qdrant).", waha_url, waha_api_key, session)
            return True
        try:
            await qdrant.delete_by_source(agent_id, source_name)
            await _send_reply(chat_id, f"Documento '{source_name}' removido do RAG.", waha_url, waha_api_key, session)
        except Exception:
            logger.exception("Failed to delete RAG source='%s' agent=%s", source_name, agent_id)
            await _send_reply(chat_id, f"Erro ao remover {source_name}.", waha_url, waha_api_key, session)
        return True

    # Unknown /rag subcommand
    if cmd.startswith("/rag"):
        await _send_reply(
            chat_id,
            "Comandos:\n"
            "/rag — iniciar ingestão\n"
            "/rag list — listar documentos\n"
            "/rag clear <nome> — remover documento\n"
            "/rag cancel — cancelar",
            waha_url, waha_api_key, session,
        )
        return True

    return False


async def _handle_rag_state(
    chat_id: str,
    state: str,
    text: str,
    payload: dict,
    has_media: bool,
    rag_store: RagSessionStore,
    instance,  # AgentInstance
    waha_url: str,
    waha_api_key: str,
    session: str,
) -> bool:
    """
    Handle messages when the admin is in the middle of a RAG session
    (waiting_doc or waiting_label state).

    Returns True if the message was handled (should NOT go to debounce buffer).
    """
    agent_id = instance.agent_id

    if state == "waiting_doc":
        # We expect a document here
        if has_media and _is_ingestable_document(payload):
            # Download the file
            data = await _fetch_media_bytes(payload, waha_url, waha_api_key, session, chat_id)
            if data:
                filename = _get_document_filename(payload)
                try:
                    await rag_store.set_pending_doc(chat_id, filename, data)
                    await rag_store.set_state(chat_id, "waiting_label")
                    await _send_reply(
                        chat_id,
                        f"Arquivo '{filename}' recebido.\n\n"
                        "Qual é esse documento?\n"
                        "Exemplo: \"manual\", \"precos\", \"catalogo\"\n\n"
                        "/rag cancel para cancelar.",
                        waha_url, waha_api_key, session,
                    )
                except ValueError as e:
                    await rag_store.clear(chat_id)
                    await _send_reply(chat_id, str(e), waha_url, waha_api_key, session)
            else:
                await _send_reply(
                    chat_id,
                    "⚠️ Não consegui baixar o arquivo. Tente enviar novamente.",
                    waha_url, waha_api_key, session,
                )
            return True

        elif has_media:
            # Not an ingestable type
            await _send_reply(
                chat_id,
                "Tipo de arquivo não suportado para RAG.\n"
                "Formatos aceitos: PDF, DOCX, TXT, MD, JPG, PNG\n\n"
                "Digite /rag cancel para cancelar.",
                waha_url, waha_api_key, session,
            )
            return True

        elif text:
            await _send_reply(
                chat_id,
                "⚠️ Aguardando um documento (PDF/DOCX/TXT).\n"
                "Por favor envie o arquivo, ou digite /rag cancel.",
                waha_url, waha_api_key, session,
            )
            return True

    elif state == "waiting_label":
        if not text:
            await _send_reply(
                chat_id,
                "⚠️ Por favor envie o nome do documento em texto.\n"
                "Exemplo: \"cardápio\", \"preços\"\n\n"
                "Digite /rag cancel para cancelar.",
                waha_url, waha_api_key, session,
            )
            return True

        # Got the label — ingest!
        label = text.strip()
        pending = await rag_store.get_pending_doc(chat_id)
        if pending is None:
            await rag_store.clear(chat_id)
            await _send_reply(
                chat_id,
                "⚠️ Documento não encontrado (sessão expirou?). Use /rag para recomeçar.",
                waha_url, waha_api_key, session,
            )
            return True

        original_filename, data = pending
        # Clear the session state immediately
        await rag_store.clear(chat_id)

        if instance.ingest is None:
            await _send_reply(chat_id, "⚠️ RAG não disponível (sem Qdrant).", waha_url, waha_api_key, session)
            return True

        await _send_reply(
            chat_id,
            f"Ingerindo '{original_filename}' como '{label}'... aguarde.",
            waha_url, waha_api_key, session,
        )

        # Run ingestion in background so webhook can return quickly
        asyncio.create_task(
            _run_ingest(
                data=data,
                filename=original_filename,
                label=label,
                agent_id=agent_id,
                ingest_uc=instance.ingest,
                chat_id=chat_id,
                waha_url=waha_url,
                waha_api_key=waha_api_key,
                session=session,
            )
        )
        return True

    return False


async def _run_ingest(
    data: bytes,
    filename: str,
    label: str,
    agent_id: str,
    ingest_uc,
    chat_id: str,
    waha_url: str,
    waha_api_key: str,
    session: str,
) -> None:
    """Background task: write bytes to temp file and ingest into Qdrant."""
    suffix = Path(filename).suffix or ".bin"
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(data)
            tmp_path = Path(tmp.name)

        # Ingest with the user's label as source name (single call)
        stored = await _ingest_with_label(ingest_uc, tmp_path, agent_id, label)
        tmp_path.unlink(missing_ok=True)

        await _send_reply(
            chat_id,
            f"'{label}' ingerido com sucesso ({stored} chunks). O agente já pode usar esse documento.",
            waha_url, waha_api_key, session,
        )
    except Exception:
        logger.exception("RAG ingest failed for label='%s' agent=%s", label, agent_id)
        await _send_reply(
            chat_id,
            f"Erro ao ingerir '{label}'. Verifique os logs.",
            waha_url, waha_api_key, session,
        )
        try:
            tmp_path.unlink(missing_ok=True)
        except Exception:
            pass


async def _ingest_with_label(ingest_uc, file_path: Path, agent_id: str, label: str) -> int:
    """
    Ingest a file but use `label` as the source name instead of the filename.
    Patches the internal behavior by temporarily renaming the file to the label.
    """
    from uuid import uuid4
    from core.use_cases.ingest_documents import chunk_text, _PDF_EXTS, _DOCX_EXTS, _TEXT_EXTS, _IMAGE_EXTS

    ext = file_path.suffix.lower()

    # Extract text based on extension
    if ext in _PDF_EXTS:
        from core.use_cases.ingest_documents import _extract_pdf
        text = _extract_pdf(file_path)
    elif ext in _DOCX_EXTS:
        from core.use_cases.ingest_documents import _extract_docx
        text = _extract_docx(file_path)
    elif ext in _TEXT_EXTS:
        from core.use_cases.ingest_documents import _extract_text
        text = _extract_text(file_path)
    elif ext in _IMAGE_EXTS:
        from core.use_cases.ingest_documents import _describe_image
        text = await _describe_image(file_path, ingest_uc._config)
    else:
        return 0

    if not text.strip():
        return 0

    chunks = chunk_text(text)
    stored = 0
    for i, chunk in enumerate(chunks):
        point_id = str(uuid4())
        try:
            await ingest_uc._qdrant.upsert_document_chunk(
                point_id=point_id,
                text=chunk,
                agent_id=agent_id,
                source=label,   # use the user's label as source name
                chunk_index=i,
            )
            stored += 1
        except Exception:
            logger.exception("Failed to store chunk %d for label='%s'", i, label)

    return stored


# ---------------------------------------------------------------------------
# Webhook endpoint
# ---------------------------------------------------------------------------


@router.post("/webhook", status_code=status.HTTP_200_OK)
async def waha_webhook(request: Request) -> dict[str, str]:
    """
    Receive WAHA events and route real incoming messages to the debounce buffer.

    NOWEB-aware: handles missing `type` field, @lid contacts, ack=2 messages,
    multiple media items per conversation window.

    Admin commands (/rag ...) are intercepted before the debounce buffer
    for phones listed in business.yml → agent.admin_phones.
    """
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON")

    event_type = body.get("event", "")
    if event_type != "message":
        return {"status": "ignored", "event": event_type}

    payload = body.get("payload", {})

    # Skip our own messages
    if payload.get("fromMe", False):
        return {"status": "ignored", "reason": "fromMe"}

    # --- Detect real incoming messages ---
    # NOWEB: real messages have body text OR media, regardless of `type` or `ack`
    has_media = bool(payload.get("hasMedia"))
    body_text = (payload.get("body") or "").strip()

    if not body_text and not has_media:
        return {"status": "ignored", "reason": "no_content"}

    # Extract chat_id (@lid for unsaved contacts — WAHA handles delivery)
    chat_id = payload.get("chatId") or payload.get("from") or ""
    if not chat_id:
        return {"status": "ignored", "reason": "no_chat_id"}

    logger.info(
        "Message: chat_id=%s hasMedia=%s body=%r",
        chat_id, has_media, body_text[:40],
    )

    # Get app state
    app_state = request.app.state
    waha_api_key: str = getattr(app_state, "waha_api_key", "")
    waha_url: str = getattr(app_state, "waha_url", "http://localhost:3000")
    session_name: str = body.get("session", "default")

    registry = getattr(app_state, "registry", None)

    # --- Agent switch commands (/{agent_id} or /{agent_name}) ---
    cmd = body_text.strip().lower()
    if cmd.startswith("/") and registry is not None:
        from infrastructure.redis_client import get_redis as _get_redis
        _redis = await _get_redis()

        # /agentes — list all available agents
        if cmd == "/agentes":
            lines = ["Agentes disponíveis:"]
            for inst in registry.all_instances():
                lines.append(f"  /{inst.agent_id} — {inst.config.agent.name} ({inst.config.agent.company})")
            lines.append("\n/sair — voltar ao atendimento padrão")
            await _send_reply(chat_id, "\n".join(lines), waha_url, waha_api_key, session_name)
            return {"status": "listed_agents"}

        # /sair /default /inicio — reset to default catch-all
        if cmd in _RESET_COMMANDS:
            await _redis.delete(f"active_agent:{chat_id}")
            default_inst = registry.get_by_session_and_phone(session_name, chat_id)
            name = default_inst.config.agent.name if default_inst else "atendimento padrão"
            await _send_reply(chat_id, f"Ok! Voltando para {name}.", waha_url, waha_api_key, session_name)
            return {"status": "agent_reset"}

        # /{agent_id} or /{agent_name} — switch to that agent
        target_inst = registry.get_by_command(cmd)
        if target_inst is not None:
            await _redis.setex(f"active_agent:{chat_id}", _AGENT_MODE_TTL, target_inst.agent_id)
            await _send_reply(
                chat_id,
                f"Agora você está falando com {target_inst.config.agent.name}. Como posso ajudar?",
                waha_url, waha_api_key, session_name,
            )
            return {"status": "agent_switched", "agent": target_inst.agent_id}

    # Route to correct agent: Redis-stored mode → phone routing → catch-all
    if registry is not None:
        from infrastructure.redis_client import get_redis as _get_redis
        _redis = await _get_redis()
        stored = await _redis.get(f"active_agent:{chat_id}")
        if stored:
            instance = registry.get_by_agent_id(stored)
        if not stored or instance is None:
            # Check session-level active agent set by CRM operator switch
            session_active = await _redis.get(factive_agent_session:{session_name})
            if session_active:
                sid = session_active.decode() if isinstance(session_active, bytes) else session_active
                instance = registry.get_by_agent_id(sid)
        if instance is None:
            instance = registry.get_by_session_and_phone(session_name, chat_id)
        if instance is None:
            logger.warning("No agent for session=%s", session_name)
            return {"status": "ignored", "reason": f"unknown_session:{session_name}"}
        debouncer: MessageDebouncer = instance.debouncer
        agent_id: str = instance.agent_id
        media_port: MediaPort = instance.media
        config = instance.config
    else:
        debouncer = app_state.debouncer
        agent_id = app_state.agent_id
        media_port = app_state.media
        config = app_state.config
        instance = None

    # Rate limit check
    rate_limiter = getattr(app_state, "rate_limiter", None)
    if rate_limiter and not await rate_limiter.is_allowed(chat_id):
        logger.warning("Rate limit exceeded for chat_id=%s", chat_id)
        return {"status": "throttled", "chat_id": chat_id}

    # ---------------------------------------------------------------------------
    # Admin RAG command handling (text messages from authorized phones)
    # ---------------------------------------------------------------------------
    admin_phones = getattr(config.agent, "admin_phones", [])
    is_admin_user = _is_admin(chat_id, admin_phones)

    if is_admin_user and instance is not None:
        from infrastructure.redis_client import get_redis
        redis = await get_redis()
        rag_store = RagSessionStore(redis=redis, agent_id=agent_id)
        rag_state = await rag_store.get_state(chat_id)

        # Check for /rag text commands first
        if body_text and body_text.strip().startswith("/rag"):
            handled = await _handle_rag_command(
                chat_id=chat_id,
                text=body_text,
                rag_store=rag_store,
                instance=instance,
                waha_url=waha_url,
                waha_api_key=waha_api_key,
                session=session_name,
            )
            if handled:
                return {"status": "admin_command", "command": "rag"}
        
        # /gerar_relatorio command
        if body_text and body_text.strip().lower() == "/gerar_relatorio":
            from core.use_cases.generate_report import GenerateReportUseCase
            from adapters.outbound.document.pdf_adapter import PDFDocumentAdapter
            
            template_path = f"agents/{agent_id}/docs/template_requisitos.txt"
            pdf_adapter = PDFDocumentAdapter(template_path)
            
            generate_report = GenerateReportUseCase(
                memory=instance.memory,
                document=pdf_adapter,
                gateway=instance.gateway,
                llm=instance.primary_llm,
                agent_phone=config.agent.admin_phones[0] if config.agent.admin_phones else chat_id,
            )
            
            await _send_reply(
                chat_id,
                "⏳ Gerando relatório... aguarde ~30 segundos",
                waha_url,
                waha_api_key,
                session_name,
            )
            
            asyncio.create_task(
                _generate_report_task(
                    generate_report,
                    chat_id,
                    agent_id,
                    waha_url,
                    waha_api_key,
                    session_name,
                )
            )
            
            return {"status": "generating_report"}

        # Handle ongoing RAG session state (waiting for doc or label)
        if rag_state != "idle":
            handled = await _handle_rag_state(
                chat_id=chat_id,
                state=rag_state,
                text=body_text,
                payload=payload,
                has_media=has_media,
                rag_store=rag_store,
                instance=instance,
                waha_url=waha_url,
                waha_api_key=waha_api_key,
                session=session_name,
            )
            if handled:
                return {"status": "admin_rag_flow", "state": rag_state}

    # ---------------------------------------------------------------------------
    # Normal message handling
    # ---------------------------------------------------------------------------

    push_name: str = (payload.get("pushName") or "").strip()

    # --- Text message ---
    if not has_media:
        await _queue(debouncer, chat_id, body_text, push_name=push_name)
        logger.info("Queued text from chat_id=%s len=%d", chat_id, len(body_text))
        return {"status": "queued", "type": "text"}

    # --- Media message: process async, do NOT block webhook response ---
    asyncio.create_task(
        _handle_media(
            payload=payload,
            chat_id=chat_id,
            debouncer=debouncer,
            media=media_port,
            waha_url=waha_url,
            waha_api_key=waha_api_key,
            session=session_name,
            agent_id=agent_id,
            push_name=push_name,
        )
    )
    logger.info("Scheduled media processing: chat_id=%s", chat_id)
    return {"status": "processing", "type": _detect_media_type(payload) or "media"}


async def _handle_media(
    payload: dict[str, Any],
    chat_id: str,
    debouncer: MessageDebouncer,
    media: MediaPort,
    waha_url: str,
    waha_api_key: str,
    session: str,
    agent_id: str,
    push_name: str = "",
) -> None:
    """Background task: download + process media, push to debounce buffer."""
    try:
        text = await _process_media(
            payload, media, waha_url, waha_api_key, session, chat_id
        )
        await _queue(debouncer, chat_id, text, push_name=push_name)
        logger.info("Media processed and queued: chat_id=%s len=%d", chat_id, len(text))
    except Exception:
        logger.exception("Unhandled error in _handle_media for chat_id=%s", chat_id)


async def _queue(debouncer: MessageDebouncer, chat_id: str, text: str, push_name: str = "") -> None:
    """Serialise and push a message into the debounce buffer."""
    data = json.dumps({"text": text, "chat_id": chat_id, "push_name": push_name})
    await debouncer.push_message(chat_id, data)
