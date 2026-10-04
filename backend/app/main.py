"""
VORTEX VPN - Main FastAPI Application
Production-grade ASGI application powering the VORTEX VPN control plane.
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.app.config import settings
from backend.app.database.session import init_db, AsyncSessionLocal
from backend.app.services.server_service import ServerService
from backend.app.services.blocklist_service import blocklist_manager
from backend.app.security.headers import SecurityHeadersMiddleware

# Import API Routers
from backend.app.api.auth import router as auth_router
from backend.app.api.users import router as users_router
from backend.app.api.devices import router as devices_router
from backend.app.api.servers import router as servers_router
from backend.app.api.vpn import router as vpn_router
from backend.app.api.dns import router as dns_router
from backend.app.api.admin import router as admin_router
from backend.app.api.health import router as health_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle management."""
    # 1. Initialize Database Tables
    await init_db()

    # 2. Seed Initial VPN Fleet Nodes if needed
    async with AsyncSessionLocal() as session:
        await ServerService.seed_initial_fleet(session)

    # 3. Load DNS Blocklist Cache
    blocklist_manager.load_from_cache()

    yield
    # Shutdown procedures (clean sockets, close pools)


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Production-grade WireGuard VPN Control Plane & DNS Privacy Shield API",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Apply Security Headers Middleware
app.add_middleware(SecurityHeadersMiddleware)

# Apply CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Endpoints
API_V1_PREFIX = "/api/v1"
app.include_router(auth_router, prefix=API_V1_PREFIX)
app.include_router(users_router, prefix=API_V1_PREFIX)
app.include_router(devices_router, prefix=API_V1_PREFIX)
app.include_router(servers_router, prefix=API_V1_PREFIX)
app.include_router(vpn_router, prefix=API_V1_PREFIX)
app.include_router(dns_router, prefix=API_V1_PREFIX)
app.include_router(admin_router, prefix=API_V1_PREFIX)
app.include_router(health_router, prefix=API_V1_PREFIX)
app.include_router(health_router)  # also expose /health at root


from fastapi.exception_handlers import http_exception_handler, request_validation_exception_handler
from fastapi.exceptions import RequestValidationError, HTTPException


# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    if isinstance(exc, HTTPException):
        return await http_exception_handler(request, exc)
    if isinstance(exc, RequestValidationError):
        return await request_validation_exception_handler(request, exc)
    # Log error safely without exposing raw internal stack traces in production
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal service error occurred. Please try again later."}
    )


# Mount Static Client UI for web and Android WebView access
client_ui_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "client-ui"))
if os.path.isdir(client_ui_path):
    app.mount("/", StaticFiles(directory=client_ui_path, html=True), name="client-ui")
