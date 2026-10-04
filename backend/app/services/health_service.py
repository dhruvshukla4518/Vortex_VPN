"""
VORTEX VPN - Health & Telemetry Evaluation Service
Evaluates node responsiveness, flags stale heartbeats, and computes fleet health scores.
"""
from datetime import datetime, timezone, timedelta
from typing import Dict, Any
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.server import VPNServer
from backend.app.models.connection import VPNConnection
from backend.app.models.user import User


class HealthService:
    @staticmethod
    async def evaluate_fleet_health(db: AsyncSession) -> Dict[str, Any]:
        """
        Scan all VPN nodes. Mark servers with stale heartbeats (> 120s) as offline.
        Compute fleet availability metrics.
        """
        now = datetime.now(timezone.utc)
        stale_threshold = now - timedelta(seconds=120)

        stmt = select(VPNServer)
        result = await db.execute(stmt)
        servers = list(result.scalars().all())

        total = len(servers)
        online_count = 0
        total_bandwidth = 0.0
        total_active_connections = 0

        for s in servers:
            # Check if heartbeat is fresh (handle sqlite timezone-naive datetimes)
            lhc = s.last_health_check
            if lhc:
                if lhc.tzinfo is None:
                    lhc = lhc.replace(tzinfo=timezone.utc)
                if lhc < stale_threshold:
                    if s.status == "online":
                        s.status = "degraded"
            if s.status == "online":
                online_count += 1
            total_bandwidth += s.bandwidth_usage_mbps
            total_active_connections += s.active_connections

        await db.commit()

        # Total registered users count
        u_stmt = select(func.count(User.id))
        u_res = await db.execute(u_stmt)
        total_users = u_res.scalar() or 0

        # Total active connections
        c_stmt = select(func.count(VPNConnection.id)).where(VPNConnection.status == "connected")
        c_res = await db.execute(c_stmt)
        active_conns = c_res.scalar() or 0

        availability_pct = round((online_count / max(total, 1)) * 100, 1)

        return {
            "total_servers": total,
            "online_servers": online_count,
            "availability_percentage": availability_pct,
            "total_bandwidth_mbps": round(total_bandwidth, 1),
            "active_connections": active_conns,
            "total_users": total_users,
            "status": "HEALTHY" if availability_pct >= 66.0 else "DEGRADED"
        }
