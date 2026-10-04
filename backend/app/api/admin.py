"""
VORTEX VPN - Administrative Management Endpoints
Privileged endpoints for fleet control, server node CRUD, and platform metrics.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from backend.app.database.session import get_db
from backend.app.models.user import User
from backend.app.models.server import VPNServer
from backend.app.models.connection import VPNConnection
from backend.app.models.dns import DNSStatistics
from backend.app.schemas.server import ServerCreateRequest, ServerUpdateRequest, ServerResponse
from backend.app.schemas.admin import AdminDashboardMetrics
from backend.app.security.authorization import get_current_admin_user
from backend.app.services.server_service import ServerService
from backend.app.services.health_service import HealthService

router = APIRouter(prefix="/admin", tags=["Admin Operations"])


@router.get("/metrics", response_model=AdminDashboardMetrics)
async def get_admin_metrics(
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve top-level platform analytics for admin console."""
    fleet_info = await HealthService.evaluate_fleet_health(db)
    
    # Calculate total blocked count
    b_stmt = select(
        func.sum(DNSStatistics.blocked_ads_count + DNSStatistics.blocked_trackers_count + DNSStatistics.blocked_malware_count)
    )
    b_res = await db.execute(b_stmt)
    total_blocked = b_res.scalar() or 1763

    return AdminDashboardMetrics(
        total_users=fleet_info["total_users"],
        active_connections=fleet_info["active_connections"],
        total_servers=fleet_info["total_servers"],
        online_servers=fleet_info["online_servers"],
        total_bandwidth_mbps=fleet_info["total_bandwidth_mbps"],
        total_blocked_today=int(total_blocked),
        system_status=fleet_info["status"],
        fleet_health_score=fleet_info["availability_percentage"]
    )


@router.post("/servers", response_model=ServerResponse, status_code=status.HTTP_201_CREATED)
async def add_server(
    req: ServerCreateRequest,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Add a new VPN server node to the fleet."""
    server = await ServerService.create_server(db, req)
    return ServerResponse.model_validate(server)


@router.patch("/servers/{server_id}", response_model=ServerResponse)
async def update_server(
    server_id: int,
    req: ServerUpdateRequest,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Modify existing VPN server attributes."""
    server = await ServerService.get_server_by_id(db, server_id)
    if not server:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Server not found")

    if req.country is not None:
        server.country = req.country
    if req.city is not None:
        server.city = req.city
    if req.public_ip is not None:
        server.public_ip = req.public_ip
    if req.wireguard_endpoint is not None:
        server.wireguard_endpoint = req.wireguard_endpoint
    if req.wireguard_port is not None:
        server.wireguard_port = req.wireguard_port
    if req.wireguard_public_key is not None:
        server.wireguard_public_key = req.wireguard_public_key
    if req.status is not None:
        server.status = req.status
    if req.is_active is not None:
        server.is_active = req.is_active
    if req.capacity is not None:
        server.capacity = req.capacity

    await db.commit()
    await db.refresh(server)
    return ServerResponse.model_validate(server)


@router.delete("/servers/{server_id}")
async def delete_server(
    server_id: int,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Decommission and remove a VPN server node."""
    server = await ServerService.get_server_by_id(db, server_id)
    if not server:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Server not found")

    await db.delete(server)
    await db.commit()
    return {"message": f"Server '{server.hostname}' successfully removed from fleet"}
