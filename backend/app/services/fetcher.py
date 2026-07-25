"""Responsible for one thing only: safely fetching a URL over HTTP.

Translates every possible httpx failure mode into a well-defined
PagePulseError so callers never need to know about httpx internals.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass

import httpx

from app.core.config import get_settings
from app.core.exceptions import (
    ConnectionFailedError,
    DNSResolutionError,
    RequestTimeoutError,
    ResponseTooLargeError,
    SSLVerificationError,
    TooManyRedirectsError,
    UnsupportedContentTypeError,
    UpstreamHTTPError,
)

logger = logging.getLogger(__name__)
settings = get_settings()

_HTML_CONTENT_TYPES = ("text/html", "application/xhtml+xml")


@dataclass(frozen=True)
class FetchResult:
    """Everything downstream parsing/reporting needs from a fetch."""

    final_url: str
    status_code: int
    response_time_ms: int
    content_type: str
    body: str
    content_size_bytes: int


async def fetch_page(url: str) -> FetchResult:
    """Fetch `url`, returning a FetchResult or raising a PagePulseError subclass."""
    timeout = httpx.Timeout(
        timeout=settings.request_timeout_seconds,
        connect=settings.connect_timeout_seconds,
    )
    headers = {"User-Agent": settings.user_agent, "Accept": "text/html,application/xhtml+xml"}

    last_exc: Exception | None = None

    for attempt in range(settings.max_retries + 1):
        started = time.perf_counter()
        try:
            async with httpx.AsyncClient(
                timeout=timeout,
                follow_redirects=True,
                max_redirects=settings.max_redirects,
                headers=headers,
            ) as client:
                async with client.stream("GET", url) as response:
                    elapsed_ms = int((time.perf_counter() - started) * 1000)
                    return await _consume_response(response, elapsed_ms)

        except httpx.TooManyRedirects as exc:
            raise TooManyRedirectsError() from exc
        except httpx.ConnectTimeout as exc:
            last_exc = exc
        except httpx.ReadTimeout as exc:
            last_exc = exc
        except httpx.TimeoutException as exc:
            last_exc = exc
        except httpx.ConnectError as exc:
            last_exc = _translate_connect_error(exc)
            break  # DNS/connection-refused errors are not worth retrying.
        except httpx.RequestError as exc:
            last_exc = ConnectionFailedError(str(exc))
            break

        # Simple linear backoff between retry attempts.
        if attempt < settings.max_retries:
            logger.warning("Retrying fetch for %s (attempt %s)", url, attempt + 1)
            time.sleep(settings.retry_backoff_seconds)

    if isinstance(last_exc, PagePulseErrorTypes):
        raise last_exc
    raise RequestTimeoutError()


# httpx wraps SSL errors inside ConnectError; inspect the cause to disambiguate.
def _translate_connect_error(exc: httpx.ConnectError) -> Exception:
    cause = str(exc).lower()
    if "ssl" in cause or "certificate" in cause:
        return SSLVerificationError()
    if "name or service not known" in cause or "nodename nor servname" in cause or "getaddrinfo failed" in cause:
        return DNSResolutionError()
    return ConnectionFailedError()


async def _consume_response(response: httpx.Response, elapsed_ms: int) -> FetchResult:
    content_type = response.headers.get("content-type", "").split(";")[0].strip().lower()

    if response.status_code >= 400:
        raise UpstreamHTTPError(response.status_code)

    if content_type and not any(content_type.startswith(ct) for ct in _HTML_CONTENT_TYPES):
        raise UnsupportedContentTypeError(
            f"Expected an HTML page but received content-type '{content_type}'."
        )

    chunks: list[bytes] = []
    total = 0
    async for chunk in response.aiter_bytes():
        total += len(chunk)
        if total > settings.max_response_bytes:
            raise ResponseTooLargeError()
        chunks.append(chunk)

    raw = b"".join(chunks)
    # Decode defensively - malformed/mislabeled encodings should never crash the app.
    body = raw.decode(response.encoding or "utf-8", errors="replace") if raw else ""

    return FetchResult(
        final_url=str(response.url),
        status_code=response.status_code,
        response_time_ms=elapsed_ms,
        content_type=content_type or "unknown",
        body=body,
        content_size_bytes=total,
    )


# Grouped for the isinstance check above - anything we deliberately raised mid-loop.
PagePulseErrorTypes = (
    ConnectionFailedError,
    DNSResolutionError,
    SSLVerificationError,
    RequestTimeoutError,
)
