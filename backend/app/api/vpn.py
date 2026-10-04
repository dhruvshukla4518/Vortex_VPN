"""
VORTEX VPN - VPN Connection Lifecycle Endpoints
Connect, disconnect, status checks, and security diagnostics.
"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

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
