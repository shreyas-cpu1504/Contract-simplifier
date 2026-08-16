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

        risk_level, risk_score, risk_reasons, user_impact = (
            cls._analyze_risk(clause)
        )

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
            risk_level=risk_level,
            risk_score=risk_score,
            risk_reasons=risk_reasons,
            user_impact=user_impact,
            recommendations=cls._generate_recommendations(
                clause,
                risk_level,
                risk_reasons,
            ),
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

        clean = " ".join(text.split())
        lower = clean.lower()

        if (
            ("payment" in lower or "pay" in lower)
            and "30 days" in lower
            and "invoice" in lower
        ):
            return (
                "The client must pay the company within 30 days "
                "after receiving an invoice."
            )

        if "late fee" in lower:
            return (
                "The client may have to pay an additional charge "
                "if payment is made late."
            )

        if "immediately" in lower and "terminate" in lower:
            if "breach" in lower:
                return (
                    "The company can end the agreement immediately "
                    "if the client seriously violates its obligations."
                )

            return (
                "A party may be able to end the agreement immediately "
                "when the stated conditions occur."
            )

        if "terminate" in lower:
            return (
                "The agreement contains rules allowing one or more "
                "parties to end the contract."
            )

        if "confidential" in lower and "third parties" in lower:
            return (
                "Confidential information must generally be kept private "
                "and cannot be shared with outside parties without permission."
            )

        if "confidential" in lower:
            return (
                "The parties are required to protect confidential information "
                "from unauthorized disclosure."
            )

        if "indemnif" in lower:
            return (
                "One party may have to compensate the other for certain "
                "losses, claims, damages, or expenses."
            )

        if "non-compete" in lower or "non compete" in lower:
            return (
                "The clause restricts a party from competing or performing "
                "certain activities for a specified period or scope."
            )

        if "exclusive" in lower:
            return (
                "The agreement may restrict a party from working with "
                "other parties for the specified period or activities."
            )

        if "waive" in lower:
            return (
                "A party may be giving up a particular right or legal protection."
            )

        if "breach" in lower:
            return (
                "The clause explains what happens when a party "
                "fails to meet its contractual obligations."
            )

        if "penalty" in lower:
            return (
                "A financial penalty may apply when the specified "
                "contractual condition is violated."
            )

        if "liability" in lower:
            return (
                "The clause defines when a party may be financially "
                "responsible for losses or damages."
            )

        if (
            "obligation" in lower
            or "shall" in lower
            or "must" in lower
        ):
            return (
                "The clause creates a responsibility that a party "
                "is required to follow."
            )

        if "may" in lower:
            return (
                "The clause gives a party a possible right, permission, "
                "or ability to take the stated action."
            )

        return (
            "This clause describes a contractual term that should be "
            "reviewed together with the surrounding agreement."
        )

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

        clean = " ".join(text.split())

        if re.search(
            r"\b(?:client|customer)\s+(?:shall|must)\s+pay\b",
            clean,
            re.IGNORECASE,
        ):
            if re.search(
                r"\blate\s+fee\b",
                clean,
                re.IGNORECASE,
            ):
                return [
                    "Client must pay the applicable late fee when payment is delayed."
                ]

            return [
                "Client must pay the Company as specified in the agreement."
            ]

        if re.search(
            r"\b(?:shall|must)\s+pay\b",
            clean,
            re.IGNORECASE,
        ):
            if re.search(
                r"\blate\s+fee\b",
                clean,
                re.IGNORECASE,
            ):
                return [
                    "The specified party must pay the applicable late fee when payment is delayed."
                ]

            return [
                "The specified party must make the required payment."
            ]

        if re.search(
            r"\b(?:shall|must)\s+keep\b.*\bconfidential\b",
            clean,
            re.IGNORECASE,
        ):
            return [
                "The specified party must keep the covered information confidential."
            ]

        if re.search(
            r"\b(?:shall|must)\s+not\s+(?:be\s+)?disclosed?\b",
            clean,
            re.IGNORECASE,
        ):
            if re.search(
                r"\bto\s+third\s+parties\b",
                clean,
                re.IGNORECASE,
            ):
                return [
                    "Confidential information must not be disclosed to third parties without the required permission."
                ]

            return [
                "The specified party must not disclose the covered information."
            ]

        if re.search(
            r"\bcannot\s+be\s+shared\b.*\b(?:outside|third)\s+part(?:y|ies)\b",
            clean,
            re.IGNORECASE,
        ):
            return [
                "The covered confidential information must not be shared with outside parties without permission."
            ]

        if re.search(
            r"\bmust\s+generally\s+be\s+kept\s+private\b",
            clean,
            re.IGNORECASE,
        ):
            return [
                "The covered confidential information must be kept private."
            ]

        if re.search(
            r"\bis\s+required\s+to\b",
            clean,
            re.IGNORECASE,
        ):
            return [
                "The clause creates a required contractual responsibility."
            ]

        if re.search(
            r"\bagrees\s+to\b",
            clean,
            re.IGNORECASE,
        ):
            return [
                "The clause creates a contractual commitment."
            ]

        if re.search(
            r"\bobligation\b",
            clean,
            re.IGNORECASE,
        ):
            return [
                "The clause creates a contractual obligation."
            ]

        if re.search(
            r"\bmust\b",
            clean,
            re.IGNORECASE,
        ):
            return [
                "The clause requires the specified party to perform the stated action."
            ]

        if re.search(
            r"\bshall\b",
            clean,
            re.IGNORECASE,
        ):
            return [
                "The clause requires the specified party to perform the stated action."
            ]

        return []

    @staticmethod
    def _extract_rights(
        text: str,
    ) -> list[str]:

        clean = " ".join(text.split())

        if re.search(
            r"\bEither\s+party\s+may\s+terminate\b",
            clean,
            re.IGNORECASE,
        ):
            return [
                "Either party has the right to terminate the agreement under the stated conditions."
            ]

        if re.search(
            r"\bCompany\s+may\s+terminate\b",
            clean,
            re.IGNORECASE,
        ):
            return [
                "The Company has the right to terminate the agreement under the stated conditions."
            ]

        if re.search(
            r"\bClient\s+may\s+terminate\b",
            clean,
            re.IGNORECASE,
        ):
            return [
                "The Client has the right to terminate the agreement under the stated conditions."
            ]

        if re.search(
            r"\bmay\s+terminate\b",
            clean,
            re.IGNORECASE,
        ):
            return [
                "A party has the right to terminate the agreement under the stated conditions."
            ]

        if re.search(
            r"\bis\s+entitled\s+to\b",
            clean,
            re.IGNORECASE,
        ):
            return [
                "The clause grants the specified party an entitlement."
            ]

        if re.search(
            r"\bright\s+to\b",
            clean,
            re.IGNORECASE,
        ):
            return [
                "The clause grants the specified party a contractual right."
            ]

        if re.search(
            r"\bmay\b",
            clean,
            re.IGNORECASE,
        ):
            return [
                "The clause gives the specified party permission or discretion to take the stated action."
            ]

        if re.search(
            r"\bcan\b",
            clean,
            re.IGNORECASE,
        ):
            return [
                "The clause gives the specified party the ability to take the stated action."
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
            "pay",
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
            if re.search(
                rf"\b{re.escape(word)}\b",
                lower_text,
            ):
                found.append(word)

        currency_patterns = [
            r"\$\s*\d+(?:,\d{3})*(?:\.\d+)?",
            r"\d+(?:,\d{3})*(?:\.\d+)?\s*(?:USD|INR|EUR|GBP)\b",
            r"\b\d+(?:\.\d+)?\s*%",
        ]

        for pattern in currency_patterns:
            matches = re.findall(
                pattern,
                text,
                re.IGNORECASE,
            )
            found.extend(matches)

        return list(dict.fromkeys(found))

    @classmethod
    def _analyze_risk(
        cls,
        clause: Clause,
    ) -> tuple[str, int, list[str], str]:

        text = clause.text.lower()

        high_risk_rules = {
            "immediately":
                (
                    40,
                    "The clause allows an action to happen immediately "
                    "without a normal notice period."
                ),

            "unlimited liability":
                (
                    50,
                    "The clause may create potentially unlimited financial liability."
                ),

            "indemnify":
                (
                    40,
                    "The clause may require one party to cover losses, claims, or damages."
                ),

            "indemnification":
                (
                    40,
                    "The clause may require one party to cover losses, claims, or damages."
                ),

            "penalty":
                (
                    40,
                    "The clause contains a financial penalty or consequence."
                ),

            "non-compete":
                (
                    40,
                    "The clause may restrict a party from competing or working in certain circumstances."
                ),

            "exclusive":
                (
                    30,
                    "The clause may restrict the user from working with alternative parties."
                ),

            "waive":
                (
                    40,
                    "The clause may cause a party to give up a legal right or protection."
                ),
        }

        medium_risk_rules = {
            "late fee":
                (
                    30,
                    "Late payment may result in an additional financial charge."
                ),

            "terminate":
                (
                    30,
                    "The agreement contains termination rights or consequences."
                ),

            "breach":
                (
                    30,
                    "The clause creates consequences related to a breach of the agreement."
                ),

            "confidential":
                (
                    20,
                    "The clause creates confidentiality responsibilities."
                ),

            "damages":
                (
                    20,
                    "The clause refers to potential financial responsibility for damages."
                ),
        }

        high_reasons = []
        medium_reasons = []

        high_score = 0
        medium_score = 0

        for term, (score, reason) in high_risk_rules.items():
            if term in text:
                high_score += score
                high_reasons.append(reason)

        for term, (score, reason) in medium_risk_rules.items():
            if term in text:
                medium_score += score
                medium_reasons.append(reason)

        if high_reasons:
            score = min(100, high_score)

            reasons = list(
                dict.fromkeys(high_reasons)
            )

            return (
                "HIGH",
                score,
                reasons,
                cls._generate_user_impact(
                    "HIGH",
                    reasons,
                ),
            )

        if medium_reasons:
            score = min(69, medium_score)

            reasons = list(
                dict.fromkeys(medium_reasons)
            )

            return (
                "MEDIUM",
                score,
                reasons,
                cls._generate_user_impact(
                    "MEDIUM",
                    reasons,
                ),
            )

        return (
            "LOW",
            10,
            [],
            "No major risk indicators were detected by the current rule-based analysis.",
        )

    @staticmethod
    def _generate_user_impact(
        risk_level: str,
        reasons: list[str],
    ) -> str:

        if risk_level == "HIGH":
            return (
                "This clause may have a significant effect on the "
                "user's financial, contractual, or legal position "
                "and should be reviewed carefully."
            )

        if risk_level == "MEDIUM":
            return (
                "This clause contains terms that may affect the "
                "user's responsibilities or rights and deserves "
                "attention during review."
            )

        return (
            "This clause appears relatively routine based on "
            "the current rule-based analysis."
        )

    @staticmethod
    def _generate_recommendations(
        clause: Clause,
        risk_level: str,
        risk_reasons: list[str],
    ) -> list[str]:

        text = clause.text.lower()

        recommendations = []

        if "immediately" in text:
            recommendations.extend([
                "Check what events allow immediate action or termination.",
                "Verify whether a notice or cure period should apply.",
                "Review the consequences of immediate termination carefully.",
            ])

        if (
            "unlimited liability" in text
            or "indemnify" in text
            or "indemnification" in text
        ):
            recommendations.extend([
                "Check whether the financial liability has a clear limit or cap.",
                "Identify exactly which losses, claims, or damages are covered.",
                "Review whether the liability is proportionate to the agreement.",
            ])

        if "penalty" in text:
            recommendations.extend([
                "Verify the amount and conditions of the penalty.",
                "Check when the penalty becomes applicable.",
                "Consider whether the penalty is clearly defined in the agreement.",
            ])

        if "late fee" in text:
            recommendations.extend([
                "Verify the late-fee amount or calculation method.",
                "Check when the late fee becomes applicable.",
                "Confirm whether there is a grace period for late payment.",
            ])

        if "terminate" in text:
            recommendations.extend([
                "Check who has the right to terminate the agreement.",
                "Review the required notice period.",
                "Check whether termination creates additional obligations or costs.",
            ])

        if "breach" in text:
            recommendations.extend([
                "Identify what actions or events constitute a breach.",
                "Check what consequences follow from a breach.",
                "Verify whether the agreement provides a cure or correction period.",
            ])

        if "confidential" in text:
            recommendations.extend([
                "Identify what information is considered confidential.",
                "Check how long the confidentiality obligation continues.",
                "Verify which disclosures are permitted.",
            ])

        if "non-compete" in text:
            recommendations.extend([
                "Check the duration and scope of the restriction.",
                "Review which activities or businesses are restricted.",
                "Verify the circumstances in which the restriction applies.",
            ])

        if "exclusive" in text:
            recommendations.extend([
                "Check whether the agreement prevents working with other parties.",
                "Review the duration and scope of the exclusivity requirement.",
            ])

        if "waive" in text:
            recommendations.extend([
                "Identify which right or protection is being waived.",
                "Check whether the waiver applies permanently or only in specific circumstances.",
            ])

        if not recommendations:
            if risk_level == "LOW":
                recommendations.append(
                    "No specific action is currently suggested by the rule-based analysis."
                )
            else:
                recommendations.append(
                    "Review the clause carefully against the surrounding agreement."
                )

        return list(
            dict.fromkeys(recommendations)
        )
