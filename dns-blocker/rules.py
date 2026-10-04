"""
VORTEX VPN - DNS Custom Rules & Allowlists
Handles custom user rules where allowlist takes absolute precedence over blocklists.
"""
from typing import Set


class RuleManager:
    def __init__(self):
        self._allowlist: Set[str] = set()
        self._custom_blocklist: Set[str] = set()

    def allow(self, domain: str) -> None:
        norm = domain.lower().strip().strip(".")
        self._allowlist.add(norm)
        self._custom_blocklist.discard(norm)

    def disallow(self, domain: str) -> None:
        norm = domain.lower().strip().strip(".")
        self._allowlist.discard(norm)

    def block(self, domain: str) -> None:
        norm = domain.lower().strip().strip(".")
        self._custom_blocklist.add(norm)
        self._allowlist.discard(norm)

    def unblock(self, domain: str) -> None:
        norm = domain.lower().strip().strip(".")
        self._custom_blocklist.discard(norm)

    def is_allowed(self, domain: str) -> bool:
        """Check if domain or parent is explicitly allowed."""
        norm = domain.lower().strip().strip(".")
        if norm in self._allowlist:
            return True
        parts = norm.split(".")
        for i in range(1, len(parts) - 1):
            if ".".join(parts[i:]) in self._allowlist:
                return True
        return False

    def is_custom_blocked(self, domain: str) -> bool:
        """Check if domain or parent is in custom user blocklist."""
        norm = domain.lower().strip().strip(".")
        if norm in self._custom_blocklist:
            return True
        parts = norm.split(".")
        for i in range(1, len(parts) - 1):
            if ".".join(parts[i:]) in self._custom_blocklist:
                return True
        return False
