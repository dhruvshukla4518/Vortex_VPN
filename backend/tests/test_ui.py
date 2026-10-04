"""
VORTEX VPN - UI Static Serving Verification Test
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_ui_index_served(client: AsyncClient):
    """Verify that root endpoint serves the VORTEX VPN client UI HTML."""
    resp = await client.get("/")
    assert resp.status_code == 200
    assert "VORTEX VPN" in resp.text
    assert "vortex-hero-container" in resp.text
    assert "hero-connect-btn" in resp.text
