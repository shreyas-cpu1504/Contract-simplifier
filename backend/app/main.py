from fastapi import FastAPI

from app.api.v1.ingestion import router as ingestion_router
from app.api.v1.file_ingestion import router as file_ingestion_router
from app.api.v1.clauses import router as clauses_router
from app.api.v1.qa import router as qa_router
from app.api.v1.media_ingestion import router as media_ingestion_router

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
    ingestion_router,
    prefix=settings.api_prefix,
)

app.include_router(
    file_ingestion_router,
    prefix=settings.api_prefix,
)

app.include_router(
    clauses_router,
    prefix=settings.api_prefix,
)

app.include_router(
    qa_router,
    prefix=settings.api_prefix,
)

app.include_router(
    media_ingestion_router,
    prefix=settings.api_prefix,
)
