import ipaddress
import socket
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, HttpUrl, field_validator


SSRF_BLOCKED_HOSTS = {"localhost", "0.0.0.0"}

SSRF_BLOCKED_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
]


def _is_ssrf_url(url: str) -> bool:
    """Возвращает True если URL ведёт на приватный или внутренний адрес."""
    try:
        hostname = urlparse(url).hostname
        if not hostname:
            return True
        if hostname.lower() in SSRF_BLOCKED_HOSTS:
            return True
        resolved = socket.getaddrinfo(hostname, None)
        for *_, sockaddr in resolved:
            ip = ipaddress.ip_address(sockaddr[0])
            if any(ip in net for net in SSRF_BLOCKED_NETWORKS):
                return True
    except (socket.gaierror, ValueError):
        return True
    return False


class ShortURLCreate(BaseModel):
    original_url: HttpUrl

    @field_validator("original_url")
    @classmethod
    def validate_no_ssrf(cls, v: HttpUrl) -> HttpUrl:
        if str(v.scheme) not in ("http", "https"):
            raise ValueError("Only http and https schemes are allowed.")
        if _is_ssrf_url(str(v)):
            raise ValueError("URL points to a private or reserved address.")
        return v


class ShortURLResponse(BaseModel):
    short_code: str
    original_url: str
    clicks: int

    model_config = ConfigDict(from_attributes=True)


class ShortURLDeleteResponse(BaseModel):
    status: str = "deleted"
    short_code: str
