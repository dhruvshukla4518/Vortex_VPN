"""
VORTEX VPN - Server Schemas
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class ServerBase(BaseModel):
    country: str
    country_code: str = Field(..., max_length=4)
    city: str
    hostname: str
    public_ip: str
    wireguard_endpoint: str
    wireguard_port: int = 51820
    wireguard_public_key: str
    internal_subnet: str = "10.8.0.0/24"
    capacity: int = 1000


class ServerCreateRequest(ServerBase):
    pass


class ServerUpdateRequest(BaseModel):
    country: Optional[str] = None
    city: Optional[str] = None
    public_ip: Optional[str] = None
    wireguard_endpoint: Optional[str] = None
    wireguard_port: Optional[int] = None
    wireguard_public_key: Optional[str] = None
    status: Optional[str] = None
    is_active: Optional[bool] = None
    capacity: Optional[int] = None


class ServerHealthReport(BaseModel):
    hostname: str
    latency_ms: float
    packet_loss: float
    cpu_usage: float
    memory_usage: float
    bandwidth_usage_mbps: float
    active_connections: int
    wireguard_status: str = "active"


class ServerResponse(ServerBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str
    is_active: bool
    latency_ms: float
    packet_loss: float
    cpu_usage: float
    memory_usage: float
    bandwidth_usage_mbps: float
    active_connections: int
    load_percentage: float
    score: float
    last_health_check: datetime
    created_at: datetime


class FastestServerSelectionResponse(BaseModel):
    server: ServerResponse
    selection_reason: str
    score: float
    evaluated_nodes: int
