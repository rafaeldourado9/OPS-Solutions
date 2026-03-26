# Deploy na AWS — Guia Completo

## Visão Geral

```
EC2 (Ubuntu 22.04 + GPU)
├── Docker Compose
│   ├── agent        (FastAPI — porta 8000)
│   ├── redis        (debounce + keyspace events)
│   ├── qdrant       (memória semântica + RAG)
│   ├── postgres     (histórico completo)
│   ├── ollama       (LLM local + embeddings + whisper — GPU)
│   └── waha         (WhatsApp gateway — porta 3000)
└── Caddy (reverse proxy + HTTPS automático — porta 443)
```

---

## 1. Escolher a Instância EC2

| Instância | GPU | VRAM | RAM | vCPU | Preço On-Demand | Preço Spot |
|-----------|-----|------|-----|------|-----------------|------------|
| **g4dn.xlarge** | T4 | 16 GB | 16 GB | 4 | ~$0.526/h | ~$0.16/h |
| **g5.xlarge** | A10G | 24 GB | 16 GB | 4 | ~$1.006/h | ~$0.30/h |
| g4dn.2xlarge | T4 | 16 GB | 32 GB | 8 | ~$0.752/h | ~$0.23/h |

**Recomendação**: `g4dn.xlarge` com Spot Instance. O T4 roda llama3.1:8b + nomic-embed-text + whisper tranquilo. Se quiser llava:13b simultâneo, vai de `g5.xlarge`.

**Disco**: 80 GB gp3 mínimo (modelos Ollama ocupam ~15 GB, imagens Docker ~5 GB, dados ~5 GB, sobra espaço).

**AMI**: Ubuntu 22.04 LTS (ami mais recente da Canonical).

---

## 2. Security Group

```
Inbound:
  SSH        TCP 22     Seu IP apenas
  HTTPS      TCP 443    0.0.0.0/0       (webhook do WAHA + health)
  Custom     TCP 3000   Seu IP apenas   (WAHA dashboard — temporário, fechar depois do QR)

Outbound:
  All traffic  0.0.0.0/0  (WhatsApp, Gemini API, download de modelos)
```

> Depois de escanear o QR no WAHA dashboard, feche a porta 3000.

---

## 3. Provisionar e Acessar

```bash
# SSH na instância
ssh -i sua-chave.pem ubuntu@<IP-PUBLICO>
```

---

## 4. Bootstrap Automático

```bash
# Baixar e rodar o script de setup
curl -sO https://raw.githubusercontent.com/<seu-repo>/main/scripts/setup_ec2.sh
chmod +x setup_ec2.sh
sudo REPO_URL=https://github.com/<seu-repo>.git ./setup_ec2.sh

# Reboot obrigatório (drivers NVIDIA precisam)
sudo reboot
```

O script instala:
- Docker + Docker Compose v2
- NVIDIA drivers (detecta T4/A10G automaticamente)
- NVIDIA Container Toolkit (GPU no Docker)
- Clona o repo em `/opt/whatsapp-agent`

---

## 5. Configurar .env

```bash
cd /opt/whatsapp-agent
cp .env.example .env
nano .env
```

**Valores obrigatórios para produção:**

```bash
# LLM — obrigatório
GEMINI_API_KEY=sua-chave-aqui

# WAHA — trocar os defaults!
WAHA_API_KEY=uma-senha-forte-aqui
WAHA_DASHBOARD_USER=admin
WAHA_DASHBOARD_PASSWORD=outra-senha-forte

# Webhook — usar o container hostname, não localhost
WAHA_HOOK_URL=http://agent:8000/webhook

# PostgreSQL — trocar a senha padrão
DATABASE_URL=postgresql+asyncpg://postgres:SENHA_FORTE@postgres:5432/whatsapp_agent

# Agentes que rodam
AGENT_IDS=ops_solutions,maya,snowden

# Logs em JSON para produção
LOG_JSON=true
LOG_LEVEL=INFO
```

**Trocar a senha do PostgreSQL no docker-compose também:**

```bash
# No docker-compose.yml, seção postgres > environment:
POSTGRES_PASSWORD: MESMA_SENHA_FORTE
```

---

## 6. Configurar Caddy (HTTPS + Reverse Proxy)

Caddy dá HTTPS automático via Let's Encrypt. Sem configurar certificado manual.

```bash
# Criar Caddyfile
cat > /opt/whatsapp-agent/Caddyfile << 'EOF'
{
    email seu-email@dominio.com
}

seu-dominio.com {
    # Webhook do WAHA (precisa ser acessível publicamente)
    handle /webhook* {
        reverse_proxy agent:8000
    }

    # Health check
    handle /health {
        reverse_proxy agent:8000
    }

    # Bloqueia todo o resto
    handle {
        respond "Not Found" 404
    }
}
EOF
```

Adicionar o Caddy no docker-compose. Crie `docker-compose.prod.yml`:

```bash
cat > /opt/whatsapp-agent/docker-compose.prod.yml << 'EOF'
services:
  caddy:
    image: caddy:2-alpine
    container_name: whatsapp-agent-caddy
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile:ro
      - caddy-data:/data
      - caddy-config:/config
    networks:
      - agent-network
    depends_on:
      - agent

  # Overrides para produção
  agent:
    environment:
      - LOG_JSON=true
      - LOG_LEVEL=INFO

  waha:
    environment:
      # Webhook via Caddy/rede interna
      WHATSAPP_HOOK_URL: http://agent:8000/webhook

  # Não expor portas internas em produção
  redis:
    ports: !reset []
  qdrant:
    ports: !reset []
  postgres:
    ports: !reset []
  ollama:
    ports: !reset []
  agent:
    ports: !reset []

volumes:
  caddy-data:
  caddy-config:
EOF
```

> **Sem domínio?** Use o IP público direto com Caddy em modo HTTP, ou acesse `http://<IP>:8000` e pule o Caddy.

---

## 7. Atualizar Webhook do WAHA

No `.env`, o WAHA precisa postar o webhook para o container do agent (rede interna Docker):

```bash
# No .env
WAHA_HOOK_URL=http://agent:8000/webhook
```

Se não usar Caddy e o WAHA precisar chamar o agent pela rede Docker, isso já funciona porque estão na mesma `agent-network`.

---

## 8. Subir Tudo

```bash
cd /opt/whatsapp-agent

# Com Caddy (HTTPS)
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Sem Caddy (HTTP direto)
docker compose up -d

# Acompanhar logs
docker compose logs -f agent
docker compose logs -f ollama   # ver download dos modelos
```

**Primeira vez demora** — o Ollama baixa ~8 GB em modelos. Acompanhe:
```bash
docker compose logs -f ollama
# Esperar até ver "✅ Modelos baixados!"
```

---

## 9. Conectar WhatsApp

```bash
# Abrir o dashboard WAHA no browser
# http://<IP-PUBLICO>:3000/dashboard
# Login: admin / <sua senha do .env>
```

1. Clique na sessão "default"
2. Escaneie o QR code com o WhatsApp do número que vai ser o agente
3. Aguarde status "CONNECTED"
4. **Feche a porta 3000 no Security Group** (segurança)

---

## 10. Ingerir Documentos RAG

```bash
# Para cada agente que tem documentos em agents/<nome>/docs/
docker compose exec agent python scripts/ingest.py --agent ops_solutions
docker compose exec agent python scripts/ingest.py --agent maya
docker compose exec agent python scripts/ingest.py --agent snowden
```

---

## 11. Verificar Saúde

```bash
# Health check
curl http://localhost:8000/health

# Ou via Caddy
curl https://seu-dominio.com/health

# Status de todos os containers
docker compose ps

# Logs do agent
docker compose logs -f agent --tail=50
```

Todos os containers devem estar `(healthy)`.

---

## 12. Monitorar em Produção

### Logs
```bash
# Logs em tempo real
docker compose logs -f agent

# Últimas 100 linhas
docker compose logs --tail=100 agent

# Logs de um serviço específico
docker compose logs -f ollama
docker compose logs -f waha
```

### Uso de recursos
```bash
# CPU, RAM, rede de cada container
docker stats

# Uso de disco
df -h
docker system df
```

### GPU
```bash
# Uso da GPU pelo Ollama
nvidia-smi

# Watch contínuo
watch -n 2 nvidia-smi
```

---

## 13. Atualizar o Código

```bash
cd /opt/whatsapp-agent

# Puxar mudanças
git pull

# Rebuild só do agent (rápido se requirements.txt não mudou)
docker compose build agent

# Restart só do agent (zero downtime pros outros serviços)
docker compose up -d agent

# Se mudou requirements.txt, rebuild sem cache
docker compose build --no-cache agent
docker compose up -d agent
```

---

## 14. Backup

### PostgreSQL (histórico de conversas)
```bash
# Dump
docker compose exec postgres pg_dump -U postgres whatsapp_agent > backup_$(date +%Y%m%d).sql

# Restore
docker compose exec -T postgres psql -U postgres whatsapp_agent < backup_20260319.sql
```

### Qdrant (embeddings)
```bash
# Os dados ficam no volume qdrant-data
# Snapshot via API
curl -X POST http://localhost:6333/collections/ops_solutions_chats/snapshots
curl -X POST http://localhost:6333/collections/ops_solutions_rules/snapshots
```

### WAHA (sessão WhatsApp)
```bash
# O volume waha-data mantém a sessão ativa
# Se perder, precisa escanear QR de novo
```

### Backup automatizado (cron)
```bash
# Adicionar no crontab do host
crontab -e

# Backup diário do PostgreSQL às 3h da manhã
0 3 * * * cd /opt/whatsapp-agent && docker compose exec -T postgres pg_dump -U postgres whatsapp_agent | gzip > /opt/backups/pg_$(date +\%Y\%m\%d).sql.gz

# Limpar backups com mais de 30 dias
0 4 * * * find /opt/backups -name "pg_*.sql.gz" -mtime +30 -delete
```

---

## 15. Troubleshooting

| Problema | Causa provável | Solução |
|----------|---------------|---------|
| Agent não responde | Ollama ainda baixando modelos | `docker compose logs ollama` — esperar |
| "Connection refused" no webhook | WAHA não alcança o agent | Verificar `WAHA_HOOK_URL` e que estão na mesma rede |
| GPU não detectada | Drivers NVIDIA não instalados | `nvidia-smi` — se falhar, reboot e rodar setup_ec2.sh de novo |
| Ollama lento | Rodando em CPU (GPU não mapeada) | Verificar `deploy.resources.reservations.devices` no compose |
| WAHA desconecta | Sessão expirou | Dashboard → reconectar → escanear QR novamente |
| "Out of memory" | llama3.1:8b + llava:7b simultâneo | Reduzir `num_ctx` nos agents ou usar instância maior |
| Porta 8000 não acessível | Security Group bloqueando | Adicionar regra inbound TCP 8000 (ou usar Caddy na 443) |

---

## 16. Custos Estimados (Mês)

| Item | Custo estimado |
|------|---------------|
| g4dn.xlarge Spot (24/7) | ~$115/mês |
| g4dn.xlarge On-Demand (24/7) | ~$380/mês |
| EBS 80 GB gp3 | ~$6.40/mês |
| Gemini API (depende do uso) | ~$5-50/mês |
| **Total Spot** | **~$125-170/mês** |
| **Total On-Demand** | **~$390-430/mês** |

> Spot Instances podem ser interrompidas. Para produção crítica, use On-Demand ou Reserved Instance (desconto de ~40%).

---

## Checklist de Deploy

```
[ ] EC2 provisionada (g4dn.xlarge, Ubuntu 22.04, 80 GB gp3)
[ ] Security Group configurado (22, 443, 3000 temporário)
[ ] setup_ec2.sh executado + reboot
[ ] nvidia-smi mostra a GPU
[ ] .env configurado (GEMINI_API_KEY, senhas fortes)
[ ] docker compose up -d
[ ] Todos containers healthy (docker compose ps)
[ ] Modelos Ollama baixados (docker compose logs ollama)
[ ] QR code escaneado no WAHA dashboard
[ ] Porta 3000 fechada no Security Group
[ ] Documentos RAG ingeridos
[ ] Teste: mandar mensagem no WhatsApp → agente responde
[ ] Backup do PostgreSQL configurado (cron)
[ ] Caddy com HTTPS (se tiver domínio)
```
