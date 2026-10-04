# VORTEX VPN — Linux Server Node Deployment Guide

This guide walks through deploying a production WireGuard VPN server node on an Ubuntu 22.04 LTS or Debian 12 VPS.

---

## 1. Prerequisites
- A Linux VPS with a static public IPv4 address and root access.
- Kernel headers and WireGuard support.
- Open UDP port `51820` on any cloud firewall (e.g. AWS Security Group, Hetzner, DigitalOcean).

---

## 2. Automated Node Setup

1. Clone or copy the deployment directory to the server:
```bash
git clone https://github.com/your-org/vortex-vpn.git /opt/vortex-vpn
cd /opt/vortex-vpn
```

2. Run the automated WireGuard setup script as root:
```bash
chmod +x deployment/wireguard/setup_wireguard.sh
sudo deployment/wireguard/setup_wireguard.sh
```

The script will:
- Install `wireguard` and `resolvconf`.
- Enable kernel IP forwarding in `/etc/sysctl.d/99-vortex.conf`.
- Generate `/etc/wireguard/server_private.key` and `/etc/wireguard/server_public.key`.
- Configure `wg0.conf` with NAT masquerading rules.
- Enable and start `wg-quick@wg0`.

---

## 3. Install DNS Privacy Blocker on Node

1. Install Python 3.12+ and dependencies:
```bash
sudo apt install -y python3-pip python3-venv
python3 -m venv /opt/vortex-vpn/.venv
/opt/vortex-vpn/.venv/bin/pip install -r pyproject.toml
```

2. Install systemd service:
```bash
sudo cp deployment/systemd/vortex-dns.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now vortex-dns.service
```

---

## 4. Install Server Monitoring Agent

1. Configure environment in `/opt/vortex-vpn/.env`:
```ini
CONTROL_PLANE_URL=https://api.vortexvpn.net
SERVER_HOSTNAME=de-fra-01.vortexvpn.net
AGENT_SECRET_KEY=your-secure-agent-secret
```

2. Enable and start agent:
```bash
sudo cp deployment/systemd/vortex-agent.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now vortex-agent.service
```

---

## 5. Register Server Node on Control Plane

Register the newly deployed node via the Streamlit Admin Console or via REST API:
```bash
curl -X POST https://api.vortexvpn.net/api/v1/admin/servers \
  -H "Authorization: Bearer <ADMIN_JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "country": "Germany",
    "country_code": "DE",
    "city": "Frankfurt",
    "hostname": "de-fra-01.vortexvpn.net",
    "public_ip": "<YOUR_VPS_PUBLIC_IP>",
    "wireguard_endpoint": "<YOUR_VPS_PUBLIC_IP>:51820",
    "wireguard_public_key": "<SERVER_PUBLIC_KEY_FROM_STEP_2>",
    "internal_subnet": "10.8.0.0/24",
    "capacity": 2000
  }'
```
