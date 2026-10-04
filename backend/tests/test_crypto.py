"""
VORTEX VPN - Cryptography Test Suite
Verifies standard WireGuard Curve25519 (X25519) key generation, public key derivation,
and key length validations.
"""
import pytest
from backend.app.services.crypto_service import WireGuardCryptoService


def test_curve25519_keypair_generation():
    """Verify generated keypair adheres to WireGuard Base64 32-byte specs."""
    private_key, public_key = WireGuardCryptoService.generate_keypair()
    assert isinstance(private_key, str)
    assert isinstance(public_key, str)
    assert WireGuardCryptoService.validate_key(private_key)
    assert WireGuardCryptoService.validate_key(public_key)
    assert private_key != public_key


def test_public_key_derivation():
    """Verify that public key derived from private key exactly matches original public key."""
    private_key, expected_public = WireGuardCryptoService.generate_keypair()
    derived_public = WireGuardCryptoService.get_public_key(private_key)
    assert derived_public == expected_public


def test_preshared_key_generation():
    """Verify pre-shared key (PSK) generates valid 32-byte Base64 key."""
    psk = WireGuardCryptoService.generate_preshared_key()
    assert WireGuardCryptoService.validate_key(psk)
