"""
VORTEX VPN - DNS Blocker Unit Tests
"""
import pytest
import dns.message
import dns.rdatatype
from blocklist import DomainBlocklist
from rules import RuleManager
from cache import DNSCache
from dns_server import DNSFilteringServer, DNSProtocol


def test_domain_blocklist_matching():
    bl = DomainBlocklist(["doubleclick.net", "telemetry.example.com"])
    
    # Exact match
    assert bl.is_blocked("doubleclick.net") is True
    assert bl.is_blocked("telemetry.example.com") is True
    
    # Subdomain match
    assert bl.is_blocked("ad.doubleclick.net") is True
    assert bl.is_blocked("deep.nested.telemetry.example.com") is True
    
    # Clean domain
    assert bl.is_blocked("wikipedia.org") is False
    assert bl.is_blocked("google.com") is False


def test_allowlist_precedence():
    rm = RuleManager()
    rm.block("tracking.com")
    assert rm.is_custom_blocked("tracking.com") is True
    
    # Allow takes precedence
    rm.allow("tracking.com")
    assert rm.is_allowed("tracking.com") is True
    assert rm.is_custom_blocked("tracking.com") is False


def test_dns_cache_ttl():
    cache = DNSCache(max_entries=10, min_ttl=60)
    query = dns.message.make_query("example.com", "A")
    reply = dns.message.make_response(query)
    
    cache.set("example.com", dns.rdatatype.A, reply)
    assert cache.size == 1
    
    cached = cache.get("example.com", dns.rdatatype.A)
    assert cached is not None
    assert cache.get("nonexistent.com", dns.rdatatype.A) is None


def test_blocked_response_synthesis():
    server = DNSFilteringServer(port=5354)
    protocol = DNSProtocol(server)
    
    # Test IPv4 (A) blocked query
    query_a = dns.message.make_query("adservice.google.com", "A")
    resp_a = protocol.build_blocked_response(query_a, query_a.question[0])
    assert len(resp_a.answer) == 1
    assert resp_a.answer[0][0].address == "0.0.0.0"
    
    # Test IPv6 (AAAA) blocked query
    query_aaaa = dns.message.make_query("adservice.google.com", "AAAA")
    resp_aaaa = protocol.build_blocked_response(query_aaaa, query_aaaa.question[0])
    assert len(resp_aaaa.answer) == 1
    assert resp_aaaa.answer[0][0].address == "::"
