# ---------------------------------------------------------------------------
# WhatsApp Agent — Production Dockerfile
# ---------------------------------------------------------------------------
# Multi-stage build: dependencies layer cached separately from app code.
# Runs as non-root user. Includes ffmpeg for video frame extraction.
# ---------------------------------------------------------------------------

FROM python:3.11-slim AS base

# System packages: ffmpeg (video frames) + git (pip from GitHub) + curl + Playwright deps
# pkg-config + libavdevice-dev: required to build PyAV (dep of faster-whisper/OpenVoice)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       ffmpeg curl git \
       pkg-config libavdevice-dev \
       libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 \
       libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 \
       libgbm1 libasound2 libpango-1.0-0 libpangocairo-1.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ---------------------------------------------------------------------------
# Dependency layer (cached unless requirements.txt changes)
# ---------------------------------------------------------------------------
FROM base AS deps

COPY requirements.txt .

# Playwright browsers go to a shared path accessible by any user
ENV PLAYWRIGHT_BROWSERS_PATH=/opt/playwright-browsers

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir --no-deps \
       "git+https://github.com/myshell-ai/OpenVoice.git" \
       "git+https://github.com/myshell-ai/MeloTTS.git" \
    && playwright install chromium \
    && chmod -R o+rx /opt/playwright-browsers

# ---------------------------------------------------------------------------
# Application layer
# ---------------------------------------------------------------------------
FROM deps AS app

# Copy only source code (no tests, no docs, no .git)
COPY core/       core/
COPY adapters/   adapters/
COPY api/        api/
COPY infrastructure/ infrastructure/
COPY scripts/    scripts/
COPY agents/     agents/

# Pre-download OpenVoice v2 checkpoints (~200MB, cached in Docker layer)
RUN python -c "\
try:\n\
    from huggingface_hub import snapshot_download\n\
    snapshot_download('myshell-ai/OpenVoice', local_dir='/app/checkpoints_v2')\n\
    print('OpenVoice v2 checkpoints downloaded.')\n\
except Exception as e:\n\
    print(f'OpenVoice checkpoints download skipped: {e}')\n\
" || true

# Create non-root user with writable cache dirs for numba/torch/huggingface
RUN addgroup --system appgroup \
    && adduser --system --ingroup appgroup --no-create-home appuser \
    && mkdir -p /home/appuser/.cache /home/appuser/.local /home/appuser/.numba \
    && chown -R appuser:appgroup /app /home/appuser

USER appuser

ENV NUMBA_CACHE_DIR=/home/appuser/.numba \
    HF_HOME=/home/appuser/.cache/huggingface \
    MPLCONFIGDIR=/home/appuser/.cache/matplotlib

# ---------------------------------------------------------------------------
# Runtime configuration
# ---------------------------------------------------------------------------
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PLAYWRIGHT_BROWSERS_PATH=/opt/playwright-browsers \
    LOG_LEVEL=INFO \
    LOG_JSON=true \
    AGENT_ID=empresa_x \
    PORT=8000

EXPOSE 8000

# Healthcheck: hits /health every 30s, 3 retries before marking unhealthy
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port ${PORT} --workers 1 --loop asyncio"]
