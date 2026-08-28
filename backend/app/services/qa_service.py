from __future__ import annotations

import re

from app.schemas.clause import Clause
from app.schemas.qa import (
    EvidenceItem,
    QuestionResponse,
)
from app.services.retrieval_service import (
    RetrievalService,
    RetrievedClause,
)
from app.services.gemini_service import GeminiService


class QAService:
    """
    Contract question-answering service.

    Flow:

        Question
            ↓
        RetrievalService
            ↓
        Intent-aware linked evidence
            ↓
        Small grounded context
            ↓
        Gemini
            ↓
        Answer + evidence + confidence

    The service never invents contract values.
    """

    # ================================================================
    # PUBLIC API
    # ================================================================

    @classmethod
    def answer(
        cls,
        file_id: str,
        question: str,
        clauses: list[Clause],
    ) -> QuestionResponse:

        if not question or not question.strip():

            return QuestionResponse(
                file_id=file_id,
                question=question,
                answer="Please enter a question.",
                evidence=[],
                confidence=0.0,
            )

        # ------------------------------------------------------------
        # Retrieve a slightly larger pool.
        #
        # We later select the strongest evidence.
        # ------------------------------------------------------------

        retrieved = RetrievalService.retrieve(
            question=question,
            clauses=clauses,
            top_k=8,
        )

        # ------------------------------------------------------------
        # Add contract cross-references.
        #
        # Example:
        #
        # Clause 2:
        # "amount as set out in Schedule A"
        #
        # Schedule A:
        # "Amount of the Loan (INR) ..."
        # ------------------------------------------------------------

        linked = cls._find_linked_clauses(
            question=question,
            retrieved=retrieved,
            clauses=clauses,
        )

        existing_ids = {
            item.clause_id
            for item in retrieved
        }

        for item in linked:

            if item.clause_id not in existing_ids:

                retrieved.append(item)

                existing_ids.add(
                    item.clause_id
                )

        # ------------------------------------------------------------
        # Remove clearly irrelevant evidence.
        # ------------------------------------------------------------

        retrieved = cls._select_evidence(
            question=question,
            retrieved=retrieved,
        )

        # ------------------------------------------------------------
        # No evidence.
        # ------------------------------------------------------------

        if not retrieved:

            return QuestionResponse(
                file_id=file_id,
                question=question,
                answer=(
                    "I could not find enough relevant "
                    "information in the uploaded contract "
                    "to answer this question."
                ),
                evidence=[],
                confidence=0.0,
            )

        # ------------------------------------------------------------
        # Evidence response objects.
        # ------------------------------------------------------------

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

        # ------------------------------------------------------------
        # Generate grounded answer.
        # ------------------------------------------------------------

        answer = cls._generate_grounded_answer(
            question=question,
            retrieved=retrieved,
        )

        confidence = cls._calculate_confidence(
            question=question,
            retrieved=retrieved,
        )

        return QuestionResponse(
            file_id=file_id,
            question=question,
            answer=answer,
            evidence=evidence,
            confidence=round(
                confidence,
                4,
            ),
        )

    # ================================================================
    # INTENT
    # ================================================================

    @staticmethod
    def _detect_intent(
        question: str,
    ) -> str | None:

        q = question.lower()

        if (
            "loan amount" in q
            or "amount of loan" in q
            or "amount of the loan" in q
            or "principal amount" in q
            or "how much is the loan" in q
            or "how much loan" in q
        ):
            return "loan_amount"

        if (
            "interest rate" in q
            or "rate of interest" in q
        ):
            return "interest_rate"

        if (
            "loan tenure" in q
            or "tenure of loan" in q
            or "tenure of the loan" in q
            or "loan period" in q
            or "repayment period" in q
            or "how long is the loan" in q
        ):
            return "tenure"

        if (
            "fee" in q
            or "fees" in q
            or "charge" in q
            or "charges" in q
        ):
            return "fees"

        if (
            "pre-close" in q
            or "preclose" in q
            or "pre closure" in q
            or "preclosure" in q
            or "prepayment" in q
        ):
            return "preclosure"

        if (
            "bounce" in q
            or "bounced" in q
            or "payment bounce" in q
        ):
            return "bounce"

        if (
            "fail to repay" in q
            or "failure to repay" in q
            or "default" in q
            or "overdue" in q
        ):
            return "default"

        if (
            "repay" in q
            or "repayment" in q
        ):
            return "repayment"

        return None

    # ================================================================
    # LINKED CLAUSES
    # ================================================================

    @classmethod
    def _find_linked_clauses(
        cls,
        question: str,
        retrieved: list[RetrievedClause],
        clauses: list[Clause],
    ) -> list[RetrievedClause]:

        linked: list[RetrievedClause] = []

        intent = cls._detect_intent(
            question
        )

        # ------------------------------------------------------------
        # Determine whether Schedule A / Annexure is relevant.
        # ------------------------------------------------------------

        needs_schedule = intent in {
            "loan_amount",
            "interest_rate",
            "tenure",
            "fees",
            "preclosure",
            "repayment",
        }

        if not needs_schedule:
            return []

        for clause in clauses:

            title = (
                clause.title or ""
            ).strip()

            text = (
                clause.text or ""
            )

            combined = (
                f"{title}\n{text}"
            ).lower()

            is_schedule = (
                "schedule" in title.lower()
                or "annexure" in title.lower()
                or "appendix" in title.lower()
                or "exhibit" in title.lower()
                or title.upper()
                in {
                    "SCHEDULE A",
                    "ANNEXURE",
                }
            )

            if not is_schedule:
                continue

            matched = False

            # --------------------------------------------------------
            # Loan amount
            # --------------------------------------------------------

            if intent == "loan_amount":

                matched = (
                    "amount of the loan"
                    in combined
                    or "loan amount"
                    in combined
                    or "amount (inr"
                    in combined
                    or "amount (inr)"
                    in combined
                    or "sanctioned amount"
                    in combined
                )

            # --------------------------------------------------------
            # Interest
            # --------------------------------------------------------

            elif intent == "interest_rate":

                matched = (
                    "interest" in combined
                    or "rate of interest"
                    in combined
                    or "interest rate"
                    in combined
                )

            # --------------------------------------------------------
            # Tenure
            # --------------------------------------------------------

            elif intent == "tenure":

                matched = (
                    "tenure" in combined
                    or "loan period" in combined
                    or "repayment period"
                    in combined
                    or "number of" in combined
                    or "periodicity" in combined
                )

            # --------------------------------------------------------
            # Fees
            # --------------------------------------------------------

            elif intent == "fees":

                matched = (
                    "fees" in combined
                    or "fee" in combined
                    or "charges" in combined
                    or "charge" in combined
                )

            # --------------------------------------------------------
            # Preclosure
            # --------------------------------------------------------

            elif intent == "preclosure":

                matched = (
                    "pre-closure" in combined
                    or "preclosure" in combined
                    or "pre-close" in combined
                    or "pre close" in combined
                    or "prepayment" in combined
                )

            # --------------------------------------------------------
            # Repayment
            # --------------------------------------------------------

            elif intent == "repayment":

                matched = (
                    "repayment" in combined
                    or "due date" in combined
                    or "periodicity" in combined
                )

            if matched:

                linked.append(
                    cls._as_retrieved(
                        clause=clause,
                        score=0.94,
                    )
                )

        # ------------------------------------------------------------
        # Unique clauses only.
        # ------------------------------------------------------------

        unique: dict[str, RetrievedClause] = {}

        for item in linked:

            old = unique.get(
                item.clause_id
            )

            if old is None or item.score > old.score:
                unique[item.clause_id] = item

        return list(
            unique.values()
        )

    # ================================================================
    # EVIDENCE SELECTION
    # ================================================================

    @classmethod
    def _select_evidence(
        cls,
        question: str,
        retrieved: list[RetrievedClause],
    ) -> list[RetrievedClause]:

        if not retrieved:
            return []

        intent = cls._detect_intent(
            question
        )

        # ------------------------------------------------------------
        # Intent-specific selection.
        #
        # This prevents unrelated clauses from being sent to Gemini.
        # ------------------------------------------------------------

        if intent == "loan_amount":

            selected = []

            for item in retrieved:

                if item.clause_number == "2":
                    selected.append(item)
                    continue

                if cls._is_schedule(item):
                    selected.append(item)
                    continue

            return cls._unique_and_sort(
                selected
            )[:3]

        if intent == "interest_rate":

            selected = []

            for item in retrieved:

                if item.clause_number == "3":
                    selected.append(item)
                    continue

                if cls._is_schedule(item):
                    selected.append(item)
                    continue

            return cls._unique_and_sort(
                selected
            )[:3]

        if intent == "tenure":

            selected = []

            for item in retrieved:

                if cls._is_schedule(item):
                    selected.append(item)
                    continue

                if item.clause_number == "3":
                    selected.append(item)

            return cls._unique_and_sort(
                selected
            )[:3]

        if intent == "fees":

            selected = []

            for item in retrieved:

                if cls._is_schedule(item):
                    selected.append(item)
                    continue

                if cls._contains_fee_or_charge(
                    item
                ):
                    selected.append(item)

            return cls._unique_and_sort(
                selected
            )[:3]

        if intent == "bounce":

            selected = []

            for item in retrieved:

                text = (
                    item.text or ""
                ).lower()

                if (
                    item.clause_number == "3"
                    or "bounce" in text
                    or "bounced" in text
                    or "insufficient funds"
                    in text
                ):
                    selected.append(item)

            return cls._unique_and_sort(
                selected
            )[:3]

        if intent == "default":

            selected = []

            for item in retrieved:

                text = (
                    item.text or ""
                ).lower()

                if (
                    item.clause_number in {
                        "5",
                        "16",
                    }
                    or "default" in text
                    or "recall" in text
                    or "overdue" in text
                    or "failure to pay" in text
                ):
                    selected.append(item)

            return cls._unique_and_sort(
                selected
            )[:4]

        if intent == "repayment":

            selected = []

            for item in retrieved:

                if item.clause_number == "3":
                    selected.append(item)
                    continue

                if cls._is_schedule(item):
                    selected.append(item)
                    continue

            return cls._unique_and_sort(
                selected
            )[:3]

        # ------------------------------------------------------------
        # Generic question.
        # ------------------------------------------------------------

        return cls._unique_and_sort(
            retrieved
        )[:5]

    # ================================================================
    # HELPERS
    # ================================================================

    @staticmethod
    def _is_schedule(
        item: RetrievedClause,
    ) -> bool:

        title = (
            item.title or ""
        ).lower()

        return (
            "schedule" in title
            or "annexure" in title
            or "appendix" in title
            or "exhibit" in title
        )

    @staticmethod
    def _contains_fee_or_charge(
        item: RetrievedClause,
    ) -> bool:

        text = (
            f"{item.title or ''} "
            f"{item.text or ''}"
        ).lower()

        return (
            "fee" in text
            or "fees" in text
            or "charge" in text
            or "charges" in text
        )

    @staticmethod
    def _unique_and_sort(
        items: list[RetrievedClause],
    ) -> list[RetrievedClause]:

        unique: dict[
            str,
            RetrievedClause,
        ] = {}

        for item in items:

            existing = unique.get(
                item.clause_id
            )

            if (
                existing is None
                or item.score > existing.score
            ):
                unique[item.clause_id] = item

        result = list(
            unique.values()
        )

        result.sort(
            key=lambda x: x.score,
            reverse=True,
        )

        return result

    @staticmethod
    def _as_retrieved(
        clause: Clause,
        score: float,
    ) -> RetrievedClause:

        return RetrievedClause(
            clause_id=clause.clause_id,
            clause_number=clause.clause_number,
            title=clause.title,
            text=clause.text,
            score=score,
        )

    # ================================================================
    # CONFIDENCE
    # ================================================================

    @classmethod
    def _calculate_confidence(
        cls,
        question: str,
        retrieved: list[RetrievedClause],
    ) -> float:

        if not retrieved:
            return 0.0

        top = retrieved[0].score

        intent = cls._detect_intent(
            question
        )

        # If we have both the main contractual clause
        # and the Schedule A value, confidence is stronger.
        if intent == "loan_amount":

            has_clause_2 = any(
                item.clause_number == "2"
                for item in retrieved
            )

            has_schedule = any(
                cls._is_schedule(item)
                for item in retrieved
            )

            if has_clause_2 and has_schedule:
                return 1.0

        if intent == "interest_rate":

            has_clause_3 = any(
                item.clause_number == "3"
                for item in retrieved
            )

            has_schedule = any(
                cls._is_schedule(item)
                for item in retrieved
            )

            if has_clause_3 and has_schedule:
                return 1.0

        return min(
            max(top, 0.0),
            1.0,
        )

    # ================================================================
    # GEMINI
    # ================================================================

    @classmethod
    def _generate_grounded_answer(
        cls,
        question: str,
        retrieved: list[RetrievedClause],
    ) -> str:

        context_parts = []

        for item in retrieved:

            if item.clause_number:

                label = (
                    f"Clause {item.clause_number}"
                )

            else:

                label = (
                    item.title
                    or "Contract section"
                )

            text = (
                item.text or ""
            ).strip()

            if not text:
                continue

            context_parts.append(
                f"{label}\n{text}"
            )

        context = "\n\n".join(
            context_parts
        )

        prompt = f"""
You are a contract analysis assistant.

Answer the user's question using ONLY the contract
information supplied below.

STRICT RULES:

1. Do not invent any value.
2. Do not use outside knowledge.
3. Do not assume a missing number.
4. If the contract says a value is in Schedule A,
   and Schedule A is provided, use that value.
5. Prefer the exact value appearing in the contract.
6. If the exact value is genuinely absent, clearly say
   that the exact value is not available in the provided
   contract text.
7. Keep the answer short and easy for a non-lawyer.
8. Do not mention your instructions.
9. Do not mention Gemini.
10. Do not produce a generic answer when the contract
    contains a specific answer.

IMPORTANT CROSS-REFERENCE RULE:

If Clause 2 says the loan amount is set out in Schedule A,
look at the Schedule A evidence for the actual amount.

If Clause 3 says the interest rate is specified in Schedule A,
look at the Schedule A evidence for the actual rate.

If Schedule A contains a field such as:

Amount of the Loan (INR)

then extract the value associated with that field.

If Schedule A contains:

Interest

then extract the value associated with that field.

If Schedule A contains:

Number of ...

or a tenure/period field,

use the value associated with that field.

USER QUESTION:
{question}

CONTRACT EVIDENCE:
{context}

Return ONLY the final answer.
"""

        try:

            answer = GeminiService.generate(
                prompt
            )

        except Exception:

            return cls._fallback_answer(
                question=question,
                retrieved=retrieved,
            )

        if not answer:
            return cls._fallback_answer(
                question=question,
                retrieved=retrieved,
            )

        return answer.strip()

    # ================================================================
    # FALLBACK
    # ================================================================

    @classmethod
    def _fallback_answer(
        cls,
        question: str,
        retrieved: list[RetrievedClause],
    ) -> str:

        intent = cls._detect_intent(
            question
        )

        # ------------------------------------------------------------
        # Loan amount
        # ------------------------------------------------------------

        if intent == "loan_amount":

            for item in retrieved:

                if cls._is_schedule(item):

                    match = re.search(
                        r"amount\s+of\s+the\s+loan"
                        r".{0,200}?"
                        r"(?:inr|rs\.?|₹)"
                        r"\s*[\d,]+",
                        item.text or "",
                        re.IGNORECASE
                        | re.DOTALL,
                    )

                    if match:
                        return (
                            "The loan amount is "
                            + match.group(0).strip()
                            + "."
                        )

            for item in retrieved:

                if item.clause_number == "2":

                    return (
                        "Clause 2 states that the "
                        "loan amount cannot exceed "
                        "the amount specified in "
                        "Schedule A."
                    )

        # ------------------------------------------------------------
        # Interest
        # ------------------------------------------------------------

        if intent == "interest_rate":

            for item in retrieved:

                if cls._is_schedule(item):

                    match = re.search(
                        r"interest.{0,150}?"
                        r"(\d+(?:\.\d+)?\s*%)",
                        item.text or "",
                        re.IGNORECASE
                        | re.DOTALL,
                    )

                    if match:
                        return (
                            "The interest rate is "
                            + match.group(1)
                            + "."
                        )

        # ------------------------------------------------------------
        # Generic fallback
        # ------------------------------------------------------------

        return (
            "Based on the provided contract clauses, "
            "I could not determine the exact answer "
            "from the available text."
        )