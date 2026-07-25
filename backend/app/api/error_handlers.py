"""Centralized exception -> HTTP response translation.

Nothing in the app should ever leak a raw stack trace to the client. Every
handled error becomes a clean {error_code, message} JSON body; anything
unanticipated is caught by the catch-all handler and logged server-side.
"""
from __future__ import annotations

import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.exceptions import PagePulseError
from app.models.schemas import ErrorResponse

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(PagePulseError)
    async def handle_page_pulse_error(request: Request, exc: PagePulseError) -> JSONResponse:
        logger.info("Handled error %s: %s (%s)", exc.error_code, exc.message, request.url)
        return JSONResponse(
            status_code=exc.http_status,
            content=ErrorResponse(error_code=exc.error_code, message=exc.message).model_dump(),
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        first_error = exc.errors()[0] if exc.errors() else {}
        field = ".".join(str(loc) for loc in first_error.get("loc", []) if loc != "body")
        detail = first_error.get("msg", "Invalid request payload.")
        message = f"{field}: {detail}" if field else detail
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=ErrorResponse(error_code="validation_error", message=message).model_dump(),
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception while processing %s", request.url)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                error_code="internal_error",
                message="Something went wrong on our end. Please try again shortly.",
            ).model_dump(),
        )
