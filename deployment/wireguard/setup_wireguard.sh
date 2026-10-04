#!/usr/bin/env bash
# ==============================================================================
# VORTEX VPN - Linux Node WireGuard Setup Script
# Run with root privileges on the VPN server node (Ubuntu 22.04+ / Debian 12+)
# ==============================================================================
set -euo pipefail

echo "==> [VORTEX VPN] Initializing WireGuard Node..."

# 1. Update packages & install WireGuard
apt-get update -y
apt-get install -y wireguard iptables resolvconf

# 2. Enable IPv4 and IPv6 packet forwarding
echo "==> Configuring sysctl kernel packet forwarding..."
cat <<EOF > /etc/sysctl.d/99-vortex.conf
net.ipv4.ip_forward = 1
net.ipv6.conf.all.forwarding = 1
net.core.default_qdisc = fq
net.ipv4.tcp_congestion_control = bbr
EOF
sysctl -p /etc/sysctl.d/99-vortex.conf

# 3. Generate Server Keypair if missing
WG_DIR="/etc/wireguard"
mkdir -p "$WG_DIR"
chmod 700 "$WG_DIR"

if [ ! -f "$WG_DIR/server_private.key" ]; then
    echo "==> Generating WireGuard Curve25519 keypair..."
    wg genkey | tee "$WG_DIR/server_private.key" | wg pubkey > "$WG_DIR/server_public.key"
    chmod 600 "$WG_DIR/server_private.key"
fi

SERVER_PRIV_KEY=$(cat "$WG_DIR/server_private.key")
SERVER_PUB_KEY=$(cat "$WG_DIR/server_public.key")

echo "=================================================="
echo "SERVER PUBLIC KEY: $SERVER_PUB_KEY"
echo "=================================================="

# 4. Detect default public network interface
DEFAULT_IFACE=$(ip -4 route ls | grep default | grep -Po '(?<=dev )(\S+)' | head -1)
echo "==> Detected Public Network Interface: $DEFAULT_IFACE"

# 5. Populate wg0.conf
cat <<EOF > "$WG_DIR/wg0.conf"
[Interface]
Address = 10.8.0.1/24, fd42:42:42::1/64
ListenPort = 51820
PrivateKey = $SERVER_PRIV_KEY

PostUp = iptables -A FORWARD -i wg0 -j ACCEPT; iptables -t nat -A POSTROUTING -o $DEFAULT_IFACE -j MASQUERADE; ip6tables -A FORWARD -i wg0 -j ACCEPT; ip6tables -t nat -A POSTROUTING -o $DEFAULT_IFACE -j MASQUERADE; iptables -t nat -A PREROUTING -i wg0 -p udp --dport 53 -j REDIRECT --to-ports 5353
PostDown = iptables -D FORWARD -i wg0 -j ACCEPT; iptables -t nat -D POSTROUTING -o $DEFAULT_IFACE -j MASQUERADE; ip6tables -D FORWARD -i wg0 -j ACCEPT; ip6tables -t nat -D POSTROUTING -o $DEFAULT_IFACE -j MASQUERADE; iptables -t nat -D PREROUTING -i wg0 -p udp --dport 53 -j REDIRECT --to-ports 5353
EOF

# 6. Enable and start WireGuard systemd service
systemctl enable wg-quick@wg0
systemctl restart wg-quick@wg0

echo "==> [VORTEX VPN] WireGuard is active and listening on port 51820."
wg show wg0
