"""
VORTEX VPN - Configuration Management
Loads settings from environment variables and .env file with safe defaults.
"""
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Application
    APP_NAME: str = "VORTEX VPN"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    # Database
    # Defaults to SQLite async for zero-dependency local dev and testing.
    # Set to postgresql+asyncpg://... in production.
    DATABASE_URL: str = "sqlite+aiosqlite:///./vortex_vpn.db"

    # Redis
    REDIS_URL: Optional[str] = "redis://localhost:6379/0"

    # Security & JWT
    JWT_SECRET_KEY: str = Field(
        default="vortex-development-secret-key-min-32-chars-replace-in-prod",
        description="Secret key for signing JWT tokens"
    )
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    AGENT_SECRET_KEY: str = "vortex-agent-node-secret-key-change-in-production"

    # WireGuard Subnet Defaults
    WIREGUARD_IPV4_SUBNET: str = "10.8.0.0/24"
    WIREGUARD_IPV6_SUBNET: str = "fd42:42:42::/64"
    WIREGUARD_DEFAULT_PORT: int = 51820
    WIREGUARD_DNS_SERVER: str = "10.8.0.1"

    # DNS Blocker Engine
    DNS_BIND_HOST: str = "0.0.0.0"
    DNS_BIND_PORT: int = 5353
    DNS_UPSTREAM_PRIMARY: str = "9.9.9.9"
    DNS_UPSTREAM_SECONDARY: str = "1.1.1.1"
    DNS_CACHE_TTL_MIN: int = 300
    DNS_CACHE_MAX_ENTRIES: int = 50000

    # Rate Limiting (requests per minute)
    RATE_LIMIT_AUTH: int = 20
    RATE_LIMIT_DEFAULT: int = 120

    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:8000,http://127.0.0.1:8000,http://localhost:3000,http://localhost:8501"

    @property
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

    # Privacy
    PRIVACY_STRICT_DATA_MINIMIZATION: bool = True
    AUDIT_LOG_RETENTION_DAYS: int = 7


settings = Settings()
