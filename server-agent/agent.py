"""
VORTEX VPN - Server Agent Daemon
Lightweight agent running on each VPN node to report real-time health,
resource utilization, and WireGuard status back to the control plane.
"""
import os
import time
import asyncio
from typing import Dict, Any, Optional
import httpx

from monitoring import get_system_metrics, measure_ping_latency
from wireguard_monitor import get_wireguard_status


class ServerAgent:
    def __init__(
        self,
        hostname: Optional[str] = None,
        control_plane_url: Optional[str] = None,
        secret_key: Optional[str] = None,
        interface: str = "wg0",
        interval: int = 15
    ):
        self.hostname = hostname or os.getenv("SERVER_HOSTNAME", "de-fra-01.vortexvpn.net")
        self.control_plane_url = control_plane_url or os.getenv("CONTROL_PLANE_URL", "http://127.0.0.1:8000")
        self.secret_key = secret_key or os.getenv("AGENT_SECRET_KEY", "vortex-agent-node-secret-key-change-in-production")
        self.interface = interface
        self.interval = interval
        self.running = False

    def build_telemetry_payload(self) -> Dict[str, Any]:
        """Gather all node metrics into standard ServerHealthReport payload."""
        sys_metrics = get_system_metrics()
        latency_ms, packet_loss = measure_ping_latency()
        wg_info = get_wireguard_status(self.interface)

        return {
            "hostname": self.hostname,
            "latency_ms": latency_ms,
            "packet_loss": packet_loss,
            "cpu_usage": sys_metrics["cpu_usage"],
            "memory_usage": sys_metrics["memory_usage"],
            "bandwidth_usage_mbps": sys_metrics["bandwidth_usage_mbps"],
            "active_connections": wg_info["active_peers"],
            "wireguard_status": wg_info["status"]
        }

    async def send_heartbeat(self) -> bool:
        """Send authenticated telemetry report to control plane."""
        payload = self.build_telemetry_payload()
        endpoint = f"{self.control_plane_url.rstrip('/')}/api/v1/health/heartbeat"
        headers = {
            "X-Agent-Key": self.secret_key,
            "Content-Type": "application/json"
        }

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.post(endpoint, json=payload, headers=headers)
                return resp.status_code == 200
        except Exception:
            return False

    async def run_loop(self):
        """Continuous heartbeat reporting loop."""
        self.running = True
        while self.running:
            await self.send_heartbeat()
            await asyncio.sleep(self.interval)

    def stop(self):
        self.running = False


if __name__ == "__main__":
    agent = ServerAgent()
    print(f"Starting VORTEX Server Agent for {agent.hostname}...")
    try:
        asyncio.run(agent.run_loop())
    except KeyboardInterrupt:
        print("Server Agent stopped.")
