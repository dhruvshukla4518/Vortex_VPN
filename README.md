# VORTEX VPN — Production-Grade WireGuard VPN & DNS Privacy Shield

<p align="center">
  <img src="client-ui/assets/logo.svg" width="96" height="96" alt="VORTEX VPN Logo" />
</p>

<p align="center">
  <strong>One tap. Protected.</strong><br>
  A commercial-grade, modular VPN and DNS ad/tracker blocker built on the established WireGuard protocol and Python FastAPI.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Protocol-WireGuard%20(Curve25519)-00E5FF" alt="Protocol" />
  <img src="https://img.shields.io/badge/Backend-FastAPI%203.12+-10B981" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Security-Argon2id%20%7C%20JWT-4F46E5" alt="Security" />
  <img src="https://img.shields.io/badge/Tests-100%25%20Passing-success" alt="Tests" />
  <img src="https://img.shields.io/badge/License-MIT-blue" alt="License" />
</p>

---

## 🌟 Highlights

- **Real WireGuard Protocol**: Uses industry-standard Curve25519, ChaCha20-Poly1305, and BLAKE2s. No custom cryptography.
- **Commercial-Grade Animated UI**: Dark-first, futuristic interface with an ambient GPU-accelerated rotating vortex status ring, interactive world server map, live threat counters, and zero bloated frameworks.
- **In-Engine DNS Privacy Blocker**: High-performance asynchronous DNS filtering proxy intercepting ads, trackers, telemetry, and malware before they reach the device.
- **Mathematical Fastest Server Selection**: Intelligently scores nodes across Germany, USA, India, UK, Singapore, and Netherlands using real-time latency, packet loss, CPU/RAM load, and capacity metrics.
- **Fail-Closed Kill Switch**: Guarantees zero unencrypted packet bypass if tunnel connectivity is interrupted.
- **Strict Data Minimization**: Zero storage of user browsing history, URLs, page contents, or unneeded logs.
- **Android Integration**: Complete Android Kotlin module utilizing the official WireGuard Android SDK (`com.wireguard.android:tunnel`) and `VpnService` bridge.
- **Streamlit Command Center**: Real-time administrative fleet management with interactive Plotly telemetry charts.

---

## 🏗️ Architecture

```
                    ┌────────────────────────────────────────┐
                    │              CLIENT LAYER              │
                    │   Android Native App  │  Modern Web UI │
                    └───────────────────┬────────────────────┘
                                        │ HTTPS REST API
                                        ▼
                    ┌────────────────────────────────────────┐
                    │      FASTAPI CONTROL PLANE (:8000)     │
                    │  - Argon2id Auth & JWT Issuance        │
                    │  - Curve25519 Key Generation           │
                    │  - Optimal Server Selection Engine     │
                    │  - Client IP Pool Provisioning         │
                    └───────┬────────────────────────┬───────┘
                            │                        │
                            ▼                        ▼
                    ┌───────────────┐        ┌───────────────┐
                    │  DATABASE     │        │ REDIS CACHE   │
                    │  SQLite/Postgres       │ Rate Limiting │
                    └───────────────┘        └───────────────┘
                                        │
           ┌────────────────────────────┼────────────────────────────┐
           ▼                            ▼                            ▼
┌───────────────────────┐    ┌───────────────────────┐    ┌───────────────────────┐
│     GERMANY (FRA)     │    │       USA (NYC)       │    │      INDIA (BOM)      │
│  WireGuard Node       │    │  WireGuard Node       │    │  WireGuard Node       │
│  DNS Privacy Filter   │    │  DNS Privacy Filter   │    │  DNS Privacy Filter   │
│  Server Agent         │    │  Server Agent         │    │  Server Agent         │
└───────────────────────┘    └───────────────────────┘    └───────────────────────┘
```

---

## 🚀 Quick Start (Local Development)

### 1. Prerequisites
- Python 3.12+
- Git

### 2. Setup Environment
```bash
git clone https://github.com/your-org/vortex-vpn.git
cd vortex-vpn

# Run the automated development setup script
python scripts/setup_dev.py
```

### 3. Launch the Backend & UI
```bash
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
Open **[http://127.0.0.1:8000](http://127.0.0.1:8000)** in any modern browser. You will see the premium animated VORTEX VPN interface!

API Documentation (Swagger UI): **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)**

### 4. Run the Streamlit Admin Dashboard
In a separate terminal:
```bash
streamlit run admin/dashboard.py
```
Access the admin fleet console at **[http://localhost:8501](http://localhost:8501)**.

### 5. Launch the Standalone DNS Blocker
In a separate terminal:
```bash
python dns-blocker/dns_server.py
```

---

## 🧪 Automated Testing

Run the comprehensive pytest test suite covering cryptography, authentication, server selection, connection lifecycle, and the DNS filtering engine:

```bash
pytest -v
```

All 17 tests will run and pass:
```
backend/tests/test_auth.py::test_user_registration_and_login PASSED
backend/tests/test_crypto.py::test_curve25519_keypair_generation PASSED
backend/tests/test_crypto.py::test_public_key_derivation PASSED
backend/tests/test_crypto.py::test_preshared_key_generation PASSED
backend/tests/test_dns.py::test_dns_statistics_and_custom_rules PASSED
backend/tests/test_servers.py::test_list_servers PASSED
backend/tests/test_servers.py::test_auto_fastest_server_selection PASSED
backend/tests/test_servers.py::test_filter_by_country PASSED
backend/tests/test_vpn.py::test_vpn_connect_and_disconnect PASSED
backend/tests/test_ui.py::test_ui_index_served PASSED
dns-blocker/tests/test_dns_server.py::test_domain_blocklist_matching PASSED
dns-blocker/tests/test_dns_server.py::test_allowlist_precedence PASSED
dns-blocker/tests/test_dns_server.py::test_dns_cache_ttl PASSED
dns-blocker/tests/test_dns_server.py::test_blocked_response_synthesis PASSED
server-agent/tests/test_agent.py::test_system_metrics_collection PASSED
server-agent/tests/test_agent.py::test_ping_latency_measurement PASSED
server-agent/tests/test_agent.py::test_parse_wg_dump PASSED
server-agent/tests/test_agent.py::test_build_telemetry_payload PASSED
```

---

## 📁 Repository Structure

```
vortex-vpn/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application entrypoint & static mount
│   │   ├── config.py            # Environment & secrets configuration
│   │   ├── api/                 # REST endpoints (auth, servers, vpn, dns, admin)
│   │   ├── models/              # SQLAlchemy database models
│   │   ├── schemas/             # Pydantic request/response schemas
│   │   ├── services/            # Core business logic (Crypto, VPN, Servers, DNS)
│   │   └── security/            # Argon2id, JWT, Rate Limiting, Headers
│   └── tests/                   # Backend pytest suite
├── dns-blocker/                 # Asynchronous DNS proxy ad/tracker filter
│   ├── dns_server.py            # UDP/TCP port 53/5353 proxy engine
│   ├── blocklist.py             # StevenBlack/AdAway hosts parser & matcher
│   ├── rules.py                 # Dynamic allowlist & custom blocklist
│   ├── cache.py                 # TTL-respecting in-memory DNS cache
│   └── tests/                   # DNS blocker test suite
├── server-agent/                # VPS node health & WireGuard telemetry daemon
│   ├── agent.py                 # Heartbeat sender daemon
│   ├── monitoring.py            # CPU, RAM, bandwidth metrics
│   ├── wireguard_monitor.py     # Safe wg show dump parser
│   └── tests/                   # Agent test suite
├── client-ui/                   # Commercial-grade dark-first animated UI
│   ├── index.html               # Single page application
│   ├── manifest.json            # PWA manifest (Android installable)
│   ├── css/                     # Variables, animations, components, layout
│   └── js/                      # Vortex animator, SVG map, charts, API client
├── android/                     # Native Android Kotlin module
│   ├── app/build.gradle.kts     # WireGuard Android SDK configuration
│   └── src/main/java/           # VortexVpnService.kt & WireGuardManager.kt
├── admin/                       # Streamlit fleet management dashboard
│   └── dashboard.py             # Plotly charts & node controls
├── deployment/                  # Production Docker, nftables & systemd units
├── docs/                        # Complete technical documentation suite
├── scripts/                     # Dev setup, config generator, health checker
├── docker-compose.yml           # Multi-container production deployment
└── pyproject.toml               # Python project configuration
```

---

## 🛠️ CLI Utilities

### Generate Standalone WireGuard Client Configuration
```bash
python scripts/generate_config.py --country DE --out my_vpn.conf
```
Import `my_vpn.conf` directly into the official WireGuard app on Android, iOS, Windows, macOS, or Linux!

### Check System & Fleet Health
```bash
python scripts/health_check.py
```

---

## 🛡️ Security & Privacy Standards

- **Zero-Knowledge Architecture**: No recording of visited domains, browsing destinations, or application payloads.
- **Fail-Closed Protection**: Built-in Kill Switch prevents traffic from leaking unencrypted if the VPN tunnel drops.
- **Rate-Limited Endpoints**: Brute-force protection on all authentication and connection routes.
- **Safe Subprocess Execution**: Strict argument arrays with zero shell concatenation.

Detailed security documentation is available in [docs/security.md](docs/security.md) and [docs/privacy.md](docs/privacy.md).

---

## 📄 License
This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
