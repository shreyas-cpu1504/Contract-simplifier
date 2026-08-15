from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.schemas.file_ingestion import (
    FileIngestionResponse,
    FileType,
)
from app.services.file_ingestion_service import FileIngestionService
from app.services.text_extraction_service import TextExtractionService


router = APIRouter(
    prefix="/ingestion",
    tags=["Ingestion"],
)


@router.post(
    "/file",
    response_model=FileIngestionResponse,
)
async def ingest_file(
    file: UploadFile = File(...),
) -> FileIngestionResponse:

    try:
        file_id, content = await FileIngestionService.read_file(file)

        extracted_text = TextExtractionService.extract(
            filename=file.filename,
            content=content,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    if not extracted_text:
        raise HTTPException(
            status_code=400,
            detail="No readable text could be extracted from the file.",
        )

    FileIngestionService.save_extracted_text(
        file_id=file_id,
        extracted_text=extracted_text,
    )

    extension = Path(file.filename).suffix.lower()

    return FileIngestionResponse(
        message="File received and text extracted successfully.",
        file_id=file_id,
        file_type=FileType(extension[1:]),
        filename=file.filename,
        size_bytes=len(content),
        extracted_text=extracted_text,
        character_count=len(extracted_text),
    )
