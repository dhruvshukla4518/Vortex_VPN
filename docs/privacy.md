# VORTEX VPN — Privacy Policy & Data Minimization

## 1. Core Privacy Philosophy

VORTEX VPN operates on strict **data minimization** and zero-knowledge principles. We believe that privacy is a fundamental human right.

---

## 2. What We DO NOT Collect or Store

- **NO Browsing History**: We never monitor, inspect, record, or store the domains, URLs, or IP addresses that you visit.
- **NO HTTPS Interception**: We never perform SSL/TLS MITM or inspect encrypted application payloads.
- **NO DNS Resolution Logs**: Our DNS blocker processes queries in-memory. Only anonymous, aggregate counters (e.g. total ads blocked) are retained.
- **NO Private Keys**: Your WireGuard private keys are generated on your device or transmitted only once during initial provisioning. We do not keep copies of private keys.

---

## 3. What We Collect & Why

| Data Point | Purpose | Retention |
| :--- | :--- | :--- |
| **Email & Username** | Account identification and authentication | Lifetime of account |
| **Hashed Password** | Argon2id cryptographic password verification | Lifetime of account |
| **Device Public Key** | Binding your device to WireGuard peer configuration | Until device revoked |
| **Daily Blocked Counters** | Providing user privacy dashboard metrics | Rolling 30 days |
| **Connection Timestamp** | Operational session management & concurrency | Purged on disconnect |

---

## 4. Anonymization & Data Pruning

- Public client IP addresses are truncated to `/24` subnets or discarded immediately upon session establishment.
- Live blocked activity feeds display only the intercepted threat domain and category, and are rotated automatically every 24 hours.
