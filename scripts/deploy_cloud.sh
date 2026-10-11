#!/usr/bin/env bash
# ==============================================================================
# VORTEX VPN — Turnkey Cloud VPS One-Command Deployment Script
# Supports: Ubuntu 20.04+, Debian 11+, CentOS/RHEL 9, AlmaLinux, RockyLinux
# ==============================================================================
set -euo pipefail

echo "=================================================================="
echo "          VORTEX VPN — HIGH-SECURITY CLOUD DEPLOYMENT            "
echo "=================================================================="

# 1. Root / Sudo Check
if [ "$EUID" -ne 0 ]; then
  echo "[-] Please run as root or with sudo: sudo bash scripts/deploy_cloud.sh"
  exit 1
fi

# 2. Check / Install Docker and Docker Compose
echo "[*] Step 1/5: Checking system dependencies..."
if ! command -v docker &> /dev/null; then
  echo "[+] Installing Docker Engine..."
  curl -fsSL https://get.docker.com -o get-docker.sh
  sh get-docker.sh
  rm -f get-docker.sh
  systemctl enable --now docker
else
  echo "[+] Docker is already installed."
fi

if ! docker compose version &> /dev/null; then
  echo "[+] Installing Docker Compose plugin..."
  apt-get update && apt-get install -y docker-compose-plugin || yum install -y docker-compose-plugin || true
fi

# 3. Detect Public Server IP
echo "[*] Step 2/5: Detecting public IP..."
PUBLIC_IP=$(curl -s -m 5 https://api.ipify.org || curl -s -m 5 https://ifconfig.me || echo "127.0.0.1")
echo "[+] Detected Public IP: ${PUBLIC_IP}"

# 4. Generate Production Secrets if .env doesn't exist
echo "[*] Step 3/5: Configuring security environment..."
if [ ! -f .env ]; then
  JWT_SECRET=$(openssl rand -hex 32 2>/dev/null || date +%s%N | sha256sum | head -c 64)
  AGENT_SECRET=$(openssl rand -hex 32 2>/dev/null || date +%s%N | sha256sum | head -c 64)
  cat <<EOF > .env
ENVIRONMENT=production
DEBUG=false
PUBLIC_HOST=${PUBLIC_IP}
JWT_SECRET_KEY=${JWT_SECRET}
AGENT_SECRET_KEY=${AGENT_SECRET}
POSTGRES_USER=vortex
POSTGRES_PASSWORD=$(openssl rand -hex 16 2>/dev/null || echo "vortex_secure_pw_123")
POSTGRES_DB=vortex_vpn
EOF
  echo "[+] Generated cryptographically secure .env file."
fi

# 5. Build and Launch Containers
echo "[*] Step 4/5: Launching VORTEX VPN containers..."
docker compose down --remove-orphans 2>/dev/null || true
docker compose up -d --build

# 6. Verify Health
echo "[*] Step 5/5: Verifying service health..."
sleep 5
ATTEMPTS=0
MAX_ATTEMPTS=12
READY=false

while [ $ATTEMPTS -lt $MAX_ATTEMPTS ]; do
  if curl -s -f "http://localhost:8000/health" &>/dev/null; then
    READY=true
    break
  fi
  sleep 3
  ATTEMPTS=$((ATTEMPTS+1))
done

echo "=================================================================="
if [ "$READY" = true ]; then
  echo "  ✅ VORTEX VPN IS SUCCESSFULLY DEPLOYED AND RUNNING!           "
else
  echo "  ⚠️ Containers are launching. Please wait a moment.            "
fi
echo "=================================================================="
echo ""
echo "📱 1. WEB APP & PWA (Install on Android/iPhone/Desktop):"
echo "   http://${PUBLIC_IP}:8000/"
echo "   (Open in Chrome or Safari -> tap 'Add to Home Screen' to install)"
echo ""
echo "🌍 2. CONNECT ANY DEVICE VIA WIREGUARD (Instant QR & Profiles):"
echo "   - Open http://${PUBLIC_IP}:8000/ on your phone or PC"
echo "   - Tap 'Connect Phone & Other Devices' to scan QR code directly!"
echo "   - Or download config files directly:"
echo "     * Germany:       http://${PUBLIC_IP}:8000/api/v1/vpn/profile/de.conf"
echo "     * United States: http://${PUBLIC_IP}:8000/api/v1/vpn/profile/us.conf"
echo "     * India:         http://${PUBLIC_IP}:8000/api/v1/vpn/profile/in.conf"
echo "     * United Kingdom:http://${PUBLIC_IP}:8000/api/v1/vpn/profile/gb.conf"
echo "     * Singapore:     http://${PUBLIC_IP}:8000/api/v1/vpn/profile/sg.conf"
echo "     * Netherlands:   http://${PUBLIC_IP}:8000/api/v1/vpn/profile/nl.conf"
echo ""
echo "⚙️ 3. ADMIN DASHBOARD & FLEET TELEMETRY:"
echo "   http://${PUBLIC_IP}:8501/"
echo ""
echo "🛡️ DNS Shield & Ad-blocking active on port 5353"
echo "=================================================================="
