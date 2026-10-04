"""
VORTEX VPN - Server Agent Unit Tests
"""
import pytest
from monitoring import get_system_metrics, measure_ping_latency
from wireguard_monitor import parse_wg_dump, get_wireguard_status
from agent import ServerAgent


def test_system_metrics_collection():
    metrics = get_system_metrics()
    assert "cpu_usage" in metrics
    assert "memory_usage" in metrics
    assert "bandwidth_usage_mbps" in metrics
    assert isinstance(metrics["cpu_usage"], float)
    assert isinstance(metrics["memory_usage"], float)
    assert metrics["memory_usage"] > 0.0


def test_ping_latency_measurement():
    lat, loss = measure_ping_latency()
    assert isinstance(lat, float)
    assert isinstance(loss, float)
    assert lat >= 0.0
    assert 0.0 <= loss <= 100.0


def test_parse_wg_dump():
    sample_dump = (
        "4C3sYg9a...=\tk7d8...=\t51820\t0\n"
        "peer1_pub==\t(none)\t198.51.100.1:44322\t10.8.0.2/32\t1728000000\t1024000\t2048000\t25\n"
        "peer2_pub==\t(none)\t203.0.113.5:51820\t10.8.0.3/32\t1728000050\t512000\t8192000\t25\n"
    )
    result = parse_wg_dump(sample_dump)
    assert result["status"] == "active"
    assert result["active_peers"] == 2
    assert len(result["peers"]) == 2
    assert result["peers"][0]["public_key"] == "peer1_pub=="
    assert result["peers"][0]["transfer_rx_bytes"] == 1024000


def test_build_telemetry_payload():
    agent = ServerAgent(hostname="test-node.vortexvpn.net")
    payload = agent.build_telemetry_payload()
    assert payload["hostname"] == "test-node.vortexvpn.net"
    assert "cpu_usage" in payload
    assert "memory_usage" in payload
    assert "bandwidth_usage_mbps" in payload
    assert "active_connections" in payload
    assert "wireguard_status" in payload
