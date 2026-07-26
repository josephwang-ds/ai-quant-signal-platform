"""ASGI middleware for body-size limits, rate limiting, and safe request logs."""

from __future__ import annotations

import json
import logging
import time
from typing import Any

from starlette.datastructures import Headers
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.security.client_ip import resolve_client_ip
from app.security.logging_redaction import safe_log_extra
from app.security.rate_limit import check_rate_limit, classify_endpoint
from app.security.settings import get_demo_protection_settings

logger = logging.getLogger("app.security")

RATE_LIMIT_DETAIL = "Too many requests. Please wait a moment and try again."
BODY_TOO_LARGE_DETAIL = "Request body is too large for this demo deployment."


class DemoProtectionMiddleware:
    """Body size + rate-limit gate with redacted operational logging."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        settings = get_demo_protection_settings()
        headers = Headers(scope=scope)
        method = scope.get("method", "GET").upper()
        path = scope.get("path", "") or "/"
        peer = None
        client = scope.get("client")
        if client:
            peer = client[0]

        client_ip = resolve_client_ip(
            peer_ip=peer,
            x_forwarded_for=headers.get("x-forwarded-for"),
            x_real_ip=headers.get("x-real-ip"),
            trusted_proxy_ips=settings.trusted_proxy_ips,
        )

        content_length = headers.get("content-length")
        if content_length is not None:
            try:
                length = int(content_length)
            except ValueError:
                length = -1
            if length > settings.max_request_body_bytes:
                await _send_json(
                    send,
                    status=413,
                    body={"detail": BODY_TOO_LARGE_DETAIL},
                )
                return

        tier = classify_endpoint(method, path)
        limited = check_rate_limit(client_key=f"{tier}:{client_ip}", tier=tier)
        if limited is not None:
            await _send_json(
                send,
                status=429,
                body={"detail": RATE_LIMIT_DETAIL},
                headers=[
                    (
                        b"retry-after",
                        str(limited.retry_after_seconds).encode("ascii"),
                    ),
                ],
            )
            logger.info(
                "rate_limit_exceeded",
                extra=safe_log_extra(
                    {
                        "endpoint": path,
                        "method": method,
                        "status_code": 429,
                        "tier": limited.tier,
                    }
                ),
            )
            return

        try:
            receive = await _receive_with_body_limit(
                receive, max_bytes=settings.max_request_body_bytes
            )
        except _BodyTooLarge:
            await _send_json(
                send,
                status=413,
                body={"detail": BODY_TOO_LARGE_DETAIL},
            )
            return

        started = time.perf_counter()
        status_code_holder = {"value": 500}

        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                status_code_holder["value"] = int(message.get("status", 500))
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            duration_ms = int((time.perf_counter() - started) * 1000)
            logger.info(
                "request_completed",
                extra=safe_log_extra(
                    {
                        "endpoint": path,
                        "method": method,
                        "status_code": status_code_holder["value"],
                        "duration_ms": duration_ms,
                        "tier": tier,
                    }
                ),
            )


class _BodyTooLarge(Exception):
    pass


async def _receive_with_body_limit(receive: Receive, *, max_bytes: int) -> Receive:
    """Buffer the request body up to max_bytes, then replay it to the app."""
    chunks: list[bytes] = []
    total = 0
    more_body = True
    while more_body:
        message = await receive()
        if message["type"] != "http.request":
            # Unexpected first message; pass through as a one-shot replay.
            async def passthrough() -> Message:
                return message

            return passthrough
        chunk = message.get("body", b"") or b""
        total += len(chunk)
        if total > max_bytes:
            raise _BodyTooLarge()
        chunks.append(chunk)
        more_body = bool(message.get("more_body"))

    body = b"".join(chunks)
    sent = False

    async def replay() -> Message:
        nonlocal sent
        if not sent:
            sent = True
            return {"type": "http.request", "body": body, "more_body": False}
        return await receive()

    return replay


async def _send_json(
    send: Send,
    *,
    status: int,
    body: dict[str, Any],
    headers: list[tuple[bytes, bytes]] | None = None,
) -> None:
    payload = json.dumps(body).encode("utf-8")
    response_headers: list[tuple[bytes, bytes]] = [
        (b"content-type", b"application/json"),
        (b"content-length", str(len(payload)).encode("ascii")),
    ]
    if headers:
        response_headers.extend(headers)
    await send(
        {
            "type": "http.response.start",
            "status": status,
            "headers": response_headers,
        }
    )
    await send({"type": "http.response.body", "body": payload})
