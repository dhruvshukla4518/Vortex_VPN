"""
VORTEX VPN - VPN Connection Lifecycle & WireGuard Config Test Suite
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_vpn_connect_and_disconnect(client: AsyncClient):
    """Test full VPN connect workflow, config generation, and disconnect."""
    # 1. Register user
    reg_resp = await client.post("/api/v1/auth/register", json={
        "email": "vpnuser@vortexvpn.net",
        "username": "vpnmaster",
        "password": "SecurePassword987!"
    })
    token = reg_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Check initial status (Disconnected)
    status_resp = await client.get("/api/v1/vpn/status", headers=headers)
    assert status_resp.status_code == 200
    assert status_resp.json()["is_connected"] is False

    # 3. Connect to AUTO / Fastest server
    conn_resp = await client.post("/api/v1/vpn/connect", json={}, headers=headers)
    assert conn_resp.status_code == 200
    conn_data = conn_resp.json()
    assert conn_data["status"] == "connected"
    assert "connection_id" in conn_data
    assert "assigned_ipv4" in conn_data
    assert "wireguard_config" in conn_data

    # Verify synthesized WireGuard configuration
    wg_config = conn_data["wireguard_config"]
    assert "[Interface]" in wg_config["raw_config"]
    assert "[Peer]" in wg_config["raw_config"]
    assert "DNS = 10.8.0.1" in wg_config["raw_config"]
    assert "AllowedIPs = 0.0.0.0/0, ::/0" in wg_config["raw_config"]

    # 4. Check status while connected
    connected_status = await client.get("/api/v1/vpn/status", headers=headers)
    assert connected_status.status_code == 200
    s_data = connected_status.json()
    assert s_data["is_connected"] is True
    assert s_data["server_country"] is not None
    assert s_data["dns_protection"] is True
    assert s_data["leak_protection_status"] == "PASS"

    # 5. Check security diagnostics
    diag_resp = await client.get("/api/v1/vpn/diagnostics", headers=headers)
    assert diag_resp.status_code == 200
    assert diag_resp.json()["dns_leak_status"] == "PASS"
    assert diag_resp.json()["kill_switch_ready"] is True

    # 6. Disconnect
    disconn_resp = await client.post(
        "/api/v1/vpn/disconnect",
        json={"connection_id": conn_data["connection_id"], "bytes_uploaded_mb": 12.4, "bytes_downloaded_mb": 48.2},
        headers=headers
    )
    assert disconn_resp.status_code == 200
    assert disconn_resp.json()["is_connected"] is False
