from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ClauseAnalysis:
    clause_id: str
    clause_number: Optional[str] = None
    clause_type: Optional[str] = None
    meaning: Optional[str] = None

    # ------------------------------------------------------------------
    # Entities / participants
    # ------------------------------------------------------------------
    parties: list[str] = field(default_factory=list)
    persons: list[str] = field(default_factory=list)
    organizations: list[str] = field(default_factory=list)
    authorities: list[str] = field(default_factory=list)

    # ------------------------------------------------------------------
    # Legal effects / actions
    # ------------------------------------------------------------------
    obligations: list[str] = field(default_factory=list)
    duties: list[str] = field(default_factory=list)
    rights: list[str] = field(default_factory=list)
    permissions: list[str] = field(default_factory=list)
    prohibitions: list[str] = field(default_factory=list)
    powers: list[str] = field(default_factory=list)

    # ------------------------------------------------------------------
    # Logic / conditions
    # ------------------------------------------------------------------
    conditions: list[str] = field(default_factory=list)
    exceptions: list[str] = field(default_factory=list)
    triggers: list[str] = field(default_factory=list)
    consequences: list[str] = field(default_factory=list)

    # ------------------------------------------------------------------
    # Time
    # ------------------------------------------------------------------
    deadlines: list[str] = field(default_factory=list)
    durations: list[str] = field(default_factory=list)
    dates: list[str] = field(default_factory=list)

    # ------------------------------------------------------------------
    # Financial
    # ------------------------------------------------------------------
    monetary_terms: list[str] = field(default_factory=list)
    percentages: list[str] = field(default_factory=list)
    quantities: list[str] = field(default_factory=list)
    currencies: list[str] = field(default_factory=list)
    fees: list[str] = field(default_factory=list)
    penalties: list[str] = field(default_factory=list)
    taxes: list[str] = field(default_factory=list)

    # ------------------------------------------------------------------
    # Legal / regulatory
    # ------------------------------------------------------------------
    laws: list[str] = field(default_factory=list)
    regulations: list[str] = field(default_factory=list)
    statutes: list[str] = field(default_factory=list)
    sections: list[str] = field(default_factory=list)
    articles: list[str] = field(default_factory=list)
    rules: list[str] = field(default_factory=list)
    case_references: list[str] = field(default_factory=list)
    legal_references: list[str] = field(default_factory=list)

    # ------------------------------------------------------------------
    # Subject matter
    # ------------------------------------------------------------------
    assets: list[str] = field(default_factory=list)
    property_terms: list[str] = field(default_factory=list)
    goods: list[str] = field(default_factory=list)
    services: list[str] = field(default_factory=list)
    information: list[str] = field(default_factory=list)
    documents: list[str] = field(default_factory=list)

    # ------------------------------------------------------------------
    # Disputes / enforcement
    # ------------------------------------------------------------------
    dispute_terms: list[str] = field(default_factory=list)
    jurisdiction: list[str] = field(default_factory=list)
    governing_law: list[str] = field(default_factory=list)
    arbitration: list[str] = field(default_factory=list)
    remedies: list[str] = field(default_factory=list)
    enforcement: list[str] = field(default_factory=list)

    # ------------------------------------------------------------------
    # Privacy / data / confidentiality
    # ------------------------------------------------------------------
    privacy_terms: list[str] = field(default_factory=list)
    confidentiality_terms: list[str] = field(default_factory=list)
    data_terms: list[str] = field(default_factory=list)

    # ------------------------------------------------------------------
    # Employment
    # ------------------------------------------------------------------
    employment_terms: list[str] = field(default_factory=list)
    compensation_terms: list[str] = field(default_factory=list)
    benefits: list[str] = field(default_factory=list)
    leave_terms: list[str] = field(default_factory=list)

    # ------------------------------------------------------------------
    # Loans / credit
    # ------------------------------------------------------------------
    loan_terms: list[str] = field(default_factory=list)
    interest_terms: list[str] = field(default_factory=list)
    repayment_terms: list[str] = field(default_factory=list)
    collateral: list[str] = field(default_factory=list)
    default_terms: list[str] = field(default_factory=list)

    # ------------------------------------------------------------------
    # Intellectual property / restrictions
    # ------------------------------------------------------------------
    intellectual_property_terms: list[str] = field(default_factory=list)
    restriction_terms: list[str] = field(default_factory=list)
    non_compete_terms: list[str] = field(default_factory=list)
    exclusivity_terms: list[str] = field(default_factory=list)
    waiver_terms: list[str] = field(default_factory=list)

    # ------------------------------------------------------------------
    # Notices / procedural material
    # ------------------------------------------------------------------
    notice_terms: list[str] = field(default_factory=list)
    procedural_terms: list[str] = field(default_factory=list)

    # ------------------------------------------------------------------
    # Risk
    # ------------------------------------------------------------------
    risk_level: str = "LOW"
    risk_score: int = 0
    risk_reasons: list[str] = field(default_factory=list)

    # ------------------------------------------------------------------
    # User-facing interpretation
    # ------------------------------------------------------------------
    user_impact: Optional[str] = None
    recommendations: list[str] = field(default_factory=list)


class ClauseAnalysisService:
    """
    Universal deterministic clause analyzer.

    IMPORTANT:
    This service does NOT assume that the input is a commercial contract.

    It can analyze individual provisions from:
        - contracts
        - employment letters
        - offer letters
        - loan documents
        - leases
        - government notices
        - policies
        - regulations
        - legal notices
        - court-related documents
        - agreements
        - terms and conditions
        - compliance documents
        - other legal / administrative documents

    This is the deterministic foundation.

    Later layers can add:
        - NER
        - embeddings
        - LLM analysis
        - RAG
        - legal knowledge retrieval
        - document-level reasoning

    without changing the basic analysis model.
    """

    # ================================================================
    # Core patterns
    # ================================================================

    PARTY_WORDS = [
        "client", "customer", "company", "employer", "employee",
        "borrower", "lender", "tenant", "landlord", "licensor",
        "licensee", "contractor", "consultant", "supplier", "vendor",
        "buyer", "seller", "applicant", "respondent", "petitioner",
        "plaintiff", "defendant", "authority", "government",
        "department", "agency", "regulator", "provider", "recipient",
        "issuer", "holder", "owner", "operator", "individual",
        "party", "parties", "subscriber", "member", "beneficiary",
        "guarantor", "agent", "principal"
    ]

    OBLIGATION_PATTERNS = [
        r"\bshall\b",
        r"\bmust\b",
        r"\bis required to\b",
        r"\bare required to\b",
        r"\bagrees to\b",
        r"\bundertakes to\b",
        r"\bis responsible for\b",
        r"\bare responsible for\b",
        r"\bhas a duty to\b",
        r"\bduty to\b",
        r"\bwill provide\b",
        r"\bwill pay\b",
        r"\bwill submit\b",
        r"\bwill comply\b",
    ]

    RIGHT_PATTERNS = [
        r"\bhas the right to\b",
        r"\bhave the right to\b",
        r"\bis entitled to\b",
        r"\bare entitled to\b",
        r"\bis permitted to\b",
        r"\bare permitted to\b",
        r"\bhas authority to\b",
        r"\bhave authority to\b",
    ]

    PROHIBITION_PATTERNS = [
        r"\bshall not\b",
        r"\bmust not\b",
        r"\bmay not\b",
        r"\bcannot\b",
        r"\bcan not\b",
        r"\bprohibited\b",
        r"\bforbidden\b",
        r"\bnot permitted\b",
        r"\bwithout permission\b",
        r"\bwithout authorization\b",
        r"\bwithout authorisation\b",
    ]

    CONDITION_PATTERNS = [
        r"\bif\b",
        r"\bunless\b",
        r"\bprovided that\b",
        r"\bsubject to\b",
        r"\bon the condition that\b",
        r"\bwhere\b",
        r"\bwhen\b",
        r"\bin the event that\b",
        r"\bin the event of\b",
    ]

    TRIGGER_PATTERNS = [
        r"\bupon\b",
        r"\bwhen\b",
        r"\bif\b",
        r"\bafter\b",
        r"\bbefore\b",
        r"\bon receipt of\b",
        r"\bon occurrence of\b",
        r"\bin the event of\b",
        r"\bfollowing\b",
        r"\bfrom the date of\b",
    ]

    EXCEPTION_PATTERNS = [
        r"\bexcept\b",
        r"\bexcept where\b",
        r"\bunless\b",
        r"\bnotwithstanding\b",
        r"\bprovided that\b",
        r"\bsubject to\b",
        r"\bother than\b",
        r"\bexcluding\b",
    ]

    DATE_PATTERNS = [
        r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
        r"\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b",
        r"\b\d{1,2}(?:st|nd|rd|th)?\s+"
        r"(?:January|February|March|April|May|June|July|August|"
        r"September|October|November|December)"
        r"(?:\s+\d{4})?\b",
        r"\b(?:January|February|March|April|May|June|July|August|"
        r"September|October|November|December)"
        r"\s+\d{1,2}(?:st|nd|rd|th)?"
        r"(?:,\s*|\s+)\d{4}\b",
    ]

    DURATION_PATTERN = (
        r"\b\d+(?:\.\d+)?\s+"
        r"(?:second|seconds|minute|minutes|hour|hours|"
        r"day|days|week|weeks|month|months|year|years)\b"
    )

    MONEY_PATTERN = (
        r"(?:(?:INR|USD|EUR|GBP|JPY|AUD|CAD)\s*"
        r"(?:\d{1,3}(?:,\d{3})*|\d+)(?:\.\d+)?"
        r"|(?:Rs\.?|\$)\s*"
        r"(?:\d{1,3}(?:,\d{3})*|\d+)(?:\.\d+)?"
        r"|\b\d{1,3}(?:,\d{3})*(?:\.\d+)?\s*"
        r"(?:rupees|dollars|euros|pounds|yen)\b)"
    )

    PERCENT_PATTERN = r"\b\d+(?:\.\d+)?\s*%"

    LEGAL_REFERENCE_PATTERNS = {
        "sections": [
            r"\b(?:section|sec\.?)\s+[A-Za-z0-9().-]+"
        ],
        "articles": [
            r"\b(?:article|art\.?)\s+[A-Za-z0-9().-]+"
        ],
        "rules": [
            r"\b(?:rule|rules)\s+[A-Za-z0-9().-]+"
        ],
        "regulations": [
            r"\b(?:regulation|regulations)\s+[A-Za-z0-9().-]+"
        ],
        "statutes": [
            r"\b(?:statute|statutes)\s+[A-Za-z0-9().-]+"
        ],
        "laws": [
            r"\b(?:law|laws|act|acts)\s+[A-Za-z0-9().,&'() -]{2,80}"
        ],
    }

    # ================================================================
    # Analysis
    # ================================================================

    @classmethod
    def analyze_clause(cls, clause) -> ClauseAnalysis:
        text = cls._clean(getattr(clause, "text", "") or "")

        result = ClauseAnalysis(
            clause_id=getattr(clause, "clause_id", "") or "",
            clause_number=getattr(clause, "clause_number", None),
            clause_type=getattr(clause, "clause_type", None),
        )

        if not text:
            result.meaning = "No substantive text was available for analysis."
            result.user_impact = (
                "No substantive content was available for deterministic analysis."
            )
            return result

        # Entities
        result.parties = cls._extract_parties(text)
        result.organizations = cls._extract_organizations(text)
        result.authorities = cls._extract_authorities(text)

        # Legal effects
        result.obligations = cls._extract_by_patterns(
            text, cls.OBLIGATION_PATTERNS
        )
        result.duties = list(result.obligations)

        result.rights = cls._extract_by_patterns(
            text, cls.RIGHT_PATTERNS
        )

        result.permissions = cls._extract_by_patterns(
            text,
            [
                r"\bmay\s+(?!result\b|cause\b|lead\b|constitute\b)",
                r"\bis permitted to\b",
                r"\bare permitted to\b",
                r"\bhas permission to\b",
                r"\bhave permission to\b",
                r"\bis authorized to\b",
                r"\bare authorized to\b",
                r"\bis authorised to\b",
                r"\bare authorised to\b",
                r"\bhas authority to\b",
                r"\bhave authority to\b",
            ],
        )

        result.prohibitions = cls._extract_by_patterns(
            text, cls.PROHIBITION_PATTERNS
        )

        # Conditions
        result.conditions = cls._extract_by_patterns(
            text, cls.CONDITION_PATTERNS
        )

        result.exceptions = cls._extract_by_patterns(
            text, cls.EXCEPTION_PATTERNS
        )

        result.triggers = cls._extract_by_patterns(
            text, cls.TRIGGER_PATTERNS
        )

        result.consequences = cls._keyword_sentences(
            text,
            [
                "consequence",
                "consequences",
                "result",
                "resulting",
                "penalty",
                "remedy",
                "remedies",
                "liable",
                "liability",
                "default",
                "termination",
                "damages",
                "sanction",
                "fine",
            ],
        )

        # Time
        result.durations = cls._regex_extract(
            text, cls.DURATION_PATTERN
        )
        result.deadlines = list(result.durations)
        result.dates = cls._extract_dates(text)

        # Financial
        result.monetary_terms = cls._extract_money(text)
        result.percentages = cls._regex_extract(
            text, cls.PERCENT_PATTERN
        )

        result.currencies = cls._extract_currencies(text)

        result.fees = cls._keyword_sentences(
            text,
            ["fee", "fees", "charge", "charges", "commission"],
        )

        result.penalties = cls._keyword_sentences(
            text,
            ["penalty", "penalties", "fine", "fines"],
        )

        result.taxes = cls._keyword_sentences(
            text,
            ["tax", "taxes", "gst", "vat", "withholding", "duty"],
        )

        result.quantities = cls._extract_quantities(text)

        # Legal / regulatory
        result.sections = cls._extract_legal(
            text, "sections"
        )
        result.articles = cls._extract_legal(
            text, "articles"
        )
        result.rules = cls._extract_legal(
            text, "rules"
        )
        result.regulations = cls._extract_legal(
            text, "regulations"
        )
        result.statutes = cls._extract_legal(
            text, "statutes"
        )
        result.laws = cls._extract_legal(
            text, "laws"
        )

        result.case_references = cls._keyword_sentences(
            text,
            [
                "case",
                "judgment",
                "judgement",
                "court",
                "tribunal",
                "decision",
                "citation",
                "precedent",
                "petition",
                "appeal",
                "order",
            ],
        )

        result.legal_references = cls._unique(
            result.laws
            + result.regulations
            + result.statutes
            + result.sections
            + result.articles
            + result.rules
            + result.case_references
        )

        # Subject matter
        result.assets = cls._keyword_sentences(
            text,
            [
                "asset",
                "assets",
                "property",
                "equipment",
                "vehicle",
                "land",
                "building",
                "shares",
                "securities",
                "inventory",
            ],
        )

        result.property_terms = cls._keyword_sentences(
            text,
            [
                "real estate",
                "premises",
                "lease",
                "tenant",
                "landlord",
                "ownership",
                "title to",
                "property rights",
                "property ownership",
                "immovable property",
                "movable property",
            ],
        )

        result.goods = cls._keyword_sentences(
            text,
            [
                "goods",
                "product",
                "products",
                "merchandise",
                "materials",
                "inventory",
            ],
        )

        result.services = cls._keyword_sentences(
            text,
            [
                "service",
                "services",
                "software",
                "support",
                "maintenance",
                "consulting",
                "development",
            ],
        )

        result.information = cls._keyword_sentences(
            text,
            [
                "information",
                "data",
                "records",
                "personal information",
                "personal data",
                "confidential information",
            ],
        )

        result.documents = cls._keyword_sentences(
            text,
            [
                "document",
                "documents",
                "certificate",
                "notice",
                "report",
                "application",
                "form",
                "statement",
                "invoice",
            ],
        )

        # Dispute / enforcement
        result.dispute_terms = cls._keyword_sentences(
            text,
            [
                "dispute",
                "disputes",
                "litigation",
                "court proceedings",
                "legal proceedings",
                "arising out of or in connection with",
                "settled by arbitration",
                "resolved by arbitration",
            ],
        )

        result.jurisdiction = cls._keyword_sentences(
            text,
            [
                "jurisdiction",
                "court",
                "venue",
                "territorial jurisdiction",
            ],
        )

        result.governing_law = cls._keyword_sentences(
            text,
            [
                "governing law",
                "governed by",
                "applicable law",
                "laws of",
            ],
        )

        result.arbitration = cls._keyword_sentences(
            text,
            [
                "arbitration",
                "arbitrator",
                "arbitral",
            ],
        )

        result.remedies = cls._keyword_sentences(
            text,
            [
                "remedy",
                "remedies",
                "damages",
                "injunction",
                "relief",
                "compensation",
                "restitution",
            ],
        )

        result.enforcement = cls._keyword_sentences(
            text,
            [
                "enforce",
                "enforcement",
                "enforceable",
                "execution",
                "execute",
                "compliance",
            ],
        )

        # Privacy / confidentiality
        result.privacy_terms = cls._keyword_sentences(
            text,
            [
                "privacy",
                "personal data",
                "personal information",
                "privacy policy",
                "data protection",
                "data privacy",
            ],
        )

        result.confidentiality_terms = cls._keyword_sentences(
            text,
            [
                "confidential",
                "confidentiality",
                "non-disclosure",
                "nda",
                "secret",
                "trade secret",
            ],
        )

        result.data_terms = cls._keyword_sentences(
            text,
            [
                "data",
                "processing",
                "processor",
                "controller",
                "consent",
                "collect",
                "collection",
                "storage",
                "sharing",
                "disclosure",
                "retention",
            ],
        )

        # Employment
        result.employment_terms = cls._keyword_sentences(
            text,
            [
                "employee",
                "employer",
                "employment",
                "job",
                "salary",
                "wages",
                "probation",
                "notice period",
                "working hours",
                "job duties",
                "termination of employment",
                "promotion",
                "disciplinary",
            ],
        )

        result.compensation_terms = cls._keyword_sentences(
            text,
            [
                "salary",
                "wages",
                "compensation",
                "bonus",
                "commission",
                "remuneration",
                "stipend",
                "payroll",
                "gross pay",
                "net pay",
                "base pay",
                "base salary",
                "annual salary",
                "monthly salary",
                "hourly wage",
            ],
        )

        result.benefits = cls._keyword_sentences(
            text,
            [
                "benefit",
                "benefits",
                "insurance",
                "provident fund",
                "pension",
                "allowance",
                "medical",
            ],
        )

        result.leave_terms = cls._keyword_sentences(
            text,
            [
                "leave",
                "vacation",
                "holiday",
                "sick leave",
                "maternity",
                "paternity",
                "absence",
            ],
        )

        # Loans / credit
        result.loan_terms = cls._keyword_sentences(
            text,
            [
                "loan",
                "borrower",
                "lender",
                "principal",
                "credit",
                "facility",
                "financing",
                "disbursement",
            ],
        )

        result.interest_terms = cls._keyword_sentences(
            text,
            [
                "interest rate",
                "interest",
                "annual percentage rate",
                "apr",
                "rate of interest",
            ],
        )

        result.repayment_terms = cls._keyword_sentences(
            text,
            [
                "repayment",
                "repay",
                "installment",
                "instalment",
                "emi",
                "amortization",
                "amortisation",
                "maturity",
            ],
        )

        result.collateral = cls._keyword_sentences(
            text,
            [
                "collateral",
                "security",
                "secured",
                "mortgage",
                "pledge",
                "lien",
                "guarantee",
                "guarantor",
            ],
        )

        result.default_terms = cls._keyword_sentences(
            text,
            [
                "default",
                "event of default",
                "failure to pay",
                "non-payment",
                "nonpayment",
                "overdue",
            ],
        )

        # IP / restrictions
        result.intellectual_property_terms = cls._keyword_sentences(
            text,
            [
                "intellectual property",
                "copyright",
                "patent",
                "trademark",
                "trade mark",
                "license",
                "licence",
                "invention",
                "royalty",
                "proprietary",
                "know-how",
            ],
        )

        result.restriction_terms = cls._keyword_sentences(
            text,
            [
                "restriction",
                "restrict",
                "restricted",
                "prohibit",
                "prohibited",
                "limitation",
                "limit",
            ],
        )

        result.non_compete_terms = cls._keyword_sentences(
            text,
            [
                "non-compete",
                "non compete",
                "noncompetition",
                "not compete",
            ],
        )

        result.exclusivity_terms = cls._keyword_sentences(
            text,
            [
                "exclusive",
                "exclusivity",
                "sole",
                "exclusive dealing",
            ],
        )

        result.waiver_terms = cls._keyword_sentences(
            text,
            [
                "waive",
                "waiver",
                "waived",
            ],
        )

        # Notices / procedure
        result.notice_terms = cls._keyword_sentences(
            text,
            [
                "notice",
                "written notice",
                "notification",
                "notify",
                "notified",
                "service of notice",
            ],
        )

        result.procedural_terms = cls._keyword_sentences(
            text,
            [
                "procedure",
                "procedures",
                "process",
                "application",
                "hearing",
                "appeal",
                "review",
                "submission",
                "filing",
            ],
        )

        # Risk
        (
            result.risk_level,
            result.risk_score,
            result.risk_reasons,
        ) = cls._calculate_risk(result, text)

        # Interpretation
        result.meaning = cls._generate_meaning(result, text)
        result.user_impact = cls._generate_user_impact(result)
        result.recommendations = cls._generate_recommendations(result)

        return result

    # ================================================================
    # Text helpers
    # ================================================================

    @staticmethod
    def _clean(text: str) -> str:
        text = text.replace("\r\n", "\n")
        text = text.replace("\r", "\n")
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n+", "\n", text)
        return text.strip()

    @staticmethod
    def _unique(values: list[str]) -> list[str]:
        result = []
        seen = set()

        for value in values:
            clean = str(value).strip()

            if not clean:
                continue

            key = clean.casefold()

            if key not in seen:
                seen.add(key)
                result.append(clean)

        return result

    @classmethod
    def _sentences(cls, text: str) -> list[str]:
        parts = re.split(
            r"(?<=[.!?;])\s+|\n+",
            text,
        )

        return [
            part.strip()
            for part in parts
            if part.strip()
        ]

    @staticmethod
    def _is_heading(sentence: str) -> bool:
        """
        Return True when a sentence is likely to be a clause heading
        rather than substantive contractual text.
        """

        value = sentence.strip()

        if not value:
            return True

        # Numbered headings such as "1. PAYMENT"
        if re.match(
            r"^\d+(?:\.\d+)*\.?\s+[A-Z][A-Z\s_-]{2,}$",
            value,
        ):
            return True

        # Plain uppercase headings such as "CONFIDENTIALITY"
        if (
            len(value) <= 80
            and value.upper() == value
            and re.search(r"[A-Z]", value)
            and not re.search(r"[.!?]", value)
        ):
            return True

        return False


    @classmethod
    def _keyword_sentences(
        cls,
        text: str,
        keywords: list[str],
    ) -> list[str]:
        found = []

        for sentence in cls._sentences(text):
            if cls._is_heading(sentence):
                continue

            lower = sentence.lower()

            for keyword in keywords:
                keyword_lower = keyword.lower().strip()

                if not keyword_lower:
                    continue

                # Multi-word phrases can safely use substring matching.
                if " " in keyword_lower:
                    matched = keyword_lower in lower
                else:
                    # Single words require word boundaries so that
                    # "pay" does not match "repayment", etc.
                    pattern = (
                        r"(?<!\w)"
                        + re.escape(keyword_lower)
                        + r"(?!\w)"
                    )
                    matched = re.search(pattern, lower) is not None

                if matched:
                    found.append(sentence)
                    break

        return cls._unique(found)

    @classmethod
    def _extract_by_patterns(
        cls,
        text: str,
        patterns: list[str],
    ) -> list[str]:
        found = []

        for sentence in cls._sentences(text):
            for pattern in patterns:
                try:
                    if re.search(
                        pattern,
                        sentence,
                        re.IGNORECASE,
                    ):
                        found.append(sentence)
                        break
                except re.error:
                    continue

        return cls._unique(found)

    @classmethod
    def _regex_extract(
        cls,
        text: str,
        pattern: str,
    ) -> list[str]:
        try:
            return cls._unique(
                [
                    match.group(0).strip()
                    for match in re.finditer(
                        pattern,
                        text,
                        re.IGNORECASE,
                    )
                ]
            )
        except re.error:
            return []

    # ================================================================
    # Entity extraction
    # ================================================================

    @classmethod
    def _extract_parties(cls, text: str) -> list[str]:
        found = []

        for word in cls.PARTY_WORDS:
            if re.search(
                rf"\b{re.escape(word)}\b",
                text,
                re.IGNORECASE,
            ):
                found.append(word.title())

        return cls._unique(found)

    @classmethod
    def _extract_organizations(cls, text: str) -> list[str]:
        """
        Extract likely named organizations.

        Generic contractual party labels such as Client, Company,
        Party, Customer, Employer, and Employee are not treated as
        organization names.
        """

        patterns = [
            r"\b[A-Z][A-Za-z0-9&.,'()-]*(?:\s+[A-Z][A-Za-z0-9&.,'()-]*){0,5}\s+(?:"
            r"Limited|Ltd\.?|"
            r"Corporation|Corp\.?|"
            r"Inc\.?|"
            r"LLC|"
            r"LLP|"
            r"Pvt\.?\s+Ltd\.?|"
            r"Private\s+Limited|"
            r"PLC|"
            r"Bank|"
            r"University|"
            r"Institute|"
            r"Foundation|"
            r"Authority"
            r")\b"
        ]

        found = []

        for pattern in patterns:
            found.extend(
                cls._regex_extract(text, pattern)
            )

        blocked = {
            "The Company",
            "The Client",
            "The Agreement",
            "This Agreement",
            "Either Party",
            "This Clause",
            "The Court",
            "The Government",
        }

        generic_party_words = {
            "client",
            "company",
            "party",
            "customer",
            "employer",
            "employee",
            "borrower",
            "lender",
            "seller",
            "buyer",
            "supplier",
            "vendor",
            "contractor",
            "consultant",
            "licensor",
            "licensee",
        }

        cleaned = []

        for value in found:
            value = value.strip()

            if value in blocked:
                continue

            words = value.split()

            # Remove a candidate if it consists only of generic
            # contractual party terminology.
            meaningful_words = [
                word.strip(".,")
                for word in words
                if word.strip(".,").casefold()
                not in generic_party_words
            ]

            if not meaningful_words:
                continue

            # Avoid sentences that merely contain a generic party
            # label before an organization-like suffix.
            lower_value = value.casefold()

            if (
                "this agreement is between" in lower_value
                or "agreement is between" in lower_value
            ):
                continue

            cleaned.append(value)

        return cls._unique(cleaned)


    @classmethod
    def _extract_authorities(cls, text: str) -> list[str]:
        return cls._keyword_sentences(
            text,
            [
                "government",
                "ministry",
                "department",
                "authority",
                "agency",
                "regulator",
                "regulatory authority",
                "commission",
                "court",
                "tribunal",
                "municipality",
                "local authority",
                "police",
                "bank",
                "central bank",
                "tax authority",
            ],
        )

    # ================================================================
    # Time / money
    # ================================================================

    @classmethod
    def _extract_dates(cls, text: str) -> list[str]:
        found = []

        for pattern in cls.DATE_PATTERNS:
            found.extend(
                cls._regex_extract(text, pattern)
            )

        return cls._unique(found)

    @classmethod
    def _extract_money(cls, text: str) -> list[str]:
        return cls._regex_extract(
            text,
            cls.MONEY_PATTERN,
        )

    @classmethod
    def _extract_currencies(cls, text: str) -> list[str]:
        patterns = [
            r"\bINR\b",
            r"\bUSD\b",
            r"\bEUR\b",
            r"\bGBP\b",
            r"\bJPY\b",
            r"\bAUD\b",
            r"\bCAD\b",
            r"?",
            r"\$",
            r"�",
            r"�",
            r"�",
            r"\brupees?\b",
            r"\bdollars?\b",
            r"\beuros?\b",
            r"\bpounds?\b",
            r"\byen\b",
        ]

        found = []

        for pattern in patterns:
            found.extend(
                cls._regex_extract(text, pattern)
            )

        return cls._unique(found)

    @classmethod
    def _extract_quantities(cls, text: str) -> list[str]:
        patterns = [
            r"\b\d+(?:\.\d+)?\s*(?:kg|kgs|kilograms?)\b",
            r"\b\d+(?:\.\d+)?\s*(?:g|grams?)\b",
            r"\b\d+(?:\.\d+)?\s*(?:km|kilometers?|kilometres?)\b",
            r"\b\d+(?:\.\d+)?\s*(?:m|meters?|metres?)\b",
            r"\b\d+(?:\.\d+)?\s*(?:litres?|liters?|L)\b",
            r"\b\d+(?:\.\d+)?\s*(?:units?|items?|shares?)\b",
        ]

        found = []

        for pattern in patterns:
            found.extend(
                cls._regex_extract(text, pattern)
            )

        return cls._unique(found)

    # ================================================================
    # Legal references
    # ================================================================

    @classmethod
    def _extract_legal(
        cls,
        text: str,
        category: str,
    ) -> list[str]:
        found = []

        for pattern in cls.LEGAL_REFERENCE_PATTERNS.get(
            category,
            [],
        ):
            found.extend(
                cls._regex_extract(text, pattern)
            )

        return cls._unique(found)

    # ================================================================
    # Meaning
    # ================================================================

    @classmethod
    def _generate_meaning(
        cls,
        result: ClauseAnalysis,
        text: str,
    ) -> str:
        """
        Generate a concise deterministic explanation of the clause.

        This is intentionally rule-based for the current analysis layer.
        Later, an AI/LLM layer can provide richer contextual explanations.
        """

        parts = []

        # ------------------------------------------------------------
        # Obligations / duties
        # ------------------------------------------------------------
        obligation_sentences = cls._unique(
            result.obligations + result.duties
        )

        if obligation_sentences:
            if len(obligation_sentences) == 1:
                parts.append(
                    "It requires: "
                    + obligation_sentences[0]
                )
            else:
                parts.append(
                    "It creates the following requirements: "
                    + " ".join(obligation_sentences)
                )

        # ------------------------------------------------------------
        # Rights / permissions
        # ------------------------------------------------------------
        right_sentences = cls._unique(
            result.rights + result.permissions
        )

        if right_sentences:
            if len(right_sentences) == 1:
                parts.append(
                    "It gives the following right or permission: "
                    + right_sentences[0]
                )
            else:
                parts.append(
                    "It also provides these rights or permissions: "
                    + " ".join(right_sentences)
                )

        # ------------------------------------------------------------
        # Prohibitions
        # ------------------------------------------------------------
        if result.prohibitions:
            if len(result.prohibitions) == 1:
                parts.append(
                    "It restricts the following action: "
                    + result.prohibitions[0]
                )
            else:
                parts.append(
                    "It contains restrictions on the following actions: "
                    + " ".join(result.prohibitions)
                )

        # ------------------------------------------------------------
        # Conditions / triggers
        # ------------------------------------------------------------
        if result.conditions:
            parts.append(
                "It applies subject to these conditions: "
                + " ".join(result.conditions)
            )

        if result.triggers:
            parts.append(
                "It is triggered by: "
                + " ".join(result.triggers)
            )

        # ------------------------------------------------------------
        # Consequences
        # ------------------------------------------------------------
        if result.consequences:
            parts.append(
                "It specifies these consequences: "
                + " ".join(result.consequences)
            )

        # ------------------------------------------------------------
        # Financial terms
        # ------------------------------------------------------------
        if result.monetary_terms and not obligation_sentences:
            parts.append(
                "It contains monetary terms including: "
                + ", ".join(result.monetary_terms)
            )

        # ------------------------------------------------------------
        # Timing
        # ------------------------------------------------------------
        timing = cls._unique(
            result.dates
            + result.deadlines
            + result.durations
        )

        if timing and not obligation_sentences:
            parts.append(
                "The required timing is: "
                + ", ".join(timing)
            )

        # ------------------------------------------------------------
        # Disputes / jurisdiction
        # ------------------------------------------------------------
        if result.dispute_terms:
            parts.append(
                "It addresses dispute resolution or enforcement."
            )

        if result.jurisdiction:
            parts.append(
                "It specifies or affects the applicable jurisdiction."
            )

        if result.arbitration:
            parts.append(
                "It contains an arbitration-related provision."
            )

        # ------------------------------------------------------------
        # Privacy / data
        # ------------------------------------------------------------
        if result.data_terms or result.privacy_terms:
            parts.append(
                "It addresses data, privacy, or information-handling matters."
            )

        # ------------------------------------------------------------
        # Employment
        # ------------------------------------------------------------
        if result.employment_terms:
            parts.append(
                "It concerns employment-related terms."
            )

        # ------------------------------------------------------------
        # Loans
        # ------------------------------------------------------------
        if result.loan_terms:
            parts.append(
                "It concerns loan, credit, financing, or repayment terms."
            )

        # ------------------------------------------------------------
        # Property
        # ------------------------------------------------------------
        if result.property_terms:
            parts.append(
                "It concerns property, ownership, possession, or related terms."
            )

        # ------------------------------------------------------------
        # Intellectual property
        # ------------------------------------------------------------
        if result.intellectual_property_terms:
            parts.append(
                "It concerns intellectual-property rights or restrictions."
            )

        # ------------------------------------------------------------
        # Confidentiality
        # ------------------------------------------------------------
        if result.confidentiality_terms:
            parts.append(
                "It creates confidentiality or non-disclosure requirements."
            )

        # ------------------------------------------------------------
        # Legal references
        # ------------------------------------------------------------
        if result.legal_references:
            parts.append(
                "It contains legal, statutory, regulatory, or judicial references."
            )

        # ------------------------------------------------------------
        # Fallback
        # ------------------------------------------------------------
        if not parts:
            return (
                "This provision defines the relationship or general terms between the parties."

            )

        return " ".join(parts)


    # ================================================================
    # Risk
    # ================================================================

    @classmethod
    def _calculate_risk(
        cls,
        result: ClauseAnalysis,
        text: str,
    ) -> tuple[str, int, list[str]]:
        lower = text.lower()

        score = 0
        reasons = []

        high_rules = [
            (
                "unlimited liability",
                45,
                "The provision may create potentially unlimited liability."
            ),
            (
                "indemnify",
                35,
                "The provision may require one party to cover losses or claims."
            ),
            (
                "indemnification",
                35,
                "The provision may require one party to cover losses or claims."
            ),
            (
                "waive",
                30,
                "The provision may involve giving up a right or protection."
            ),
            (
                "waiver",
                30,
                "The provision may involve giving up a right or protection."
            ),
            (
                "non-compete",
                30,
                "The provision may impose a significant restriction on activities."
            ),
            (
                "non compete",
                30,
                "The provision may impose a significant restriction on activities."
            ),
            (
                "irrevocable",
                30,
                "The provision describes an action or authority as irrevocable."
            ),
            (
                "without notice",
                25,
                "The provision may permit action without prior notice."
            ),
        ]

        medium_rules = [
            (
                "penalty",
                20,
                "The provision contains a penalty or financial consequence."
            ),
            (
                "late fee",
                15,
                "Late action may result in an additional financial charge."
            ),
            (
                "default",
                20,
                "The provision contains default-related consequences."
            ),
            (
                "termination",
                15,
                "The provision contains termination-related rights or consequences."
            ),
            (
                "breach",
                20,
                "The provision contains breach-related consequences."
            ),
            (
                "confidential",
                10,
                "The provision creates confidentiality responsibilities."
            ),
            (
                "jurisdiction",
                10,
                "The provision affects where legal proceedings may occur."
            ),
            (
                "arbitration",
                10,
                "The provision requires or refers to arbitration."
            ),
            (
                "collateral",
                15,
                "The provision involves security or collateral."
            ),
            (
                "guarantee",
                15,
                "The provision may create a guarantee obligation."
            ),
            (
                "interest rate",
                10,
                "The provision contains an interest-rate term."
            ),
        ]

        for phrase, weight, reason in high_rules:
            if phrase in lower:
                score += weight
                reasons.append(reason)

        for phrase, weight, reason in medium_rules:
            if phrase in lower:
                score += weight
                reasons.append(reason)

        # Additional structural signals
        if len(result.prohibitions) >= 2:
            score += 10
            reasons.append(
                "The provision contains multiple restrictions or prohibitions."
            )

        if result.monetary_terms and result.penalties:
            score += 10
            reasons.append(
                "The provision combines financial terms with penalties or consequences."
            )

        if result.legal_references and result.consequences:
            score += 5
            reasons.append(
                "The provision combines legal references with stated consequences."
            )

        score = min(score, 100)
        reasons = cls._unique(reasons)

        if score >= 60:
            level = "HIGH"
        elif score >= 20:
            level = "MEDIUM"
        else:
            level = "LOW"

        if not reasons:
            reasons = [
                "No major risk indicator was detected by the current deterministic rules."
            ]

        return level, score, reasons

    # ================================================================
    # Impact
    # ================================================================

    @staticmethod
    def _generate_user_impact(
        result: ClauseAnalysis,
    ) -> str:
        categories = []

        mapping = [
            (result.obligations, "obligations or duties"),
            (result.rights, "rights or permissions"),
            (result.prohibitions, "restrictions"),
            (result.conditions, "conditions"),
            (result.dates + result.deadlines, "timing"),
            (result.monetary_terms, "financial terms"),
            (result.legal_references, "legal or regulatory references"),
            (result.case_references, "judicial references"),
            (result.data_terms, "data or privacy matters"),
            (result.employment_terms, "employment matters"),
            (result.loan_terms, "loan or credit matters"),
            (result.property_terms, "property matters"),
            (result.dispute_terms, "dispute or enforcement matters"),
            (result.intellectual_property_terms, "intellectual property matters"),
        ]

        for values, label in mapping:
            if values:
                categories.append(label)

        categories = ClauseAnalysisService._unique(categories)

        if not categories:
            return (
                "No specific impact category was confidently "
                "identified by the current deterministic analysis."
            )

        return (
            "This provision contains "
            + ", ".join(categories)
            + " that may affect the relevant reader or parties."
        )

    # ================================================================
    # Recommendations
    # ================================================================

    @classmethod
    def _generate_recommendations(
        cls,
        result: ClauseAnalysis,
    ) -> list[str]:
        recommendations = []

        if result.obligations:
            recommendations.append(
                "Identify who is responsible for each obligation or duty."
            )

        if result.rights or result.permissions:
            recommendations.append(
                "Identify who receives each right, permission, or authority."
            )

        if result.prohibitions:
            recommendations.append(
                "Review the scope of each restriction and any exceptions."
            )

        if result.conditions or result.triggers:
            recommendations.append(
                "Identify the events or conditions that activate the provision."
            )

        if result.dates or result.deadlines or result.durations:
            recommendations.append(
                "Verify all dates, deadlines, notice periods, and durations."
            )

        if result.monetary_terms:
            recommendations.append(
                "Verify amounts, rates, fees, payment terms, and calculation methods."
            )

        if result.penalties:
            recommendations.append(
                "Check when penalties or financial consequences become applicable."
            )

        if result.legal_references:
            recommendations.append(
                "Verify the cited law, regulation, section, rule, or legal reference."
            )

        if result.case_references:
            recommendations.append(
                "Verify the referenced case, judgment, court decision, or proceeding."
            )

        if result.data_terms or result.privacy_terms:
            recommendations.append(
                "Check what data is collected, used, shared, stored, and retained."
            )

        if result.confidentiality_terms:
            recommendations.append(
                "Check what information is protected, permitted disclosures, and duration."
            )

        if result.loan_terms:
            recommendations.append(
                "Review principal, interest, repayment, default, security, and related conditions."
            )

        if result.employment_terms:
            recommendations.append(
                "Review duties, compensation, benefits, leave, notice, and employment conditions."
            )

        if result.property_terms:
            recommendations.append(
                "Review ownership, possession, property description, rent, and related conditions."
            )

        if result.intellectual_property_terms:
            recommendations.append(
                "Review ownership, licensing, permitted use, and restrictions on intellectual property."
            )

        if result.dispute_terms or result.jurisdiction:
            recommendations.append(
                "Review dispute procedures, jurisdiction, venue, and available remedies."
            )

        if result.risk_level in {"MEDIUM", "HIGH"}:
            recommendations.append(
                "Review this provision together with related provisions elsewhere in the document."
            )

        if not recommendations:
            recommendations.append(
                "Review this provision together with the surrounding document for context."
            )

        return cls._unique(recommendations)

    # ================================================================
    # Batch analysis
    # ================================================================

    @classmethod
    def analyze(cls, clause):
        return cls.analyze_clause(clause)

    @classmethod
    def analyze_clauses(
        cls,
        clauses,
    ) -> list[ClauseAnalysis]:
        return [
            cls.analyze_clause(clause)
            for clause in clauses
        ]
