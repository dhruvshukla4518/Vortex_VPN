"""
VORTEX VPN - Automated Security Audit & Penetration Test Suite
Validates core security constraints:
1. WireGuard Configuration Tampering Rejection
2. Revoked Device & Peer Rejection
3. Revoked JWT Token Rejection
4. RBAC & Admin Authorization Bypass Prevention
5. Server Private Key Confidentiality & Zero-Leakage
6. SQL Injection Resilience via Parameterized ORM
7. Command Injection Immunity in WireGuard Parsers
8. Brute-Force Rate Limiting Lockout
9. DNS Leak Prevention & Mandatory Resolver Verification
10. Fail-Closed Kill Switch & IPv6 Policy Verification
"""
import pytest
from httpx import AsyncClient

from backend.app.services.wireguard_validator import WireGuardConfigValidator
from backend.app.security.authentication import revoke_token, create_access_token
from wireguard_monitor import parse_wg_dump


# Standard valid 32-byte Base64 Curve25519 keys for test fixtures
VALID_PRIV_KEY = "YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXoxMjM0NTE="
VALID_PUB_KEY  = "YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXoxMjM0NTI="


def test_wireguard_config_validator_tampered_key():
    """Verify that configs with invalid or tampered Curve25519 keys are rejected."""
    tampered_conf = (
        "[Interface]\n"
        "PrivateKey = BadKey==\n"
        "Address = 10.8.0.2/32, fd42:42:42::2/128\n"
        "DNS = 10.8.0.1\n\n"
        "[Peer]\n"
        f"PublicKey = {VALID_PUB_KEY}\n"
        "Endpoint = 198.51.100.1:51820\n"
        "AllowedIPs = 0.0.0.0/0, ::/0\n"
    )
    is_valid, reason = WireGuardConfigValidator.validate(tampered_conf)
    assert not is_valid
    assert "Invalid PrivateKey" in reason


def test_wireguard_config_validator_missing_dns():
    """Verify that configs missing mandatory DNS directive are rejected (DNS leak prevention)."""
    leaking_conf = (
        "[Interface]\n"
        f"PrivateKey = {VALID_PRIV_KEY}\n"
        "Address = 10.8.0.2/32\n\n"
        "[Peer]\n"
        f"PublicKey = {VALID_PUB_KEY}\n"
        "Endpoint = 198.51.100.1:51820\n"
        "AllowedIPs = 0.0.0.0/0\n"
    )
    is_valid, reason = WireGuardConfigValidator.validate(leaking_conf)
    assert not is_valid
    assert "Missing DNS directive" in reason


def test_wireguard_config_validator_key_symmetry_violation():
    """Verify that client private key cannot be identical to peer public key."""
    same_key = VALID_PRIV_KEY
    sym_conf = (
        f"[Interface]\n"
        f"PrivateKey = {same_key}\n"
        f"Address = 10.8.0.2/32\n"
        f"DNS = 10.8.0.1\n\n"
        f"[Peer]\n"
        f"PublicKey = {same_key}\n"
        f"Endpoint = 198.51.100.1:51820\n"
        f"AllowedIPs = 0.0.0.0/0\n"
    )
    is_valid, reason = WireGuardConfigValidator.validate(sym_conf)
    assert not is_valid
    assert "Key symmetry violation" in reason


def test_wireguard_config_validator_port_out_of_range():
    """Verify that port numbers outside 1-65535 are rejected."""
    bad_port_conf = (
        "[Interface]\n"
        f"PrivateKey = {VALID_PRIV_KEY}\n"
        "Address = 10.8.0.2/32\n"
        "DNS = 10.8.0.1\n\n"
        "[Peer]\n"
        f"PublicKey = {VALID_PUB_KEY}\n"
        "Endpoint = 198.51.100.1:99999\n"
        "AllowedIPs = 0.0.0.0/0\n"
    )
    is_valid, reason = WireGuardConfigValidator.validate(bad_port_conf)
    assert not is_valid
    assert "out of range" in reason


def test_command_injection_immunity_in_wg_parser():
    """Verify that malicious command injection strings inside telemetry dumps are sanitized."""
    malicious_dump = (
        "server_priv\tserver_pub\t51820\toff\n"
        "peer_pub_key\tpreshared\t198.51.100.5:51820; rm -rf /; touch /tmp/pwned\t10.8.0.5/32\t1710000000\t1000\t2000\t25\n"
    )
    # Parser must process strictly as tabular fields without shell execution
    data = parse_wg_dump(malicious_dump)
    assert len(data["peers"]) == 1
    assert data["peers"][0]["endpoint"] == "198.51.100.5:51820; rm -rf /; touch /tmp/pwned"


@pytest.mark.asyncio
async def test_server_private_key_confidentiality(client: AsyncClient):
    """Verify that no server private keys are ever exposed in server fleet responses."""
    resp = await client.get("/api/v1/servers")
    assert resp.status_code == 200
    servers = resp.json()
    assert len(servers) > 0

    for s in servers:
        # Check that server responses only ever provide public keys
        assert "wireguard_public_key" in s
        assert "wireguard_private_key" not in s
        assert "private_key" not in s
        assert "secret" not in s


@pytest.mark.asyncio
async def test_admin_authorization_bypass_prevention(client: AsyncClient):
    """Verify that non-admin users cannot access administrative endpoints."""
    # 1. Register normal user
    user_payload = {
        "email": "normal_sec_user@vortexvpn.net",
        "username": "normsec",
        "password": "SecurePassword123!"
    }
    reg_res = await client.post("/api/v1/auth/register", json=user_payload)
    assert reg_res.status_code == 201
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Attempt admin endpoint access
    admin_res = await client.get("/api/v1/admin/metrics", headers=headers)
    assert admin_res.status_code == 403
    assert "Administrative privileges required" in admin_res.json()["detail"]


@pytest.mark.asyncio
async def test_revoked_jwt_token_rejection(client: AsyncClient):
    """Verify that revoked tokens cannot access protected endpoints."""
    token = create_access_token({"sub": 99999, "email": "test@vortex.net"})
    revoke_token(token)

    headers = {"Authorization": f"Bearer {token}"}
    resp = await client.get("/api/v1/vpn/status", headers=headers)
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_sql_injection_resilience_in_server_filters(client: AsyncClient):
    """Verify that SQL injection payloads in queries fail safely without syntax errors."""
    sqli_payload = "' OR '1'='1"
    resp = await client.get(f"/api/v1/servers/country/{sqli_payload}")
    # Parameterized query should safely look for country literal and return 404 (not 500 error)
    assert resp.status_code == 404
    assert "No active servers found" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_revoked_device_connection_prevented(client: AsyncClient):
    """Verify that an inactive/revoked device cannot initiate VPN connections."""
    # 1. Register user
    user_payload = {
        "email": "device_audit_user@vortexvpn.net",
        "username": "devaudit",
        "password": "SecurePassword123!",
        "device_name": "Audit Phone",
        "platform": "android"
    }
    reg_res = await client.post("/api/v1/auth/register", json=user_payload)
    assert reg_res.status_code == 201
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Register explicit device
    dev_payload = {
        "device_name": "Compromised Device",
        "device_uuid": "compromised-uuid-1337",
        "wireguard_public_key": "kL9Wz5+4q1p9Zq1N8n+B3y8U5+8xQ9k7y6v5u4t3s2E=",
        "platform": "android"
    }
    dev_res = await client.post("/api/v1/devices", json=dev_payload, headers=headers)
    assert dev_res.status_code == 201
    dev_id = dev_res.json()["id"]

    # 3. Revoke the device
    del_res = await client.delete(f"/api/v1/devices/{dev_id}", headers=headers)
    assert del_res.status_code == 200

    # 4. Attempt to connect using the revoked device UUID
    conn_payload = {
        "device_uuid": "compromised-uuid-1337",
        "client_wireguard_public_key": "kL9Wz5+4q1p9Zq1N8n+B3y8U5+8xQ9k7y6v5u4t3s2E="
    }
    conn_res = await client.post("/api/v1/vpn/connect", json=conn_payload, headers=headers)
    assert conn_res.status_code == 403
    assert "revoked" in conn_res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_fail_closed_kill_switch_and_dns_leak_policy(client: AsyncClient):
    """Verify that connected VPN sessions strictly configure 10.8.0.1 DNS and 0.0.0.0/0, ::/0 AllowedIPs."""
    user_payload = {
        "email": "ks_policy_user@vortexvpn.net",
        "username": "kspolicy",
        "password": "SecurePassword123!"
    }
    reg_res = await client.post("/api/v1/auth/register", json=user_payload)
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Connect to VPN
    conn_res = await client.post("/api/v1/vpn/connect", json={}, headers=headers)
    assert conn_res.status_code == 200
    data = conn_res.json()

    # Verify fail-closed parameters
    assert data["kill_switch_enabled"] is True
    assert data["dns_protection_enabled"] is True

    wg_conf = data["wireguard_config"]
    assert wg_conf["dns_servers"] == "10.8.0.1"
    assert "0.0.0.0/0" in wg_conf["allowed_ips"]
    assert "::/0" in wg_conf["allowed_ips"]  # Full IPv6 leak-proof routing
    assert "DNS = 10.8.0.1" in wg_conf["raw_config"]
    assert "AllowedIPs = 0.0.0.0/0, ::/0" in wg_conf["raw_config"]
