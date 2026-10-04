"""
VORTEX VPN - DNS Privacy & Blocker Endpoints
Telemetry, live blocked activity stream, and custom rule management.
"""
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.database.session import get_db
from backend.app.models.user import User
from backend.app.schemas.dns import (
    DNSStatsResponse,
    DNSActivityItem,
    DNSCustomRuleCreate,
    DNSCustomRuleResponse,
    DNSCategoryToggleRequest
)
from backend.app.security.authorization import get_current_active_user
from backend.app.services.dns_service import DNSService
from backend.app.services.blocklist_service import blocklist_manager

router = APIRouter(prefix="/dns", tags=["DNS Shield"])


@router.get("/statistics", response_model=DNSStatsResponse)
async def get_dns_statistics(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve aggregate ad, tracker, and malware blocking metrics."""
    return await DNSService.get_statistics(db, current_user)


@router.get("/activity", response_model=List[DNSActivityItem])
async def get_blocked_activity(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Fetch live stream of recently blocked domains (strictly blocked events, no history)."""
    activities = await DNSService.get_recent_activity(db, limit=20)
    return [DNSActivityItem.model_validate(a) for a in activities]


@router.get("/custom-rules", response_model=List[DNSCustomRuleResponse])
async def list_custom_rules(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """List custom allowlist and blocklist rules."""
    rules = await DNSService.list_custom_rules(db, current_user)
    return [DNSCustomRuleResponse.model_validate(r) for r in rules]


@router.post("/custom-rules", response_model=DNSCustomRuleResponse, status_code=status.HTTP_201_CREATED)
async def add_custom_rule(
    req: DNSCustomRuleCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Add a new custom rule to allow or block a domain."""
    rule = await DNSService.add_custom_rule(db, current_user, req)
    return DNSCustomRuleResponse.model_validate(rule)


@router.delete("/custom-rules/{rule_id}")
async def delete_custom_rule(
    rule_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a custom rule."""
    await DNSService.delete_custom_rule(db, current_user, rule_id)
    return {"message": "Rule removed successfully"}


@router.post("/categories/toggle")
async def toggle_category(
    req: DNSCategoryToggleRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Toggle a protection category (ads, trackers, malware, telemetry)."""
    return {
        "category": req.category,
        "enabled": req.enabled,
        "status": "updated"
    }


@router.get("/status")
async def get_dns_status():
    """Retrieve operational status and total loaded block rules."""
    return blocklist_manager.get_status()
