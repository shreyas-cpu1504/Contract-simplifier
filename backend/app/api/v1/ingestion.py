from fastapi import APIRouter

from app.schemas.ingestion import (
    IngestionResponse,
    TextIngestionRequest,
)
from app.services.ingestion_service import IngestionService


router = APIRouter(
    prefix="/ingestion",
    tags=["Ingestion"],
)


@router.post(
    "/text",
    response_model=IngestionResponse,
)
async def ingest_text(
    request: TextIngestionRequest,
) -> IngestionResponse:
    normalized = IngestionService.process_text(
        input_type=request.input_type,
        content=request.content,
    )

    return IngestionResponse(
        message="Text received successfully.",
        input_type=normalized.input_type,
        character_count=normalized.character_count,
    )
