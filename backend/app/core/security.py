"""URL validation and SSRF-mitigation helpers.

This is a best-effort guard appropriate for an assignment/MVP scope, not a
bulletproof SSRF defense. It rejects obviously dangerous targets
(localhost, private/reserved IP ranges, non-http(s) schemes) before any
network call is made, and re-checks resolved IPs.
"""
from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse

from app.core.config import get_settings
from app.core.exceptions import DisallowedTargetError, InvalidURLError

settings = get_settings()

_DISALLOWED_HOSTNAMES = {"localhost", "localhost.localdomain"}


def validate_url_format(raw_url: str) -> str:
    """Validate basic URL structure and scheme. Returns the normalized URL."""
    if not raw_url or not raw_url.strip():
        raise InvalidURLError("URL must not be empty.")

    candidate = raw_url.strip()
    parsed = urlparse(candidate)

    if parsed.scheme.lower() not in settings.allowed_schemes_list:
        raise InvalidURLError(
            f"URL scheme must be one of {settings.allowed_schemes_list}."
        )
    if not parsed.netloc or not parsed.hostname:
        raise InvalidURLError("URL must include a valid host.")
    if "." not in parsed.hostname and parsed.hostname != "localhost":
        # Extremely permissive but catches obvious typos like "https://example"
        raise InvalidURLError("URL host does not look like a valid domain.")

    return candidate


def _is_disallowed_ip(ip_str: str) -> bool:
    try:
        ip = ipaddress.ip_address(ip_str)
    except ValueError:
        return True  # If we can't parse it, don't trust it.

    return (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    )


def enforce_ssrf_guard(raw_url: str) -> None:
    """Reject URLs that point at localhost or private/reserved network ranges."""
    if settings.allow_private_network_targets:
        return

    hostname = urlparse(raw_url).hostname or ""
    if hostname.lower() in _DISALLOWED_HOSTNAMES:
        raise DisallowedTargetError()

    try:
        resolved = socket.getaddrinfo(hostname, None)
    except socket.gaierror:
        # Let the fetcher surface this as a proper DNS error later; not our job here.
        return

    for family, _, _, _, sockaddr in resolved:
        ip_str = sockaddr[0]
        if _is_disallowed_ip(ip_str):
            raise DisallowedTargetError(
                f"Resolved address {ip_str} is a private/reserved network target."
            )
