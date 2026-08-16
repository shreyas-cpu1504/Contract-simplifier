from fastapi import APIRouter, HTTPException

from app.schemas.clause import ClauseSegmentationResponse
from app.schemas.clause_analysis import ClauseAnalysisResponse
from app.schemas.contract_summary import ContractSummary

from app.services.clause_classifier_service import (
    ClauseClassifierService,
)
from app.services.clause_segmentation_service import (
    ClauseSegmentationService,
)
from app.services.clause_storage_service import (
    ClauseStorageService,
)
from app.services.clause_analysis_service import (
    ClauseAnalysisService,
)
from app.services.contract_summary_service import (
    ContractSummaryService,
)
from app.services.file_ingestion_service import (
    FileIngestionService,
)


router = APIRouter(
    prefix="/clauses",
    tags=["Clauses"],
)


def _load_clauses(file_id: str):
    extracted_path = (
        FileIngestionService.EXTRACTED_DIR
        / f"{file_id}.txt"
    )

    if not extracted_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Extracted document not found.",
        )

    clauses = ClauseStorageService.load_clauses(
        file_id
    )

    if not clauses:
        text = extracted_path.read_text(
            encoding="utf-8",
        )

        clauses = ClauseSegmentationService.segment(
            text
        )

        if not clauses:
            raise HTTPException(
                status_code=400,
                detail="No clauses could be detected.",
            )

        clauses = ClauseClassifierService.classify_many(
            clauses
        )

        ClauseStorageService.save_clauses(
            file_id=file_id,
            clauses=clauses,
        )

    elif any(
        clause.clause_type is None
        for clause in clauses
    ):
        clauses = ClauseClassifierService.classify_many(
            clauses
        )

        ClauseStorageService.save_clauses(
            file_id=file_id,
            clauses=clauses,
        )

    return clauses


@router.get(
    "/{file_id}",
    response_model=ClauseSegmentationResponse,
)
async def get_clauses(
    file_id: str,
) -> ClauseSegmentationResponse:

    clauses = _load_clauses(file_id)

    return ClauseSegmentationResponse(
        file_id=file_id,
        clause_count=len(clauses),
        clauses=clauses,
    )


@router.get(
    "/{file_id}/analysis",
    response_model=ClauseAnalysisResponse,
)
async def get_clause_analysis(
    file_id: str,
) -> ClauseAnalysisResponse:

    clauses = _load_clauses(file_id)

    analyses = ClauseAnalysisService.analyze_many(
        clauses
    )

    return ClauseAnalysisResponse(
        file_id=file_id,
        analysis_count=len(analyses),
        analyses=analyses,
    )


@router.get(
    "/{file_id}/summary",
    response_model=ContractSummary,
)
async def get_contract_summary(
    file_id: str,
) -> ContractSummary:

    clauses = _load_clauses(file_id)

    analyses = ClauseAnalysisService.analyze_many(
        clauses
    )

    return ContractSummaryService.generate(
        file_id=file_id,
        analyses=analyses,
    )
