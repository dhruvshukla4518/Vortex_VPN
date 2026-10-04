"""
VORTEX VPN - Admin Dashboard Schemas
"""
from typing import List, Dict, Any
from pydantic import BaseModel
from backend.app.schemas.server import ServerResponse


class AdminDashboardMetrics(BaseModel):
    total_users: int
    active_connections: int
    total_servers: int
    online_servers: int
    total_bandwidth_mbps: float
    total_blocked_today: int
    system_status: str
    fleet_health_score: float


class AdminServerStats(BaseModel):
    servers: List[ServerResponse]
    metrics: AdminDashboardMetrics
    recent_audit_events: List[Dict[str, Any]]
