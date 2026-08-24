from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.schemas.media_ingestion import (
    MediaIngestionResponse,
    MediaType,
)
from app.services.audio_transcription_service import (
    AudioTranscriptionService,
)
from app.services.video_transcription_service import (
    VideoTranscriptionService,
)


router = APIRouter(
    prefix="/ingestion",
    tags=["Media Ingestion"],
)


@router.post(
    "/audio",
    response_model=MediaIngestionResponse,
)
async def ingest_audio(
    file: UploadFile = File(...),
) -> MediaIngestionResponse:

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is required.",
        )

    extension = Path(file.filename).suffix.lower()

    if extension not in AudioTranscriptionService.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported audio file type: "
                f"{extension or 'unknown'}"
            ),
        )

    try:
        content = await file.read()

        if not content:
            raise ValueError("Uploaded audio file is empty.")

        media_id = str(uuid4())

        transcript = AudioTranscriptionService.transcribe(
            filename=file.filename,
            content=content,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    return MediaIngestionResponse(
        message="Audio received and transcribed successfully.",
        media_id=media_id,
        media_type=MediaType.AUDIO,
        filename=file.filename,
        size_bytes=len(content),
        transcript=transcript,
        character_count=len(transcript),
    )


@router.post(
    "/video",
    response_model=MediaIngestionResponse,
)
async def ingest_video(
    file: UploadFile = File(...),
) -> MediaIngestionResponse:

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is required.",
        )

    extension = Path(file.filename).suffix.lower()

    if extension not in VideoTranscriptionService.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported video file type: "
                f"{extension or 'unknown'}"
            ),
        )

    try:
        content = await file.read()

        if not content:
            raise ValueError("Uploaded video file is empty.")

        media_id = str(uuid4())

        transcript = VideoTranscriptionService.transcribe(
            filename=file.filename,
            content=content,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    return MediaIngestionResponse(
        message="Video received and transcribed successfully.",
        media_id=media_id,
        media_type=MediaType.VIDEO,
        filename=file.filename,
        size_bytes=len(content),
        transcript=transcript,
        character_count=len(transcript),
    )