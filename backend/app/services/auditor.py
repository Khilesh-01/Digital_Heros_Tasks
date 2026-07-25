"""Orchestrates a full page audit: validate -> fetch -> parse -> report."""
from __future__ import annotations

import logging

from app.core.security import enforce_ssrf_guard, validate_url_format
from app.models.schemas import AuditReport
from app.services.fetcher import fetch_page
from app.services.parser import parse_html

logger = logging.getLogger(__name__)


async def run_audit(raw_url: str) -> AuditReport:
    url = validate_url_format(raw_url)
    enforce_ssrf_guard(url)

    result = await fetch_page(url)
    parsed = parse_html(result.body)

    logger.info(
        "Audit complete url=%s status=%s time_ms=%s words=%s",
        result.final_url,
        result.status_code,
        result.response_time_ms,
        parsed.word_count,
    )

    return AuditReport(
        url=result.final_url,
        status=result.status_code,
        response_time_ms=result.response_time_ms,
        title=parsed.title,
        meta_description=parsed.meta_description,
        h1_count=parsed.h1_count,
        images_without_alt=parsed.images_without_alt,
        word_count=parsed.word_count,
        total_images=parsed.total_images,
        canonical_url=parsed.canonical_url,
        og_title=parsed.og_title,
        favicon_present=parsed.favicon_present,
        language=parsed.language,
        content_size_bytes=result.content_size_bytes,
        seo_score=parsed.seo_score,
    )
