"""
RASTRO — Blindagem anti-SSRF (Sprint 7)

Bloqueia URLs que apontem para redes internas, loopback, metadata
endpoints de cloud ou hostnames internos ANTES de qualquer scraping.

Uso:
    from backend.security import check_ssrf, SSRFError

    try:
        check_ssrf(url)
    except SSRFError as e:
        # retornar 422 com e.code e e.message
"""

from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse

# ── Redes bloqueadas (RFC 1918, RFC 5735, RFC 4291 e derivados) ───
_BLOCKED_NETWORKS: list[ipaddress.IPv4Network | ipaddress.IPv6Network] = [
    # IPv4 — reservados / privados / link-local
    ipaddress.ip_network("0.0.0.0/8"),           # "this" network
    ipaddress.ip_network("10.0.0.0/8"),           # privado (RFC 1918)
    ipaddress.ip_network("100.64.0.0/10"),        # Carrier-grade NAT (RFC 6598)
    ipaddress.ip_network("127.0.0.0/8"),          # loopback (RFC 990)
    ipaddress.ip_network("169.254.0.0/16"),       # link-local / IMDS AWS·GCP·Azure
    ipaddress.ip_network("172.16.0.0/12"),        # privado (RFC 1918)
    ipaddress.ip_network("192.0.0.0/24"),         # IETF Protocol Assignments
    ipaddress.ip_network("192.0.2.0/24"),         # TEST-NET-1 (documentação)
    ipaddress.ip_network("192.168.0.0/16"),       # privado (RFC 1918)
    ipaddress.ip_network("198.18.0.0/15"),        # benchmark testing (RFC 2544)
    ipaddress.ip_network("198.51.100.0/24"),      # TEST-NET-2 (documentação)
    ipaddress.ip_network("203.0.113.0/24"),       # TEST-NET-3 (documentação)
    ipaddress.ip_network("240.0.0.0/4"),          # reservado (RFC 1112)
    ipaddress.ip_network("255.255.255.255/32"),   # broadcast

    # IPv6 — reservados / privados / link-local
    ipaddress.ip_network("::1/128"),              # loopback
    ipaddress.ip_network("::/128"),               # endereço não especificado
    ipaddress.ip_network("::ffff:0:0/96"),        # IPv4-mapped
    ipaddress.ip_network("64:ff9b::/96"),         # IPv4/IPv6 translation (RFC 6052)
    ipaddress.ip_network("fc00::/7"),             # unique local (RFC 4193)
    ipaddress.ip_network("fe80::/10"),            # link-local (RFC 4291)
    ipaddress.ip_network("ff00::/8"),             # multicast
]

# ── Hostnames internos exatos ──────────────────────────────────────
_BLOCKED_HOSTNAMES: frozenset[str] = frozenset({
    "localhost",
    "broadcasthost",
    "metadata",
    "metadata.google.internal",   # GCP IMDS
})

# ── Sufixos de TLD internos ────────────────────────────────────────
_BLOCKED_SUFFIXES: tuple[str, ...] = (
    ".local",
    ".internal",
    ".corp",
    ".lan",
    ".home",
    ".intranet",
    ".localhost",
    ".example",   # RFC 2606 — domínio reservado para testes
    ".invalid",   # RFC 2606
    ".test",      # RFC 2606
)


# ── Exceção pública ───────────────────────────────────────────────

class SSRFError(ValueError):
    """
    Levantada quando uma URL é rejeitada pela blindagem anti-SSRF.

    Attributes:
        code: Código de erro (ex.: "SSRF_BLOCKED_IP").
        message: Mensagem segura para exibir ao usuário.
    """

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


# ── API pública ───────────────────────────────────────────────────

def check_ssrf(url: str) -> None:
    """
    Valida que a URL não aponta para redes internas ou metadata endpoints.

    Deve ser chamada ANTES de qualquer scraping (Playwright, httpx, etc.).
    Levanta :class:`SSRFError` se a URL for considerada perigosa.

    Fluxo de verificação:
        1. Hostname bloqueado exato
        2. Sufixo de TLD interno
        3. IP literal → verificar range
        4. Resolução DNS → verificar todos os IPs retornados
    """
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower().rstrip(".")

    if not host:
        raise SSRFError("SSRF_INVALID_HOST", "Hostname ausente ou inválido.")

    # 1. Hostname bloqueado exato
    if host in _BLOCKED_HOSTNAMES:
        raise SSRFError(
            "SSRF_BLOCKED_HOSTNAME",
            "URL aponta para um hostname interno bloqueado por política de segurança.",
        )

    # 2. Sufixo de TLD interno
    for suffix in _BLOCKED_SUFFIXES:
        if host.endswith(suffix):
            raise SSRFError(
                "SSRF_BLOCKED_HOSTNAME",
                "URL aponta para um domínio com sufixo interno bloqueado "
                f"(\"{suffix}\").",
            )

    # 3. IP literal (sem resolução DNS)
    try:
        ip_obj = ipaddress.ip_address(host)
        _assert_ip_is_public(ip_obj)
        return  # IP público — aprovado
    except ValueError:
        pass  # não é IP literal → seguir para DNS

    # 4. Resolução DNS → inspeciona cada IP retornado
    try:
        addrinfos = socket.getaddrinfo(
            host, None,
            family=socket.AF_UNSPEC,
            type=socket.SOCK_STREAM,
        )
    except socket.gaierror as exc:
        # DNS falhou: não sabemos o IP → bloquear por precaução
        raise SSRFError(
            "SSRF_DNS_FAILURE",
            f"Não foi possível resolver o hostname \"{host}\". "
            "Verifique se a URL está correta e acessível publicamente.",
        ) from exc

    for _family, _type, _proto, _canonname, sockaddr in addrinfos:
        raw_ip = sockaddr[0].split("%")[0]  # remove zona IPv6 (ex: "fe80::1%lo0")
        try:
            _assert_ip_is_public(ipaddress.ip_address(raw_ip))
        except SSRFError:
            raise  # re-raise com o código original


# ── Helpers privados ──────────────────────────────────────────────

def _assert_ip_is_public(
    ip: ipaddress.IPv4Address | ipaddress.IPv6Address,
) -> None:
    """Levanta SSRFError se o IP pertencer a qualquer range bloqueado."""
    for network in _BLOCKED_NETWORKS:
        if ip.version == network.version and ip in network:
            raise SSRFError(
                "SSRF_BLOCKED_IP",
                "URL aponta para um endereço IP reservado ou privado. "
                "O RASTRO não acessa redes internas.",
            )
