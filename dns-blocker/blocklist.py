"""
VORTEX VPN - DNS Blocker Engine: Blocklist & Fast Domain Matcher
Implements O(1) set lookup and hierarchical subdomain matching.
"""
import os
import re
from typing import Set, Iterable

DOMAIN_PATTERN = re.compile(
    r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$"
)

# Built-in baseline ad and tracker domains
BASE_BLOCKLIST = {
    "doubleclick.net", "adservice.google.com", "pagead2.googlesyndication.com",
    "googleads.g.doubleclick.net", "adclick.g.doubleclick.net", "ads.yahoo.com",
    "adnxs.com", "secure-metrics.adnxs.com", "advertising.com", "ads.inmobi.com",
    "criteo.com", "taboola.com", "outbrain.com", "telemetry.analytics.net",
    "pixel.facebook.com", "telemetry.microsoft.com", "crashlytics.com",
    "quantserve.com", "hotjar.com", "scorecardresearch.com",
    "malware-payload-dist.org", "phishing-bank-login.com"
}


class DomainBlocklist:
    def __init__(self, initial_domains: Iterable[str] = BASE_BLOCKLIST):
        self._blocked_domains: Set[str] = set()
        for d in initial_domains:
            self.add(d)

    def add(self, domain: str) -> None:
        """Add domain to blocklist after normalization."""
        norm = domain.lower().strip().strip(".")
        if norm:
            self._blocked_domains.add(norm)

    def remove(self, domain: str) -> None:
        norm = domain.lower().strip().strip(".")
        self._blocked_domains.discard(norm)

    def is_blocked(self, domain: str) -> bool:
        """
        Check if domain or any parent domain is present in blocklist.
        Example: 'ads.tracking.doubleclick.net' matches 'doubleclick.net'.
        """
        norm = domain.lower().strip().strip(".")
        if not norm:
            return False

        if norm in self._blocked_domains:
            return True

        # Check domain parent hierarchy
        parts = norm.split(".")
        for i in range(1, len(parts) - 1):
            parent = ".".join(parts[i:])
            if parent in self._blocked_domains:
                return True

        return False

    def load_hosts_file(self, file_path: str) -> int:
        """Parse standard hosts format file and load valid blocked domains."""
        if not os.path.exists(file_path):
            return 0

        count = 0
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "#" in line:
                    line = line.split("#")[0].strip()

                parts = line.split()
                if len(parts) >= 2:
                    ip, candidate = parts[0], parts[1]
                    if ip in ("0.0.0.0", "127.0.0.1", "::", "::1"):
                        candidate = candidate.lower().strip(".")
                        if candidate not in ("localhost", "local", "broadcasthost") and DOMAIN_PATTERN.match(candidate):
                            self.add(candidate)
                            count += 1
                elif len(parts) == 1:
                    candidate = parts[0].lower().strip(".")
                    if DOMAIN_PATTERN.match(candidate):
                        self.add(candidate)
                        count += 1

        return count

    @property
    def total_rules(self) -> int:
        return len(self._blocked_domains)
