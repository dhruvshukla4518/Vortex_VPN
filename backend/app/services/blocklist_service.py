"""
VORTEX VPN - Blocklist Download & Rule Management Service
Safely downloads, validates, normalizes, deduplicates, and caches domain blocklists.
Treats all external downloaded content strictly as data.
"""
import os
import re
from datetime import datetime, timezone
from typing import Set, Dict, Any, List
import httpx

from backend.app.config import settings

DOMAIN_REGEX = re.compile(
    r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$"
)

# Standard default blocked domains to guarantee immediate out-of-the-box ad/tracker blocking
DEFAULT_BLOCKED_DOMAINS: Set[str] = {
    # High-profile Ad Networks
    "doubleclick.net", "adservice.google.com", "pagead2.googlesyndication.com",
    "adclick.g.doubleclick.net", "googleads.g.doubleclick.net", "ads.yahoo.com",
    "adnxs.com", "secure-metrics.adnxs.com", "advertising.com", "ads.mopub.com",
    "ads.inmobi.com", "adcolony.com", "vungle.com", "unityads.unity3d.com",
    "criteo.com", "cas.criteo.com", "rubiconproject.com", "openx.net",
    "taboola.com", "outbrain.com", "popads.net", "propellerads.com",
    
    # Telemetry & User Tracking
    "telemetry.analytics.net", "analytics.google.com", "google-analytics.com",
    "pixel.facebook.com", "graph.facebook.com", "tr.snapchat.com",
    "telemetry.microsoft.com", "vortex.data.microsoft.com", "app-measurement.com",
    "crashlytics.com", "scorecardresearch.com", "quantserve.com", "hotjar.com",
    "mixpanel.com", "segment.io", "branch.io", "appsflyer.com",
    
    # Known Phishing & Malware Domains
    "malware-payload-dist.org", "phishing-bank-login.com", "cryptominer-pool.net",
    "trojan-payload-delivery.cc", "ransomware-payment-gateway.xyz"
}


class BlocklistService:
    def __init__(self, cache_dir: str = "dns-blocker/cache"):
        self.cache_dir = cache_dir
        self.cache_file = os.path.join(cache_dir, "compiled_blocklist.txt")
        self.blocked_domains: Set[str] = set(DEFAULT_BLOCKED_DOMAINS)
        self.last_updated: datetime = datetime.now(timezone.utc)
        self.version: str = "1.0.0"
        self._ensure_cache_dir()

    def _ensure_cache_dir(self) -> None:
        os.makedirs(self.cache_dir, exist_ok=True)

    def parse_hosts_content(self, text: str) -> Set[str]:
        """
        Parse hosts file or plain domain list safely.
        Validates domains against strict regex and excludes loopback/invalid entries.
        """
        extracted: Set[str] = set()
        for line in text.splitlines():
            line = line.strip()
            # Strip comments
            if not line or line.startswith("#"):
                continue
            if "#" in line:
                line = line.split("#")[0].strip()

            parts = line.split()
            domain = ""
            if len(parts) == 1:
                # Plain domain list
                domain = parts[0]
            elif len(parts) >= 2:
                # Standard hosts format: 0.0.0.0 domain.com or 127.0.0.1 domain.com
                ip, candidate = parts[0], parts[1]
                if ip in ("0.0.0.0", "127.0.0.1", "::", "::1"):
                    domain = candidate

            domain = domain.lower().strip()
            if domain in ("localhost", "local", "broadcasthost"):
                continue
            if DOMAIN_REGEX.match(domain):
                extracted.add(domain)

        return extracted

    async def update_from_feed(self, url: str) -> int:
        """Download remote blocklist feed safely via HTTP and merge."""
        try:
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    domains = self.parse_hosts_content(resp.text)
                    self.blocked_domains.update(domains)
                    self.last_updated = datetime.now(timezone.utc)
                    self._save_to_cache()
                    return len(domains)
        except Exception as e:
            # Fallback gracefully without breaking DNS operation
            pass
        return 0

    def _save_to_cache(self) -> None:
        """Persist compiled blocklist to disk for quick bootstrap."""
        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                for d in sorted(self.blocked_domains):
                    f.write(f"{d}\n")
        except Exception:
            pass

    def load_from_cache(self) -> int:
        """Load blocklist from local disk cache."""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    domains = {line.strip() for line in f if line.strip()}
                    self.blocked_domains.update(domains)
                    return len(self.blocked_domains)
            except Exception:
                pass
        return len(self.blocked_domains)

    def is_blocked(self, domain: str) -> bool:
        """Check if domain or any parent domain is blocked."""
        domain = domain.lower().strip(".")
        if domain in self.blocked_domains:
            return True

        # Check subdomains (e.g., test.adservice.google.com -> adservice.google.com)
        parts = domain.split(".")
        for i in range(1, len(parts) - 1):
            parent = ".".join(parts[i:])
            if parent in self.blocked_domains:
                return True

        return False

    def get_status(self) -> Dict[str, Any]:
        return {
            "total_rules": len(self.blocked_domains),
            "last_updated": self.last_updated.isoformat(),
            "version": self.version,
            "cache_file": self.cache_file
        }


# Singleton blocklist instance
blocklist_manager = BlocklistService()
