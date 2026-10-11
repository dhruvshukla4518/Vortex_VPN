"""
VORTEX VPN - VPN Connection Lifecycle Endpoints
Connect, disconnect, status checks, and security diagnostics.
"""
from fastapi import APIRouter, Depends, Request, HTTPException, status
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import settings
from backend.app.database.session import get_db
from backend.app.models.user import User
from backend.app.schemas.vpn import (
    VPNConnectRequest,
    VPNConnectResponse,
    VPNDisconnectRequest,
    VPNStatusResponse,
    DiagnosticResult
)
from backend.app.security.authorization import get_current_active_user
from backend.app.services.vpn_service import VPNService
from backend.app.services.server_service import ServerService
from backend.app.services.crypto_service import WireGuardCryptoService

router = APIRouter(prefix="/vpn", tags=["VPN"])


@router.post("/connect", response_model=VPNConnectResponse)
async def connect_vpn(
    req: VPNConnectRequest,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Initiate VPN connection, provision client WireGuard config with DNS leak protection,
    and activate secure routing tunnel.
    """
    client_ip = request.client.host if request.client else "127.0.0.1"
    response = await VPNService.connect(db, current_user, req, client_ip=client_ip)
    return response


@router.post("/disconnect", response_model=VPNStatusResponse)
async def disconnect_vpn(
    req: VPNDisconnectRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Terminate the active VPN tunnel session."""
    response = await VPNService.disconnect(db, current_user, req)
    return response


@router.get("/status", response_model=VPNStatusResponse)
async def get_vpn_status(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Fetch active VPN connection status, duration, latency, and throughput."""
    return await VPNService.get_active_status(db, current_user)


@router.get("/diagnostics", response_model=DiagnosticResult)
async def get_diagnostics(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Run full security diagnostics (DNS leak check, IPv4/IPv6 status, kill switch)."""
    return await VPNService.run_diagnostics(db, current_user)


@router.get("/profile/{country_code}.conf", response_class=PlainTextResponse)
async def download_profile_config(
    country_code: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Directly download a ready-to-use WireGuard configuration profile for mobile & desktop devices.
    Zero-friction profile generation for mobile phones, tablets, and laptops.
    """
    server, reason, _ = await ServerService.select_fastest_server(db, country_code=country_code.upper())
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No active VPN node found for region '{country_code}'"
        )
    
    client_priv, client_pub = WireGuardCryptoService.generate_keypair()
    assigned_ipv4 = "10.8.0.5/32"
    assigned_ipv6 = "fd42:42:42::5/128"
    dns_resolver = settings.WIREGUARD_DNS_SERVER

    raw_config = (
        f"[Interface]\n"
        f"# VORTEX VPN Profile: {server.country} ({server.city})\n"
        f"# Client Identity: {client_pub}\n"
        f"PrivateKey = {client_priv}\n"
        f"Address = {assigned_ipv4}, {assigned_ipv6}\n"
        f"DNS = {dns_resolver}\n\n"
        f"[Peer]\n"
        f"PublicKey = {server.wireguard_public_key}\n"
        f"Endpoint = {server.wireguard_endpoint}\n"
        f"AllowedIPs = 0.0.0.0/0, ::/0\n"
        f"PersistentKeepalive = 25\n"
    )

    headers = {
        "Content-Disposition": f"attachment; filename=vortex_{country_code.lower()}.conf"
    }
    return PlainTextResponse(content=raw_config, headers=headers)

