"""Pydantic models for request/response contracts."""
from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class AuditRequest(BaseModel):
    """Request body for POST /audit."""

    url: str = Field(
        ...,
        description="The public URL to audit.",
        examples=["https://example.com"],
        min_length=1,
        max_length=2048,
    )

    @field_validator("url")
    @classmethod
    def strip_whitespace(cls, value: str) -> str:
        return value.strip()


class AuditReport(BaseModel):
    """Successful audit result, matching the assignment's response contract."""

    url: str = Field(..., description="The final URL that was audited (post-redirects).")
    status: int = Field(..., description="HTTP status code returned by the target page.")
    response_time_ms: int = Field(..., description="Time taken to fetch the page, in milliseconds.")
    title: str | None = Field(None, description="The page's <title> content, if present.")
    meta_description: str | None = Field(None, description="The page's meta description, if present.")
    h1_count: int = Field(..., description="Number of <h1> elements found on the page.")
    images_without_alt: int = Field(..., description="Number of <img> tags missing usable alt text.")
    word_count: int = Field(..., description="Approximate count of visible words on the page.")

    # --- Bonus / extended fields (do not break the required contract) ---
    total_images: int | None = Field(None, description="Total number of <img> tags found.")
    canonical_url: str | None = Field(None, description="Canonical URL, if declared.")
    og_title: str | None = Field(None, description="Open Graph title, if present.")
    favicon_present: bool | None = Field(None, description="Whether a favicon reference was found.")
    language: str | None = Field(None, description="Declared page language (html lang attribute).")
    content_size_bytes: int | None = Field(None, description="Size of the response body in bytes.")
    seo_score: int | None = Field(None, description="Lightweight 0-100 heuristic SEO health score.")


class ErrorResponse(BaseModel):
    """Uniform error envelope returned for every failure case. Never contains a stack trace."""

    error_code: str = Field(..., description="Machine-readable error identifier.")
    message: str = Field(..., description="Human-readable, user-safe explanation of the failure.")


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str
