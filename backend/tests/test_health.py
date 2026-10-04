import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_health_check_endpoint(client: AsyncClient):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "fleet" in data
    assert data["fleet"]["total_servers"] >= 1
    assert data["fleet"]["availability_percentage"] >= 0.0
