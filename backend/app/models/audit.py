"""
VORTEX VPN - Audit Log Model
Stores operational security events without capturing sensitive user payloads or credentials.
"""
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.models.base import Base


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    event_type: Mapped[str] = mapped_column(String(64), index=True, nullable=False)  # AUTH_LOGIN, VPN_CONNECT, KEY_ROTATE
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
        nullable=False
    )
