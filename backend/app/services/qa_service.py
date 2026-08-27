from app.schemas.clause import Clause
from app.schemas.qa import (
    EvidenceItem,
    QuestionResponse,
)
from app.services.retrieval_service import (
    RetrievalService,
)
from app.services.gemini_service import GeminiService


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

        answer = cls._generate_grounded_answer(
            question=question,
            retrieved=retrieved,
        )

        # This is a retrieval-based confidence proxy.
        # It represents how strongly the top retrieved clause
        # matches the user's question, not Gemini's probability.
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
    def _generate_grounded_answer(
        question: str,
        retrieved,
    ) -> str:

        context_parts = []

        for item in retrieved:
            clause_label = (
                f"Clause {item.clause_number}"
                if item.clause_number
                else f"Clause {item.clause_id}"
            )

            title = item.title or "Untitled"

            context_parts.append(
                f"{clause_label} - {title}\n"
                f"{item.text}"
            )

        context = "\n\n".join(context_parts)

        prompt = f"""
You are a contract analysis assistant.

Answer the user's question using ONLY the contract clauses
provided below.

Do not invent facts.
Do not use outside legal information.
Do not make assumptions that are not supported by the clauses.

If the provided clauses do not contain enough information to
answer the question, clearly say that the contract information
provided is insufficient.

Explain the answer in simple language suitable for a
non-lawyer.

User question:
{question}

Relevant contract clauses:
{context}

Return only the answer to the user's question.
"""

        return GeminiService.generate(prompt)