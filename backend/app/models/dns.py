"""
VORTEX VPN - DNS Models
Stores aggregate DNS blocking statistics, custom allow/block rules, and blocklist feed metadata.
"""
from datetime import datetime, timezone, date
from typing import Optional
from sqlalchemy import String, Integer, Boolean, DateTime, Date, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.models.base import Base, TimestampMixin


class DNSStatistics(Base, TimestampMixin):
    __tablename__ = "dns_statistics"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    device_id: Mapped[int] = mapped_column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), index=True, nullable=False)
    stat_date: Mapped[date] = mapped_column(Date, default=lambda: datetime.now(timezone.utc).date(), index=True, nullable=False)
    
    blocked_ads_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    blocked_trackers_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    blocked_malware_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_queries_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    @property
    def total_blocked(self) -> int:
        return self.blocked_ads_count + self.blocked_trackers_count + self.blocked_malware_count


class DNSCustomRule(Base, TimestampMixin):
    __tablename__ = "dns_custom_rules"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    domain: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    action: Mapped[str] = mapped_column(String(16), default="block", nullable=False)  # 'allow' or 'block'
    category: Mapped[str] = mapped_column(String(32), default="custom", nullable=False)  # ads, trackers, malware, custom
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class DNSBlocklistFeed(Base, TimestampMixin):
    __tablename__ = "dns_blocklist_feeds"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    category: Mapped[str] = mapped_column(String(32), default="ads", nullable=False)
    rule_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    version: Mapped[str] = mapped_column(String(64), default="1.0.0", nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    last_error: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)


class DNSBlockedActivity(Base):
    """
    Privacy-conscious live stream of blocked domains only.
    Purged periodically (configurable retention, default 24h).
    """
    __tablename__ = "dns_blocked_activity"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    device_id: Mapped[int] = mapped_column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), index=True, nullable=False)
    domain: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(32), default="tracker", nullable=False)  # ads, tracker, malware
    blocked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
        nullable=False
    )
