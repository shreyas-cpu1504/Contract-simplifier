import re

from app.schemas.clause import Clause


class ClauseClassifierService:

    KEYWORDS = {
        "PAYMENT": [
            "pay",
            "payment",
            "invoice",
            "fee",
            "price",
            "amount",
            "compensation",
        ],
        "TERMINATION": [
            "terminate",
            "termination",
            "terminate this agreement",
            "end this agreement",
        ],
        "CONFIDENTIALITY": [
            "confidential",
            "confidentiality",
            "disclose",
            "non-disclosure",
        ],
        "OBLIGATION": [
            "shall",
            "must",
            "required to",
            "agrees to",
            "obligation",
        ],
        "LIABILITY": [
            "liable",
            "liability",
            "damages",
            "indemnify",
            "indemnification",
        ],
        "GOVERNING_LAW": [
            "governing law",
            "laws of",
            "jurisdiction",
        ],
        "DISPUTE_RESOLUTION": [
            "dispute",
            "arbitration",
            "mediation",
        ],
        "INTELLECTUAL_PROPERTY": [
            "intellectual property",
            "copyright",
            "trademark",
            "patent",
            "ownership",
        ],
        "DATA_PROTECTION": [
            "personal data",
            "personal information",
            "data protection",
            "privacy",
        ],
        "DEFINITION": [
            "means",
            "defined as",
            "refers to",
        ],
    }

    @classmethod
    def classify(cls, clause: Clause) -> Clause:

        text = " ".join(
            filter(
                None,
                [
                    clause.title,
                    clause.text,
                ],
            )
        ).lower()

        # Strong rule for definitions:
        # "Agreement" means ...
        if re.search(r'"[^"]+"\s+means\b', clause.text):
            return clause.model_copy(
                update={"clause_type": "DEFINITION"}
            )

        scores = {}

        for clause_type, keywords in cls.KEYWORDS.items():

            score = 0

            for keyword in keywords:

                matches = re.findall(
                    rf"\b{re.escape(keyword.lower())}\b",
                    text,
                )

                score += len(matches)

            if score > 0:
                scores[clause_type] = score

        if scores:
            best_type = max(
                scores,
                key=scores.get,
            )
        else:
            best_type = "GENERAL"

        return clause.model_copy(
            update={
                "clause_type": best_type,
            }
        )

    @classmethod
    def classify_many(
        cls,
        clauses: list[Clause],
    ) -> list[Clause]:

        return [
            cls.classify(clause)
            for clause in clauses
        ]