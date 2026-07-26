"""Client IP resolution that does not blindly trust X-Forwarded-For."""

from __future__ import annotations

from typing import Iterable


def resolve_client_ip(
    *,
    peer_ip: str | None,
    x_forwarded_for: str | None,
    x_real_ip: str | None,
    trusted_proxy_ips: Iterable[str],
) -> str:
    """
    Resolve the client IP for rate limiting.

    - Always start from the direct TCP peer (`peer_ip`).
    - Only consult forwarding headers when that peer is in `trusted_proxy_ips`.
    - When trusted, walk X-Forwarded-For from the right, skipping trusted hops,
      and return the first untrusted address (the apparent client).
    - Never treat an arbitrary unauthenticated X-Forwarded-For as authoritative.
    """
    peer = (peer_ip or "").strip() or "unknown"
    trusted = {ip.strip() for ip in trusted_proxy_ips if ip and ip.strip()}
    if peer not in trusted:
        return peer

    forwarded = _parse_forwarded_for(x_forwarded_for)
    if forwarded:
        for candidate in reversed(forwarded):
            if candidate not in trusted:
                return candidate
        return forwarded[0]

    real_ip = (x_real_ip or "").strip()
    if real_ip and real_ip not in trusted:
        return real_ip

    return peer


def _parse_forwarded_for(value: str | None) -> list[str]:
    if not value:
        return []
    parts: list[str] = []
    for raw in value.split(","):
        item = raw.strip()
        if not item:
            continue
        # Drop optional port on IPv4 host:port forms only.
        if item.count(":") == 1 and "." in item:
            item = item.split(":", 1)[0].strip()
        if item:
            parts.append(item)
    return parts
