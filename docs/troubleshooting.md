# VORTEX VPN — Troubleshooting & Diagnostic Guide

## 1. Common Issues & Solutions

### A. WireGuard Handshake Fails / No Packets Received
- **Symptoms**: Client shows connected, but no bytes are received (`0 B received`).
- **Possible Causes**:
  1. **UDP Port 51820 Blocked**: Cloud provider firewall or security group blocks inbound UDP 51820.
     - *Fix*: Allow UDP 51820 in AWS Security Groups, Hetzner Cloud Firewall, or DigitalOcean Cloud Firewall.
  2. **IP Forwarding Disabled**: The kernel drops forwarded packets.
     - *Fix*: Check `sysctl net.ipv4.ip_forward`. It must return `1`. Enable via `sudo sysctl -w net.ipv4.ip_forward=1`.
  3. **NAT Masquerading Missing**: The public network interface is not `eth0`.
     - *Fix*: Check interface with `ip -4 route ls`. If named `ens3` or `enp1s0`, update the `MASQUERADE` rule accordingly in `wg0.conf`.

---

### B. DNS Queries Not Resolving
- **Symptoms**: Web pages fail to resolve while VPN is connected.
- **Possible Causes**:
  1. **DNS Blocker Service Inactive**:
     - *Fix*: Verify DNS service is running: `sudo systemctl status vortex-dns.service`.
  2. **Port 53 Redirection Missing**:
     - *Fix*: Ensure iptables/nftables redirect port 53 to port 5353:
       `iptables -t nat -A PREROUTING -i wg0 -p udp --dport 53 -j REDIRECT --to-ports 5353`

---

### C. Server Shows "Degraded" or "Offline" on Dashboard
- **Symptoms**: Node latency or load is not updating in the Streamlit admin dashboard.
- **Possible Causes**:
  1. **Mismatched `AGENT_SECRET_KEY`**: The server agent token does not match the control plane secret.
     - *Fix*: Verify `.env` file on both the control plane and node have identical `AGENT_SECRET_KEY`.
  2. **Network Timeout**: The node cannot resolve or reach `CONTROL_PLANE_URL`.
     - *Fix*: Run `curl -I <CONTROL_PLANE_URL>/api/v1/health` from the node terminal.

---

### D. Android VPN Permission Prompt Loops
- **Symptoms**: Tapping Connect keeps showing the system VPN dialog.
- **Cause**: The Android device already has an Always-On VPN profile active for another provider.
- **Fix**: Open Android Settings $\rightarrow$ Network & Internet $\rightarrow$ VPN $\rightarrow$ Disable "Always-on VPN" for third-party apps.
