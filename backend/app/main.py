from fastapi import FastAPI

from app.api.v1.router import router as api_router
from app.core.config import get_settings
from app.schemas.health import HealthResponse


settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="AI-powered multimodal contract intelligence platform",
    version=settings.app_version,
)


@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["System"],
)
async def health_check() -> HealthResponse:
    return HealthResponse(
        status="healthy",
        service=settings.app_name,
        version=settings.app_version,
    )


app.include_router(
    api_router,
    prefix=settings.api_prefix,
)
