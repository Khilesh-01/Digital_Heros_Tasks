"""Integration tests for the FastAPI routes.

The HTTP fetch layer is mocked so these tests run offline and
deterministically - only our own code is under test here.
"""
import httpx
import pytest

from app.core.exceptions import (
    DNSResolutionError,
    RequestTimeoutError,
    UnsupportedContentTypeError,
    UpstreamHTTPError,
)
from app.services import auditor
from app.services.fetcher import FetchResult

SAMPLE_HTML = """
<html lang="en"><head><title>Sample</title>
<meta name="description" content="A sample page."></head>
<body><h1>Hello</h1><p>Some sample words for counting purposes here.</p>
<img src="a.png"></body></html>
"""


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "version" in body


def test_audit_happy_path(client, monkeypatch):
    async def fake_fetch_page(url: str) -> FetchResult:
        return FetchResult(
            final_url=url,
            status_code=200,
            response_time_ms=42,
            content_type="text/html",
            body=SAMPLE_HTML,
            content_size_bytes=len(SAMPLE_HTML),
        )

    monkeypatch.setattr(auditor, "fetch_page", fake_fetch_page)

    response = client.post("/audit", json={"url": "https://example.com"})
    assert response.status_code == 200

    body = response.json()
    assert body["status"] == 200
    assert body["title"] == "Sample"
    assert body["meta_description"] == "A sample page."
    assert body["h1_count"] == 1
    assert body["images_without_alt"] == 1
    assert body["word_count"] > 0
    assert body["response_time_ms"] == 42


def test_audit_rejects_invalid_url(client):
    response = client.post("/audit", json={"url": "not-a-url"})
    assert response.status_code == 422
    body = response.json()
    assert body["error_code"] == "invalid_url"
    assert "message" in body


def test_audit_rejects_empty_url(client):
    response = client.post("/audit", json={"url": ""})
    assert response.status_code in (422,)
    body = response.json()
    assert "message" in body


def test_audit_handles_timeout(client, monkeypatch):
    async def fake_fetch_page(url: str) -> FetchResult:
        raise RequestTimeoutError()

    monkeypatch.setattr(auditor, "fetch_page", fake_fetch_page)

    response = client.post("/audit", json={"url": "https://slow-example.com"})
    assert response.status_code == 504
    assert response.json()["error_code"] == "timeout"


def test_audit_handles_dns_failure(client, monkeypatch):
    async def fake_fetch_page(url: str) -> FetchResult:
        raise DNSResolutionError()

    monkeypatch.setattr(auditor, "fetch_page", fake_fetch_page)

    response = client.post("/audit", json={"url": "https://does-not-exist.invalid"})
    assert response.status_code == 502
    assert response.json()["error_code"] == "dns_error"


def test_audit_handles_non_html_content(client, monkeypatch):
    async def fake_fetch_page(url: str) -> FetchResult:
        raise UnsupportedContentTypeError()

    monkeypatch.setattr(auditor, "fetch_page", fake_fetch_page)

    response = client.post("/audit", json={"url": "https://example.com/file.pdf"})
    assert response.status_code == 422
    assert response.json()["error_code"] == "unsupported_content_type"


def test_audit_handles_upstream_404(client, monkeypatch):
    async def fake_fetch_page(url: str) -> FetchResult:
        raise UpstreamHTTPError(404)

    monkeypatch.setattr(auditor, "fetch_page", fake_fetch_page)

    response = client.post("/audit", json={"url": "https://example.com/missing"})
    assert response.status_code == 502
    assert response.json()["error_code"] == "upstream_http_error"


def test_audit_never_leaks_stack_trace_on_unexpected_error(client, monkeypatch):
    async def fake_fetch_page(url: str) -> FetchResult:
        raise ValueError("boom - something truly unexpected")

    monkeypatch.setattr(auditor, "fetch_page", fake_fetch_page)

    response = client.post("/audit", json={"url": "https://example.com"})
    assert response.status_code == 500
    body = response.json()
    assert body["error_code"] == "internal_error"
    assert "boom" not in body["message"]
    assert "Traceback" not in body["message"]
