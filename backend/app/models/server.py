"""
VORTEX VPN - Server Model
Stores information about VPN server nodes across different countries and their live health metrics.
"""
from datetime import datetime, timezone
from typing import List, TYPE_CHECKING
from sqlalchemy import String, Integer, Float, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from backend.app.models.connection import VPNConnection


class VPNServer(Base, TimestampMixin):
    __tablename__ = "vpn_servers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    country: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    country_code: Mapped[str] = mapped_column(String(4), index=True, nullable=False)  # DE, US, IN, GB, SG, NL
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    hostname: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    public_ip: Mapped[str] = mapped_column(String(45), nullable=False)  # IPv4 or IPv6
    wireguard_endpoint: Mapped[str] = mapped_column(String(255), nullable=False)
    wireguard_port: Mapped[int] = mapped_column(Integer, default=51820, nullable=False)
    wireguard_public_key: Mapped[str] = mapped_column(String(64), nullable=False)
    internal_subnet: Mapped[str] = mapped_column(String(64), default="10.8.0.0/24", nullable=False)
    
    # Operational Status: online, offline, maintenance, degraded
    status: Mapped[str] = mapped_column(String(32), default="online", index=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Real-time Metrics (reported by server agent)
    latency_ms: Mapped[float] = mapped_column(Float, default=45.0, nullable=False)
    packet_loss: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    cpu_usage: Mapped[float] = mapped_column(Float, default=15.0, nullable=False)
    memory_usage: Mapped[float] = mapped_column(Float, default=30.0, nullable=False)
    bandwidth_usage_mbps: Mapped[float] = mapped_column(Float, default=12.5, nullable=False)
    
    # Capacity
    capacity: Mapped[int] = mapped_column(Integer, default=1000, nullable=False)
    active_connections: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    last_health_check: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    connections: Mapped[List["VPNConnection"]] = relationship("VPNConnection", back_populates="server")

    @property
    def load_percentage(self) -> float:
        """Calculate combined server resource load."""
        if self.capacity <= 0:
            return 100.0
        conn_ratio = (self.active_connections / self.capacity) * 100
        # Weighted resource load: 40% CPU, 30% RAM, 30% Connection Capacity
        return round((self.cpu_usage * 0.4) + (self.memory_usage * 0.3) + (conn_ratio * 0.3), 1)

    @property
    def score(self) -> float:
        """
        Server selection algorithm score. Lower is better.
        Considers latency, packet loss, load percentage, and capacity availability.
        """
        if self.status != "online" or not self.is_active:
            return 999999.0
        
        # Factors:
        # Latency (weight 1.0)
        # Packet Loss penalty (weight 15.0 per %)
        # Resource Load penalty (weight 0.8 per %)
        # Full capacity penalty
        conn_load = (self.active_connections / max(self.capacity, 1)) * 100.0
        score_val = (
            (self.latency_ms * 1.0) +
            (self.packet_loss * 15.0) +
            (self.load_percentage * 0.8) +
            (conn_load * 0.5)
        )
        return round(score_val, 2)
