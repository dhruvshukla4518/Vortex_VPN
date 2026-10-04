"""
VORTEX VPN - Device Management Endpoints
Enables users to register devices, inspect active devices, and revoke access.
"""
from typing import List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from backend.app.database.session import get_db
from backend.app.models.user import User
from backend.app.models.device import Device
from backend.app.schemas.device import DeviceRegisterRequest, DeviceResponse
from backend.app.security.authorization import get_current_active_user

router = APIRouter(prefix="/devices", tags=["Devices"])


@router.get("", response_model=List[DeviceResponse])
async def list_devices(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """List all registered devices for the current user."""
    stmt = select(Device).where(
        and_(Device.user_id == current_user.id, Device.is_active == True)
    ).order_by(Device.last_seen.desc())
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.post("", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED)
async def register_device(
    req: DeviceRegisterRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Register a new device with its client WireGuard public key."""
    # Check if device UUID already exists
    stmt = select(Device).where(Device.device_uuid == req.device_uuid)
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()

    if existing:
        existing.device_name = req.device_name
        existing.wireguard_public_key = req.wireguard_public_key
        existing.platform = req.platform
        existing.is_active = True
        existing.last_seen = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(existing)
        return existing

    device = Device(
        user_id=current_user.id,
        device_name=req.device_name,
        device_uuid=req.device_uuid,
        wireguard_public_key=req.wireguard_public_key,
        platform=req.platform,
        is_active=True,
        last_seen=datetime.now(timezone.utc)
    )
    db.add(device)
    await db.commit()
    await db.refresh(device)
    return device


@router.delete("/{device_id}")
async def revoke_device(
    device_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Revoke access for a specific device."""
    stmt = select(Device).where(
        and_(Device.id == device_id, Device.user_id == current_user.id)
    )
    result = await db.execute(stmt)
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")

    device.is_active = False
    await db.commit()
    return {"message": f"Device '{device.device_name}' revoked successfully"}
