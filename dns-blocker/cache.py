"""
VORTEX VPN - DNS Cache
High-performance in-memory cache respecting DNS TTL limits.
"""
import time
from typing import Optional, Dict, Tuple
import dns.message


class DNSCache:
    def __init__(self, max_entries: int = 50000, min_ttl: int = 60, max_ttl: int = 86400):
        self.max_entries = max_entries
        self.min_ttl = min_ttl
        self.max_ttl = max_ttl
        # Key: (qname, qtype, qclass) -> Value: (dns.message.Message, expiry_timestamp)
        self._cache: Dict[Tuple[str, int, int], Tuple[dns.message.Message, float]] = {}

    def get(self, qname: str, qtype: int, qclass: int = 1) -> Optional[dns.message.Message]:
        key = (qname.lower(), qtype, qclass)
        entry = self._cache.get(key)
        if not entry:
            return None

        msg, expiry = entry
        if time.time() > expiry:
            del self._cache[key]
            return None

        return msg

    def set(self, qname: str, qtype: int, msg: dns.message.Message, qclass: int = 1) -> None:
        if len(self._cache) >= self.max_entries:
            # Simple eviction of oldest entries
            self._purge_expired()
            if len(self._cache) >= self.max_entries:
                # Remove first 100 entries
                keys = list(self._cache.keys())[:100]
                for k in keys:
                    del self._cache[k]

        # Determine effective TTL from answers
        ttl = self.min_ttl
        for rrset in msg.answer:
            if rrset.ttl:
                ttl = max(self.min_ttl, min(rrset.ttl, self.max_ttl))
                break

        key = (qname.lower(), qtype, qclass)
        self._cache[key] = (msg, time.time() + ttl)

    def _purge_expired(self) -> None:
        now = time.time()
        expired = [k for k, (_, exp) in self._cache.items() if now > exp]
        for k in expired:
            del self._cache[k]

    def clear(self) -> None:
        self._cache.clear()

    @property
    def size(self) -> int:
        return len(self._cache)
