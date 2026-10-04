"""
VORTEX VPN - Upstream DNS Resolver
Asynchronously forwards allowed DNS queries to privacy-respecting upstream DNS providers
(Quad9 with DNSSEC, Cloudflare) with fallback handling.
"""
from typing import Optional, List
import dns.message
import dns.asyncquery

DEFAULT_UPSTREAMS = ["9.9.9.9", "1.1.1.1"]


class UpstreamResolver:
    def __init__(self, upstream_servers: Optional[List[str]] = None, timeout: float = 3.0):
        self.upstream_servers = upstream_servers or DEFAULT_UPSTREAMS
        self.timeout = timeout

    async def resolve(self, query: dns.message.Message) -> Optional[dns.message.Message]:
        """
        Forward DNS query message to upstream resolvers.
        Tries primary upstream via UDP, falling back to secondary or TCP if truncated.
        """
        for server in self.upstream_servers:
            try:
                response = await dns.asyncquery.udp(
                    query,
                    server,
                    timeout=self.timeout
                )
                if response.flags & dns.flags.TC:
                    # Truncated response: retry with TCP
                    response = await dns.asyncquery.tcp(
                        query,
                        server,
                        timeout=self.timeout
                    )
                return response
            except Exception:
                continue

        return None
