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

    STOP_WORDS = {
        "the", "a", "an", "is", "are", "was", "were",
        "be", "been", "being", "to", "of", "in", "on",
        "at", "for", "and", "or", "with", "this", "that",
        "what", "when", "where", "who", "which", "how",
        "does", "do", "did", "can", "could", "would",
        "should", "will", "shall", "may", "might", "must",
        "upon", "agreement", "contract", "within", "from",
        "by", "as", "it", "its", "their", "them", "they",
        "he", "she", "his", "her", "my", "your", "our",
        "me", "you", "i", "there", "here", "about", "into",
        "after", "before", "during", "than", "then", "if",
        "customer", "party", "parties", "person", "people",
        "provider", "service", "services", "information",
        "terms", "term", "rights", "right", "obligation",
        "obligations", "happens", "happen", "long", "have",
        "get", "give",
    }

    IRREGULAR_WORDS = {
        "paid": "pay",
        "pays": "pay",
        "paying": "pay",
        "fees": "fee",
        "charges": "charge",
        "charged": "charge",
        "charging": "charge",
        "payments": "payment",
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
        "received": "receive",
        "receives": "receive",
        "receiving": "receive",
        "provided": "provide",
        "provides": "provide",
        "providing": "provide",
        "shared": "share",
        "shares": "share",
        "sharing": "share",
        "losses": "loss",
        "days": "day",
        "months": "month",
        "years": "year",
        "notices": "notice",
        "parties": "party",
        "services": "service",
        "invoices": "invoice",
        "percentages": "percentage",
        "bounced": "bounce",
        "bounces": "bounce",
        "bouncing": "bounce",
        "defaulted": "default",
        "defaults": "default",
        "defaulting": "default",
        "repaid": "repay",
        "repays": "repay",
        "repaying": "repay",
        "recalled": "recall",
        "recalls": "recall",
        "recalling": "recall",
        "failed": "fail",
        "fails": "fail",
        "failing": "fail",
        "preclosed": "preclose",
        "preclosing": "preclose",
    }

    # ============================================================
    # MAIN
    # ============================================================

    @classmethod
    def retrieve(
        cls,
        question: str,
        clauses: list[Clause],
        top_k: int = 5,
    ) -> list[RetrievedClause]:

        if not question or not question.strip():
            return []

        question = question.strip()
        question_tokens = cls._tokenize(question)

        if not question_tokens:
            return []

        intent = cls._detect_intent(question)

        results = []

        for clause in clauses:

            text = (
                f"{clause.title or ''} "
                f"{clause.text or ''}"
            )

            clause_tokens = cls._tokenize(text)

            if not clause_tokens:
                continue

            overlap = (
                question_tokens
                & clause_tokens
            )

            score = cls._calculate_score(
                question=question,
                question_tokens=question_tokens,
                clause_tokens=clause_tokens,
                overlap=overlap,
                clause=clause,
                intent=intent,
            )

            if score <= 0:
                continue

            results.append(
                RetrievedClause(
                    clause_id=clause.clause_id,
                    clause_number=clause.clause_number,
                    title=clause.title,
                    text=clause.text,
                    score=round(score, 4),
                )
            )

        results.sort(
            key=lambda item: (
                item.score,
                cls._clause_number_sort_key(
                    item.clause_number
                ),
            ),
            reverse=True,
        )

        return results[:top_k]

    # ============================================================
    # INTENT
    # ============================================================

    @staticmethod
    def _detect_intent(question: str) -> str | None:

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
            "fees" in q
            or "fee" in q
            or "charges" in q
            or "charge" in q
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

    # ============================================================
    # SCHEDULE DETECTION
    # ============================================================

    @staticmethod
    def _is_schedule(clause: Clause) -> bool:

        title = (
            clause.title or ""
        ).strip().lower()

        if title.startswith("schedule"):
            return True

        if title.startswith("annexure"):
            return True

        if title.startswith("appendix"):
            return True

        if title.startswith("exhibit"):
            return True

        return False

    # ============================================================
    # SCHEDULE FIELD MATCH
    # ============================================================

    @staticmethod
    def _schedule_contains(
        clause: Clause,
        intent: str,
    ) -> bool:

        text = (
            f"{clause.title or ''} "
            f"{clause.text or ''}"
        ).lower()

        if intent == "loan_amount":
            return bool(
                re.search(
                    r"amount\s+of\s+the\s+loan",
                    text,
                )
                or re.search(
                    r"loan\s+amount",
                    text,
                )
                or re.search(
                    r"amount\s*\(\s*inr",
                    text,
                )
                or re.search(
                    r"sanctioned\s+amount",
                    text,
                )
            )

        if intent == "interest_rate":
            return (
                "interest" in text
                or "rate of interest" in text
                or "interest rate" in text
            )

        if intent == "tenure":
            return (
                "tenure" in text
                or "loan period" in text
                or "repayment period" in text
                or "periodicity" in text
                or "number of" in text
            )

        if intent == "fees":
            return (
                "fees" in text
                or "fee" in text
                or "charges" in text
                or "charge" in text
            )

        return False

    # ============================================================
    # SCORE
    # ============================================================

    @classmethod
    def _calculate_score(
        cls,
        question: str,
        question_tokens: set[str],
        clause_tokens: set[str],
        overlap: set[str],
        clause: Clause,
        intent: str | None,
    ) -> float:

        text = (
            f"{clause.title or ''} "
            f"{clause.text or ''}"
        ).lower()

        is_schedule = cls._is_schedule(
            clause
        )

        # ========================================================
        # INTENT QUESTIONS
        # ========================================================

        if intent:

            # ----------------------------------------------------
            # LOAN AMOUNT
            # ----------------------------------------------------

            if intent == "loan_amount":

                if is_schedule:
                    if cls._schedule_contains(
                        clause,
                        intent,
                    ):
                        # Schedule is important evidence,
                        # but Clause 2 should remain the primary
                        # contractual reference.
                        return 0.92

                    return 0.05

                if clause.clause_number == "2":
                    return 0.98

                if (
                    "loan amount" in text
                    or "amount of the loan" in text
                    or "amount set out" in text
                ):
                    return 0.70

                if (
                    "loan" in text
                    and "amount" in text
                ):
                    return 0.55

                if overlap:
                    return 0.25

                return 0.0

            # ----------------------------------------------------
            # INTEREST RATE
            # ----------------------------------------------------

            if intent == "interest_rate":

                if is_schedule:
                    if cls._schedule_contains(
                        clause,
                        intent,
                    ):
                        return 0.92

                    return 0.05

                if clause.clause_number == "3":
                    return 0.98

                if (
                    "interest rate" in text
                    or "rate of interest" in text
                ):
                    return 0.70

                if "interest" in text:
                    return 0.40

                return 0.0

            # ----------------------------------------------------
            # TENURE
            # ----------------------------------------------------

            if intent == "tenure":

                if is_schedule:
                    if cls._schedule_contains(
                        clause,
                        intent,
                    ):
                        return 0.92

                    return 0.05

                if clause.clause_number == "3":
                    return 0.80

                if "tenure" in text:
                    return 0.65

                if "loan period" in text:
                    return 0.60

                if "repayment period" in text:
                    return 0.60

                if overlap:
                    return 0.20

                return 0.0

            # ----------------------------------------------------
            # FEES
            # ----------------------------------------------------

            if intent == "fees":

                if is_schedule:
                    if cls._schedule_contains(
                        clause,
                        intent,
                    ):
                        return 0.92

                    return 0.05

                if (
                    "fees / charges" in text
                    or "fees/charges" in text
                ):
                    return 0.90

                if (
                    "fee" in text
                    or "charge" in text
                ):
                    return 0.50

                if overlap:
                    return 0.20

                return 0.0

            # ----------------------------------------------------
            # PRE-CLOSURE
            # ----------------------------------------------------

            if intent == "preclosure":

                if (
                    "pre-close" in text
                    or "pre -close" in text
                    or "preclosure" in text
                    or "prepayment" in text
                ):
                    return 0.95

                if is_schedule:
                    return 0.85

                if clause.clause_number == "3":
                    return 0.65

                if overlap:
                    return 0.20

                return 0.0

            # ----------------------------------------------------
            # PAYMENT BOUNCE
            # ----------------------------------------------------

            if intent == "bounce":

                if clause.clause_number == "3":

                    if (
                        "bounce" in text
                        or "bounced" in text
                        or "insufficient funds"
                        in text
                    ):
                        return 0.98

                if (
                    "bounce" in text
                    or "bounced" in text
                    or "insufficient funds"
                    in text
                ):
                    return 0.70

                if is_schedule:
                    return 0.40

                return 0.0

            # ----------------------------------------------------
            # DEFAULT
            # ----------------------------------------------------

            if intent == "default":

                score = 0.0

                if "default" in text:
                    score += 0.35

                if "failure" in text:
                    score += 0.20

                if "recall" in text:
                    score += 0.20

                if "recover" in text:
                    score += 0.15

                if "overdue" in text:
                    score += 0.20

                if "repayment" in text:
                    score += 0.10

                if clause.clause_number == "5":
                    score += 0.15

                if clause.clause_number == "16":
                    score += 0.20

                return min(
                    score,
                    0.95,
                )

            # ----------------------------------------------------
            # REPAYMENT
            # ----------------------------------------------------

            if intent == "repayment":

                if clause.clause_number == "3":
                    score = 0.75

                    if "due dates" in text:
                        score += 0.15

                    if "repayment" in text:
                        score += 0.10

                    return min(
                        score,
                        0.95,
                    )

                if is_schedule:
                    return 0.85

                if "repayment" in text:
                    return 0.45

                if "due date" in text:
                    return 0.50

                return 0.0

        # ========================================================
        # GENERAL QUESTION
        # ========================================================

        if not overlap:
            return 0.0

        score = (
            len(overlap)
            / max(len(question_tokens), 1)
        ) * 0.60

        if clause.title:

            title_tokens = cls._tokenize(
                clause.title
            )

            title_overlap = (
                question_tokens
                & title_tokens
            )

            score += min(
                0.20,
                len(title_overlap) * 0.10,
            )

        # Schedule should not automatically dominate
        # normal clauses in general questions.
        if is_schedule:
            score *= 0.80

        return min(
            score,
            0.90,
        )

    # ============================================================
    # TOKENIZE
    # ============================================================

    @classmethod
    def _tokenize(
        cls,
        text: str,
    ) -> set[str]:

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

            if not normalized:
                continue

            if normalized in cls.STOP_WORDS:
                continue

            tokens.add(normalized)

        return tokens

    # ============================================================
    # NORMALIZE WORD
    # ============================================================

    @classmethod
    def _normalize_word(
        cls,
        word: str,
    ) -> str:

        word = word.lower().strip()

        if not word:
            return word

        if word in cls.IRREGULAR_WORDS:
            return cls.IRREGULAR_WORDS[word]

        if (
            word.endswith("ies")
            and len(word) > 4
        ):
            return word[:-3] + "y"

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

        if (
            word.endswith("es")
            and len(word) > 4
        ):
            return word[:-2]

        if (
            word.endswith("s")
            and len(word) > 3
        ):
            return word[:-1]

        return word

    # ============================================================
    # SORTING
    # ============================================================

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