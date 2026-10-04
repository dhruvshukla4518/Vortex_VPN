"""
VORTEX VPN - Authentication Schemas
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class RegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=128)
    device_name: Optional[str] = Field(default="My Device", max_length=100)
    platform: Optional[str] = Field(default="android", max_length=32)


class LoginRequest(BaseModel):
    email_or_username: str
    password: str
    device_name: Optional[str] = "My Device"
    platform: Optional[str] = "android"


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: int
    username: str
    email: str
    is_admin: bool


class TokenRefreshRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    username: str
    is_active: bool
    is_admin: bool
    created_at: datetime
