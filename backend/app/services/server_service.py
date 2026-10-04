"""
VORTEX VPN - Server Fleet & Fastest Server Selection Service
Manages VPN nodes across countries and computes optimal server routing.
"""
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Tuple
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.server import VPNServer
from backend.app.schemas.server import ServerCreateRequest, ServerUpdateRequest, ServerHealthReport
from backend.app.services.crypto_service import WireGuardCryptoService


class ServerService:
    @staticmethod
    async def list_servers(db: AsyncSession, only_active: bool = True) -> List[VPNServer]:
        """Retrieve all VPN servers."""
        stmt = select(VPNServer)
        if only_active:
            stmt = stmt.where(VPNServer.is_active == True)
        stmt = stmt.order_by(VPNServer.country.asc(), VPNServer.city.asc())
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_server_by_id(db: AsyncSession, server_id: int) -> Optional[VPNServer]:
        """Fetch server by primary key."""
        stmt = select(VPNServer).where(VPNServer.id == server_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_servers_by_country(db: AsyncSession, country_code: str) -> List[VPNServer]:
        """Fetch all servers in a specified country."""
        stmt = select(VPNServer).where(
            and_(
                VPNServer.country_code == country_code.upper(),
                VPNServer.is_active == True
            )
        ).order_by(VPNServer.latency_ms.asc())
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def select_fastest_server(
        db: AsyncSession,
        country_code: Optional[str] = None
    ) -> Tuple[Optional[VPNServer], str, int]:
        """
        Optimal server selection algorithm based on real-time health, latency, load, and availability.
        Returns:
            Tuple[Optional[VPNServer], reason_str, evaluated_nodes_count]
        """
        stmt = select(VPNServer).where(
            and_(
                VPNServer.is_active == True,
                VPNServer.status == "online"
            )
        )
        if country_code:
            stmt = stmt.where(VPNServer.country_code == country_code.upper())

        result = await db.execute(stmt)
        candidate_servers = list(result.scalars().all())

        if not candidate_servers:
            # Fallback: check if degraded servers are available
            fallback_stmt = select(VPNServer).where(VPNServer.is_active == True)
            if country_code:
                fallback_stmt = fallback_stmt.where(VPNServer.country_code == country_code.upper())
            fallback_result = await db.execute(fallback_stmt)
            candidate_servers = list(fallback_result.scalars().all())
            if not candidate_servers:
                return None, "No active VPN servers available matching criteria", 0

        # Score candidate servers (lower score = superior performance)
        candidate_servers.sort(key=lambda s: s.score)
        selected = candidate_servers[0]
        
        reason = (
            f"Selected {selected.city}, {selected.country} with optimal score of {selected.score} "
            f"(Latency: {selected.latency_ms}ms, Load: {selected.load_percentage}%, Loss: {selected.packet_loss}%)"
        )
        return selected, reason, len(candidate_servers)

    @staticmethod
    async def create_server(db: AsyncSession, req: ServerCreateRequest) -> VPNServer:
        """Register a new VPN server node."""
        server = VPNServer(
            country=req.country,
            country_code=req.country_code.upper(),
            city=req.city,
            hostname=req.hostname,
            public_ip=req.public_ip,
            wireguard_endpoint=req.wireguard_endpoint,
            wireguard_port=req.wireguard_port,
            wireguard_public_key=req.wireguard_public_key,
            internal_subnet=req.internal_subnet,
            capacity=req.capacity,
            status="online",
            is_active=True,
            last_health_check=datetime.now(timezone.utc)
        )
        db.add(server)
        await db.commit()
        await db.refresh(server)
        return server

    @staticmethod
    async def update_health(db: AsyncSession, report: ServerHealthReport) -> Optional[VPNServer]:
        """Update live telemetry metrics reported by server agent."""
        stmt = select(VPNServer).where(VPNServer.hostname == report.hostname)
        result = await db.execute(stmt)
        server = result.scalar_one_or_none()
        if not server:
            return None

        server.latency_ms = report.latency_ms
        server.packet_loss = report.packet_loss
        server.cpu_usage = report.cpu_usage
        server.memory_usage = report.memory_usage
        server.bandwidth_usage_mbps = report.bandwidth_usage_mbps
        server.active_connections = report.active_connections
        server.status = "online" if report.wireguard_status == "active" else "degraded"
        server.last_health_check = datetime.now(timezone.utc)

        await db.commit()
        await db.refresh(server)
        return server

    @staticmethod
    async def seed_initial_fleet(db: AsyncSession) -> None:
        """Seed initial multi-country server fleet if table is empty."""
        stmt = select(VPNServer)
        result = await db.execute(stmt)
        existing = result.scalars().first()
        if existing:
            return  # Fleet already populated

        # Seed global nodes with valid WireGuard public keys
        nodes = [
            {
                "country": "Germany", "country_code": "DE", "city": "Frankfurt",
                "hostname": "de-fra-01.vortexvpn.net", "public_ip": "194.36.191.10",
                "wireguard_endpoint": "de-fra-01.vortexvpn.net", "latency_ms": 38.0,
                "packet_loss": 0.0, "cpu_usage": 18.0, "memory_usage": 32.0,
                "bandwidth_usage_mbps": 24.5, "capacity": 2000, "active_connections": 142
            },
            {
                "country": "United States", "country_code": "US", "city": "New York",
                "hostname": "us-nyc-01.vortexvpn.net", "public_ip": "143.244.200.5",
                "wireguard_endpoint": "us-nyc-01.vortexvpn.net", "latency_ms": 68.0,
                "packet_loss": 0.1, "cpu_usage": 22.0, "memory_usage": 40.0,
                "bandwidth_usage_mbps": 45.2, "capacity": 2500, "active_connections": 230
            },
            {
                "country": "India", "country_code": "IN", "city": "Mumbai",
                "hostname": "in-bom-01.vortexvpn.net", "public_ip": "103.159.214.2",
                "wireguard_endpoint": "in-bom-01.vortexvpn.net", "latency_ms": 22.0,
                "packet_loss": 0.0, "cpu_usage": 14.0, "memory_usage": 28.0,
                "bandwidth_usage_mbps": 18.3, "capacity": 1500, "active_connections": 95
            },
            {
                "country": "United Kingdom", "country_code": "GB", "city": "London",
                "hostname": "gb-lon-01.vortexvpn.net", "public_ip": "185.193.124.8",
                "wireguard_endpoint": "gb-lon-01.vortexvpn.net", "latency_ms": 45.0,
                "packet_loss": 0.0, "cpu_usage": 19.0, "memory_usage": 35.0,
                "bandwidth_usage_mbps": 30.1, "capacity": 2000, "active_connections": 160
            },
            {
                "country": "Singapore", "country_code": "SG", "city": "Singapore",
                "hostname": "sg-sin-01.vortexvpn.net", "public_ip": "139.180.192.15",
                "wireguard_endpoint": "sg-sin-01.vortexvpn.net", "latency_ms": 48.0,
                "packet_loss": 0.0, "cpu_usage": 16.0, "memory_usage": 29.0,
                "bandwidth_usage_mbps": 21.0, "capacity": 1500, "active_connections": 110
            },
            {
                "country": "Netherlands", "country_code": "NL", "city": "Amsterdam",
                "hostname": "nl-ams-01.vortexvpn.net", "public_ip": "194.187.249.20",
                "wireguard_endpoint": "nl-ams-01.vortexvpn.net", "latency_ms": 41.0,
                "packet_loss": 0.0, "cpu_usage": 20.0, "memory_usage": 36.0,
                "bandwidth_usage_mbps": 28.0, "capacity": 2000, "active_connections": 180
            }
        ]

        for n in nodes:
            _, pub_key = WireGuardCryptoService.generate_keypair()
            server = VPNServer(
                country=n["country"],
                country_code=n["country_code"],
                city=n["city"],
                hostname=n["hostname"],
                public_ip=n["public_ip"],
                wireguard_endpoint=f"{n['wireguard_endpoint']}:51820",
                wireguard_port=51820,
                wireguard_public_key=pub_key,
                internal_subnet="10.8.0.0/24",
                latency_ms=n["latency_ms"],
                packet_loss=n["packet_loss"],
                cpu_usage=n["cpu_usage"],
                memory_usage=n["memory_usage"],
                bandwidth_usage_mbps=n["bandwidth_usage_mbps"],
                capacity=n["capacity"],
                active_connections=n["active_connections"],
                status="online",
                is_active=True,
                last_health_check=datetime.now(timezone.utc)
            )
            db.add(server)

        await db.commit()
