"""
VORTEX VPN - Authentication & Device Test Suite
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_user_registration_and_login(client: AsyncClient):
    """Test full registration and login cycle."""
    email = "testuser@vortexvpn.net"
    password = "SuperSecurePassword123!"
    username = "testpilot"

    # 1. Register User
    reg_resp = await client.post("/api/v1/auth/register", json={
        "email": email,
        "username": username,
        "password": password,
        "device_name": "Test Android Phone",
        "platform": "android"
    })
    assert reg_resp.status_code == 201
    data = reg_resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["username"] == username

    # 2. Duplicate Registration Rejection
    dup_resp = await client.post("/api/v1/auth/register", json={
        "email": email,
        "username": "anothername",
        "password": password
    })
    assert dup_resp.status_code == 409

    # 3. Successful Login
    login_resp = await client.post("/api/v1/auth/login", json={
        "email_or_username": email,
        "password": password
    })
    assert login_resp.status_code == 200
    login_data = login_resp.json()
    assert "access_token" in login_data
    access_token = login_data["access_token"]
    refresh_token = login_data["refresh_token"]

    # 4. Token Refresh
    refresh_resp = await client.post("/api/v1/auth/refresh", json={
        "refresh_token": refresh_token
    })
    assert refresh_resp.status_code == 200
    assert "access_token" in refresh_resp.json()

    # 5. Invalid Password Rejection
    bad_login = await client.post("/api/v1/auth/login", json={
        "email_or_username": email,
        "password": "WrongPassword!"
    })
    assert bad_login.status_code == 401

    # 6. Authenticated User Profile
    headers = {"Authorization": f"Bearer {access_token}"}
    me_resp = await client.get("/api/v1/users/me", headers=headers)
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == email
