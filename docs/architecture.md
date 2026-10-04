# VORTEX VPN — Architecture Specification

## 1. High-Level Architecture Overview

VORTEX VPN is designed as a distributed, modular VPN and DNS privacy system separating the control plane, data plane, and client presentation layer.

```
┌────────────────────────────────────────────────────────┐
│                      CLIENT LAYER                      │
│  Android App (Kotlin / VpnService) │ Web & Desktop UI │
└──────────────────────────┬─────────────────────────────┘
                           │ HTTPS REST API
                           ▼
┌────────────────────────────────────────────────────────┐
│             FASTAPI CONTROL PLANE (PORT 8000)          │
│  - Argon2id Auth & JWT Issuance                        │
│  - Curve25519 Key Generation                           │
│  - Optimal Server Selection Engine                     │
│  - Client IP Subnet Pool Provisioning                  │
└────────────┬─────────────────────────────┬─────────────┘
             │                             │
             ▼                             ▼
┌─────────────────────────┐   ┌──────────────────────────┐
│   DATABASE & REDIS      │   │  TELEMETRY & FLEET MGMT  │
│   PostgreSQL / SQLite   │   │  Health Checks & Scoring │
└─────────────────────────┘   └────────────┬─────────────┘
                                           │
       ┌───────────────────────────────────┼───────────────────────────────────┐
       │                                   │                                   │
       ▼                                   ▼                                   ▼
┌─────────────────────────┐   ┌─────────────────────────┐   ┌─────────────────────────┐
│   GERMANY NODE (FRA)    │   │     USA NODE (NYC)      │   │    INDIA NODE (BOM)     │
│  - WireGuard wg0:51820  │   │  - WireGuard wg0:51820  │   │  - WireGuard wg0:51820  │
│  - Python DNS Blocker   │   │  - Python DNS Blocker   │   │  - Python DNS Blocker   │
│  - Server Agent         │   │  - Server Agent         │   │  - Server Agent         │
└─────────────────────────┘   └─────────────────────────┘   └─────────────────────────┘
```

---

## 2. Server Selection Algorithm

The `AUTO / FASTEST` server algorithm computes a composite score for each online node. **Lower scores represent superior connection quality**:

$$\text{Score} = (\text{Latency}_{\text{ms}} \times 1.0) + (\text{Loss}_{\%} \times 15.0) + (\text{ResourceLoad}_{\%} \times 0.8) + (\text{CapacityLoad}_{\%} \times 0.5)$$

Where:
- $\text{ResourceLoad} = (0.4 \times \text{CPU}) + (0.3 \times \text{RAM}) + (0.3 \times \frac{\text{ActiveConns}}{\text{Capacity}} \times 100)$
- Only nodes with `status == 'online'` and a heartbeat reported within the last $120\text{ seconds}$ are eligible.
- If a chosen node experiences sudden degradation, the control plane automatically returns a fallback healthy node.

---

## 3. WireGuard Encrypted Tunneling & Subnets

Each VPN server node manages an internal dual-stack subnet:
- **IPv4**: `10.8.0.0/24` (Gateway: `10.8.0.1`, Clients: `10.8.0.2` to `10.8.0.254`)
- **IPv6**: `fd42:42:42::/64` (Gateway: `fd42:42:42::1`, Clients: `fd42:42:42::2/128`)

Client configurations enforce zero-leak routing:
```ini
[Interface]
Address = 10.8.0.X/32, fd42:42:42::X/128
DNS = 10.8.0.1

[Peer]
PublicKey = <SERVER_PUBLIC_KEY>
Endpoint = <SERVER_IP>:51820
AllowedIPs = 0.0.0.0/0, ::/0
PersistentKeepalive = 25
```

---

## 4. DNS Ad/Tracker Filtering Engine

All client DNS queries are intercepted by the internal DNS gateway at `10.8.0.1:53` and redirected via firewall rules to port `5353`:
1. **Rule Evaluation**:
   - Explicit user **Allowlist** takes absolute precedence.
   - If present in the compiled **Blocklist** or custom block rules:
     - Returns `0.0.0.0` for type `A` queries.
     - Returns `::` for type `AAAA` queries.
     - Returns empty `NOERROR` for other query types.
2. **Upstream Forwarding**:
   - Allowed queries query the local in-memory TTL cache.
   - Cache misses are forwarded asynchronously to Quad9 (`9.9.9.9` with DNSSEC) and Cloudflare (`1.1.1.1`).
   - Responses are cached respecting TTL boundaries (minimum 60s, maximum 86400s).
