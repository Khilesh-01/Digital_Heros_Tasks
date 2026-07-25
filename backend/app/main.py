"""Page Pulse API entrypoint."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.error_handlers import register_exception_handlers
from app.api.routes import router
from app.core.config import get_settings
from app.core.logging_config import configure_logging

settings = get_settings()
configure_logging()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Page Pulse audits any public URL and reports HTTP status, response "
        "time, and on-page SEO/structure signals."
    ),
    contact={"name": "Digital Heroes Training Task", "url": "https://digitalheroesco.com"},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

register_exception_handlers(app)
app.include_router(router)


@app.get("/", tags=["System"], include_in_schema=False)
async def root() -> dict[str, str]:
    return {"message": "Page Pulse API - see /docs for API documentation."}
