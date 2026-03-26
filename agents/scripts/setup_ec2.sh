#!/bin/bash
# setup_ec2.sh — Bootstrap script for Ubuntu 22.04 on g4dn.xlarge (or any GPU instance)
#
# Run once after provisioning the EC2 instance:
#   chmod +x setup_ec2.sh && sudo ./setup_ec2.sh
#
# What this does:
#   1. Installs Docker + Docker Compose v2
#   2. Installs NVIDIA drivers + NVIDIA Container Toolkit (for Ollama GPU)
#   3. Configures Docker to use NVIDIA runtime by default
#   4. Clones the repo and guides you through the .env setup

set -euo pipefail

REPO_URL="${REPO_URL:-}"  # Set this to your git repo URL before running
INSTALL_DIR="/opt/whatsapp-agent"

echo "========================================"
echo "  WhatsApp Agent — EC2 Bootstrap"
echo "========================================"

# ---------------------------------------------------------------------------
# 1. System update
# ---------------------------------------------------------------------------
apt-get update -y
apt-get upgrade -y
apt-get install -y curl git unzip ca-certificates gnupg lsb-release

# ---------------------------------------------------------------------------
# 2. Docker
# ---------------------------------------------------------------------------
echo ">>> Installing Docker..."
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" \
  > /etc/apt/sources.list.d/docker.list

apt-get update -y
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

systemctl enable docker
systemctl start docker

# Add ubuntu user to docker group (avoids sudo on every command)
usermod -aG docker ubuntu

echo ">>> Docker installed: $(docker --version)"
echo ">>> Docker Compose: $(docker compose version)"

# ---------------------------------------------------------------------------
# 3. NVIDIA drivers (for g4dn = T4 GPU, g5 = A10G GPU)
# ---------------------------------------------------------------------------
echo ">>> Installing NVIDIA drivers..."
apt-get install -y linux-headers-$(uname -r)

# Use ubuntu-drivers for automatic driver selection
apt-get install -y ubuntu-drivers-common
ubuntu-drivers install --gpgpu || true

# Verify (may need reboot first)
nvidia-smi || echo "WARNING: nvidia-smi failed — reboot may be needed"

# ---------------------------------------------------------------------------
# 4. NVIDIA Container Toolkit (lets Docker use the GPU)
# ---------------------------------------------------------------------------
echo ">>> Installing NVIDIA Container Toolkit..."
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey \
  | gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg

curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list \
  | sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' \
  > /etc/apt/sources.list.d/nvidia-container-toolkit.list

apt-get update -y
apt-get install -y nvidia-container-toolkit

# Configure Docker to use NVIDIA runtime by default
nvidia-ctk runtime configure --runtime=docker --set-as-default
systemctl restart docker

echo ">>> NVIDIA Container Toolkit installed"

# ---------------------------------------------------------------------------
# 5. Clone repo
# ---------------------------------------------------------------------------
if [ -n "$REPO_URL" ]; then
  echo ">>> Cloning repo to $INSTALL_DIR..."
  git clone "$REPO_URL" "$INSTALL_DIR"
  cd "$INSTALL_DIR"
else
  echo ""
  echo ">>> REPO_URL not set. Clone manually:"
  echo "    git clone <your-repo-url> $INSTALL_DIR"
  echo "    cd $INSTALL_DIR"
fi

# ---------------------------------------------------------------------------
# 6. .env setup reminder
# ---------------------------------------------------------------------------
cat <<'EOF'

========================================
  Next steps
========================================

1. Go to the project directory:
   cd /opt/whatsapp-agent

2. Copy and fill the .env file:
   cp .env.example .env
   nano .env

   Key values to set:
     GEMINI_API_KEY=...
     WAHA_API_KEY=<choose a strong key>
     WAHA_DASHBOARD_PASSWORD=<choose a strong password>

3. Start all services (with production overrides):
   docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

4. Watch logs:
   docker compose logs -f agent

5. Scan the WhatsApp QR code:
   Open http://<EC2-PUBLIC-IP>:3000/dashboard in your browser
   (make sure port 3000 is open in your EC2 Security Group — only for your IP)

6. Ingest RAG documents for each agent:
   docker compose exec agent python scripts/ingest.py --agent ops_solutions
   docker compose exec agent python scripts/ingest.py --agent maya
   docker compose exec agent python scripts/ingest.py --agent snowden

========================================
  Recommended EC2 Security Group rules
========================================

Inbound:
  SSH     TCP 22    Your IP only
  Custom  TCP 3000  Your IP only   (WAHA dashboard — for QR scan, can close after)
  Custom  TCP 8000  Your IP only   (API health check — optional)

Outbound:
  All traffic — 0.0.0.0/0         (WhatsApp, Gemini API, model downloads)

NOTE: After scanning the QR code and WhatsApp is connected,
you can close port 3000 in the Security Group for extra security.

EOF

echo ">>> Bootstrap complete. Reboot recommended before starting services:"
echo "    sudo reboot"
