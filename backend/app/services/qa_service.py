from app.schemas.clause import Clause
from app.schemas.qa import (
    EvidenceItem,
    QuestionResponse,
)
from app.services.retrieval_service import (
    RetrievalService,
)


class QAService:

    @classmethod
    def answer(
        cls,
        file_id: str,
        question: str,
        clauses: list[Clause],
    ) -> QuestionResponse:

        retrieved = RetrievalService.retrieve(
            question=question,
            clauses=clauses,
            top_k=3,
        )

        evidence = [
            EvidenceItem(
                clause_id=item.clause_id,
                clause_number=item.clause_number,
                title=item.title,
                text=item.text,
                relevance_score=item.score,
            )
            for item in retrieved
        ]

        if not retrieved:
            return QuestionResponse(
                file_id=file_id,
                question=question,
                answer=(
                    "I could not find a sufficiently relevant "
                    "clause in the uploaded contract to answer "
                    "this question."
                ),
                evidence=[],
                confidence=0.0,
            )

        answer = cls._build_grounded_answer(
            question=question,
            retrieved=retrieved,
        )

        confidence = min(
            max(retrieved[0].score, 0.0),
            1.0,
        )

        return QuestionResponse(
            file_id=file_id,
            question=question,
            answer=answer,
            evidence=evidence,
            confidence=round(confidence, 4),
        )

    @staticmethod
    def _build_grounded_answer(
        question: str,
        retrieved,
    ) -> str:

        primary = retrieved[0]

        clause_label = (
            f"Clause {primary.clause_number}"
            if primary.clause_number
            else f"Clause {primary.clause_id}"
        )

        return (
            f"Based on {clause_label}: "
            f"{primary.text.strip()}"
        )