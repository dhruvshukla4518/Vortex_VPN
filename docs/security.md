# VORTEX VPN — Security Model & Hardening Guide

## 1. Cryptographic Primitives & Key Management

- **Tunnel Encryption**: WireGuard protocol utilizing:
  - **Curve25519 (X25519)** for elliptic-curve key exchange.
  - **ChaCha20-Poly1305** for authenticated symmetric data encryption.
  - **BLAKE2s** for secure hashing.
- **Strict Key Separation**:
  - Client private keys are generated ephemerally via standard Python `cryptography` primitives and transmitted once to the authenticated client over TLS.
  - **Private keys are never stored on the control plane database or file system.**
  - Pre-shared keys (PSK) are 256-bit high-entropy random byte arrays.

---

## 2. Authentication & Authorization

- **Password Storage**: Passwords are saved as one-way Argon2id hashes:
  - `time_cost = 3`
  - `memory_cost = 65536 KB (64 MB)`
  - `parallelism = 4`
  - `hash_len = 32 bytes`
- **Token Security**:
  - JWT Access Tokens: Valid for 15 minutes, signed with HMAC-SHA256 (`HS256`).
  - Refresh Tokens: Valid for 7 days, rotated on use.
  - In-memory and database revocation blacklist for revoked sessions.
- **Server Agent Authentication**:
  - Node agents authenticate via cryptographically random pre-shared token passed in header `X-Agent-Key`.

---

## 3. Network Defense & Fail-Closed Kill Switch

- **Fail-Closed Design**:
  - On Android: Native `VpnService.Builder.setBlocking(true)` blocks all non-VPN network traffic if the tunnel drops.
  - On Linux: `nftables` input/forward policies are set to `policy drop`, preventing unencrypted packet egress.
- **DNS Leak Prevention**:
  - Client configuration dictates `DNS = 10.8.0.1`, forcing all address resolution through the WireGuard interface.
  - Inbound port 53 traffic on the node is redirected by NAT prerouting directly to the local DNS proxy.
- **Subprocess Security**:
  - System invocations (such as `wg show`) strictly use argument arrays (`["wg", "show", "wg0", "dump"]`).
  - Shell execution (`shell=True`) and string concatenation of untrusted input are strictly forbidden.

---

## 4. Rate Limiting & Input Validation

- **Sliding-Window Limiter**: Restricts authentication attempts to 20 requests per minute per IP address, preventing brute-force dictionary attacks.
- **Pydantic Validation**: All API inputs are strictly sanitized with type bounds and regex checks.
