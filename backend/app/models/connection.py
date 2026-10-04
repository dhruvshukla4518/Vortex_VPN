"""
VORTEX VPN - VPN Connection Model
Maintains active and historical connection sessions, IP allocation, and bandwidth counters.
"""
from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from backend.app.models.user import User
    from backend.app.models.server import VPNServer


class VPNConnection(Base, TimestampMixin):
    __tablename__ = "vpn_connections"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    device_id: Mapped[int] = mapped_column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), index=True, nullable=False)
    server_id: Mapped[int] = mapped_column(Integer, ForeignKey("vpn_servers.id", ondelete="CASCADE"), index=True, nullable=False)
    
    # Internal tunnel IP addresses assigned to this connection
    assigned_ipv4: Mapped[str] = mapped_column(String(45), nullable=False)
    assigned_ipv6: Mapped[str] = mapped_column(String(45), nullable=False)
    
    # Connection state: connecting, connected, disconnecting, disconnected, error
    status: Mapped[str] = mapped_column(String(32), default="connected", index=True, nullable=False)
    
    connected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    disconnected_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Traffic metrics in megabytes
    bytes_uploaded_mb: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    bytes_downloaded_mb: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    
    # Client endpoint IP address (anonymized for privacy: /24 subnet or truncated)
    client_public_ip_anonymized: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="connections")
    server: Mapped["VPNServer"] = relationship("VPNServer", back_populates="connections")

    @property
    def duration_seconds(self) -> int:
        end_time = self.disconnected_at or datetime.now(timezone.utc)
        start_time = self.connected_at
        if start_time is None:
            return 0
        if start_time.tzinfo is None and end_time.tzinfo is not None:
            end_time = end_time.replace(tzinfo=None)
        elif start_time.tzinfo is not None and end_time.tzinfo is None:
            start_time = start_time.replace(tzinfo=None)
        return max(0, int((end_time - start_time).total_seconds()))
