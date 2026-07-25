"""HTTP route definitions. Thin layer - all logic lives in services."""
from __future__ import annotations

from fastapi import APIRouter, status

from app.core.config import get_settings
from app.models.schemas import AuditReport, AuditRequest, ErrorResponse, HealthResponse
from app.services.auditor import run_audit

router = APIRouter()
settings = get_settings()

_ERROR_RESPONSES = {
    422: {"model": ErrorResponse, "description": "Invalid request or unprocessable target"},
    502: {"model": ErrorResponse, "description": "Upstream fetch failure"},
    504: {"model": ErrorResponse, "description": "Upstream request timed out"},
}


@router.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check() -> HealthResponse:
    """Lightweight liveness probe for uptime monitors and deploy platforms."""
    return HealthResponse(status="ok", version=settings.app_version)


@router.post(
    "/audit",
    response_model=AuditReport,
    status_code=status.HTTP_200_OK,
    responses=_ERROR_RESPONSES,
    tags=["Audit"],
    summary="Audit a public URL",
)
async def audit_url(payload: AuditRequest) -> AuditReport:
    """Fetch the given URL and return an SEO/structure audit report.

    Raises domain exceptions (see app.core.exceptions) which are translated
    into uniform JSON error responses by the global exception handlers.
    """
    return await run_audit(payload.url)
