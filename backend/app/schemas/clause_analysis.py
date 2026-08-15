from pydantic import BaseModel


class ClauseAnalysis(BaseModel):
    clause_id: str
    clause_number: str | None = None
    clause_type: str | None = None

    meaning: str | None = None

    parties: list[str] = []
    obligations: list[str] = []
    rights: list[str] = []
    deadlines: list[str] = []
    conditions: list[str] = []
    monetary_terms: list[str] = []

    risk_level: str | None = None


class ClauseAnalysisResponse(BaseModel):
    file_id: str
    analysis_count: int
    analyses: list[ClauseAnalysis]
