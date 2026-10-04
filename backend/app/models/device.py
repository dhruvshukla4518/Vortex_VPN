"""
VORTEX VPN - Device Model
Tracks registered user devices, their platform, and WireGuard public keys.
"""
from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from backend.app.models.user import User


class Device(Base, TimestampMixin):
    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    device_name: Mapped[str] = mapped_column(String(100), nullable=False)
    device_uuid: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    wireguard_public_key: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    platform: Mapped[str] = mapped_column(String(32), default="android", nullable=False)  # android, windows, linux, macos
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="devices")
