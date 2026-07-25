"""Tests for URL validation and the SSRF guard."""
import pytest

from app.core.exceptions import DisallowedTargetError, InvalidURLError
from app.core.security import enforce_ssrf_guard, validate_url_format


def test_valid_https_url_passes():
    assert validate_url_format("https://example.com") == "https://example.com"


def test_empty_url_is_rejected():
    with pytest.raises(InvalidURLError):
        validate_url_format("   ")


def test_missing_scheme_is_rejected():
    with pytest.raises(InvalidURLError):
        validate_url_format("example.com")


def test_unsupported_scheme_is_rejected():
    with pytest.raises(InvalidURLError):
        validate_url_format("ftp://example.com")


def test_missing_host_is_rejected():
    with pytest.raises(InvalidURLError):
        validate_url_format("https://")


def test_localhost_is_blocked_by_ssrf_guard():
    with pytest.raises(DisallowedTargetError):
        enforce_ssrf_guard("http://localhost:8000")


def test_loopback_ip_is_blocked_by_ssrf_guard():
    with pytest.raises(DisallowedTargetError):
        enforce_ssrf_guard("http://127.0.0.1")
