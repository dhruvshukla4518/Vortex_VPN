"""
VORTEX VPN - Server Fleet Endpoints
Provides real-time server fleet status, country lists, and the AUTO / Fastest selection endpoint.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.database.session import get_db
from backend.app.schemas.server import ServerResponse, FastestServerSelectionResponse
from backend.app.services.server_service import ServerService

router = APIRouter(prefix="/servers", tags=["Servers"])


@router.get("", response_model=List[ServerResponse])
async def list_servers(
    only_active: bool = Query(default=True, description="Filter only active nodes"),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve all VPN servers with real health, latency, and load metrics."""
    servers = await ServerService.list_servers(db, only_active=only_active)
    return servers


@router.get("/auto/fastest", response_model=FastestServerSelectionResponse)
async def get_fastest_server(
    country_code: Optional[str] = Query(default=None, description="Optional country filter (e.g. DE, US, IN)"),
    db: AsyncSession = Depends(get_db)
):
    """
    Evaluate all online nodes and return the mathematically optimal server based on
    real-time ping latency, packet loss, CPU/RAM load, and available capacity.
    """
    server, reason, count = await ServerService.select_fastest_server(db, country_code=country_code)
    if not server:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No healthy VPN servers currently available"
        )
    return FastestServerSelectionResponse(
        server=ServerResponse.model_validate(server),
        selection_reason=reason,
        score=server.score,
        evaluated_nodes=count
    )


@router.get("/country/{country_code}", response_model=List[ServerResponse])
async def get_servers_by_country(
    country_code: str,
    db: AsyncSession = Depends(get_db)
):
    """Retrieve all healthy servers in a specific country."""
    servers = await ServerService.get_servers_by_country(db, country_code)
    if not servers:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No active servers found in country code '{country_code}'"
        )
    return servers


@router.get("/{server_id}", response_model=ServerResponse)
async def get_server(
    server_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Retrieve single server details."""
    server = await ServerService.get_server_by_id(db, server_id)
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found"
        )
    return server
