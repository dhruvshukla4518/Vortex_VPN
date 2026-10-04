"""
VORTEX VPN - WireGuard Cryptographic Key Service
Generates standard WireGuard Curve25519 (X25519) keypairs and pre-shared keys
strictly conforming to WireGuard cryptographic specifications.
"""
import base64
import os
from typing import Tuple
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives import serialization


class WireGuardCryptoService:
    @staticmethod
    def generate_keypair() -> Tuple[str, str]:
        """
        Generate a cryptographically secure WireGuard keypair.
        Returns:
            Tuple[str, str]: (private_key_base64, public_key_base64)
        """
        private_key = x25519.X25519PrivateKey.generate()
        public_key = private_key.public_key()

        raw_private = private_key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption()
        )
        raw_public = public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )

        private_b64 = base64.b64encode(raw_private).decode("utf-8")
        public_b64 = base64.b64encode(raw_public).decode("utf-8")
        return private_b64, public_b64

    @staticmethod
    def get_public_key(private_key_b64: str) -> str:
        """Derive the WireGuard public key from a Base64-encoded private key."""
        raw_private = base64.b64decode(private_key_b64)
        private_key = x25519.X25519PrivateKey.from_private_bytes(raw_private)
        public_key = private_key.public_key()
        raw_public = public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        return base64.b64encode(raw_public).decode("utf-8")

    @staticmethod
    def generate_preshared_key() -> str:
        """Generate a random 32-byte pre-shared symmetric key (PSK) encoded in Base64."""
        random_bytes = os.urandom(32)
        return base64.b64encode(random_bytes).decode("utf-8")

    @staticmethod
    def validate_key(key_b64: str) -> bool:
        """Validate if a string is a valid Base64-encoded 32-byte WireGuard key."""
        try:
            raw = base64.b64decode(key_b64)
            return len(raw) == 32
        except Exception:
            return False
