"""
VORTEX VPN - Standalone Client WireGuard Configuration Generator
Usage:
  python scripts/generate_config.py --country DE --out client_wg0.conf
"""
import os
import sys
import argparse
import asyncio

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.database.session import AsyncSessionLocal
from backend.app.services.server_service import ServerService
from backend.app.services.crypto_service import WireGuardCryptoService

async def generate(country_code: str, output_path: str):
    async with AsyncSessionLocal() as session:
        server, reason, _ = await ServerService.select_fastest_server(session, country_code=country_code)
        if not server:
            print(f"[ERROR] No available server found for country: {country_code}")
            return

        client_priv, client_pub = WireGuardCryptoService.generate_keypair()
        assigned_ip = "10.8.0.2/32"
        assigned_ip6 = "fd42:42:42::2/128"

        config_content = (
            f"[Interface]\n"
            f"# Client Public Key: {client_pub}\n"
            f"PrivateKey = {client_priv}\n"
            f"Address = {assigned_ip}, {assigned_ip6}\n"
            f"DNS = 10.8.0.1\n\n"
            f"[Peer]\n"
            f"# Server: {server.country} ({server.city}) - Hostname: {server.hostname}\n"
            f"PublicKey = {server.wireguard_public_key}\n"
            f"Endpoint = {server.wireguard_endpoint}\n"
            f"AllowedIPs = 0.0.0.0/0, ::/0\n"
            f"PersistentKeepalive = 25\n"
        )

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(config_content)

        print("==================================================")
        print(f"[SUCCESS] Generated WireGuard configuration: {output_path}")
        print(f"Target Server: {server.country} · {server.city} ({server.wireguard_endpoint})")
        print(f"Assigned Tunnel IP: {assigned_ip}")
        print(f"DNS Protection: 10.8.0.1")
        print("==================================================")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate VORTEX VPN WireGuard Config")
    parser.add_argument("--country", default="DE", help="Country code (DE, US, IN, GB, SG, NL)")
    parser.add_argument("--out", default="vortex_wg0.conf", help="Output .conf file path")
    args = parser.parse_args()

    asyncio.run(generate(args.country, args.out))
