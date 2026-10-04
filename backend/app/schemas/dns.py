"""
VORTEX VPN - DNS Schemas
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class DNSStatsResponse(BaseModel):
    total_blocked: int
    ads_blocked: int
    trackers_blocked: int
    malware_blocked: int
    total_queries: int
    protection_enabled: bool = True
    ad_blocking_enabled: bool = True
    tracker_blocking_enabled: bool = True
    malware_blocking_enabled: bool = True


class DNSActivityItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    domain: str
    category: str
    blocked_at: datetime


class DNSCustomRuleCreate(BaseModel):
    domain: str = Field(..., min_length=3, max_length=255)
    action: str = Field(default="block", pattern="^(allow|block)$")
    category: Optional[str] = Field(default="custom", max_length=32)


class DNSCustomRuleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    domain: str
    action: str
    category: str
    is_active: bool
    created_at: datetime


class DNSCategoryToggleRequest(BaseModel):
    category: str = Field(..., pattern="^(ads|trackers|malware|telemetry)$")
    enabled: bool


class DNSBlocklistFeedResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    url: str
    category: str
    rule_count: int
    version: str
    is_enabled: bool
    last_updated: datetime
