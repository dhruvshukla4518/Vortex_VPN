"""
VORTEX VPN - Rate Limiting
Implements sliding-window in-memory rate limiting with Redis fallback capability.
"""
import time
from collections import defaultdict
from typing import Dict, List
from fastapi import HTTPException, Request, status
from backend.app.config import settings

# In-memory sliding window store: ip -> list of timestamps
_request_history: Dict[str, List[float]] = defaultdict(list)


def check_rate_limit(request: Request, limit: int = settings.RATE_LIMIT_AUTH, window_seconds: int = 60) -> None:
    """
    Check if the client has exceeded the allowable request rate.
    Raises HTTP 429 Too Many Requests if exceeded.
    """
    # Extract client IP
    client_ip = request.client.host if request.client else "127.0.0.1"
    
    # Check X-Forwarded-For if behind reverse proxy
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        client_ip = forwarded_for.split(",")[0].strip()

    now = time.time()
    cutoff = now - window_seconds
    
    # Clean old requests
    timestamps = _request_history[client_ip]
    _request_history[client_ip] = [ts for ts in timestamps if ts > cutoff]
    
    # Check limit
    if len(_request_history[client_ip]) >= limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again shortly.",
            headers={"Retry-After": str(window_seconds)}
        )
    
    # Record current request
    _request_history[client_ip].append(now)
