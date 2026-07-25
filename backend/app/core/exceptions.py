"""Domain-specific exceptions.

Each exception maps 1:1 to a user-facing error code and HTTP status,
translated centrally in app.api.error_handlers. Business logic never
touches HTTP concerns directly - it just raises these.
"""
from __future__ import annotations


class PagePulseError(Exception):
    """Base class for all expected, handled application errors."""

    error_code: str = "internal_error"
    http_status: int = 500
    message: str = "An unexpected error occurred."

    def __init__(self, message: str | None = None):
        self.message = message or self.message
        super().__init__(self.message)


class InvalidURLError(PagePulseError):
    error_code = "invalid_url"
    http_status = 422
    message = "The provided URL is not valid."


class DisallowedTargetError(PagePulseError):
    """Raised when a URL resolves to a private/internal network target (SSRF guard)."""

    error_code = "disallowed_target"
    http_status = 422
    message = "This URL targets a private or reserved network address and cannot be audited."


class DNSResolutionError(PagePulseError):
    error_code = "dns_error"
    http_status = 502
    message = "The domain name could not be resolved."


class ConnectionFailedError(PagePulseError):
    error_code = "connection_failed"
    http_status = 502
    message = "Could not connect to the target server."


class RequestTimeoutError(PagePulseError):
    error_code = "timeout"
    http_status = 504
    message = "The request to the target page timed out."


class TooManyRedirectsError(PagePulseError):
    error_code = "redirect_loop"
    http_status = 502
    message = "The URL resulted in too many redirects."


class SSLVerificationError(PagePulseError):
    error_code = "ssl_error"
    http_status = 502
    message = "The site's SSL certificate could not be verified."


class UnsupportedContentTypeError(PagePulseError):
    error_code = "unsupported_content_type"
    http_status = 422
    message = "The URL did not return an HTML document."


class ResponseTooLargeError(PagePulseError):
    error_code = "response_too_large"
    http_status = 422
    message = "The page response exceeded the maximum allowed size."


class UpstreamHTTPError(PagePulseError):
    """The remote server responded, but with an error status (4xx/5xx)."""

    error_code = "upstream_http_error"
    http_status = 502
    message = "The target page returned an error response."

    def __init__(self, status_code: int, message: str | None = None):
        self.status_code = status_code
        super().__init__(message or f"The target page responded with HTTP {status_code}.")
