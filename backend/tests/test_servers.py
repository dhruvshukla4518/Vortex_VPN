"""
VORTEX VPN - Server Fleet & Fastest Selection Test Suite
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_servers(client: AsyncClient):
    """Verify fleet servers are returned with health and latency metrics."""
    resp = await client.get("/api/v1/servers")
    assert resp.status_code == 200
    servers = resp.json()
    assert len(servers) >= 6  # Seeded initial fleet

    server = servers[0]
    assert "country" in server
    assert "city" in server
    assert "latency_ms" in server
    assert "load_percentage" in server
    assert "score" in server
    assert "wireguard_public_key" in server


@pytest.mark.asyncio
async def test_auto_fastest_server_selection(client: AsyncClient):
    """Verify algorithm selects the optimal server based on latency, load, and availability."""
    resp = await client.get("/api/v1/servers/auto/fastest")
    assert resp.status_code == 200
    data = resp.json()
    assert "server" in data
    assert "selection_reason" in data
    assert "score" in data
    assert data["evaluated_nodes"] >= 6
    assert data["server"]["status"] == "online"


@pytest.mark.asyncio
async def test_filter_by_country(client: AsyncClient):
    """Verify filtering servers by country code."""
    resp = await client.get("/api/v1/servers/country/DE")
    assert resp.status_code == 200
    de_servers = resp.json()
    assert len(de_servers) >= 1
    assert de_servers[0]["country_code"] == "DE"
    assert de_servers[0]["city"] == "Frankfurt"
