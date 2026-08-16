from dataclasses import asdict

from fastapi import APIRouter, HTTPException

from app.schemas.clause import ClauseSegmentationResponse
from app.schemas.clause_analysis import ClauseAnalysis, ClauseAnalysisResponse
from app.schemas.clause_relationship import ClauseRelationshipResponse
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
from app.services.clause_relationship_service import (
    ClauseRelationshipService,
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


def _relationship_to_schema(relationship):
    return {
        "source_clause_id": relationship.source_clause_id,
        "target_clause_id": relationship.target_clause_id,
        "relationship_type": relationship.relationship_type,
        "evidence": relationship.evidence,
        "confidence": relationship.confidence,
        "metadata": relationship.metadata,
    }


def _analysis_to_schema(analysis) -> ClauseAnalysis:
    data = asdict(analysis)

    return ClauseAnalysis(
        clause_id=data["clause_id"],
        clause_number=data["clause_number"],
        clause_type=data["clause_type"],
        meaning=data["meaning"],

        # Service -> API schema mappings
        entities=data["parties"],
        persons=data["persons"],
        organizations=data["organizations"],
        authorities=data["authorities"],
        jurisdictions=data["jurisdiction"],

        obligations=data["obligations"],
        rights=data["rights"],
        permissions=data["permissions"],
        prohibitions=data["prohibitions"],
        duties=data["duties"],

        conditions=data["conditions"],
        exceptions=data["exceptions"],
        triggers=data["triggers"],
        consequences=data["consequences"],

        dates=data["dates"],
        deadlines=data["deadlines"],
        durations=data["durations"],

        monetary_terms=data["monetary_terms"],
        percentages=data["percentages"],
        quantities=data["quantities"],

        laws=data["laws"],
        regulations=data["regulations"],
        sections=data["sections"],
        articles=data["articles"],
        case_references=data["case_references"],

        employment_terms=data["employment_terms"],
        financial_terms=data["compensation_terms"],
        loan_terms=data["loan_terms"],
        property_terms=data["property_terms"],
        intellectual_property_terms=data["intellectual_property_terms"],
        privacy_terms=data["privacy_terms"],
        dispute_resolution_terms=data["dispute_terms"],
        confidentiality_terms=data["confidentiality_terms"],

        risk_level=data["risk_level"],
        risk_score=data["risk_score"],
        risk_reasons=data["risk_reasons"],
        user_impact=data["user_impact"],
        recommendations=data["recommendations"],
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
    "/{file_id}/relationships",
    response_model=ClauseRelationshipResponse,
)
def get_clause_relationships(file_id: str):
    clauses = _load_clauses(file_id)

    relationships = ClauseRelationshipService.analyze_relationships(
        clauses
    )

    return ClauseRelationshipResponse(
        file_id=file_id,
        relationship_count=len(relationships),
        relationships=[
            _relationship_to_schema(relationship)
            for relationship in relationships
        ],
    )


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

    analyses = ClauseAnalysisService.analyze_clauses(
        clauses
    )

    schema_analyses = [
        _analysis_to_schema(analysis)
        for analysis in analyses
    ]

    return ClauseAnalysisResponse(
        file_id=file_id,
        analysis_count=len(schema_analyses),
        analyses=schema_analyses,
    )


@router.get(
    "/{file_id}/summary",
    response_model=ContractSummary,
)
async def get_contract_summary(
    file_id: str,
) -> ContractSummary:

    clauses = _load_clauses(file_id)

    analyses = ClauseAnalysisService.analyze_clauses(
        clauses
    )

    return ContractSummaryService.generate(
        file_id=file_id,
        analyses=analyses,
    )
