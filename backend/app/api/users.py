"""
VORTEX VPN - User Profile Endpoints
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.database.session import get_db
from backend.app.models.user import User
from backend.app.schemas.auth import UserResponse
from backend.app.security.authorization import get_current_active_user

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_active_user)):
    """Fetch profile information for authenticated user."""
    return current_user
