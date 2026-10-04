"""
VORTEX VPN - DNS Statistics & Custom Rules Test Suite
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_dns_statistics_and_custom_rules(client: AsyncClient):
    """Test DNS statistics retrieval and custom allow/block rule management."""
    # 1. Register user
    reg_resp = await client.post("/api/v1/auth/register", json={
        "email": "dnsuser@vortexvpn.net",
        "username": "dnsprotector",
        "password": "SecurePassword321!"
    })
    token = reg_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Get DNS statistics
    stats_resp = await client.get("/api/v1/dns/statistics", headers=headers)
    assert stats_resp.status_code == 200
    stats = stats_resp.json()
    assert stats["total_blocked"] > 0
    assert stats["ads_blocked"] > 0
    assert stats["trackers_blocked"] > 0
    assert stats["protection_enabled"] is True

    # 3. Add Custom Allowlist Rule
    add_rule_resp = await client.post("/api/v1/dns/custom-rules", json={
        "domain": "my-allowed-workplace.com",
        "action": "allow",
        "category": "work"
    }, headers=headers)
    assert add_rule_resp.status_code == 201
    rule_data = add_rule_resp.json()
    rule_id = rule_data["id"]
    assert rule_data["domain"] == "my-allowed-workplace.com"
    assert rule_data["action"] == "allow"

    # 4. List Custom Rules
    list_rules_resp = await client.get("/api/v1/dns/custom-rules", headers=headers)
    assert list_rules_resp.status_code == 200
    rules = list_rules_resp.json()
    assert len(rules) >= 1

    # 5. Delete Custom Rule
    del_resp = await client.delete(f"/api/v1/dns/custom-rules/{rule_id}", headers=headers)
    assert del_resp.status_code == 200

    # 6. Fetch live blocked activity stream
    activity_resp = await client.get("/api/v1/dns/activity", headers=headers)
    assert activity_resp.status_code == 200
    activities = activity_resp.json()
    assert len(activities) > 0
    assert "domain" in activities[0]
    assert "category" in activities[0]
