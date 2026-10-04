"""
VORTEX VPN - Health Check & Remote Server Agent Heartbeat Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import settings
from backend.app.database.session import get_db
from backend.app.schemas.server import ServerHealthReport
from backend.app.security.authorization import verify_agent_token
from backend.app.services.server_service import ServerService
from backend.app.services.health_service import HealthService

router = APIRouter(tags=["Health & Monitoring"])


@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """Public system health check and fleet availability status."""
    fleet_health = await HealthService.evaluate_fleet_health(db)
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "fleet": fleet_health
    }


@router.post("/health/heartbeat")
async def agent_heartbeat(
    report: ServerHealthReport,
    _: bool = Depends(verify_agent_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Secure heartbeat receiver for remote server agents.
    Updates CPU, RAM, bandwidth, packet loss, and active peers.
    """
    server = await ServerService.update_health(db, report)
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Server with hostname '{report.hostname}' not registered"
        )
    return {
        "status": "acknowledged",
        "hostname": server.hostname,
        "calculated_score": server.score
    }
