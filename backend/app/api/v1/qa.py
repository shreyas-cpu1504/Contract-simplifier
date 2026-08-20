from fastapi import APIRouter

from app.schemas.qa import (
    QuestionRequest,
    QuestionResponse,
)
from app.services.qa_service import QAService

from app.api.v1.clauses import _load_clauses


router = APIRouter(
    prefix="/qa",
    tags=["Contract Q&A"],
)


@router.post(
    "/{file_id}",
    response_model=QuestionResponse,
)
async def ask_question(
    file_id: str,
    request: QuestionRequest,
) -> QuestionResponse:

    clauses = _load_clauses(file_id)

    return QAService.answer(
        file_id=file_id,
        question=request.question,
        clauses=clauses,
    )