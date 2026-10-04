#!/usr/bin/env bash
# ==============================================================================
# VORTEX VPN - Linux Client Installer Script
# Installs 'vortex' CLI command into /usr/local/bin
# ==============================================================================
set -euo pipefail

echo "==> [VORTEX VPN] Installing Linux Client..."

# Ensure python3 and wireguard-tools
if ! command -v wg-quick &> /dev/null; then
    echo "==> Installing wireguard-tools..."
    sudo apt-get update -y && sudo apt-get install -y wireguard-tools
fi

# Link CLI executable
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
sudo ln -sf "$SCRIPT_DIR/vortex_cli.py" /usr/local/bin/vortex
sudo chmod +x /usr/local/bin/vortex

echo "==> [SUCCESS] VORTEX VPN CLI installed!"
echo "Run 'vortex --help' or 'vortex connect' to start."
