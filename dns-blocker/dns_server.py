"""
VORTEX VPN - DNS Filtering Proxy Server
Asynchronous DNS proxy server running on UDP port 53/5353.
Intercepts ad/tracker/malware domains and returns zero-IP blocking records (0.0.0.0 / ::).
"""
import asyncio
from typing import Tuple, Optional
import dns.message
import dns.rdatatype
import dns.rdataclass
import dns.rrset
import dns.flags

from blocklist import DomainBlocklist
from rules import RuleManager
from cache import DNSCache
from resolver import UpstreamResolver


class DNSProtocol(asyncio.DatagramProtocol):
    def __init__(self, server: "DNSFilteringServer"):
        self.server = server
        self.transport: Optional[asyncio.DatagramTransport] = None

    def connection_made(self, transport: asyncio.DatagramTransport):
        self.transport = transport

    def datagram_received(self, data: bytes, addr: Tuple[str, int]):
        asyncio.create_task(self.handle_query(data, addr))

    async def handle_query(self, data: bytes, addr: Tuple[str, int]):
        try:
            query = dns.message.from_wire(data)
        except Exception:
            return  # Malformed DNS packet, drop silently

        if not query.question:
            return

        question = query.question[0]
        qname = question.name.to_text().rstrip(".").lower()
        qtype = question.rdtype
        qclass = question.rdclass

        # Check filtering logic
        is_blocked = False
        if self.server.rule_manager.is_allowed(qname):
            is_blocked = False
        elif (
            self.server.rule_manager.is_custom_blocked(qname) or
            self.server.blocklist.is_blocked(qname)
        ):
            is_blocked = True

        if is_blocked:
            self.server.stats["blocked_count"] += 1
            reply = self.build_blocked_response(query, question)
            if self.transport:
                self.transport.sendto(reply.to_wire(), addr)
            return

        # Allowed Domain - Check in-memory Cache
        self.server.stats["allowed_count"] += 1
        cached_resp = self.server.cache.get(qname, qtype, qclass)
        if cached_resp:
            self.server.stats["cache_hits"] += 1
            cached_resp.id = query.id
            if self.transport:
                self.transport.sendto(cached_resp.to_wire(), addr)
            return

        # Forward to Upstream Resolver
        upstream_resp = await self.server.resolver.resolve(query)
        if upstream_resp:
            self.server.cache.set(qname, qtype, upstream_resp, qclass)
            upstream_resp.id = query.id
            if self.transport:
                self.transport.sendto(upstream_resp.to_wire(), addr)
        else:
            # Server failure fallback
            servfail = dns.message.make_response(query)
            servfail.set_rcode(dns.rcode.SERVFAIL)
            if self.transport:
                self.transport.sendto(servfail.to_wire(), addr)

    def build_blocked_response(self, query: dns.message.Message, question) -> dns.message.Message:
        """Construct response returning 0.0.0.0 or :: for blocked domain."""
        reply = dns.message.make_response(query)
        reply.flags |= dns.flags.AA  # Authoritative answer
        qname = question.name
        qtype = question.rdtype

        if qtype == dns.rdatatype.A:
            rrset = dns.rrset.from_text(qname, 300, dns.rdataclass.IN, dns.rdatatype.A, "0.0.0.0")
            reply.answer.append(rrset)
        elif qtype == dns.rdatatype.AAAA:
            rrset = dns.rrset.from_text(qname, 300, dns.rdataclass.IN, dns.rdatatype.AAAA, "::")
            reply.answer.append(rrset)
        else:
            pass

        return reply


class DNSFilteringServer:
    def __init__(self, host: str = "0.0.0.0", port: int = 5353):
        self.host = host
        self.port = port
        self.blocklist = DomainBlocklist()
        self.rule_manager = RuleManager()
        self.cache = DNSCache()
        self.resolver = UpstreamResolver()
        self.transport: Optional[asyncio.DatagramTransport] = None
        self.stats = {
            "total_queries": 0,
            "blocked_count": 0,
            "allowed_count": 0,
            "cache_hits": 0
        }

    async def start(self):
        loop = asyncio.get_running_loop()
        self.transport, _ = await loop.create_datagram_endpoint(
            lambda: DNSProtocol(self),
            local_addr=(self.host, self.port)
        )

    def stop(self):
        if self.transport:
            self.transport.close()
            self.transport = None
