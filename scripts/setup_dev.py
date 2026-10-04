"""
VORTEX VPN - Development Environment Setup & Validation Script
"""
import os
import sys
import asyncio

# Ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

async def main():
    print("==================================================")
    print("VORTEX VPN - Development Environment Setup")
    print("==================================================")
    
    print("==> Checking Python dependencies...")
    try:
        import fastapi
        import uvicorn
        import sqlalchemy
        import aiosqlite
        import cryptography
        import argon2
        import jwt
        import dns
        import psutil
        print("  [OK] All core Python packages verified.")
    except ImportError as e:
        print(f"  [ERROR] Missing dependency: {e}")
        sys.exit(1)

    print("==> Initializing Database & Fleet Tables...")
    from backend.app.database.session import init_db, AsyncSessionLocal
    from backend.app.services.server_service import ServerService

    await init_db()
    async with AsyncSessionLocal() as session:
        await ServerService.seed_initial_fleet(session)
    print("  [OK] Database initialized and multi-country fleet seeded.")

    print("==> Testing WireGuard Curve25519 Cryptography...")
    from backend.app.services.crypto_service import WireGuardCryptoService
    priv, pub = WireGuardCryptoService.generate_keypair()
    assert WireGuardCryptoService.validate_key(pub)
    print(f"  [OK] Curve25519 Keypair verified (Sample Public: {pub})")

    print("\n[SUCCESS] VORTEX VPN environment is fully configured and ready!")
    print("Start the backend with:")
    print("  python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload")
    print("Open client in browser at: http://127.0.0.1:8000")

if __name__ == "__main__":
    asyncio.run(main())
