import re

from app.schemas.clause import Clause
from app.schemas.clause_analysis import ClauseAnalysis


class ClauseAnalysisService:

    @classmethod
    def analyze(
        cls,
        clause: Clause,
    ) -> ClauseAnalysis:

        text = clause.text.strip()

        return ClauseAnalysis(
            clause_id=clause.clause_id,
            clause_number=clause.clause_number,
            clause_type=clause.clause_type,
            meaning=cls._generate_basic_meaning(text),
            parties=cls._extract_parties(text),
            obligations=cls._extract_obligations(text),
            rights=cls._extract_rights(text),
            deadlines=cls._extract_deadlines(text),
            conditions=cls._extract_conditions(text),
            monetary_terms=cls._extract_monetary_terms(text),
            risk_level=cls._estimate_risk(clause),
        )

    @classmethod
    def analyze_many(
        cls,
        clauses: list[Clause],
    ) -> list[ClauseAnalysis]:

        return [
            cls.analyze(clause)
            for clause in clauses
        ]

    @staticmethod
    def _generate_basic_meaning(
        text: str,
    ) -> str:

        return text

    @staticmethod
    def _extract_parties(
        text: str,
    ) -> list[str]:

        possible_parties = [
            "Client",
            "Company",
            "Customer",
            "Provider",
            "Seller",
            "Buyer",
            "Employer",
            "Employee",
            "Party",
            "Parties",
        ]

        found = []

        for party in possible_parties:
            if re.search(
                rf"\b{re.escape(party)}\b",
                text,
                re.IGNORECASE,
            ):
                found.append(party)

        return found

    @staticmethod
    def _extract_obligations(
        text: str,
    ) -> list[str]:

        patterns = [
            r"\bshall\b",
            r"\bmust\b",
            r"\bis required to\b",
            r"\bagrees to\b",
            r"\bobligation\b",
        ]

        for pattern in patterns:
            if re.search(
                pattern,
                text,
                re.IGNORECASE,
            ):
                return [
                    "This clause creates an obligation."
                ]

        return []

    @staticmethod
    def _extract_rights(
        text: str,
    ) -> list[str]:

        patterns = [
            r"\bmay\b",
            r"\bis entitled to\b",
            r"\bright to\b",
            r"\bcan\b",
        ]

        for pattern in patterns:
            if re.search(
                pattern,
                text,
                re.IGNORECASE,
            ):
                return [
                    "This clause may provide a right or permission."
                ]

        return []

    @staticmethod
    def _extract_deadlines(
        text: str,
    ) -> list[str]:

        matches = re.findall(
            r"\b\d+\s+(?:day|days|month|months|year|years)\b",
            text,
            re.IGNORECASE,
        )

        return list(dict.fromkeys(matches))

    @staticmethod
    def _extract_conditions(
        text: str,
    ) -> list[str]:

        patterns = [
            r"\bif\b[^.]*",
            r"\bunless\b[^.]*",
            r"\bupon\b[^.]*",
            r"\bafter\b[^.]*",
            r"\bbefore\b[^.]*",
        ]

        conditions = []

        for pattern in patterns:
            matches = re.findall(
                pattern,
                text,
                re.IGNORECASE,
            )
            conditions.extend(matches)

        return list(dict.fromkeys(conditions))

    @staticmethod
    def _extract_monetary_terms(
        text: str,
    ) -> list[str]:

        found = []

        monetary_words = [
            "fee",
            "payment",
            "price",
            "amount",
            "compensation",
            "salary",
            "cost",
            "charge",
            "penalty",
        ]

        lower_text = text.lower()

        for word in monetary_words:
            if word in lower_text:
                found.append(word)

        return list(dict.fromkeys(found))

    @staticmethod
    def _estimate_risk(
        clause: Clause,
    ) -> str:

        text = clause.text.lower()

        high_risk_terms = [
            "immediately",
            "unlimited liability",
            "indemnify",
            "indemnification",
            "penalty",
            "non-compete",
            "exclusive",
            "waive",
        ]

        medium_risk_terms = [
            "late fee",
            "terminate",
            "breach",
            "confidential",
            "damages",
        ]

        if any(
            term in text
            for term in high_risk_terms
        ):
            return "HIGH"

        if any(
            term in text
            for term in medium_risk_terms
        ):
            return "MEDIUM"

        return "LOW"
