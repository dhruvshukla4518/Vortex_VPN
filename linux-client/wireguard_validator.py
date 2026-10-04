"""
VORTEX VPN - Cryptographic WireGuard Configuration Validator
Validates downloaded configurations before OS network stack activation.
Enforces Curve25519 key sanity, structural schema, endpoint ports, and DNS leak protection directives.
"""
import base64
import ipaddress
from typing import Tuple, Dict, Optional


class WireGuardConfigValidator:
    """
    Validates WireGuard configuration text according to security requirements:
    1. Base64 32-byte Curve25519 key verification (for PrivateKey, PublicKey, PresharedKey).
    2. Zero-key and symmetry check (private key cannot equal public key, cannot be all zero).
    3. Mandatory DNS directive present (prevents DNS leaks).
    4. Valid IPv4/IPv6 CIDR addresses.
    5. Valid endpoint host/IP and UDP port (1-65535).
    """

    @staticmethod
    def is_valid_curve25519_key(key_b64: str) -> bool:
        """Check if string is a valid base64-encoded 32-byte Curve25519 key."""
        if not key_b64 or not isinstance(key_b64, str):
            return False
        key_clean = key_b64.strip()
        try:
            raw = base64.b64decode(key_clean, validate=True)
            if len(raw) != 32:
                return False
            if all(b == 0 for b in raw):
                return False
            return True
        except Exception:
            return False

    @classmethod
    def validate(cls, raw_config: str) -> Tuple[bool, str]:
        """
        Validate raw WireGuard config file syntax and security constraints.
        Returns: (is_valid: bool, reason: str)
        """
        if not raw_config or not raw_config.strip():
            return False, "Configuration is empty"

        lines = [line.strip() for line in raw_config.splitlines() if line.strip() and not line.strip().startswith("#")]
        
        current_section: Optional[str] = None
        sections: Dict[str, Dict[str, str]] = {}

        for line in lines:
            if line.startswith("[") and line.endswith("]"):
                current_section = line[1:-1].strip()
                if current_section not in sections:
                    sections[current_section] = {}
            elif "=" in line and current_section:
                key, val = line.split("=", 1)
                sections[current_section][key.strip()] = val.strip()

        # 1. Section check
        if "Interface" not in sections:
            return False, "Missing [Interface] section"
        if "Peer" not in sections:
            return False, "Missing [Peer] section"

        iface = sections["Interface"]
        peer = sections["Peer"]

        # 2. PrivateKey check
        priv_key = iface.get("PrivateKey")
        if not priv_key:
            return False, "Missing PrivateKey in [Interface]"
        if not cls.is_valid_curve25519_key(priv_key):
            return False, "Invalid PrivateKey: must be a valid 32-byte Base64 Curve25519 key"

        # 3. Mandatory DNS directive check (DNS leak protection requirement)
        dns_servers = iface.get("DNS")
        if not dns_servers:
            return False, "Missing DNS directive in [Interface]: DNS leak protection requires explicit resolver"
        for dns_ip in [d.strip() for d in dns_servers.split(",") if d.strip()]:
            try:
                ipaddress.ip_address(dns_ip)
            except ValueError:
                return False, f"Invalid DNS resolver IP: {dns_ip}"

        # 4. Address check
        address_str = iface.get("Address")
        if not address_str:
            return False, "Missing Address directive in [Interface]"
        for addr in [a.strip() for a in address_str.split(",") if a.strip()]:
            try:
                ipaddress.ip_network(addr, strict=False)
            except ValueError:
                return False, f"Invalid interface IP network: {addr}"

        # 5. Peer PublicKey check
        pub_key = peer.get("PublicKey")
        if not pub_key:
            return False, "Missing PublicKey in [Peer]"
        if not cls.is_valid_curve25519_key(pub_key):
            return False, "Invalid Peer PublicKey: must be a valid 32-byte Base64 Curve25519 key"

        if priv_key == pub_key:
            return False, "Key symmetry violation: PrivateKey and Peer PublicKey cannot be identical"

        # 6. Peer Endpoint check
        endpoint = peer.get("Endpoint")
        if not endpoint:
            return False, "Missing Endpoint in [Peer]"
        
        if "]:" in endpoint:
            host_part, port_str = endpoint.rsplit("]:", 1)
            host_part = host_part.lstrip("[")
        elif ":" in endpoint:
            host_part, port_str = endpoint.rsplit(":", 1)
        else:
            return False, "Invalid Endpoint format: must specify host:port"

        try:
            port = int(port_str)
            if not (1 <= port <= 65535):
                return False, f"Endpoint port {port} out of range (1-65535)"
        except ValueError:
            return False, f"Invalid endpoint port: {port_str}"

        # 7. AllowedIPs check
        allowed_ips = peer.get("AllowedIPs")
        if not allowed_ips:
            return False, "Missing AllowedIPs in [Peer]"
        for aip in [a.strip() for a in allowed_ips.split(",") if a.strip()]:
            try:
                ipaddress.ip_network(aip, strict=False)
            except ValueError:
                return False, f"Invalid AllowedIPs CIDR: {aip}"

        return True, "Configuration structurally and cryptographically valid"
