"""
VORTEX VPN - Cryptographic Authentication & Password Security
Uses Argon2id for password hashing and PyJWT for secure token issuance.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, Set
import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHashError
from backend.app.config import settings

# Argon2id password hasher configuration (Memory: 64MB, Iterations: 3, Parallelism: 4)
ph = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=4, hash_len=32)

# In-memory revoked tokens blacklist for immediate revocation
_revoked_tokens: Set[str] = set()


def hash_password(password: str) -> str:
    """Hash password using modern Argon2id algorithm."""
    return ph.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against Argon2id hash."""
    try:
        return ph.verify(hashed_password, plain_password)
    except (VerifyMismatchError, InvalidHashError):
        return False


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create signed JWT access token."""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "iat": now,
        "exp": expire,
        "type": "access"
    })
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create signed JWT refresh token."""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({
        "iat": now,
        "exp": expire,
        "type": "refresh"
    })
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and validate JWT token signature and expiration."""
    if token in _revoked_tokens:
        return None
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None


def revoke_token(token: str) -> None:
    """Add token to revocation set."""
    _revoked_tokens.add(token)
