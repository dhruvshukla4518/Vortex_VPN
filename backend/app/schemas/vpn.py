"""
VORTEX VPN - VPN Connection & WireGuard Schemas
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class VPNConnectRequest(BaseModel):
    server_id: Optional[int] = None  # None indicates AUTO / Fastest
    country_code: Optional[str] = None  # Specific country request
    device_uuid: Optional[str] = None
    client_wireguard_public_key: Optional[str] = None


class WireGuardConfigResponse(BaseModel):
    interface_private_key: Optional[str] = None  # Only returned if generated on-the-fly
    interface_address_ipv4: str
    interface_address_ipv6: str
    dns_servers: str
    peer_public_key: str
    peer_endpoint: str
    allowed_ips: str
    persistent_keepalive: int = 25
    raw_config: str  # Ready-to-use wg0.conf text format


class VPNConnectResponse(BaseModel):
    connection_id: int
    server_id: int
    server_country: str
    server_country_code: str
    server_city: str
    server_latency_ms: float
    status: str
    assigned_ipv4: str
    assigned_ipv6: str
    wireguard_config: WireGuardConfigResponse
    kill_switch_enabled: bool = True
    dns_protection_enabled: bool = True


class VPNDisconnectRequest(BaseModel):
    connection_id: Optional[int] = None
    bytes_uploaded_mb: Optional[float] = 0.0
    bytes_downloaded_mb: Optional[float] = 0.0


class VPNStatusResponse(BaseModel):
    is_connected: bool
    connection_id: Optional[int] = None
    status: str  # disconnected, connecting, connected, reconnecting, error
    server_country: Optional[str] = None
    server_city: Optional[str] = None
    server_latency_ms: Optional[float] = None
    duration_seconds: int = 0
    bytes_uploaded_mb: float = 0.0
    bytes_downloaded_mb: float = 0.0
    dns_protection: bool = True
    kill_switch_active: bool = False
    leak_protection_status: str = "PASS"  # PASS, FAIL, UNKNOWN


class DiagnosticResult(BaseModel):
    vpn_status: str
    dns_resolver: str
    dns_leak_status: str  # PASS, FAIL, UNKNOWN
    ipv4_status: str
    ipv6_status: str
    kill_switch_ready: bool
    handshake_status: str
