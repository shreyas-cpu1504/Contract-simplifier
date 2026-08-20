import re
from dataclasses import dataclass

from app.schemas.clause import Clause


@dataclass(frozen=True)
class RetrievedClause:
    clause_id: str
    clause_number: str | None
    title: str | None
    text: str
    score: float


class RetrievalService:
    """
    Lightweight deterministic retrieval layer.

    This is the foundation for the later RAG/LLM layer.
    It retrieves contract clauses using normalized keyword overlap.
    """

    STOP_WORDS = {
        "the",
        "a",
        "an",
        "is",
        "are",
        "was",
        "were",
        "be",
        "to",
        "of",
        "in",
        "on",
        "for",
        "and",
        "or",
        "with",
        "this",
        "that",
        "what",
        "when",
        "where",
        "who",
        "how",
        "does",
        "do",
        "can",
        "may",
        "will",
        "shall",
        "upon",
        "agreement",
        "contract",
        "within",
        "from",
        "by",
        "as",
        "it",
        "its",
        "their",
        "them",
        "they",
    }

    @classmethod
    def retrieve(
        cls,
        question: str,
        clauses: list[Clause],
        top_k: int = 3,
    ) -> list[RetrievedClause]:

        question_tokens = cls._tokenize(question)

        if not question_tokens:
            return []

        scored: list[RetrievedClause] = []

        for clause in clauses:
            clause_tokens = cls._tokenize(
                f"{clause.title or ''} {clause.text}"
            )

            if not clause_tokens:
                continue

            overlap = question_tokens.intersection(
                clause_tokens
            )

            if not overlap:
                continue

            score = (
                len(overlap)
                / len(question_tokens)
            )

            scored.append(
                RetrievedClause(
                    clause_id=clause.clause_id,
                    clause_number=clause.clause_number,
                    title=clause.title,
                    text=clause.text,
                    score=round(score, 4),
                )
            )

        scored.sort(
            key=lambda item: (
                item.score,
                item.clause_number or "",
            ),
            reverse=True,
        )

        return scored[:top_k]

    @classmethod
    def _tokenize(cls, text: str) -> set[str]:
        words = re.findall(
            r"[a-zA-Z0-9]+",
            text.lower(),
        )

        tokens = set()

        for word in words:
            if word in cls.STOP_WORDS:
                continue

            if len(word) <= 1:
                continue

            tokens.add(
                cls._normalize_word(word)
            )

        return tokens

    @staticmethod
    def _normalize_word(word: str) -> str:
        """
        Small stemming/normalization layer.

        Examples:
            terminated -> terminate
            terminating -> terminate
            payments -> payment
            notices -> notice
        """

        if word.endswith("ies") and len(word) > 4:
            return word[:-3] + "y"

        if word.endswith("ing") and len(word) > 5:
            base = word[:-3]

            if base.endswith("at"):
                return base + "e"

            return base

        if word.endswith("ed") and len(word) > 4:
            base = word[:-2]

            if base.endswith("at"):
                return base + "e"

            if base.endswith("in"):
                return base + "e"

            return base

        if word.endswith("es") and len(word) > 4:
            return word[:-2]

        if word.endswith("s") and len(word) > 3:
            return word[:-1]

        return word