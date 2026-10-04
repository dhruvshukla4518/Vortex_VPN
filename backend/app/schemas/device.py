"""
VORTEX VPN - Device Schemas
"""
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class DeviceRegisterRequest(BaseModel):
    device_name: str = Field(..., max_length=100)
    device_uuid: str = Field(..., max_length=64)
    wireguard_public_key: str = Field(..., max_length=64)
    platform: str = Field(default="android", max_length=32)


class DeviceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    device_name: str
    device_uuid: str
    wireguard_public_key: str
    platform: str
    is_active: bool
    last_seen: datetime
    created_at: datetime
