from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel, HttpUrl

from app.schemas.file_ingestion import (
    FileIngestionResponse,
    FileType,
)
from app.services.file_ingestion_service import FileIngestionService
from app.services.text_extraction_service import TextExtractionService
from app.services.url_ingestion_service import URLIngestionService


router = APIRouter(
    prefix="/ingestion",
    tags=["Ingestion"],
)


class URLIngestionRequest(BaseModel):
    url: HttpUrl


@router.post(
    "/file",
    response_model=FileIngestionResponse,
)
async def ingest_file(
    file: UploadFile = File(...),
) -> FileIngestionResponse:

    try:
        file_id, content = await FileIngestionService.read_file(
            file
        )

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


@router.post(
    "/url",
    response_model=FileIngestionResponse,
)
async def ingest_url(
    request: URLIngestionRequest,
) -> FileIngestionResponse:

    try:
        filename, content = await URLIngestionService.download(
            str(request.url)
        )

        extension = Path(filename).suffix.lower()

        extracted_text = TextExtractionService.extract(
            filename=filename,
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
            detail="No readable text could be extracted from the URL.",
        )

    file_id = str(uuid4())

    FileIngestionService.UPLOAD_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    stored_filename = f"{file_id}{extension}"

    stored_path = (
        FileIngestionService.UPLOAD_DIR
        / stored_filename
    )

    stored_path.write_bytes(content)

    FileIngestionService.save_extracted_text(
        file_id=file_id,
        extracted_text=extracted_text,
    )

    return FileIngestionResponse(
        message="Contract URL received and text extracted successfully.",
        file_id=file_id,
        file_type=FileType(extension[1:]),
        filename=filename,
        size_bytes=len(content),
        extracted_text=extracted_text,
        character_count=len(extracted_text),
    )