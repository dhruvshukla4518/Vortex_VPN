# VORTEX VPN — REST API Specification

The control plane provides a RESTful API serving both mobile/web clients and server agents.
Base path: `/api/v1`

---

## 1. Authentication (`/api/v1/auth`)

### `POST /auth/register`
Register a new user account and provision default WireGuard credentials.
- **Request Body**:
  ```json
  {
    "email": "user@example.com",
    "username": "myusername",
    "password": "SecurePassword123!",
    "device_name": "Pixel 8 Pro",
    "platform": "android"
  }
  ```
- **Response** (`201 Created`):
  ```json
  {
    "access_token": "eyJhbGciOi...",
    "refresh_token": "eyJhbGciOi...",
    "token_type": "bearer",
    "expires_in": 900,
    "user_id": 1,
    "username": "myusername",
    "email": "user@example.com",
    "is_admin": false
  }
  ```

### `POST /auth/login`
Authenticate with email/username and password.
- **Request Body**:
  ```json
  {
    "email_or_username": "user@example.com",
    "password": "SecurePassword123!"
  }
  ```

### `POST /auth/refresh`
Exchange a refresh token for a newly signed access token.

---

## 2. Server Fleet (`/api/v1/servers`)

### `GET /servers`
List all active VPN nodes with live latency, load percentage, and capacity.

### `GET /servers/auto/fastest`
Evaluate all healthy nodes and return the mathematically optimal server.
- **Query Params**: `country_code` (optional, e.g. `DE`, `US`)
- **Response**:
  ```json
  {
    "server": {
      "id": 1,
      "country": "Germany",
      "country_code": "DE",
      "city": "Frankfurt",
      "latency_ms": 38.0,
      "load_percentage": 24.5,
      "score": 62.4
    },
    "selection_reason": "Selected Frankfurt, Germany with optimal score of 62.4",
    "score": 62.4,
    "evaluated_nodes": 6
  }
  ```

---

## 3. VPN Operations (`/api/v1/vpn`)

### `POST /vpn/connect`
Establish a session and generate a ready-to-use WireGuard configuration.
- **Headers**: `Authorization: Bearer <JWT>`
- **Request Body**:
  ```json
  {
    "server_id": 1,
    "country_code": "DE"
  }
  ```
- **Response**:
  ```json
  {
    "connection_id": 42,
    "server_id": 1,
    "server_country": "Germany",
    "server_city": "Frankfurt",
    "server_latency_ms": 38.0,
    "status": "connected",
    "assigned_ipv4": "10.8.0.2/32",
    "assigned_ipv6": "fd42:42:42::2/128",
    "wireguard_config": {
      "raw_config": "[Interface]\nPrivateKey = ...\nAddress = 10.8.0.2/32\nDNS = 10.8.0.1\n\n[Peer]\n..."
    }
  }
  ```

### `POST /vpn/disconnect`
Terminate an active connection and submit transfer byte metrics.

### `GET /vpn/status`
Retrieve current connection state, live duration, and throughput metrics.

### `GET /vpn/diagnostics`
Run real-time diagnostics on tunnel status, DNS leak prevention, and IPv6 security.

---

## 4. DNS Shield (`/api/v1/dns`)

### `GET /dns/statistics`
Retrieve aggregate counts of blocked ads, trackers, and malware domains.

### `GET /dns/activity`
Retrieve live stream of recently blocked domains (strictly blocked events, no personal history).

### `POST /dns/custom-rules`
Add a custom allowlist or blocklist rule.

---

## 5. Health & Heartbeat (`/api/v1/health`)

### `POST /health/heartbeat`
Authenticated endpoint for remote server agents.
- **Headers**: `X-Agent-Key: <AGENT_SECRET_KEY>`
- **Request Body**:
  ```json
  {
    "hostname": "de-fra-01.vortexvpn.net",
    "latency_ms": 38.0,
    "packet_loss": 0.0,
    "cpu_usage": 18.2,
    "memory_usage": 34.0,
    "bandwidth_usage_mbps": 22.4,
    "active_connections": 14,
    "wireguard_status": "active"
  }
  ```
