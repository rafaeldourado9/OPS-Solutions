#!/usr/bin/env bash
# Builda e sobe toda a stack OPS Solutions na ordem certa.
# Uso (a partir de qualquer diretório):
#   bash D:/CRM/infra/build.sh [--no-cache]

set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
NO_CACHE=${1:-}

echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║          OPS Solutions — build sequencial            ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

# ── 0. Garante que a rede compartilhada existe ────────────────────────────────
echo "▶ [0/3] Garantindo rede Docker 'agents_default'..."
docker network create agents_default 2>/dev/null && echo "  → rede criada" \
  || echo "  → rede já existe, ok"
echo ""

# ── 1. Agents ─────────────────────────────────────────────────────────────────
echo "▶ [1/3] Subindo agents..."
cd "$ROOT/agents"
docker compose up -d
echo "✔ agents ok"
echo ""

# ── 2. CRM (sequencial para evitar OOM) ──────────────────────────────────────
echo "▶ [2/3] Buildando CRM..."
cd "$ROOT/crm"

echo "  → pull de imagens base (postgres, rabbit, minio)..."
docker compose pull crm-postgres rabbitmq minio 2>/dev/null || true
docker compose up -d crm-postgres rabbitmq minio

echo "  → aguardando postgres healthy..."
until docker compose exec crm-postgres pg_isready -U postgres -q 2>/dev/null; do
  sleep 2
done

echo "  → buildando crm-api (LibreOffice incluído — aguarde)..."
docker compose build $NO_CACHE crm-api
docker compose up -d crm-api

echo "  → buildando crm-frontend..."
docker compose build $NO_CACHE crm-frontend
docker compose up -d crm-frontend

echo "✔ CRM ok"
echo ""

# ── 3. Nginx reverse proxy ────────────────────────────────────────────────────
echo "▶ [3/3] Subindo nginx reverse proxy na porta 80..."
cd "$ROOT/infra"
docker compose up -d nginx-proxy
echo "✔ nginx ok"
echo ""

echo "╔══════════════════════════════════════════════════════╗"
echo "║  Stack no ar!                                        ║"
echo "║  Site:     http://localhost                          ║"
echo "║  API:      http://localhost/api/v1/                  ║"
echo "║  RabbitMQ: http://localhost:15672  (guest/guest)     ║"
echo "║  MinIO:    http://localhost:9001   (minioadmin)      ║"
echo "╚══════════════════════════════════════════════════════╝"
