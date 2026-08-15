from fastapi import APIRouter, HTTPException

from app.schemas.clause import ClauseSegmentationResponse
from app.services.clause_classifier_service import (
    ClauseClassifierService,
)
from app.services.clause_segmentation_service import (
    ClauseSegmentationService,
)
from app.services.clause_storage_service import (
    ClauseStorageService,
)
from app.services.file_ingestion_service import (
    FileIngestionService,
)


router = APIRouter(
    prefix="/clauses",
    tags=["Clauses"],
)


@router.get(
    "/{file_id}",
    response_model=ClauseSegmentationResponse,
)
async def get_clauses(
    file_id: str,
) -> ClauseSegmentationResponse:

    extracted_path = (
        FileIngestionService.EXTRACTED_DIR
        / f"{file_id}.txt"
    )

    if not extracted_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Extracted document not found.",
        )

    # Try loading already processed clauses.
    existing_clauses = (
        ClauseStorageService.load_clauses(file_id)
    )

    if existing_clauses:

        # Older stored clauses may not have classification.
        if any(
            clause.clause_type is None
            for clause in existing_clauses
        ):
            classified_clauses = (
                ClauseClassifierService.classify_many(
                    existing_clauses
                )
            )

            ClauseStorageService.save_clauses(
                file_id=file_id,
                clauses=classified_clauses,
            )

            existing_clauses = classified_clauses

        return ClauseSegmentationResponse(
            file_id=file_id,
            clause_count=len(existing_clauses),
            clauses=existing_clauses,
        )

    # Read extracted text.
    text = extracted_path.read_text(
        encoding="utf-8",
    )

    # Segment document into clauses.
    clauses = ClauseSegmentationService.segment(
        text
    )

    if not clauses:
        raise HTTPException(
            status_code=400,
            detail="No clauses could be detected.",
        )

    # Classify every clause.
    classified_clauses = (
        ClauseClassifierService.classify_many(
            clauses
        )
    )

    # Store classified clauses.
    ClauseStorageService.save_clauses(
        file_id=file_id,
        clauses=classified_clauses,
    )

    return ClauseSegmentationResponse(
        file_id=file_id,
        clause_count=len(classified_clauses),
        clauses=classified_clauses,
    )
