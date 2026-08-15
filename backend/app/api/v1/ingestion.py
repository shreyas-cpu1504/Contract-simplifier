from fastapi import APIRouter

from app.schemas.ingestion import (
    IngestionResponse,
    TextIngestionRequest,
)


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
    return IngestionResponse(
        message="Text received successfully.",
        input_type=request.input_type,
        character_count=len(request.content),
    )
