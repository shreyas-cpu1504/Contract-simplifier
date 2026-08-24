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
    Deterministic contract-clause retrieval layer.

    Retrieves clauses using:
    - keyword overlap
    - lightweight word normalization
    - irregular verb normalization
    - title matching
    - phrase matching

    This is designed as the retrieval foundation for a
    later RAG / LLM layer.
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
        "been",
        "being",
        "to",
        "of",
        "in",
        "on",
        "at",
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
        "which",
        "how",
        "does",
        "do",
        "did",
        "can",
        "could",
        "would",
        "should",
        "will",
        "shall",
        "may",
        "might",
        "must",
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
        "he",
        "she",
        "his",
        "her",
        "my",
        "your",
        "our",
        "me",
        "you",
        "i",
        "there",
        "here",
        "about",
        "into",
        "after",
        "before",
        "during",
        "than",
        "then",
        "if",
        "customer",
"party",
"parties",
"person",
"people",
"provider",
"service",
"services",
"information",
"terms",
"term",
"rights",
"right",
"obligation",
"obligations",
    }

    # Common irregular forms found in natural-language questions.
    IRREGULAR_WORDS = {
        "paid": "pay",
        "pays": "pay",
        "paying": "pay",
        "fees": "fee",
        "charges": "charge",
        "charged": "charge",
        "charging": "charge",
        "payments": "payment",
        "payment": "payment",
        "terminated": "terminate",
        "terminates": "terminate",
        "terminating": "terminate",
        "cancelled": "cancel",
        "canceled": "cancel",
        "cancels": "cancel",
        "cancelling": "cancel",
        "renewed": "renew",
        "renews": "renew",
        "renewing": "renew",
        "retained": "retain",
        "retains": "retain",
        "retaining": "retain",
        "collected": "collect",
        "collects": "collect",
        "collecting": "collect",
        "processed": "process",
        "processes": "process",
        "processing": "process",
        "shared": "share",
        "shares": "share",
        "sharing": "share",
        "provided": "provide",
        "provides": "provide",
        "providing": "provide",
        "received": "receive",
        "receives": "receive",
        "receiving": "receive",
        "losses": "loss",
        "days": "day",
        "months": "month",
        "years": "year",
        "notices": "notice",
        "parties": "party",
        "services": "service",
        "invoices": "invoice",
        "percentages": "percentage",
    }

    @classmethod
    def retrieve(
        cls,
        question: str,
        clauses: list[Clause],
        top_k: int = 3,
    ) -> list[RetrievedClause]:

        if not question or not question.strip():
            return []

        question_tokens = cls._tokenize(question)

        if not question_tokens:
            return []

        scored: list[RetrievedClause] = []

        for clause in clauses:
            searchable_text = (
                f"{clause.title or ''} {clause.text}"
            )

            clause_tokens = cls._tokenize(
                searchable_text
            )

            if not clause_tokens:
                continue

            overlap = question_tokens.intersection(
                clause_tokens
            )

            if not overlap:
                continue

            score = cls._calculate_score(
                question_tokens,
                clause_tokens,
                overlap,
                clause,
            )

            if score <= 0:
                continue

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
                cls._clause_number_sort_key(
                    item.clause_number
                ),
            ),
            reverse=True,
        )

        return scored[:top_k]

    @classmethod
    def _calculate_score(
        cls,
        question_tokens: set[str],
        clause_tokens: set[str],
        overlap: set[str],
        clause: Clause,
    ) -> float:

        # Base score:
        # percentage of meaningful question tokens
        # found in the clause.
        base_score = (
            len(overlap)
            / len(question_tokens)
        )

        score = base_score

        # Title is a strong signal.
        if clause.title:
            title_tokens = cls._tokenize(
                clause.title
            )

            title_overlap = (
                question_tokens.intersection(
                    title_tokens
                )
            )

            if title_overlap:
                score += 0.20

        # Exact phrase fragments are useful signals.
        question_text = cls._normalize_text(
            question_tokens
        )

        clause_text = cls._normalize_text(
            clause_tokens
        )

        if (
            "service fee" in question_text
            and "service fee" in clause_text
        ):
            score += 0.15

        if (
            "termination fee" in question_text
            and "termination fee" in clause_text
        ):
            score += 0.15

        if (
            "cancellation charge" in question_text
            and "cancellation charge" in clause_text
        ):
            score += 0.15

        return min(score, 1.0)

    @classmethod
    def _tokenize(cls, text: str) -> set[str]:

        if not text:
            return set()

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

            normalized = cls._normalize_word(
                word
            )

            if (
                normalized
                and normalized not in cls.STOP_WORDS
            ):
                tokens.add(normalized)

        return tokens

    @classmethod
    def _normalize_word(
        cls,
        word: str,
    ) -> str:

        word = word.lower().strip()

        if not word:
            return word

        # Handle irregular English forms first.
        if word in cls.IRREGULAR_WORDS:
            return cls.IRREGULAR_WORDS[word]

        # ies -> y
        #
        # Example:
        # parties -> party
        if (
            word.endswith("ies")
            and len(word) > 4
        ):
            return word[:-3] + "y"

        # ing
        #
        # Example:
        # paying -> pay
        # terminating -> terminate
        if (
            word.endswith("ing")
            and len(word) > 5
        ):
            base = word[:-3]

            if base.endswith("at"):
                return base + "e"

            if base.endswith("v"):
                return base + "e"

            return base

        # ed
        #
        # Example:
        # terminated -> terminate
        # received -> receive
        if (
            word.endswith("ed")
            and len(word) > 4
        ):
            base = word[:-2]

            if base.endswith("at"):
                return base + "e"

            if base.endswith("iv"):
                return base + "e"

            if base.endswith("in"):
                return base + "e"

            return base

        # es
        #
        # Example:
        # notices -> notice
        if (
            word.endswith("es")
            and len(word) > 4
        ):
            return word[:-2]

        # plural s
        #
        # Example:
        # services -> service
        if (
            word.endswith("s")
            and len(word) > 3
        ):
            return word[:-1]

        return word

    @staticmethod
    def _normalize_text(
        tokens: set[str],
    ) -> str:
        return " ".join(sorted(tokens))

    @staticmethod
    def _clause_number_sort_key(
        clause_number: str | None,
    ):
        if not clause_number:
            return ()

        try:
            return tuple(
                int(part)
                for part in clause_number.split(".")
            )
        except ValueError:
            return (0,)