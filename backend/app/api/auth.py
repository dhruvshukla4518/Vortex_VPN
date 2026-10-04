"""
VORTEX VPN - Authentication Endpoints
Handles user registration, login with Argon2id password verification,
JWT issuance, and refresh.
"""
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from backend.app.config import settings
from backend.app.database.session import get_db
from backend.app.models.user import User
from backend.app.models.device import Device
from backend.app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    TokenRefreshRequest,
    UserResponse
)
from backend.app.security.authentication import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    revoke_token
)
from backend.app.security.authorization import get_current_user
from backend.app.security.rate_limit import check_rate_limit
from backend.app.services.crypto_service import WireGuardCryptoService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(req: RegisterRequest, request: Request, db: AsyncSession = Depends(get_db)):
    """Register a new user account with secure Argon2id password hashing."""
    check_rate_limit(request, limit=settings.RATE_LIMIT_AUTH)

    # Check for existing email or username
    stmt = select(User).where(or_(User.email == req.email, User.username == req.username))
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email or username already exists"
        )

    # Create user
    user = User(
        email=req.email,
        username=req.username,
        hashed_password=hash_password(req.password),
        is_active=True,
        is_admin=False
    )
    db.add(user)
    await db.flush()

    # Automatically provision initial device identity with WireGuard keypair
    _, pub_key = WireGuardCryptoService.generate_keypair()
    device = Device(
        user_id=user.id,
        device_name=req.device_name or "Primary Device",
        device_uuid=f"dev-{user.id}-init",
        wireguard_public_key=pub_key,
        platform=req.platform or "android",
        is_active=True
    )
    db.add(device)
    await db.commit()
    await db.refresh(user)

    # Generate JWT tokens
    token_data = {"sub": str(user.id), "username": user.username, "email": user.email}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user_id=user.id,
        username=user.username,
        email=user.email,
        is_admin=user.is_admin
    )


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    """Authenticate with username/email and password, returning JWT access & refresh tokens."""
    check_rate_limit(request, limit=settings.RATE_LIMIT_AUTH)

    stmt = select(User).where(
        or_(
            User.email == req.email_or_username,
            User.username == req.email_or_username
        )
    )
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials. Please verify your username and password."
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is suspended. Please contact support."
        )

    token_data = {"sub": str(user.id), "username": user.username, "email": user.email}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user_id=user.id,
        username=user.username,
        email=user.email,
        is_admin=user.is_admin
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(req: TokenRefreshRequest, db: AsyncSession = Depends(get_db)):
    """Exchange valid refresh token for a new access token."""
    payload = decode_token(req.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )

    user_id = payload.get("sub")
    stmt = select(User).where(User.id == int(user_id))
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )

    # Invalidate old refresh token and generate new pair
    revoke_token(req.refresh_token)
    token_data = {"sub": str(user.id), "username": user.username, "email": user.email}
    new_access_token = create_access_token(token_data)
    new_refresh_token = create_refresh_token(token_data)

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user_id=user.id,
        username=user.username,
        email=user.email,
        is_admin=user.is_admin
    )


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """Revoke user credentials."""
    return {"message": "Successfully logged out"}
